import json, logging, time, subprocess, sys, socket
import stomp
from twisted.internet import reactor
logging.basicConfig(filename='/var/log/autoreduction.log', level=logging.INFO)

class Listener(object):
    def __init__(self, client):
        self._client = client
        self.procList = []

    def on_error(self, headers, message):
        logging.error("Error message recieved - %s" % str(message))

    def on_message(self, headers, data):
        destination = headers['destination']

        logging.debug("Received frame destination: " + destination)
        logging.debug("Received frame body (data)" + data) 
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
        brokers = []
        brokers.append((self.config['brokers'].split(':')[0],int(self.config['brokers'].split(':')[1])))
        connection = stomp.Connection(host_and_ports=brokers, use_ssl=True)
        connection.set_listener(self.consumer_name, Listener(self))
        connection.start()
        connection.connect(self.config['amq_user'], self.config['amq_pwd'], wait=True, header={'activemq.prefetchSize': '1',})

        for queue in self.config['amq_queues']:
            logging.info("[%s] Subscribing to %s" % (self.consumer_name, queue))
            connection.subscribe(destination=queue, id=1, ack='auto')


def main():
    try:
        config = json.load(open('/etc/autoreduce/post_process_consumer.conf'))
    except:
        sys.exit()
        
    logging.info("Start post process asynchronous listener!")
    
    reactor.callWhenRunning(Consumer(config).run)
    reactor.run()
    logging.info("Stop post process asynchronous listener!")

if __name__ == '__main__':
    main()