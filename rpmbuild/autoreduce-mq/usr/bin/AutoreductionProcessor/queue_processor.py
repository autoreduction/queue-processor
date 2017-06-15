import json
import subprocess
import sys
import stomp
from twisted.internet import reactor
from autoreduction_logging_setup import logger


class Listener(object):
    def __init__(self, client, config):
        self._client = client
        self._conf = config
        self.procList = []
        self.RBList = []  # list of RB numbers of active reduction runs
        self.cancelList = []  # list of (run number, run version)s to drop (once) when we get them

    @staticmethod
    def on_error(message):
        logger.error("Error message recieved - %s" % str(message))

    def on_message(self, headers, data):
        self._client.ack(headers['message-id'], headers['subscription'])  # Remove message from queue
        destination = headers['destination']
        logger.debug("Received frame destination: " + destination)
        logger.debug("Recieved frame priority: " + headers["priority"])
                
        self.update_child_process_list()
        data_dict = json.loads(data)
        
        if "cancel" in data_dict and data_dict["cancel"]:
            self.add_cancel(data_dict)
            return    
                
        self.hold_message(destination, data)
        
    def hold_message(self, destination, data):
        logger.debug("holding thread")
        data_dict = json.loads(data)
        
        self.update_child_process_list()
        if not self.should_proceed(data_dict):  # wait while the run shouldn't proceed
            reactor.callLater(10, self.hold_message, destination, data)
            return
            
        if self.should_cancel(data_dict):
            self.cancel_run(data_dict)
            return
            
        print_dict = data_dict.copy()
        print_dict.pop("reduction_script")
        logger.debug("Calling: %s %s %s %s" % ("python", "/usr/bin/post_process_admin.py", destination, print_dict))
        proc = subprocess.Popen(["python",
                                 "/home/tip22963/autoreduction_processor/post_process_admin.py",
                                 destination,
                                 data])
        self.add_process(proc, data_dict)

    def update_child_process_list(self):
        for process in self.procList:
            if process.poll() is not None:
                index = self.procList.index(process)
                self.procList.pop(index)
                self.RBList.pop(index)
                
    def add_process(self, proc, data_dict):
        self.procList.append(proc)
        self.RBList.append(data_dict["rb_number"])
        
    def should_proceed(self, data_dict):
        if data_dict["rb_number"] in self.RBList:
            logger.info("Duplicate RB run #" + data_dict["rb_number"] + ", waiting for the first to finish.")
            return False
        else:   
            return True

    @staticmethod
    def run_tuple(data_dict):
        run_number = data_dict["run_number"]
        run_version = data_dict["run_version"] if data_dict["run_version"] is not None else 0
        return run_number, run_version

    # add this run to the cancel list, to cancel it next time it comes up
    def add_cancel(self, data_dict):
        tup = self.run_tuple(data_dict)
        if tup not in self.cancelList:
            self.cancelList.append(tup)
            
    def should_cancel(self, data_dict):
        tup = self.run_tuple(data_dict)
        return tup in self.cancelList
            
    def cancel_run(self, data_dict):
        tup = self.run_tuple(data_dict)
        self.cancelList.remove(tup)
        # don't cancel next time
        # don't send any message; it'll be handled on the frontend
        

class Consumer(object):
        
    def __init__(self, config):
        self.config = config
        self.consumer_name = "queueProcessor"
        
    def run(self):
        brokers = [(self.config['brokers'].split(':')[0], int(self.config['brokers'].split(':')[1]))]
        connection = stomp.Connection(host_and_ports=brokers, use_ssl=False)
        connection.set_listener(self.consumer_name, Listener(connection, self.config))
        logger.info("Starting ActiveMQ Connection")
        connection.start()
        logger.info("Completed ActiveMQ Connection")
        connection.connect(self.config['amq_user'],
                           self.config['amq_pwd'],
                           wait=False,
                           header={'activemq.prefetchSize': '1'})
        
        for queue in self.config['amq_queues']:
            connection.subscribe(destination=queue,
                                 id=1,
                                 ack='client-individual',
                                 header={'activemq.prefetchSize': '1'})
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
