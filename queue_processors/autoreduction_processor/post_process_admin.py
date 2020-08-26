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
import sys
from pathlib import Path
import time
import types
import traceback
from contextlib import contextmanager
import importlib.util as imp

from sentry_sdk import init

# pylint:disable=no-name-in-module,import-error
from model.message.message import Message
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
        map(merge_dicts, ["standard_vars", "advanced_vars"])
        return reduce_script

    @staticmethod
    def _reduction_script_location(instrument_name):
        """ Returns the reduction script location. """
        return MISC["scripts_directory"] % instrument_name

    def _load_reduction_script(self, instrument_name):
        """ Returns the path of the reduction script for an instrument. """
        return os.path.join(self._reduction_script_location(instrument_name), 'reduce.py')

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

    def specify_instrument_directories(self,
                                       instrument_output_directory,
                                       no_run_number_directory,
                                       temporary_directory):
        """
        Specifies instrument directories, including removal of run_number folder
        if excitations instrument
        :param instrument_output_directory: (str) Ceph directory using instrument, proposal, run no
        :param no_run_number_directory: (bool) Determine whether or not to remove run no from dir
        :param temporary_directory: (str) Temp directory location (root)
        :return (str) Directories where Autoreduction should output
        """

        directory_list = [i for i in instrument_output_directory.split('/') if i]

        if directory_list[-1] != f"{self.run_number}":
            return ValueError("directory does not follow expected format "
                              "(instrument/RB_no/run_number) \n"
                              "format: \n"
                              "%s", instrument_output_directory)

        if no_run_number_directory is True:
            # Remove the run number folder at the end
            remove_run_number_directory = instrument_output_directory.rfind('/') + 1
            instrument_output_directory = instrument_output_directory[:remove_run_number_directory]

        # Specify directories where autoreduction output will go
        return temporary_directory + instrument_output_directory

    def create_log_path(self, file_name_with_extension, log_directory):
        """
        Create log file and place in reduction_log_directory
        :param file_name_with_extension: (string) file name and extension type
        :param log_directory: (str) log directory path
        :return: (str) log file path
        """
        log_and_err_name = f"RB_{self.proposal}_Run_{self.run_number}_"
        return Path(log_directory, log_and_err_name + file_name_with_extension)

    def verify_directory_access(self, location, access_type):
        """
        Tests directory access for a given location and type of access
        :param location: (str) directory location
        :param access_type: (str) type of access to location e.g "W", "R"
        """
        if not os.access(location, getattr(sys.modules[os.__name__], f"{access_type}_OK")):
            if not os.access(location, os.F_OK):
                problem = "does not exist"
            else:
                problem = "no %s access", access_type
            raise Exception("Couldn't %s %s  -  %s" % (self.read_write_map[access_type],
                                                       location,
                                                       problem))
        logger.info("Successful %s access to %s", self.read_write_map[access_type], location)
        return True

    def write_and_readability_checks(self, directory_list, read_write):
        """
        Check a list of N directories for user specified type of access (read/write)
        :param directory_list: (list) directory list
        :param read_write: (str) Read=R, Write=W
        :return Error (Exception or ValueError) when something goes wrong
        """
        read_write = read_write.upper()

        try:
            assert self.read_write_map[read_write]  # raises key error if file input not expected

            # Verify directory access
            for location in directory_list:
                if not self.verify_directory_access(location=location, access_type=read_write):
                    raise OSError
            return True

        except KeyError as exp:
            raise KeyError("Invalid read or write input: %s read_write argument must be either"
                           " 'R' or 'W'" % read_write) from exp
        except OSError as exp:
            # If we can't access now, abort the run, and tell the server to re-run at a later time.
            self.message.message = "Permission error: %s" % exp
            self.message.retry_in = 6 * 60 * 60  # 6 hours
            logger.error(traceback.format_exc())
            raise exp

    @staticmethod
    def create_directory(list_of_paths):
        """
        Creates directory that should exist if it does not already.
        :param list_of_paths: (list) directories that should be writeable
        """

        # try to make directories which should exist
        for path in filter(lambda p: not os.path.isdir(p), list_of_paths):
            logger.info("path %s does not exist. \n "
                        "Attempting to make path.", path)
            os.makedirs(path)

    def create_final_result_and_log_directory(self, temporary_root_directory, reduce_dir):
        """
        Create final result and final log directories, stripping temporary path off of the
        front of temporary directories
        :param temporary_root_directory: (str) temporary root directory
        :param reduce_dir: (str) final reduce directory
        :return (tuple) - (str, str) final result and final log directory paths
        """
        # validate dir before slicing
        if reduce_dir.startswith(temporary_root_directory):
            result_directory = reduce_dir[len(temporary_root_directory):]
        else:
            return ValueError("The reduce directory does not start by following the expected "
                              "format: %s \n", temporary_root_directory)

        final_result_directory = self._new_reduction_data_path(result_directory)
        final_log_directory = append_path(final_result_directory, ['reduction_log'])

        logger.info("Final Result Directory = %s", final_result_directory)
        logger.info("Final log directory: %s", final_log_directory)

        return final_result_directory, final_log_directory

    def check_for_skipped_runs(self, skip_numbers, reduce_script, reduce_result_dir):
        """Check for skipped runs, updating message if run is skipped
        :param skip_numbers: (list) List of skipped run numbers
        :param reduce_script: (module) Reduction script as module
        :param reduce_result_dir: (str) Reduction result directory
        :return (str/list) Reduction output directories
        """
        if self.message.run_number not in skip_numbers:
            reduce_script = self.replace_variables(reduce_script)
            with TimeOut(MISC["script_timeout"]):
                out_directories = reduce_script.main(input_file=str(self.data_file),
                                                     output_dir=str(reduce_result_dir))
        else:
            self.message.message = "Run has been skipped in script"
        return out_directories

    def reduction_as_module(self, reduce_result_dir):
        """
        Load reduction script as module
        This works as long as reduce.py makes no assumption that it is in the same directory
        as reduce_vars, i.e. - Either it does not import it at all, or adds its location
        to os.path explicitly.
        :param reduce_result_dir: (str) Reduce result directory
        :return: (str/list) output directory
        """
        sys.path.append(MISC["mantid_path"])
        reduce_script_location = self._load_reduction_script(self.instrument)
        spec = imp.spec_from_file_location('reducescript', reduce_script_location)
        reduce_script = imp.module_from_spec(spec)
        spec.loader.exec_module(reduce_script)

        try:
            skip_numbers = reduce_script.SKIP_RUNS
        except:
            skip_numbers = []

        return self.check_for_skipped_runs(skip_numbers=skip_numbers,
                                           reduce_script=reduce_script,
                                           reduce_result_dir=reduce_result_dir)

    def validate_reduction_as_module(self, script_out, mantid_log, reduce_result, final_result):
        """
        Validate and Load reduction script as module and Add Mantid path to system path so we
        can use Mantid to run the user's script.
        :param script_out: (str) script out path
        :param mantid_log: (str) mantid log path
        :param reduce_result: (str) Directories where Autoreduction should output
        :param final_result: (str) final result path
        :return: ((str/list)/Exception) output directory or exception
        """
        try:
            with channels_redirected(script_out, mantid_log, self.reduction_log_stream):

                out_directories = self.reduction_as_module(reduce_result)
                return out_directories

        except Exception as exp:
            with open(script_out, "a") as fle:
                fle.writelines(str(exp) + "\n")
                fle.write(traceback.format_exc())
            self.copy_temp_directory(reduce_result, final_result)
            self.delete_temp_directory(reduce_result)

            # Parent except block will discard exception type, so format the type as a string
            if 'skip' in str(exp).lower():
                raise SkippedRunException(exp) from exp
            error_str = f"Error in user reduction script: {type(exp).__name__} - {exp}"
            logger.error(traceback.format_exc())
            return Exception(error_str)

    def additional_save_directories_check(self, out_directories, reduce_result):
        """
        If the reduce script specified some additional save directories, copy to there first
        :param out_directories: (str/list) output directories
        :param reduce_result: (str) reduce result directory
        """

        if out_directories:
            if isinstance(out_directories, str):
                self.copy_temp_directory(reduce_result, out_directories)
            elif isinstance(out_directories, list):
                for out_dir in out_directories:
                    if isinstance(out_dir, str):
                        self.copy_temp_directory(reduce_result, out_dir)
                    else:
                        self.log_and_message(f"Optional output directories of "
                                             f"reduce.py must be strings: {out_dir}")
            else:
                self.log_and_message(f"Optional output directories of reduce.py must be a string "
                                     f"or list of stings: {out_directories}")

    # pylint:disable=too-many-nested-blocks
    def reduce(self):
        """Start the reduction job."""
        # pylint: disable=too-many-nested-blocks
        self.message.software = self._get_mantid_version()

        try:
            # log and update AMQ message to reduction started
            self.send_reduction_message(message="started",
                                        amq_message=ACTIVEMQ_SETTINGS.reduction_started)

            # Specify instrument directories - if excitation instrument remove run_number from dir
            no_run_number_directory = False
            if self.instrument in MISC["excitation_instruments"]:
                no_run_number_directory = True

            instrument_output_directory = MISC["ceph_directory"] % (self.instrument,
                                                                    self.proposal,
                                                                    self.run_number)

            reduce_result_dir = self.specify_instrument_directories(
                instrument_output_directory=instrument_output_directory,
                no_run_number_directory=no_run_number_directory,
                temporary_directory=MISC["temp_root_directory"])

            if self.message.description is not None:
                logger.info("DESCRIPTION: %s", self.message.description)
            log_dir = reduce_result_dir + "/reduction_log/"

            # strip temp path off front of the temp directory to get the final archives directory
            final_result_dir, final_log_dir = self.create_final_result_and_log_directory(
                temporary_root_directory=MISC["temp_root_directory"],
                reduce_dir=reduce_result_dir)

            # Test path exists and access
            should_be_writeable = [reduce_result_dir, log_dir, final_result_dir, final_log_dir]
            should_be_readable = [self.data_file]

            # Try to create directory if does not exist
            self.create_directory(should_be_writeable)

            # Check permissions of paths which should be writeable and readable
            self.write_and_readability_checks(directory_list=should_be_writeable, read_write="W")
            self.write_and_readability_checks(directory_list=should_be_readable, read_write="R")

            self.message.reduction_data = []

            logger.info("----------------")
            logger.info("Reduction script: %s ...", self.reduction_script[:50])
            logger.info("Result dir: %s", reduce_result_dir)
            logger.info("Log dir: %s", log_dir)
            logger.info("Out log: %s",
                        self.create_log_path(file_name_with_extension="Script.out",
                                             log_directory=log_dir))
            logger.info("Datafile: %s", self.data_file)
            logger.info("----------------")

            logger.info("Reduction subprocess started.")
            logger.info(reduce_result_dir)
            out_directories = None

            # Create script out and mantid log paths
            script_out = self.create_log_path(file_name_with_extension="Script.out",
                                              log_directory=log_dir)
            mantid_log = self.create_log_path(file_name_with_extension="Mantid.log",
                                              log_directory=log_dir)

            # Load reduction script as module and validate
            out_directories = self.validate_reduction_as_module(script_out=script_out,
                                                                mantid_log=mantid_log,
                                                                reduce_result=reduce_result_dir,
                                                                final_result=final_result_dir)

            self.copy_temp_directory(reduce_result_dir, final_result_dir)

            # Copy to additional directories if present in reduce script
            self.additional_save_directories_check(out_directories=out_directories,
                                                   reduce_result=reduce_result_dir)

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

    def _new_reduction_data_path(self, path):
        """
        Creates a pathname for the reduction data, factoring in existing run data.
        :param path: Base path for the run data (should follow convention, without version number)
        :return: A pathname for the new reduction data
        """
        logger.info("_new_reduction_data_path argument: %s", path)
        # if there is an 'overwrite' key/member with a None/False value
        if not self.message.overwrite:
            if os.path.isdir(path):  # if the given path already exists..
                contents = os.listdir(path)
                highest_vers = -1
                for item in contents:  # ..for every item, if it's a dir and a int..
                    if os.path.isdir(os.path.join(path, item)):
                        try:  # ..store the highest int
                            vers = int(item)
                            highest_vers = max(highest_vers, vers)
                        except ValueError:
                            pass
                this_vers = highest_vers + 1
                return append_path(path, [str(this_vers)])
        # (else) if no overwrite, overwrite true, or the path doesn't exist: return version 0 path
        return append_path(path, "0")

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
