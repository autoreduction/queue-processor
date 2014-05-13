#!/usr/bin/env python
"""
Post Process Administrator. It kicks off cataloging and reduction jobs.
"""
import logging, json, socket, os, sys, subprocess, time

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
            if data.has_key('data_file'):
                self.data_file = str(data['data_file'])
                logging.info("data_file: " + self.data_file)
                if os.access(self.data_file, os.R_OK) == False:
                    if 'isisdatar80' in self.data_file:
                        self.data_file = self.data_file.replace('isisdatar80', 'isisdatar55')
                    else:
                        self.data_file = self.data_file.replace('isisdatar55', 'isisdatar80')
                    if os.access(self.data_file, os.R_OK) == False:
                        raise ValueError("data_file path (" + self.data_file + ") doesn't exist or file not readable")
            else:
                raise ValueError("data_file is missing")

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

            if data.has_key('ipts'):
                self.proposal = str(data['ipts']).upper()
                logging.info("proposal: " + self.proposal)
            #else:
            #    raise ValueError("ipts is missing")

            if data.has_key('proposal'):
                self.proposal = str(data['proposal']).upper()
                logging.info("proposal: " + self.proposal)
            else:
                raise ValueError("proposal is missing")
                
            if data.has_key('run_number'):
                self.run_number = str(data['run_number'])
                logging.info("run_number: " + self.run_number)
            else:
                raise ValueError("run_number is missing")
                 
        except ValueError:
            logging.info('JSON data error', exc_info=True)
            raise


    def reduce(self):
        print "in reduce"
        try:         
            logging.info("called /queue/" + self.conf.reduction_started + " --- " + json.dumps(self.data))  
            self.send('/queue/'+self.conf.reduction_started, json.dumps(self.data))

            # specify instrument directory  
            #instrument_dir = "/isisdatar80/ndx" + self.instrument.lower() + "/user/scripts/autoreduction/"
            #if os.path.exists(instrument_dir) == False:
            #    instrument_dir = "/isisdatar55/ndx" + self.instrument.lower() + "/user/scripts/autoreduction/"
            instrument_dir = "/home/ajm64/tmp/" + self.instrument.lower() + "/"

            # specify script to run and directory
            reduce_script_dir = instrument_dir + "scripts/"
            reduce_script_path = instrument_dir + "scripts/reduce.py"
            if os.path.exists(reduce_script_path) == False:
                self.send('/queue/'+self.conf.reduction_disabled , json.dumps(self.data))  
                logging.info("called /queue/"+self.conf.reduction_disabled + " --- " + json.dumps(self.data))  
                return
            
            # specify directory where autoreduction output goes
            reduce_result_dir = instrument_dir + "results/" + self.proposal + "/"
            if not os.path.exists(reduce_result_dir):
                os.makedirs(reduce_result_dir)

            log_dir = reduce_result_dir + "reduction_log/"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            cmd = "export set PYTHONPATH=$PYTHONPATH:" + reduce_script_dir + "; python " + reduce_script_path + " " + self.data_file + " " + reduce_result_dir
            logging.info("reduction subprocess started: " + cmd)
            out_log = os.path.join(log_dir, os.path.basename(self.data_file) + ".log")
            out_err = os.path.join(reduce_result_dir, os.path.basename(self.data_file) + ".err")
            logFile=open(out_log, "w")
            errFile=open(out_err, "w")
            proc = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=logFile, stderr=errFile, universal_newlines = True)
            proc.communicate()
            logFile.close()
            errFile.close()
            logging.info("reduction subprocess completed")
            
            if os.stat(out_err).st_size == 0:
                os.remove(out_err)
                self.send('/queue/'+self.conf.reduction_complete , json.dumps(self.data))  
                logging.info("called /queue/"+self.conf.reduction_complete + " --- " + json.dumps(self.data))     
            else:
                maxLineLength=80
                fp=file(out_err, "r")
                fp.seek(-maxLineLength-1, 2) # 2 means "from the end of the file"
                lastLine = fp.readlines()[-1]
                errMsg = lastLine.strip() + ", see reduction_log/" + os.path.basename(out_log) + " or " + os.path.basename(out_err) + " for details."
                self.data["error"] = "REDUCTION: %s" % errMsg
                self.send('/queue/'+self.conf.reduction_error , json.dumps(self.data))
                logging.error("called /queue/"+self.conf.reduction_error  + " --- " + json.dumps(self.data))       

        except Exception, e:
            self.data["error"] = "REDUCTION Error: %s " % e
            logging.error("called /queue/"+self.conf.reduction_error  + " --- " + json.dumps(self.data))
            self.send('/queue/'+self.conf.reduction_error , json.dumps(self.data))
            

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
            if destination == '/queue/REDUCTION.DATA_READY':
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


