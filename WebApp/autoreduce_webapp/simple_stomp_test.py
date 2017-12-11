import time
import sys

import stomp

from autoreduce_webapp.settings import ACTIVEMQ


class MyListener(object):
    def on_error(self, headers, message):
        print 'listener received an error %s' % message

    def on_message(self, headers, message):
        print 'listener received a message %s' % message

        
print('Starting connection to ' + str(ACTIVEMQ['broker'][0]))
print ACTIVEMQ['broker']
connection = stomp.Connection(host_and_ports=ACTIVEMQ['broker'], use_ssl=ACTIVEMQ['SSL'])
print 'Have connection'
connection.set_listener('', MyListener())
print 'Starting connection'
connection.start()
print 'Connecting'
connection.connect(ACTIVEMQ['username'], ACTIVEMQ['password'], wait=False)
print('subscribing')
connection.subscribe(destination='/queue/test', id=1, ack='auto')
print('sending')
connection.send('/queue/test', ' '.join(sys.argv[1:]))
print('sent')
time.sleep(2)
connection.disconnect()
