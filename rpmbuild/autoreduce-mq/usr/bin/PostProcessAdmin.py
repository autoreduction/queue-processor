#!/usr/bin/env python
"""
Post Process Administrator. It kicks off cataloging and reduction jobs.
"""
import logging, json, socket, os, sys, subprocess, time, shutil, imp

#from ingestNexus_mq import IngestNexus
#from ingestReduced_mq import IngestReduced
from Configuration import Configuration
from stompest.config import StompConfig
from stompest.sync import Stomp

class PostProcessAdmin:
    def __init__(self, data, conf):

        logging.info("json data: " + str(data))
        data["information"] = socket.gethostname()
        self.data = data
        self.conf = conf
        
        stompConfig = StompConfig(self.conf.brokers, self.conf.amq_user, self.conf.amq_pwd)
        self.client = Stomp(stompConfig)

        try:
            if data.has_key('data'):
                self.data_file = str(data['data'])
                logging.info("data_file: " + self.data_file)
                if os.access(self.data_file, os.R_OK) == False:
                    if 'isisdatar80' in self.data_file:
                        self.data_file = self.data_file.replace('isisdatar80', 'isisdatar55')
                    else:
                        self.data_file = self.data_file.replace('isisdatar55', 'isisdatar80')
                    if os.access(self.data_file, os.R_OK) == False:
                        raise ValueError("data path (" + self.data_file + ") doesn't exist or file not readable")
            else:
                raise ValueError("data is missing")

            if data.has_key('facility'):
                self.facility = str(data['facility']).upper()
                logging.info("facility: " + self.facility)
            else: 
                raise ValueError("facility is missing")

            if data.has_key('instrument'):
                self.instrument = str(data['instrument']).upper()
                logging.info("instrument: " + self.instrument)
            else:
                raise ValueError("instrument is missing")

            if data.has_key('rb_number'):
                self.proposal = str(data['rb_number']).upper()
                logging.info("rb_number: " + self.proposal)
            else:
                raise ValueError("rb_number is missing")
                
            if data.has_key('run_number'):
                self.run_number = str(data['run_number'])
                logging.info("run_number: " + self.run_number)
            else:
                raise ValueError("run_number is missing")
                
            if data.has_key('reduction_script'):
                self.reduction_script = str(data['reduction_script'])
                logging.info("reduction_script: " + self.reduction_script)
            else:
                raise ValueError("reduction_script is missing")
                
            if data.has_key('reduction_arguments'):
                self.reduction_arguments = str(data['reduction_arguments'])
                logging.info("reduction_arguments: " + self.reduction_arguments)
            else:
                raise ValueError("reduction_arguments is missing")

        except ValueError:
            logging.info('JSON data error', exc_info=True)
            raise

    def parse_input_variable(default, value):
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

    def replace_variables(reduce_script):
        for key in reduce_script.standard_vars:
            if key in self.reduction_arguments:
                reduce_script.standard_vars[key] = parse_input_variable(reduce_script.standard_vars[key], self.reduction_arguments[key])
        for key in reduce_script.advanced_vars:
            if key in self.reduction_arguments:
                reduce_script.advanced_vars[key] = parse_input_variable(reduce_script.advanced_vars[key], self.reduction_arguments[key])
        return reduce_script

    def linux_to_windows_path(path):
        path = path.replace('/', '\\')
        # '/isis/' maps to '\\isis\inst$\'
        path = path.replace('\\isis\\', '\\\\isis\\inst$\\')
        return path

    def windows_to_linux_path(path):
        # '\\isis\inst$\' maps to '/isis/'
        path = path.replace('\\\\isis\\inst$\\', '/isis/')
        path = path.replace('\\', '/')
        return path

    def reduce(self):
        print "in reduce"
        try:         
            logging.info("called " + self.conf.reduction_started + " --- " + json.dumps(self.data))  
            self.send(self.conf.reduction_started, json.dumps(self.data))

            # specify instrument directory  
            instrument_dir = "/isis/ndx" + self.instrument.upper() + "/user/processed/autoreduction/"

            # specify script to run and directory
            reduce_script_dir = self.reduction_script.replace('reduce.py','')
            if os.path.exists(self.reduction_script) == False:
                self.data['message'] = "Reduce script doesn't exist"
                self.send(self.conf.reduction_error , json.dumps(self.data))  
                logging.info("called "+self.conf.reduction_error + " --- " + json.dumps(self.data))  
                return
            
            # specify directory where autoreduction output goes
            reduce_result_dir = "/tmp" + instrument_dir + "results/" + self.proposal + "/" + self.run_number + "/"
            if not os.path.isdir(reduce_result_dir):
                os.makedirs(reduce_result_dir)

            log_dir = reduce_result_dir + "reduction_log/"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # Load reduction script 
            reduce_script = imp.load_source('reducescript', self.reduction_script)
            out_log = os.path.join(log_dir, os.path.basename(self.data_file) + ".log")
            out_err = os.path.join(reduce_result_dir, os.path.basename(self.data_file) + ".err")
            logFile=open(out_log, "w")
            errFile=open(out_err, "w")
            # Set the output to be the logfile
            sys.stdout = logFile
            sys.stderr = errFile
            reduce_script = replace_variables(reduce_script)
            logging.info("reduction subprocess started.")
            out_directories = reduce_script.main(data=self.data_file, output=reduce_result_dir)
            logging.info("reduction subprocess completed.")
            # Reset outputs back to default
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            
            self.data['reduction_data'] = []

            # If the reduce script specified some additional save directories, copy to there first
            if out_directories:
                if type(out_directories) is str and os.access(out_directories, os.R_OK):
                    self.data['reduction_data'].append(linux_to_windows_path(out_directories))
                    shutil.copy(reduce_result_dir, out_directories)
                elif type(out_directories) is list:
                    for out_dir in out_directories:
                        self.data['reduction_data'].append(linux_to_windows_path(out_dir))
                        if type(out_dir) is str and os.access(out_dir, os.R_OK):
                            shutil.copy(reduce_result_dir, out_dir)
            
            # Move from tmp directory to actual directory (remove /tmp from start of path)
            if not os.path.isdir(reduce_result_dir[4:]):
                os.makedirs(reduce_result_dir[4:])
            self.data['reduction_data'].append(linux_to_windows_path(reduce_result_dir[4:]))
            shutil.move(reduce_result_dir, reduce_result_dir[4:])
            
            if os.stat(out_err).st_size == 0:
                os.remove(out_err)
                self.send(self.conf.reduction_complete , json.dumps(self.data))  
                logging.info("called "+self.conf.reduction_complete + " --- " + json.dumps(self.data))     
            else:
                maxLineLength=80
                fp=file(out_err, "r")
                fp.seek(-maxLineLength-1, 2) # 2 means "from the end of the file"
                lastLine = fp.readlines()[-1]
                errMsg = lastLine.strip() + ", see reduction_log/" + os.path.basename(out_log) + " or " + os.path.basename(out_err) + " for details."
                self.data["error"] = "REDUCTION: %s" % errMsg
                self.send(self.conf.reduction_error , json.dumps(self.data))
                logging.error("called "+self.conf.reduction_error  + " --- " + json.dumps(self.data))       

        except Exception, e:
            self.data["error"] = "REDUCTION Error: %s " % e
            logging.error("called "+self.conf.reduction_error  + " --- " + json.dumps(self.data))
            self.send(self.conf.reduction_error , json.dumps(self.data))
            

    def send(self, destination, data):
        self.client.connect()
        self.client.send(destination, data)
        self.client.disconnect()
        
    def getData(self):
        return self.data
    
    
if __name__ == "__main__":

    print "\nIn PostProcessAdmin.py\n"

    try:
        conf = Configuration('/etc/autoreduce/post_process_consumer.conf')
        destination, message = sys.argv[1:3]
        logging.info("destination: " + destination)
        logging.info("message: " + message)
        data = json.loads(message)
        
        try:  
            pp = PostProcessAdmin(data, conf)
            if destination == '/queue/ReductionPending':
                pp.reduce()

        except ValueError as e:
            data["error"] = str(e)
            logging.error("JSON data error: " + json.dumps(data))
            stomp = Stomp(StompConfig(conf.brokers, conf.amq_user, conf.amq_pwd))
            stomp.connect()
            stomp.send(conf.postprocess_error, json.dumps(data))
            stomp.disconnect() 
            logging.info("Called " + conf.postprocess_error + "----" + json.dumps(data))
            raise
        
        except:
            raise
        
    except:
        sys.exit()


