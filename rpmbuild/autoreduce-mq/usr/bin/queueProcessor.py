import json, logging, time, subprocess, sys, socket

from twisted.internet import reactor, defer, task
from stompest import async, sync
from stompest.config import StompConfig
from stompest.async.listener import SubscriptionListener
from stompest.protocol import StompSpec, StompFailoverUri
from Configuration import Configuration


class Consumer(object):
        
    def __init__(self, config):
        self.stompConfig = StompConfig(config.brokers, config.amq_user, config.amq_pwd)
        self.config = config
        self.procList = []
        
    @defer.inlineCallbacks
    def run(self):
        client = yield async.Stomp(self.stompConfig).connect()
        headers = {
            # client-individual mode is necessary for concurrent processing
            # (requires ActiveMQ >= 5.2)
            StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL,
            # the maximal number of messages the broker will let you work on at the same time
            'activemq.prefetchSize': '1',
        }

        for q in self.config.queues:
            client.subscribe(q, headers, listener=SubscriptionListener(self.consume, errorDestination=self.config.postprocess_error))
        
        #print "finished run"
    
    def consume(self, client, frame):
        """
        NOTE: you can return a Deferred here
        """
        headers = frame.headers
        destination = headers['destination']
        data = frame.body

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

class HeartBeat(object):

    def __init__(self, config):
        self.stompConfig = StompConfig(config.brokers, config.amq_user, config.amq_pwd)
        self.config = config


    def count(self):
        logging.info("In HeartBeat.count")
        stomp = sync.Stomp(self.stompConfig)
        stomp.connect()
        data_dict = {"src_name": socket.gethostname(), "status": "0"}
        stomp.send(self.config.heart_beat, json.dumps(data_dict))
        logging.info("called " + self.config.heart_beat + " --- " + json.dumps(data_dict))
        stomp.disconnect() 
    

if __name__ == '__main__':
    
    try:
        config = Configuration('/etc/autoreduce/post_process_consumer.conf')
    except:
        sys.exit()
        
    logging.info("Start post process asynchronous listener!")
    
    #l = task.LoopingCall(HeartBeat(config).count)
    #l.start(5.0) # call every second

    reactor.callWhenRunning(Consumer(config).run)
    reactor.run()
    logging.info("Stop post process asynchronous listener!")
