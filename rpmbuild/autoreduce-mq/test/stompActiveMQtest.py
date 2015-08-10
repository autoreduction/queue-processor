# This is a script you may find useful to test if 
# you can subscribe and pass messages to activemq
# 
# To run the script type : python stompActiveMQtest TEXT 
# which should return back: received a message TEXT

import time
import sys

import stomp

import logging
LOG_FILENAME = 'stompActiveMQtest_logging.out'
logging.basicConfig(filename=LOG_FILENAME,
                    level=logging.DEBUG,
                    )


class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error %s' % message)
    def on_message(self, headers, message):
        print('received a message %s' % message)


brokers = [("localhost", 61613)]

# depending on which <transportConnectors> you have setup in
# /opt/activemq/conf/activemq.xml
# you may access activemq with or without ssl
conn = stomp.Connection(host_and_ports=brokers)
#conn = stomp.Connection(host_and_ports=brokers, use_ssl=True, ssl_version=3)

conn.set_listener('', MyListener())
conn.start()

# if you have setup simpleAuthentication in /opt/activemq/conf/activemq.xml
# then put in username and password 
conn.connect('autoreduce', 'xxxxxxxx', wait=False)

conn.subscribe(destination='/queue/test', id=1, ack='auto')
conn.send(body=' '.join(sys.argv[1:]), destination='/queue/test')

time.sleep(2)
conn.disconnect()
