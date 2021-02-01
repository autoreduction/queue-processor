# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# !/usr/bin/env python
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

from model.message.message import Message
from queue_processors.queue_processor.reduction_runner.reduction_exceptions import (DatafileError, ReductionScriptError)
from queue_processors.queue_processor.reduction_runner.utilities import \
    windows_to_linux_path
from queue_processors.queue_processor.reduction_runner.reduction_service import (Datafile, ReductionDirectory,
                                                                                 ReductionScript,
                                                                                 TemporaryReductionDirectory, reduce)
from queue_processors.queue_processor.settings import (MANTID_PATH, TEMP_ROOT_DIRECTORY)

logger = logging.getLogger("reduction_runner")


class ReductionRunner:
    """ Main class for the ReductionRunner """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, message):
        self.read_write_map = {"R": "read", "W": "write"}
        self.message = message
        self.admin_log_stream = io.StringIO()
        try:
            self.data_file = windows_to_linux_path(self.validate_input('data'), TEMP_ROOT_DIRECTORY)
            self.facility = self.validate_input('facility')
            self.instrument = self.validate_input('instrument').upper()
            self.proposal = str(int(self.validate_input('rb_number')))  # Integer-string validation
            self.run_number = str(int(self.validate_input('run_number')))
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

    def reduce(self):
        """Start the reduction job."""
        self.message.software = self._get_mantid_version()

        try:
            # log and update AMQ message to reduction started
            if self.message.description is not None:
                logger.info("DESCRIPTION: %s", self.message.description)

            datafile = Datafile(self.data_file)
            reduction_script = ReductionScript(self.instrument)
            reduction_dir = ReductionDirectory(self.instrument, self.proposal, self.run_number)
            temp_dir = TemporaryReductionDirectory(self.proposal, self.run_number)
            reduction_log_stream = reduce(reduction_dir, temp_dir, datafile, reduction_script)
            self.message.reduction_log = reduction_log_stream.getvalue()
            self.message.reduction_data = str(reduction_dir.path)

        except DatafileError as exp:
            logger.error("Problem reading datafile: %s", self.data_file)
            self.message.message = "REDUCTION Error: %s" % exp

        except ReductionScriptError as exp:
            logger.error("Error encountered when running the reduction script: %s", self.data_file)
            self.message.message = "REDUCTION Error: %s" % exp

        except Exception as exp:
            logger.error(traceback.format_exc())
            self.message.message = "REDUCTION Error: %s " % exp

        self.message.admin_log = self.admin_log_stream.getvalue()

    @staticmethod
    def _get_mantid_version():
        """
        Attempt to get Mantid software version
        :return: (str) Mantid version or None if not found
        """
        if MANTID_PATH not in sys.path:
            sys.path.append(MANTID_PATH)
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
    data, temp_output_file = sys.argv[1], sys.argv[2]
    try:
        message = Message()
        message.populate(data)
    except Exception as exp:
        logger.error("Could not populate message from data: %s", str(exp))
        sys.exit(1)

    log_stream_handler = None
    try:
        reduction_runner = ReductionRunner(message)
        log_stream_handler = logging.StreamHandler(reduction_runner.admin_log_stream)
        logger.addHandler(log_stream_handler)
        reduction_runner.reduce()
        # write out the reduction message
        with open(temp_output_file, "w") as out_file:
            out_file.write(reduction_runner.message.serialize())

    except ValueError as exp:
        message.message = str(exp)
        logger.info("Message data error: %s", message.serialize(limit_reduction_script=True))
        raise

    except Exception as exp:
        logger.info("ReductionRunner error: %s", str(exp))
        raise

    finally:
        if log_stream_handler is not None:
            logger.removeHandler(log_stream_handler)


if __name__ == "__main__":  # pragma : no cover
    main()
