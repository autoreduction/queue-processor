import json, logging, time, subprocess, sys, socket
import logging.handlers
import stomp
from twisted.internet import reactor
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.handlers.RotatingFileHandler('/var/log/autoreduction.log', maxBytes=104857600, backupCount=20)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
# Quite the Stomp logs as they are quite chatty
logging.getLogger('stomp').setLevel(logging.WARNING)

class Listener(object):
    def __init__(self, client):
        self._client = client
        self.procList = []

    def on_error(self, headers, message):
        logger.error("Error message recieved - %s" % str(message))

    def on_message(self, headers, data):
        destination = headers['destination']

        logger.debug("Received frame destination: " + destination)
        logger.debug("Received frame body (data)" + data) 
        proc = subprocess.Popen(["python", "/usr/bin/PostProcessAdmin.py", destination, data])
        self.procList.append(proc)
        
        if len(self.procList) > 4:
          logger.info("There are " + str(len(self.procList)) + " processors running at the moment, wait for a second")
        
        while len(self.procList) > 4:
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
            logger.info("[%s] Subscribing to %s" % (self.consumer_name, queue))
            connection.subscribe(destination=queue, id=1, ack='auto')


def main():
    try:
        config = json.load(open('/etc/autoreduce/post_process_consumer.conf'))
    except:
        sys.exit()
        
    logger.info("Start post process asynchronous listener!")
    
    reactor.callWhenRunning(Consumer(config).run)
    reactor.run()
    logger.info("Stop post process asynchronous listener!")

if __name__ == '__main__':
    main()