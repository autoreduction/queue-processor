# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
#!/usr/bin/env python
# pylint: disable=too-many-branches
# pylint: disable=broad-except
# pylint: disable=bare-except
# pylint: disable=too-many-statements
# pylint: disable=too-many-locals

"""
Post Process Administrator. It kicks off cataloging and reduction jobs.
"""
import io
import errno
import logging
import os
import shutil
import socket
import sys
import time
import types
import traceback
from contextlib import contextmanager
import importlib.util as imp

from sentry_sdk import init

# pylint:disable=no-name-in-module,import-error
from message.job import Message
from paths.path_manipulation import append_path
from queue_processors.autoreduction_processor.settings import MISC
from queue_processors.autoreduction_processor.autoreduction_logging_setup import logger
from queue_processors.autoreduction_processor.timeout import TimeOut
from utils.clients.queue_client import QueueClient
from utils.settings import ACTIVEMQ_SETTINGS

init('http://4b7c7658e2204228ad1cfd640f478857@172.16.114.151:9000/1')


class SkippedRunException(Exception):
    """
    Exception for runs that have been skipped
    Note: this is currently only the case for EnginX Event mode runs at ISIS
    """


@contextmanager
def channels_redirected(out_file, err_file, out_stream):
    """
    This context manager copies the file descriptor(fd) of stdout and stderr to the files given in
    out_file and err_file respectively. The fd is at the C level and so picks up data sent via
    Mantid. Both output streams are additionally also sent to out_stream.
    """
    old_stdout, old_stderr = sys.stdout, sys.stderr

    class MultipleChannels:
        # pylint: disable=expression-not-assigned
        """ Behaves like a stream object, but outputs to multiple streams."""
        def __init__(self, *streams):
            self.streams = streams

        def write(self, stream_message):
            """ Write to steams. """
            [stream.write(stream_message) for stream in self.streams]

        def flush(self):
            """ Flush streams. """
            [stream.flush() for stream in self.streams]

    def _redirect_channels(output_file, error_file):
        """ Redirect channels? """
        sys.stdout.flush(), sys.stderr.flush()  # pylint: disable=expression-not-assigned
        sys.stdout, sys.stderr = output_file, error_file

    with open(out_file, 'w') as out, open(err_file, 'w') as err:
        _redirect_channels(MultipleChannels(out, out_stream), MultipleChannels(err, out_stream))
        try:
            # allow code to be run with the redirected channels
            yield
        finally:
            _redirect_channels(old_stdout, old_stderr)  # restore stderr.


def windows_to_linux_path(path, temp_root_directory):
    """ Convert windows path to linux path. """
    # '\\isis\inst$\' maps to '/isis/'
    path = path.replace('\\\\isis\\inst$\\', '/isis/')
    path = path.replace('\\\\autoreduce\\data\\', temp_root_directory + '/data/')
    path = path.replace('\\', '/')
    return path


# def prettify(data):
#     """ Make dictionary pretty for printing. """
#     # Note: Only used for debug statements. Functionality added to Message.serialize
#     if type(data).__name__ == "str":
#         data_dict = json.loads(data)
#     else:
#         data_dict = data.copy()
#
#     if "reduction_script" in data_dict:
#         data_dict["reduction_script"] = data_dict["reduction_script"][:50]
#     return json.dumps(data_dict)


class PostProcessAdmin:
    """ Main class for the PostProcessAdmin """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, message, client):
        logger.debug("Message data: %s", message.serialize(limit_reduction_script=True))
        # Note: "information" isn't a Message attribute so is not accepted by Message.
        #   Do we want to store this?
        # data["information"] = socket.gethostname()

        self.message = message
        attributes_to_check = ['data', 'facility', 'instrument', 'rb_number',
                               'run_number', 'reduction_script', 'reduction_arguments']
        self.check_message_attributes_populated(attributes_to_check)

        # Note: might want to remove all of the below, use the message throughout code instead
        self.data_file = windows_to_linux_path(self.message.data,
                                               MISC["temp_root_directory"])
        self.facility = self.message.facility
        self.instrument = self.message.instrument.upper()
        self.proposal = str(int(self.message.rb_number))    # Note: This casting seems redundant?
        self.run_number = str(int(self.message.run_number))
        self.reduction_script = self.message.reduction_script
        self.reduction_arguments = self.message.reduction_arguments

        self.client = client

        self.reduction_log_stream = io.StringIO()
        self.admin_log_stream = io.StringIO()

        # try:
        #     self.data_file = windows_to_linux_path(self.validate_input('data'),
        #                                            MISC["temp_root_directory"])
        #     self.facility = self.validate_input('facility')
        #     self.instrument = self.validate_input('instrument').upper()
        #     self.proposal = str(int(self.validate_input('rb_number')))
        #     self.run_number = str(int(self.validate_input('run_number')))
        #     self.reduction_script = self.validate_input('reduction_script')
        #     self.reduction_arguments = self.validate_input('reduction_arguments')
        # except ValueError:
        #     logger.info('JSON data error', exc_info=True)
        #     raise

    # def validate_input(self, key):
    #     """
    #     Validates the input dictionary
    #     :param key: key to search for
    #     :return: The value of the key or raise an exception if none
    #     """
    #     if key in self.data:
    #         value = self.data[key]
    #         logger.debug("%s: %s", key, str(value)[:50])
    #         return value
    #     raise ValueError('%s is missing' % key)

    def check_message_attributes_populated(self, attributes):
        attribute_dict = self.message.__dict__
        for attrib in attributes:
            if attribute_dict[attrib] is None:
                return False
        return True

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
        map(merge_dicts, ["standard_vars", "advanced_vars"])
        return reduce_script

    @staticmethod
    def _reduction_script_location(instrument_name):
        """ Returns the reduction script location. """
        return MISC["scripts_directory"] % instrument_name

    def _load_reduction_script(self, instrument_name):
        """ Returns the path of the reduction script for an instrument. """
        return os.path.join(self._reduction_script_location(instrument_name), 'reduce.py')

    def reduce(self):
        """ Start the reduction job.  """
        # pylint: disable=too-many-nested-blocks
        logger.info("reduce started")
        try:
            logger.debug("Calling: %s\n%s",
                         ACTIVEMQ_SETTINGS.reduction_started,
                         self.message.serialize(limit_reduction_script=True))
            self.client.send(ACTIVEMQ_SETTINGS.reduction_started, self.message)

            # Specify instrument directory
            instrument_output_dir = MISC["ceph_directory"] % (self.instrument,
                                                              self.proposal,
                                                              self.run_number)

            if self.instrument in MISC["excitation_instruments"]:
                # Excitations would like to remove the run number folder at the end
                instrument_output_dir = instrument_output_dir[:instrument_output_dir.rfind('/') + 1]

            # Specify directories where autoreduction output will go
            reduce_result_dir = MISC["temp_root_directory"] + instrument_output_dir

            if self.message.description is not None:
                logger.info("DESCRIPTION: %s", self.message.description)

            log_dir = reduce_result_dir + "/reduction_log/"
            log_and_err_name = "RB" + self.proposal + "Run" + self.run_number
            script_out = os.path.join(log_dir, log_and_err_name + "Script.out")
            mantid_log = os.path.join(log_dir, log_and_err_name + "Mantid.log")

            # strip the temp path off the front of the temp directory to get the final archives
            # directory.
            final_result_dir = reduce_result_dir[len(MISC["temp_root_directory"]):]
            final_log_dir = log_dir[len(MISC["temp_root_directory"]):]

            final_result_dir = self._new_reduction_data_path(final_result_dir)
            final_log_dir = append_path(final_result_dir, ['reduction_log'])

            logger.info('Final Result Directory = %s', final_result_dir)
            logger.info('Final Log Directory = %s', final_log_dir)

            # test for access to result paths
            try:
                should_be_writable = [reduce_result_dir, log_dir, final_result_dir, final_log_dir]
                should_be_readable = [self.data_file]

                # try to make directories which should exist
                for path in filter(lambda p: not os.path.isdir(p), should_be_writable):
                    os.makedirs(path)

                for location in should_be_writable:
                    if not os.access(location, os.W_OK):
                        if not os.access(location, os.F_OK):
                            problem = "does not exist"
                        else:
                            problem = "no write access"
                        raise Exception("Couldn't write to %s  -  %s" % (location, problem))

                for location in should_be_readable:
                    if not os.access(location, os.R_OK):
                        if not os.access(location, os.F_OK):
                            problem = "does not exist"
                        else:
                            problem = "no read access"
                        raise Exception("Couldn't read %s  -  %s" % (location, problem))

            except Exception as exp:
                # if we can't access now, we should abort the run, and tell the server that it
                # should be re-run at a later time.
                self.message.message = "Permission error: %s" % exp
                self.message.retry_in = 6 * 60 * 60  # 6 hours
                logger.error(traceback.format_exc())
                raise exp

            self.message.reduction_data = []

            logger.info("----------------")
            logger.info("Reduction script: %s ...", self.reduction_script[:50])
            logger.info("Result dir: %s", reduce_result_dir)
            logger.info("Log dir: %s", log_dir)
            logger.info("Out log: %s", script_out)
            logger.info("Datafile: %s", self.data_file)
            logger.info("----------------")

            logger.info("Reduction subprocess started.")
            logger.info(reduce_result_dir)
            out_directories = None

            try:
                with channels_redirected(script_out, mantid_log, self.reduction_log_stream):
                    # Load reduction script as a module. This works as long as reduce.py makes no
                    # assumption that it is in the same directory as reduce_vars, i.e., either it
                    # does not import it at all, or adds its location to os.path explicitly.

                    # Add Mantid path to system path so we can use Mantid to run the user's script
                    sys.path.append(MISC["mantid_path"])
                    reduce_script_location = self._load_reduction_script(self.instrument)
                    spec = imp.spec_from_file_location('reducescript', reduce_script_location)
                    reduce_script = imp.module_from_spec(spec)
                    spec.loader.exec_module(reduce_script)

                    try:
                        skip_numbers = reduce_script.SKIP_RUNS
                    except:
                        skip_numbers = []
                    if self.message.run_number not in skip_numbers:
                        reduce_script = self.replace_variables(reduce_script)
                        with TimeOut(MISC["script_timeout"]):
                            out_directories = reduce_script.main(input_file=str(self.data_file),
                                                                 output_dir=str(reduce_result_dir))
                    else:
                        self.message.message = "Run has been skipped in script"
            except Exception as exp:
                with open(script_out, "a") as fle:
                    fle.writelines(str(exp) + "\n")
                    fle.write(traceback.format_exc())
                self.copy_temp_directory(reduce_result_dir, final_result_dir)
                self.delete_temp_directory(reduce_result_dir)

                # Parent except block will discard exception type, so format the type as a string
                if 'skip' in str(exp).lower():
                    raise SkippedRunException(exp)
                error_str = "Error in user reduction script: %s - %s" % (type(exp).__name__, exp)
                logger.error(traceback.format_exc())
                raise Exception(error_str)

            logger.info("Reduction subprocess completed.")
            logger.info("Additional save directories: %s", out_directories)

            self.copy_temp_directory(reduce_result_dir, final_result_dir)

            # If the reduce script specified some additional save directories, copy to there first
            if out_directories:
                if isinstance(out_directories, str):
                    self.copy_temp_directory(reduce_result_dir, out_directories)
                elif isinstance(out_directories, list):
                    for out_dir in out_directories:
                        if isinstance(out_dir, str):
                            self.copy_temp_directory(reduce_result_dir, out_dir)
                        else:
                            self.log_and_message(
                                "Optional output directories of reduce.py must be strings: %s" %
                                out_dir)
                else:
                    self.log_and_message("Optional output directories of reduce.py must be a string"
                                         " or list of stings: %s" % out_directories)

            # no longer a need for the temp directory used for storing of reduction results
            self.delete_temp_directory(reduce_result_dir)

        except SkippedRunException as skip_exception:
            logger.info("Run %s has been skipped on %s",
                        self.message.run_number, self.message.instrument)
            self.message.message = "Reduction Skipped: %s" % str(skip_exception)
        except Exception as exp:
            logger.error(traceback.format_exc())
            self.message.message = "REDUCTION Error: %s " % exp

        self.message.reduction_log = self.reduction_log_stream.getvalue()
        self.message.admin_log = self.admin_log_stream.getvalue()

        if self.message.message is not None:
            # This means an error has been produced somewhere
            try:
                if 'skip' in self.message.message.lower():
                    self._send_message_and_log(ACTIVEMQ_SETTINGS.reduction_skipped)
                else:
                    self._send_message_and_log(ACTIVEMQ_SETTINGS.reduction_error)

            except Exception as exp2:
                logger.info("Failed to send to queue! - %s - %s", exp2, repr(exp2))
            finally:
                logger.info("Reduction job failed")

        else:
            # reduction has successfully completed
            self.client.send(ACTIVEMQ_SETTINGS.reduction_complete, self.message)
            logger.info("Calling: %s\n%s",
                        ACTIVEMQ_SETTINGS.reduction_complete,
                        self.message.serialize(limit_reduction_script=True))
            logger.info("Reduction job successfully complete")

    def _new_reduction_data_path(self, path):
        """
        Creates a pathname for the reduction data, factoring in existing run data.
        :param path: Base path for the run data (should follow convention, without version number)
        :return: A pathname for the new reduction data
        """
        logger.info("_new_reduction_data_path argument: %s", path)
        # if there is an 'overwrite' key/member with a None/False value
        if not self.message.overwrite:
            if os.path.isdir(path):           # if the given path already exists..
                contents = os.listdir(path)
                highest_vers = -1
                for item in contents:         # ..for every item, if it's a dir and a int..
                    if os.path.isdir(os.path.join(path, item)):
                        try:                  # ..store the highest int
                            vers = int(item)
                            highest_vers = max(highest_vers, vers)
                        except ValueError:
                            pass
                this_vers = highest_vers + 1
                return append_path(path, [str(this_vers)])
        # (else) if no overwrite, overwrite true, or the path doesn't exist: return version 0 path
        return append_path(path, "0")

    def _send_message_and_log(self, destination):
        """ Send reduction run to error. """
        logger.info("\nCalling " + destination + " --- " + self.message.serialize(limit_reduction_script=True))
        self.client.send(destination, self.message)

    def copy_temp_directory(self, temp_result_dir, copy_destination):
        """
        Method that copies the temporary files held in results_directory to CEPH/archive, replacing
        old data if it exists.

        EXCITATION instrument are treated as a special case because they're done with run number
        sub-folders.
        """
        if os.path.isdir(copy_destination) \
                and self.instrument not in MISC["excitation_instruments"]:
            self._remove_directory(copy_destination)

        self.message.reduction_data.append(copy_destination)
        logger.info("Moving %s to %s", temp_result_dir, copy_destination)
        try:
            self._copy_tree(temp_result_dir, copy_destination)
        except Exception as exp:
            self.log_and_message("Unable to copy to %s - %s" % (copy_destination, exp))

    @staticmethod
    def delete_temp_directory(temp_result_dir):
        """ Remove temporary working directory """
        logger.info("Remove temp dir %s", temp_result_dir)
        try:
            shutil.rmtree(temp_result_dir, ignore_errors=True)
        except:
            logger.info("Unable to remove temporary directory - %s", temp_result_dir)

    def log_and_message(self, msg):
        """ Helper function to add text to the outgoing activemq message and to the info logs """
        logger.info(msg)
        if self.message.message == "" or self.message.message is None:
            # Only send back first message as there is a char limit
            self.message.message = msg

    def _remove_with_wait(self, remove_folder, full_path):
        """ Removes a folder or file and waits for it to be removed. """
        file_deleted = False
        for sleep in [0, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20]:
            try:
                if remove_folder:
                    os.removedirs(full_path)
                else:
                    if os.path.isfile(full_path):
                        os.remove(full_path)
                        file_deleted = True
                    elif sleep == 20:
                        logger.warning("Unable to delete file %s, file could not be found",
                                       full_path)
                    elif file_deleted is True:
                        logger.debug("file %s has been successfully deleted",
                                     full_path)
                        break
            except OSError as exp:
                if exp.errno == errno.ENOENT:
                    # File has been deleted
                    break
            time.sleep(sleep)
        else:
            self.log_and_message("Failed to delete %s" % full_path)

    def _copy_tree(self, source, dest):
        """ Copy directory tree. """
        if not os.path.exists(dest):
            os.makedirs(dest)
        for item in os.listdir(source):
            src_path = os.path.join(source, item)
            dst_path = os.path.join(dest, item)
            if os.path.isdir(src_path):
                self._copy_tree(src_path, dst_path)
            elif not os.path.exists(dst_path) or \
                                    os.stat(src_path).st_mtime - os.stat(dst_path).st_mtime > 1:
                shutil.copyfile(src_path, dst_path)

    def _remove_directory(self, directory):
        """
        Helper function to remove a directory. shutil.rmtree cannot be used as it is not robust
        enough when folders are open over the network.
        """
        try:
            for target_file in os.listdir(directory):
                full_path = os.path.join(directory, target_file)
                if os.path.isdir(full_path):
                    self._remove_directory(full_path)
                else:
                    if os.path.isfile(full_path):
                        self._remove_with_wait(False, full_path)
                    else:
                        logger.warning("Unable to find file %s.", full_path)
            self._remove_with_wait(True, directory)
        except Exception as exp:
            self.log_and_message("Unable to remove existing directory %s - %s" % (directory, exp))


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
            message.error = str(exp)  # Note: I believe this should be .message
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
            logger.info("Called %s ---- %s", ACTIVEMQ_SETTINGS.reduction_error, message.serialize(limit_reduction_script=True))
        finally:
            sys.exit()


if __name__ == "__main__":  # pragma : no cover
    main()
