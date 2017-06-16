#!/usr/bin/env python
"""
Post Process Administrator. It kicks off cataloging and reduction jobs.
"""
import json
import socket
import os
import sys
import time
import shutil
import imp
import stomp
import re
import errno
import traceback
import logging
import cStringIO
from contextlib import contextmanager
from autoreduction_logging_setup import logger
from settings import ACTIVEMQ, MISC


@contextmanager
def channels_redirected(out_file, err_file, out_stream):
    """
    This context manager copies the file descriptor(fd) of stdout and stderr to the files given in out_file and err_file
    respectively. The fd is at the C level and so picks up data sent via Mantid. Both output streams are additionally
    also sent to out_stream.
    """
    old_stdout, old_stderr = sys.stdout, sys.stderr

    # Behaves like a stream object, but outputs to multiple streams.
    class MultipleChannels(object):
        def __init__(self, *streams):
            self.streams = streams

        def write(self, stream_message):
            [stream.write(stream_message) for stream in self.streams]

        def flush(self):
            [stream.flush() for stream in self.streams]

    def _redirect_channels(output_file, error_file):
        sys.stdout.flush(), sys.stderr.flush()
        sys.stdout, sys.stderr = output_file, error_file

    with open(out_file, 'w') as out, open(err_file, 'w') as err:
        _redirect_channels(MultipleChannels(out, out_stream), MultipleChannels(err, out_stream))
        try:
            # allow code to be run with the redirected channels
            yield
        finally:
            _redirect_channels(old_stdout, old_stderr)  # restore stderr.


def linux_to_windows_path(path):
    path = path.replace('/', '\\')
    # '/isis/' maps to '\\isis\inst$\'
    path = path.replace('\\isis\\', '\\\\isis\\inst$\\')
    return path


def windows_to_linux_path(path, temp_root_directory):
    # '\\isis\inst$\' maps to '/isis/'
    path = path.replace('\\\\isis\\inst$\\', '/isis/')
    path = path.replace('\\\\autoreduce\\data\\', temp_root_directory+'/data/')
    path = path.replace('\\', '/')
    return path


def prettify(data):
    if type(data).__name__ == "str":
        data_dict = json.loads(data)
    else:
        data_dict = data.copy()
        
    if "reduction_script" in data_dict:
        data_dict["reduction_script"] = data_dict["reduction_script"][:50]
    return json.dumps(data_dict)


class PostProcessAdmin:
    def __init__(self, data, connection):
        logger.debug("json data: " + prettify(data))
        data["information"] = socket.gethostname()
        self.data = data
        self.client = connection
        
        self.reduction_log_stream = cStringIO.StringIO()
        self.admin_log_stream = cStringIO.StringIO()

        try:
            if 'data' in data:
                self.data_file = windows_to_linux_path(str(data['data']), MISC["temp_root_directory"])
                logger.debug("data_file: %s" % self.data_file)
            else:
                raise ValueError("data is missing")

            if 'facility' in data:
                self.facility = str(data['facility']).upper()
                logger.debug("facility: %s" % self.facility)
            else: 
                raise ValueError("facility is missing")

            if 'instrument' in data:
                self.instrument = str(data['instrument']).upper()
                logger.debug("instrument: %s" % self.instrument)
            else:
                raise ValueError("instrument is missing")

            if 'rb_number' in data:
                self.proposal = str(data['rb_number']).upper()
                logger.debug("rb_number: %s" % self.proposal)
            else:
                raise ValueError("rb_number is missing")
                
            if 'run_number' in data:
                self.run_number = str(int(data['run_number']))  # Cast to int to remove trailing zeros
                logger.debug("run_number: %s" % str(self.run_number))
            else:
                raise ValueError("run_number is missing")
                
            if 'reduction_script' in data:
                self.reduction_script = data['reduction_script']
                logger.debug("reduction_script: %s ..." % self.reduction_script[:50])
            else:
                raise ValueError("reduction_script is missing")
                
            if 'reduction_arguments' in data:
                self.reduction_arguments = data['reduction_arguments']
                logger.debug("reduction_arguments: %s" % self.reduction_arguments)
            else:
                raise ValueError("reduction_arguments is missing")

        except ValueError:
            logger.info('JSON data error', exc_info=True)
            raise

    @staticmethod
    def parse_input_variable(default, value):
        var_type = type(default)
        if var_type.__name__ == "str":
            return str(value)
        if var_type.__name__ == "int":
            return int(value)
        if var_type.__name__ == "list":
            return value.split(',')
        if var_type.__name__ == "bool":
            return value.lower() is 'true'
        if var_type.__name__ == "float":
            return float(value)

    def replace_variables(self, reduce_script):
        """
        We mock up the web_var module according to what's expected. The scripts want standard_vars and advanced_vars,
        e.g. https://github.com/mantidproject/mantid/blob/master/scripts/Inelastic/Direct/ReductionWrapper.py
        """
        def merge_dicts(dict_name):
            """
            Merge self.reduction_arguments[dictName] into reduce_script.web_var[dictName],
            overwriting any key that exists in both with the value from sourceDict.
            """
            def merge_dict_to_name(dictionary_name, source_dict):
                old_dict = []
                if hasattr(reduce_script.web_var, dictionary_name):
                    old_dict = getattr(reduce_script.web_var, dictionary_name)
                else:
                    pass
                old_dict.update(source_dict)
                setattr(reduce_script.web_var, dictionary_name, old_dict)

            def ascii_encode(var):
                return var.encode('ascii', 'ignore') if type(var).__name__ == "unicode" else var
            
            encoded_dict = {k: ascii_encode(v) for k, v in self.reduction_arguments[dict_name].items()}
            merge_dict_to_name(dict_name, encoded_dict)
            
        if not hasattr(reduce_script, "web_var"):
            reduce_script.web_var = imp.new_module("reduce_vars")
        map(merge_dicts, ["standard_vars", "advanced_vars"])
        return reduce_script

    @staticmethod
    def _reduction_script_location(instrument_name):
        return MISC["scripts_directory"] % instrument_name

    def _load_reduction_script(self, instrument_name):
        return os.path.join(self._reduction_script_location(instrument_name), 'reduce.py')

    def reduce(self):
        try:     
        
            logger.debug("Calling: " + ACTIVEMQ['reduction_started'] + "\n" + prettify(self.data))
            self.client.send(ACTIVEMQ['reduction_started'], json.dumps(self.data))

            # Specify instrument directory
            cycle = re.match(r'.*cycle_(\d\d_\d).*', self.data_file.lower()).group(1)
            if self.instrument in (MISC["ceph_instruments"] + MISC["excitation_instruments"]):

                instrument_dir = MISC["ceph_directory"] % (self.instrument, self.proposal, self.run_number)
                if self.instrument in MISC["excitation_instruments"]:
                    # Excitations would like to remove the run number folder at the end
                    instrument_dir = instrument_dir[:instrument_dir.rfind('/')+1]
            else:
                instrument_dir = MISC["archive_directory"] % (self.instrument,
                                                              cycle,
                                                              self.proposal,
                                                              self.run_number)
            
            # Specify directories where autoreduction output will go
            reduce_result_dir = MISC["temp_root_directory"] + instrument_dir
            if self.instrument not in MISC["excitation_instruments"]:
                run_output_dir = os.path.join(MISC["temp_root_directory"],
                                              instrument_dir[:instrument_dir.rfind('/')+1])
            else:
                run_output_dir = reduce_result_dir
                
            log_dir = reduce_result_dir + "/reduction_log/"
            log_and_err_name = "RB" + self.proposal + "Run" + self.run_number
            script_out = os.path.join(log_dir, log_and_err_name + "Script.out")
            mantid_log = os.path.join(log_dir, log_and_err_name + "Mantid.log")

            # strip the temp path off the front of the temp directory to get the final archive directory
            final_result_dir = reduce_result_dir[len(MISC["temp_root_directory"]):]
            final_log_dir = log_dir[len(MISC["temp_root_directory"]):]

            # test for access to result paths
            try:
                should_be_writable = [reduce_result_dir, log_dir, final_result_dir, final_log_dir]
                should_be_readable = [self.data_file]

                # try to make directories which should exist
                for path in filter(lambda p: not os.path.isdir(p), should_be_writable):
                    os.makedirs(path)

                does_not_exist = lambda path: not os.access(path, os.F_OK)
                not_readable = lambda path: not os.access(path, os.R_OK)
                not_writable = lambda path: not os.access(path, os.W_OK)

                # we want write access to these directories, plus the final output paths
                if len(filter(not_writable, should_be_writable)) > 0:
                    fail_path = filter(not_writable, should_be_writable)[0]
                    problem = "does not exist" if does_not_exist(fail_path) else "no write access"
                    raise Exception("Couldn't write to %s  -  %s" % (fail_path, problem))

                if len(filter(not_readable, should_be_readable)) > 0:
                    fail_path = filter(not_readable, should_be_readable)[0]
                    problem = "does not exist" if does_not_exist(fail_path) else "no read access"
                    raise Exception("Couldn't read %s  -  %s" % (fail_path, problem))
            
            except Exception as exp:
                # if we can't access now, we should abort the run, and tell the server that it should be
                # re-run at a later time
                self.data["message"] = "Permission error: %s" % exp
                # 6 hours
                self.data["retry_in"] = 6 * 60 * 60
                logger.error(traceback.format_exc())
                raise exp

            self.data['reduction_data'] = []
            if "message" not in self.data:
                self.data["message"] = ""

            logger.info("----------------")
            logger.info("Reduction script: %s ..." % self.reduction_script[:50])
            logger.info("Result dir: %s" % reduce_result_dir)
            logger.info("Run Output dir: %s" % run_output_dir)
            logger.info("Log dir: %s" % log_dir)
            logger.info("Out log: %s" % script_out)
            logger.info("Datafile: %s" % self.data_file)
            logger.info("----------------")

            logger.info("Reduction subprocess started.")

            out_directories = None

            try:
                with channels_redirected(script_out, mantid_log, self.reduction_log_stream):
                    """
                    Load reduction script as a module. This works as long as reduce.py makes no assumption that it is
                    in the same directory as reduce_vars, i.e., either it does not import it at all, or adds its
                    location to os.path explicitly.
                    """
                    logger.info('Environment Variables:')
                    logger.info(os.environ)
                    sys.path.append("/opt/Mantid/bin")
                    reduce_script_location = self._load_reduction_script(self.instrument)
                    reduce_script = imp.load_source('reducescript', reduce_script_location)

                    try:
                        skip_numbers = reduce_script.SKIP_RUNS
                    except:
                        skip_numbers = []
                        pass
                    if self.data['run_number'] not in skip_numbers:
                        reduce_script = self.replace_variables(reduce_script)
                        out_directories = reduce_script.main(input_file=str(self.data_file),
                                                             output_dir=str(reduce_result_dir))
                    else:
                        self.data['message'] = "Run has been skipped in script"
            except Exception as exp:
                with open(script_out, "a") as f:
                    f.writelines(str(exp) + "\n")
                    f.write(traceback.format_exc())
                self.copy_temp_directory(reduce_result_dir, final_result_dir)
                self.delete_temp_directory(reduce_result_dir)
                
                error_str = "Error in user reduction script: %s - %s" % (type(exp).__name__, exp)
                logger.error(traceback.format_exc())
                # Parent except block will discard exception type, so format the type as a string now
                raise Exception(error_str)

            logger.info("Reduction subprocess completed.")
            logger.info("Additional save directories: %s" % out_directories)

            self.copy_temp_directory(reduce_result_dir, final_result_dir)

            # If the reduce script specified some additional save directories, copy to there first
            if out_directories:
                if type(out_directories) is str:
                    self.copy_temp_directory(reduce_result_dir, out_directories)
                elif type(out_directories) is list:
                    for out_dir in out_directories:
                        if type(out_dir) is str:
                            self.copy_temp_directory(reduce_result_dir, out_dir)
                        else:
                            self.log_and_message("Optional output directories of reduce.py must be strings: %s" %
                                                 out_dir)
                else:
                    self.log_and_message("Optional output directories of reduce.py must be a string or list of stings: "
                                         "%s" % out_directories)

            # no longer a need for the temp directory used for temporary storing of reduction results
            self.delete_temp_directory(reduce_result_dir)

        except Exception as exp:
            logger.error(traceback.format_exc())
            self.data["message"] = "REDUCTION Error: %s " % exp

        self.data['reduction_log'] = self.reduction_log_stream.getvalue()
        self.data["admin_log"] = self.admin_log_stream.getvalue()
            
        if self.data["message"] != "":
            # This means an error has been produced somewhere
            try:
                self._send_error_and_log()
            except Exception:
                logger.info("Failed to send to queue! - %s - %s" % (e, repr(e)))
            finally:
                logger.info("Reduction job failed")
                
        else:
            # reduction has successfully completed
            self.client.send(ACTIVEMQ['reduction_complete'], json.dumps(self.data))
            print("\nCalling: " + ACTIVEMQ['reduction_complete'] + "\n" + prettify(self.data) + "\n")
            logger.info("Reduction job successfully complete")

    def _send_error_and_log(self):
        logger.info("\nCalling " + ACTIVEMQ['reduction_error'] + " --- " + prettify(self.data))
        self.client.send(ACTIVEMQ['reduction_error'], json.dumps(self.data))

    def copy_temp_directory(self, temp_result_dir, copy_destination):
        """ Method that copies the temporary files held in results_directory to CEPH/archive, replacing old data if it
        exists"""

        # EXCITATION instrument are treated as a special case because they done what run number subfolders
        if os.path.isdir(copy_destination) and self.instrument not in MISC["excitation_instruments"]:
            self._remove_directory(copy_destination)

        self.data['reduction_data'].append(linux_to_windows_path(copy_destination))
        logger.info("Moving %s to %s" % (temp_result_dir, copy_destination))
        try:
            self._copy_tree(temp_result_dir, copy_destination)
        except Exception as exp:
            self.log_and_message("Unable to copy to %s - %s" % (copy_destination, exp))

    @staticmethod
    def delete_temp_directory(temp_result_dir):
        """ Remove temporary working directory """
        logger.info("Remove temp dir %s " % temp_result_dir)
        try:
            shutil.rmtree(temp_result_dir, ignore_errors=True)
        except:
            logger.info("Unable to remove temporary directory %s - %s" % temp_result_dir)

    def log_and_message(self, msg):
        """Helper function to add text to the outgoing activemq message and to the info logs """
        logger.info(msg)
        if self.data["message"] == "":
            # Only send back first message as there is a char limit
            self.data["message"] = msg

    def _remove_with_wait(self, remove_folder, full_path):
        """
        Removes a folder or file and waits for it to be removed
        """
        for sleep in [0, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20]:
            try:
                if remove_folder:
                    os.removedirs(full_path)
                else:
                    os.remove(full_path)
            except Exception as exp:
                if exp.errno == errno.ENOENT:
                    # File has been deleted
                    break
            time.sleep(sleep)
        else:
            self.log_and_message("Failed to delete %s" % full_path)
            
    def _copy_tree(self, source, dest):
        if not os.path.exists(dest):
            os.makedirs(dest)
        for item in os.listdir(source):
            s = os.path.join(source, item)
            d = os.path.join(dest, item)
            if os.path.isdir(s):
                self._copy_tree(s, d)
            elif not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copyfile(s, d)

    def _remove_directory(self, directory):
        """
        Helper function to remove a directory. shutil.rmtree cannot be used as it is not robust enough when folders
        are open over the network.
        """
        try:
            for target_file in os.listdir(directory):
                full_path = os.path.join(directory, target_file)
                if os.path.isdir(full_path):
                    self._remove_directory(full_path)
                else:
                    self._remove_with_wait(False, full_path)
            self._remove_with_wait(True, directory)
        except Exception as exp:
            self.log_and_message("Unable to remove existing directory %s - %s" % (directory, exp))

if __name__ == "__main__":
    brokers = []
    brokers.append((ACTIVEMQ['brokers'].split(':')[0], int(ACTIVEMQ['brokers'].split(':')[1])))
    stomp_connection = stomp.Connection(host_and_ports=brokers, use_ssl=False)
    json_data = None
    try:
        logger.info("PostProcessAdmin Connecting to ActiveMQ")
        stomp_connection.start()
        stomp_connection.connect(ACTIVEMQ['amq_user'],
                                 ACTIVEMQ['amq_pwd'],
                                 wait=True,
                                 header={'activemq.prefetchSize': '1',})
        logger.info("PostProcessAdmin Successfully Connected to ActiveMQ")

        destination, message = sys.argv[1:3]
        print("destination: " + destination)
        print("message: " + prettify(message))
        json_data = json.loads(message)
        
        try:  
            pp = PostProcessAdmin(json_data, stomp_connection)
            log_stream_handler = logging.StreamHandler(pp.admin_log_stream)
            logger.addHandler(log_stream_handler)
            if destination == '/queue/ReductionPending':
                pp.reduce()

        except ValueError as e:
            json_data["error"] = str(e)
            logger.info("JSON data error: " + prettify(json_data))
            raise
        
        except Exception as e:
            logger.info("PostProcessAdmin error: %s" % e)
            raise
            
        finally:
            try:
                logger.removeHandler(log_stream_handler)
            except:
                pass
        
    except Exception as er:
        logger.info("Something went wrong: " + str(er))
        try:
            stomp_connection.send(ACTIVEMQ['postprocess_error'], json.dumps(json_data))
            print("Called " + ACTIVEMQ['postprocess_error'] + "----" + prettify(json_data))
        finally:
            sys.exit()
