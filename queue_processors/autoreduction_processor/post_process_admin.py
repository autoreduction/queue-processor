# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
#!/usr/bin/env python
# pylint: disable=broad-except
# pylint: disable=bare-except

"""
Post Process Administrator. It kicks off cataloging and reduction jobs.
"""
import io
import logging
import sys
import traceback
import types

from sentry_sdk import init

from model.message.message import Message
from queue_processors.autoreduction_processor.autoreduction_logging_setup import logger
from queue_processors.autoreduction_processor.post_process_admin_utilities import \
    windows_to_linux_path
from queue_processors.autoreduction_processor.reduction_exceptions import SkippedRunException, \
    DatafileError, \
    ReductionScriptError
from queue_processors.autoreduction_processor.reduction_service import Datafile, ReductionScript, \
    ReductionDirectory, \
    TemporaryReductionDirectory, reduce
from queue_processors.autoreduction_processor.settings import MISC
from utils.clients.queue_client import QueueClient
from utils.settings import ACTIVEMQ_SETTINGS

init('http://4b7c7658e2204228ad1cfd640f478857@172.16.114.151:9000/1')


class PostProcessAdmin:
    """ Main class for the PostProcessAdmin """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, message, client):
        logger.debug("Message data: %s", message.serialize(limit_reduction_script=True))
        self.read_write_map = {"R": "read", "W": "write"}

        self.message = message
        self.client = client

        self.reduction_log_stream = io.StringIO()
        self.admin_log_stream = io.StringIO()

        try:
            self.data_file = windows_to_linux_path(self.validate_input('data'),
                                                   MISC["temp_root_directory"])
            self.facility = self.validate_input('facility')
            self.instrument = self.validate_input('instrument').upper()
            self.proposal = str(int(self.validate_input('rb_number')))  # Integer-string validation
            self.run_number = str(int(self.validate_input('run_number')))
            self.reduction_script = self.validate_input('reduction_script')
            self.reduction_arguments = self.validate_input('reduction_arguments')
        except ValueError:
            logger.info('JSON data error', exc_info=True)
            raise

    def validate_input(self, attribute):
        """
        Validates the input message
        :param attribute: attribute to validate
        :return: The value of the key or raise an exception if none
        """
        attribute_dict = self.message.__dict__
        if attribute in attribute_dict and attribute_dict[attribute] is not None:
            value = attribute_dict[attribute]
            logger.debug("%s: %s", attribute, str(value)[:50])
            return value
        raise ValueError('%s is missing' % attribute)

    def replace_variables(self, reduce_script):
        """
        We mock up the web_var module according to what's expected. The scripts want standard_vars
        and advanced_vars, e.g.
        https://github.com/mantidproject/mantid/blob/master/scripts/Inelastic/Direct/ReductionWrapper.py
        """

        def merge_dicts(dict_name):
            """
            Merge self.reduction_arguments[dictName] into reduce_script.web_var[dictName],
            overwriting any key that exists in both with the value from sourceDict.
            """

            def merge_dict_to_name(dictionary_name, source_dict):
                """ Merge the two dictionaries. """
                old_dict = {}
                if hasattr(reduce_script.web_var, dictionary_name):
                    old_dict = getattr(reduce_script.web_var, dictionary_name)
                else:
                    pass
                old_dict.update(source_dict)
                setattr(reduce_script.web_var, dictionary_name, old_dict)

            def ascii_encode(var):
                """ ASCII encode var. """
                return var.encode('ascii', 'ignore') if type(var).__name__ == "unicode" else var

            encoded_dict = {k: ascii_encode(v) for k, v in
                            self.reduction_arguments[dict_name].items()}
            merge_dict_to_name(dict_name, encoded_dict)

        if not hasattr(reduce_script, "web_var"):
            reduce_script.web_var = types.ModuleType("reduce_vars")
        merge_dicts("standard_vars")
        merge_dicts("advanced_vars")
        return reduce_script

    def send_reduction_message(self, message, amq_message):
        """Send/Update AMQ reduction message
        :param message: (str) amq reduction  status
        :param amq_message: (str) reduction status path
        """
        try:
            logger.debug("Calling: %s\n%s",
                         amq_message,
                         self.message.serialize(limit_reduction_script=True))
            self.client.send(amq_message, self.message)
            logger.info("Reduction: %s", message)

        except AttributeError:
            logger.debug("Failed to find send reduction message: %s", amq_message)

    def determine_reduction_status(self):
        """
        Determine which message type to log and send to AMQ, triggering exception if job failed
        """
        if self.message.message is not None:
            # This means an error has been produced somewhere
            try:
                if 'skip' in self.message.message.lower():
                    self.send_reduction_message(message="Skipped",
                                                amq_message=ACTIVEMQ_SETTINGS.reduction_skipped)
                else:
                    self.send_reduction_message(message="Error",
                                                amq_message=ACTIVEMQ_SETTINGS.reduction_error)
            except Exception as exp2:
                logger.info("Failed to send to queue! - %s - %s", exp2, repr(exp2))
            finally:
                logger.info("Reduction job failed")
        else:
            # Reduction has successfully completed
            self.send_reduction_message(message="Complete",
                                        amq_message=ACTIVEMQ_SETTINGS.reduction_complete)

    def reduce(self):
        """Start the reduction job."""
        self.message.software = self._get_mantid_version()

        try:
            # log and update AMQ message to reduction started
            self.send_reduction_message(message="started",
                                        amq_message=ACTIVEMQ_SETTINGS.reduction_started)

            if self.message.description is not None:
                logger.info("DESCRIPTION: %s", self.message.description)

            datafile = Datafile(self.data_file)
            reduction_script = ReductionScript(self.instrument)
            reduction_dir = ReductionDirectory(self.instrument, self.proposal, self.run_number)
            temp_dir = TemporaryReductionDirectory(self.proposal, self.run_number)
            reduce(reduction_dir, temp_dir, datafile, reduction_script, self.run_number,
                   self.reduction_log_stream)
            self.message.reduction_data = [str(reduction_dir.path)]

        except DatafileError as exp:
            logger.error("Problem reading datafile: %s", self.data_file)
            self.message.message = "REDUCTION Error: %s" % exp

        except SkippedRunException:
            logger.info("Run %s has been skipped on %s",
                        self.message.run_number, self.message.instrument)
            self.message.message = "Run has been skipped in script"

        except ReductionScriptError as exp:
            self.message.message = "REDUCTION Error: %s" % exp

        except Exception as exp:
            logger.error(traceback.format_exc())
            self.message.message = "REDUCTION Error: %s " % exp

        self.message.reduction_log = self.reduction_log_stream.getvalue()
        self.message.admin_log = self.admin_log_stream.getvalue()
        self.determine_reduction_status()  # Send AMQ reduce status message Skipped|Error|Complete

    @staticmethod
    def _get_mantid_version():
        """
        Attempt to get Mantid software version
        :return: (str) Mantid version or None if not found
        """
        if MISC["mantid_path"] not in sys.path:
            sys.path.append(MISC['mantid_path'])
        try:
            # pylint:disable=import-outside-toplevel
            import mantid
            return mantid.__version__
        except ImportError as excep:
            logger.error("Unable to discover Mantid version as: unable to import Mantid")
            logger.error(excep)
        return None


def main():
    """ Main method. """
    queue_client = QueueClient()
    try:
        logger.info("PostProcessAdmin Connecting to ActiveMQ")
        queue_client.connect()
        logger.info("PostProcessAdmin Successfully Connected to ActiveMQ")

        destination, data = sys.argv[1:3]  # pylint: disable=unbalanced-tuple-unpacking
        message = Message()
        message.populate(data)
        logger.info("destination: %s", destination)
        logger.info("message: %s", message.serialize(limit_reduction_script=True))

        try:
            post_proc = PostProcessAdmin(message, queue_client)
            log_stream_handler = logging.StreamHandler(post_proc.admin_log_stream)
            logger.addHandler(log_stream_handler)
            if destination == '/queue/ReductionPending':
                post_proc.reduce()

        except ValueError as exp:
            message.message = str(exp)  # Note: I believe this should be .message
            logger.info("Message data error: %s", message.serialize(limit_reduction_script=True))
            raise

        except Exception as exp:
            logger.info("PostProcessAdmin error: %s", str(exp))
            raise

        finally:
            try:
                logger.removeHandler(log_stream_handler)
            except:
                pass

    except Exception as exp:
        logger.info("Something went wrong: %s", str(exp))
        try:
            queue_client.send(ACTIVEMQ_SETTINGS.reduction_error, message)
            logger.info("Called %s ---- %s", ACTIVEMQ_SETTINGS.reduction_error,
                        message.serialize(limit_reduction_script=True))
        finally:
            sys.exit()


if __name__ == "__main__":  # pragma : no cover
    main()
