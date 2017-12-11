# This is a script you may find useful to test if 
# you can subscribe and pass messages to activemq
# 
# To run the script type : python stompActiveMQtest TEXT 
# which should return back: received a message TEXT

import time
import sys
import stomp

from testconfig import LOG_FILENAME, ACTIVEMQ

import logging
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error %s' % message)
    def on_message(self, headers, message):
        print('received a message %s' % message)



conn = stomp.Connection(host_and_ports=ACTIVEMQ['broker'], use_ssl=ACTIVEMQ['SSL'], ssl_version=3)

conn.set_listener('', MyListener())
conn.start()
conn.connect(ACTIVEMQ['username'], ACTIVEMQ['password'], wait=False)

conn.subscribe(destination='/queue/test', id=1, ack='auto')
conn.send(body=' '.join(sys.argv[1:]), destination='/queue/test')

time.sleep(2)
conn.disconnect()
