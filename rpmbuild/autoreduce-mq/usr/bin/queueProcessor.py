import json, logging, time, subprocess, sys, socket
import logging.handlers
import stomp
from twisted.internet import reactor
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler('/var/log/autoreduction.log', maxBytes=104857600, backupCount=20)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
# Quiet the Stomp logs as they are quite chatty
logging.getLogger('stomp').setLevel(logging.DEBUG)


class Listener(object):
    def __init__(self, client):
        self._client = client
        self.procList = []

    def on_error(self, headers, message):
        logger.error("Error message recieved - %s" % str(message))

    def on_message(self, headers, data):
        self._client.ack(headers['message-id'], headers['subscription'])  # Remove message from queue

        process_num = 5  # processes allowed to run at one time
        destination = headers['destination']

        logger.debug("Received frame destination: " + destination)
        logger.debug("Recieved frame priority: " + headers["priority"])
        logger.debug("Calling: %s %s %s %s" % ("python", "/usr/bin/PostProcessAdmin.py", destination, data))

        proc = subprocess.Popen(["python", "/usr/bin/PostProcessAdmin.py", destination, data])
        self.procList.append(proc)
        
        if len(self.procList) >= process_num:
            logger.info("There are " + str(len(self.procList)) + " processes running at the moment, "
                                                                 "waiting until one is available")
        
        while len(self.procList) >= process_num:
            time.sleep(1.0)
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
        brokers = [(self.config['brokers'].split(':')[0],int(self.config['brokers'].split(':')[1]))]
        connection = stomp.Connection(host_and_ports=brokers, use_ssl=True, ssl_version=3)
        connection.set_listener(self.consumer_name, Listener(connection))
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
