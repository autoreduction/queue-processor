#!/usr/bin/env python
"""
Post Process Administrator. It kicks off cataloging and reduction jobs.
"""
import json, socket, os, sys, time, shutil, imp, stomp, re, errno, traceback
from contextlib import contextmanager
from autoreduction_logging_setup import logger

@contextmanager
def channels_redirected(out_file, err_file):
    """
    This context manager copies the file descriptor(fd) of stdout and stderr to the files given in out_file and err_file
    respectively. The fd is at the C level and so picks up data sent via Mantid.
    """
    out_fd = sys.stdout.fileno()
    err_fd = sys.stderr.fileno()

    def _redirect_channels(out_file, err_file):
        # Close and flush
        sys.stdout.close()
        sys.stderr.close()

        # Copy fds
        os.dup2(out_file.fileno(), out_fd)
        os.dup2(err_file.fileno(), err_fd)

        # Python writes to fds
        sys.stdout = os.fdopen(out_fd, 'w')
        sys.stderr = os.fdopen(err_fd, 'w')

    with os.fdopen(os.dup(out_fd), 'w') as old_stdout:
        with os.fdopen(os.dup(err_fd), 'w') as old_stderr:
            with open(out_file, 'w') as out:
                with open(err_file, 'w') as err:
                    _redirect_channels(out, err)
                    try:
                        yield  # allow code to be run with the redirected channels
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


class PostProcessAdmin:
    def __init__(self, data, conf, connection):

        logger.debug("json data: " + str(data))
        data["information"] = socket.gethostname()
        self.data = data
        self.conf = conf
        self.client = connection

        try:
            if data.has_key('data'):
                self.data_file = windows_to_linux_path(str(data['data']), self.conf["temp_root_directory"])
                logger.debug("data_file: %s" % self.data_file)
            else:
                raise ValueError("data is missing")

            if data.has_key('facility'):
                self.facility = str(data['facility']).upper()
                logger.debug("facility: %s" % self.facility)
            else: 
                raise ValueError("facility is missing")

            if data.has_key('instrument'):
                self.instrument = str(data['instrument']).upper()
                logger.debug("instrument: %s" % self.instrument)
            else:
                raise ValueError("instrument is missing")

            if data.has_key('rb_number'):
                self.proposal = str(data['rb_number']).upper()
                logger.debug("rb_number: %s" % self.proposal)
            else:
                raise ValueError("rb_number is missing")
                
            if data.has_key('run_number'):
                self.run_number = str(int(data['run_number']))  # Cast to int to remove trailing zeros
                logger.debug("run_number: %s" % str(self.run_number))
            else:
                raise ValueError("run_number is missing")
                
            if data.has_key('reduction_script'):
                self.reduction_script = windows_to_linux_path(str(data['reduction_script']), self.conf["temp_root_directory"])
                logger.debug("reduction_script: %s" % str(self.reduction_script))
            else:
                raise ValueError("reduction_script is missing")
                
            if data.has_key('reduction_arguments'):
                self.reduction_arguments = data['reduction_arguments']
                logger.debug("reduction_arguments: %s" % self.reduction_arguments)
            else:
                raise ValueError("reduction_arguments is missing")

        except ValueError:
            logger.info('JSON data error', exc_info=True)
            raise

    def parse_input_variable(self, default, value):
        varType = type(default)
        if varType.__name__ == "str":
            return str(value)
        if varType.__name__ == "int":
            return int(value)
        if varType.__name__ == "list":
            return value.split(',')
        if varType.__name__ == "bool":
            return (value.lower() is 'true')
        if varType.__name__ == "float":
            return float(value)

    def replace_variables(self, reduce_script):
        if hasattr(reduce_script, 'web_var'):
            if hasattr(reduce_script.web_var, 'standard_vars'):
                for key in reduce_script.web_var.standard_vars:
                    if 'standard_vars' in self.reduction_arguments and key in self.reduction_arguments['standard_vars']:
                        if type(self.reduction_arguments['standard_vars'][key]).__name__ == 'unicode':
                            self.reduction_arguments['standard_vars'][key] = self.reduction_arguments['standard_vars'][key].encode('ascii','ignore')
                        reduce_script.web_var.standard_vars[key] = self.reduction_arguments['standard_vars'][key]
            if hasattr(reduce_script.web_var, 'advanced_vars'):
                for key in reduce_script.web_var.advanced_vars:
                    if 'advanced_vars' in self.reduction_arguments and key in self.reduction_arguments['advanced_vars']:
                        if type(self.reduction_arguments['advanced_vars'][key]).__name__ == 'unicode':
                            self.reduction_arguments['advanced_vars'][key] = self.reduction_arguments['advanced_vars'][key].encode('ascii','ignore')
                        reduce_script.web_var.advanced_vars[key] = self.reduction_arguments['advanced_vars'][key]
        return reduce_script

    def reduce(self):
        logger.debug("In reduce() method")
        try:         
            logger.debug("Calling: " + self.conf['reduction_started'] + "\n" + json.dumps(self.data))
            self.client.send(self.conf['reduction_started'], json.dumps(self.data))

            # specify instrument directory
            cycle = re.match(r'.*cycle_(\d\d_\d).*', self.data_file.lower()).group(1)
            if self.instrument in (self.conf["ceph_instruments"] + self.conf["excitation_instruments"]):
                cycle = re.sub('[_]', '', cycle)
                instrument_dir = self.conf["ceph_directory"] % (self.instrument, self.proposal, self.run_number)
                if self.instrument in self.conf["excitation_instruments"]:
                    #Excitations would like to remove the run number folder at the end
                    instrument_dir = instrument_dir[:instrument_dir.rfind('/')+1]
            else:
                instrument_dir = self.conf["archive_directory"] % (self.instrument, cycle, self.proposal, self.run_number)

            # specify script to run and directory
            if os.path.exists(os.path.join(self.reduction_script, "reduce.py")) is False:
                self.data['message'] = "Reduce script doesn't exist within %s" % self.reduction_script
                logger.debug(self.data['message'])
                self._send_error_and_log()
                return
            
            # specify directory where autoreduction output goes
            reduce_result_dir = self.conf["temp_root_directory"] + instrument_dir
            if self.instrument not in self.conf["excitation_instruments"]:
                run_output_dir = os.path.join(self.conf["temp_root_directory"], instrument_dir[:instrument_dir.rfind('/')+1])
            else:
                run_output_dir = reduce_result_dir

            if not os.path.isdir(reduce_result_dir):
                os.makedirs(reduce_result_dir)

            log_dir = reduce_result_dir + "/reduction_log/"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            self.data['reduction_data'] = []
            if "message" not in self.data:
                self.data["message"] = ""

            # Load reduction script
            sys.path.append(self.reduction_script)

            log_and_err_name = "RB" + self.proposal + "Run" + self.run_number
            script_out = os.path.join(log_dir, log_and_err_name + "Script.out")
            mantid_log = os.path.join(log_dir, log_and_err_name + "Mantid.log")

            logger.info("----------------")
            logger.info("Reduction script: %s" % self.reduction_script)
            logger.info("Result dir: %s" % reduce_result_dir)
            logger.info("Run Output dir: %s" % run_output_dir)
            logger.info("Log dir: %s" % log_dir)
            logger.info("Out log: %s" % script_out)
            logger.info("----------------")

            logger.info("Reduction subprocess started.")

            try:
                with channels_redirected(script_out, mantid_log):
                    reduce_script = imp.load_source('reducescript', os.path.join(self.reduction_script, "reduce.py"))
                    try:
                        skip_numbers = reduce_script.SKIP_RUNS
                    except:
                        skip_numbers = []
                        pass
                    if self.data['run_number'] not in skip_numbers:
                        reduce_script = self.replace_variables(reduce_script)
                        out_directories = reduce_script.main(input_file=str(self.data_file), output_dir=str(reduce_result_dir))
                    else:
                        self.data['message'] = "Run has been skipped in script"
            except Exception as e:
                with open(script_out, "a") as f:
                    f.writelines(str(e) + "\n")
                    f.write(traceback.format_exc())
                self.copy_temp_directory(reduce_result_dir, reduce_result_dir[len(self.conf["temp_root_directory"]):])
                self.delete_temp_directory(reduce_result_dir)
                
                errorStr = "Error in user reduction script: %s - %s" % (type(e).__name__, e)
                raise Exception(errorStr) # parent except block will discard exception type, so format the type as a string now


            logger.info("Reduction subprocess completed.")
            logger.info("Additional save directories: %s" % out_directories)

            self.copy_temp_directory(reduce_result_dir, reduce_result_dir[len(self.conf["temp_root_directory"]):])

            # If the reduce script specified some additional save directories, copy to there first
            if out_directories:
                if type(out_directories) is str:
                    self.copy_temp_directory(reduce_result_dir, out_directories)
                elif type(out_directories) is list:
                    for out_dir in out_directories:
                        if type(out_dir) is str:
                            self.copy_temp_directory(reduce_result_dir, out_dir)
                        else:
                            self.log_and_message("Optional output directories of reduce.py must be strings: %s" % out_dir)
                else:
                    self.log_and_message("Optional output directories of reduce.py must be a string or list of stings: %s" % out_directories)

                    
            # no longer a need for the temp directory used for temporary storing of reduction results
            self.delete_temp_directory(reduce_result_dir)

        except Exception as e:
            self.data["message"] = "REDUCTION Error: %s " % e

            
        if self.data["message"] != "":
            # This means an error has been produced somewhere
            try:
                self._send_error_and_log()
            except Exception as e:
                logger.info("Failed to send to queue! - %s - %s" % (e, repr(e)))
            finally:
                logger.info("Reduction job failed")
        else:
            self.client.send(self.conf['reduction_complete'], json.dumps(self.data))
            print("\nCalling: " + self.conf['reduction_complete'] + "\n" + json.dumps(self.data) + "\n")
            logger.info("Reduction job successfully complete")

    def _send_error_and_log(self):
        logger.info("Called " + self.conf['reduction_error'] + " --- " + json.dumps(self.data))
        self.client.send(self.conf['reduction_error'], json.dumps(self.data))

    def copy_temp_directory(self, temp_result_dir, copy_destination):
        """ Method that copies the temporary files held in results_directory to CEPH/archive, replacing old data if it
        exists"""

        # EXCITATION instrument are treated as a special case because they done what run number subfolders
        if os.path.isdir(copy_destination) and self.instrument not in self.conf["excitation_instruments"]:
            self._remove_directory(copy_destination)

        self.data['reduction_data'].append(linux_to_windows_path(copy_destination))
        logger.info("Moving %s to %s" % (temp_result_dir, copy_destination))
        try:
            self._copy_tree(temp_result_dir, copy_destination)
        except Exception as e:
            self.log_and_message("Unable to copy to %s - %s" % (copy_destination, e))


    def delete_temp_directory(self, temp_result_dir):
        """ Remove temporary working directory """
        logger.info("Remove temp dir %s " % temp_result_dir)
        try:
            shutil.rmtree(temp_result_dir, ignore_errors=True)
        except Exception as e:
            logger.info("Unable to remove temporary directory %s - %s" % temp_result_dir)



    def log_and_message(self, message):
        """Helper function to add text to the outgoing activemq message and to the info logs """
        logger.info(message)
        if self.data["message"] == "":
            # Only send back first message as there is a char limit
            self.data["message"] = message

    def _remove_with_wait(self, remove_folder, full_path):
        """ Removes a folder or file and waits for it to be removed
        """
        for sleep in [0, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20]:
            try:
                if remove_folder:
                    os.removedirs(full_path)
                else:
                    os.remove(full_path)
            except Exception as e:
                if e.errno == errno.ENOENT:
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
        """ Helper function to remove a directory. shutil.rmtree cannot be used as it is not robust enough when folders
        are open over the network.
        """
        try:
            for file in os.listdir(directory):
                full_path = os.path.join(directory, file)
                if os.path.isdir(full_path):
                    self._remove_directory(full_path)
                else:
                    self._remove_with_wait(False, full_path)
            self._remove_with_wait(True, directory)
        except Exception as e:
            self.log_and_message("Unable to remove existing directory %s - %s" % (directory, e))

if __name__ == "__main__":
    print("\n> In PostProcessAdmin.py\n")

    try:
        conf = json.load(open('/etc/autoreduce/post_process_consumer.conf'))

        brokers = []
        brokers.append((conf['brokers'].split(':')[0],int(conf['brokers'].split(':')[1])))
        connection = stomp.Connection(host_and_ports=brokers, use_ssl=True, ssl_version=3)
        connection.start()
        connection.connect(conf['amq_user'], conf['amq_pwd'], wait=True, header={'activemq.prefetchSize': '1',})

        destination, message = sys.argv[1:3]
        print("destination: " + destination)
        print("message: " + message)
        data = json.loads(message)
        
        try:  
            pp = PostProcessAdmin(data, conf, connection)
            if destination == '/queue/ReductionPending':
                pp.reduce()

        except ValueError as e:
            data["error"] = str(e)
            logger.info("JSON data error: " + json.dumps(data))

            connection.send(conf['postprocess_error'], json.dumps(data))
            print("Called " + conf['postprocess_error'] + "----" + json.dumps(data))
            raise
        
        except:
            raise
        
    except Exception as er:
        logger.info("Something went wrong: " + str(er))
        sys.exit()
