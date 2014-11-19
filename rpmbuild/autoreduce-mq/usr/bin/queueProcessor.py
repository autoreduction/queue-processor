import json, logging, time, subprocess, sys, socket
import stomp
from twisted.internet import reactor
from Configuration import Configuration

class Listener(object):
    def __init__(self, client):
        self._client = client
        self.procList = []

    def on_error(self, headers, message):
        logging.error("Error recieved - %s" % str(message))

    def on_message(self, headers, data):
        destination = headers['destination']

        logging.info("Received frame destination: " + destination)
        logging.info("Received frame body (data)" + data) 
        proc = subprocess.Popen(["python", "/usr/bin/PostProcessAdmin.py", destination, data])
        self.procList.append(proc)

        while len(self.procList) > 4:
            logging.info("There are " + str(len(self.procList)) + " processors running at the moment, wait for a second")
            time.sleep(1.0)
            self.updateChildProcessList()

        self.updateChildProcessList()
        
    def updateChildProcessList(self):
        for i in self.procList:
            if i.poll() is not None:
                self.procList.remove(i)

class Consumer(object):
        
    def __init__(self, config):
        self.config = config
        self.consumer_name = "queueProcessor"
        
    def run(self):
        connection = stomp.Connection(host_and_ports=self.config.brokers, use_ssl=True)
        connection.set_listener(self.consumer_name, Listener(self))
        connection.start()
        connection.connect(self.config.amq_user, self.config.amq_pwd, wait=True, header={StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL,'activemq.prefetchSize': '1',})

        for queue in self.config.amq_queues:
            logging.info("[%s] Subscribing to %s" % (self.consumer_name, queue))
            connection.subscribe(destination=queue, id=1, ack='auto')


if __name__ == '__main__':
    
    try:
        config = Configuration('/etc/autoreduce/post_process_consumer.conf')
    except:
        sys.exit()
        
    logging.info("Start post process asynchronous listener!")
    
    reactor.callWhenRunning(Consumer(config).run)
    reactor.run()
    logging.info("Stop post process asynchronous listener!")
