import json, time, subprocess, sys
import stomp
from twisted.internet import reactor
from autoreduction_logging_setup import logger

class Listener(object):
    def __init__(self, client, config):
        self._client = client
        self._conf = config
        self.procList = []
        self.RBList = [] # list of RB numbers of active reduction runs
        self.cancelList = [] # list of (run number, run version)s to drop (once) when we get them

    def on_error(self, headers, message):
        logger.error("Error message recieved - %s" % str(message))

    def on_message(self, headers, data):
        self._client.ack(headers['message-id'], headers['subscription'])  # Remove message from queue
        
        destination = headers['destination']

        logger.debug("Received frame destination: " + destination)
        logger.debug("Recieved frame priority: " + headers["priority"])
                
        self.updateChildProcessList()
        data_dict = json.loads(data)
        
        if "cancel" in data_dict and data_dict["cancel"]:
            self.addCancel(data_dict)
            return    
                
        reactor.callInThread(self.holdMessage, destination, data) # no loop here, to prevent blocking the consumer
        
    def holdMessage(self, destination, data):
        logger.debug("holding thread")
        data_dict = json.loads(data)
        while not self.shouldProceed(data_dict): # wait while the run shouldn't proceed
            reactor.callFromThread(self.updateChildProcessList) # update in the reactor thread, for thread safety
            time.sleep(10.0)
            
        if self.shouldCancel(data_dict):
            self.cancelRun(data_dict)
            return
            
        print_dict = data_dict.copy()
        print_dict.pop("reduction_script")
        logger.debug("Calling: %s %s %s %s" % ("python", "/usr/bin/PostProcessAdmin.py", destination, print_dict))
        proc = subprocess.Popen(["python", "/usr/bin/PostProcessAdmin.py", destination, data])
        reactor.callFromThread(self.addProc, proc, data_dict)

        
    def updateChildProcessList(self):
        for process in self.procList:
            if process.poll() is not None:
                index = self.procList.index(process)
                self.procList.pop(index)
                self.RBList.pop(index)
                
    def addProc(self, proc, data_dict):
        self.procList.append(proc)
        self.RBList.append(data_dict["rb_number"])
        
    def shouldProceed(self, data_dict):
        if data_dict["rb_number"] in self.RBList:
            logger.info("Duplicate RB run #" + data_dict["rb_number"] + ", waiting for the first to finish.")
            return False
            
        else:   
            return True
            
            
    def runTuple(self, data_dict):
        runNumber = data_dict["run_number"]
        runVersion = data_dict["run_version"] if data_dict["run_version"] is not None else 0
        return (runNumber, runVersion)
            
    def addCancel(self, data_dict): # add this run to the cancel list, to cancel it next time it comes up
        tup = self.runTuple(data_dict)
        if tup not in self.cancelList:
            self.cancelList.append(tup)
            
    def shouldCancel(self, data_dict):
        tup = self.runTuple(data_dict)
        return tup in self.cancelList
            
    def cancelRun(self, data_dict):
        tup = self.runTuple(data_dict)
        self.cancelList.remove(tup) # don't cancel next time
        data_dict["message"] = "Run cancelled by user"
        self._client.send(self._conf['postprocess_error'], json.dumps(data_dict)) # send the error back
        

class Consumer(object):
        
    def __init__(self, config):
        self.config = config
        self.consumer_name = "queueProcessor"
        
    def run(self):
        brokers = [(self.config['brokers'].split(':')[0],int(self.config['brokers'].split(':')[1]))]
        connection = stomp.Connection(host_and_ports=brokers, use_ssl=True, ssl_version=3)
        connection.set_listener(self.consumer_name, Listener(connection, self.config))
        connection.start()
        connection.connect(self.config['amq_user'], self.config['amq_pwd'], wait=False, header={'activemq.prefetchSize': '1'})
        
        for queue in self.config['amq_queues']:
            connection.subscribe(destination=queue, id=1, ack='client-individual', header={'activemq.prefetchSize': '1'})
            logger.info("[%s] Subscribing to %s" % (self.consumer_name, queue))

def main():
    try:
        config = json.load(open('/etc/autoreduce/post_process_consumer.conf'))
    except:
        logger.info("Can't open post_process_consumer.conf")
        sys.exit()
        
    logger.info("Start post process asynchronous listener!")
    reactor.callWhenRunning(Consumer(config).run)
    reactor.run()
    logger.info("Stop post process asynchronous listener!")

if __name__ == '__main__':
    main()
