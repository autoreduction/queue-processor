"""
This is a script you may find useful to test if
you can subscribe and pass messages to activemq

To run the script type : python stompActiveMQtest TEXT
which should return back: received a message TEXT
"""
from __future__ import print_function
import logging
import time
import sys
import stomp

from scripts.activemq_tests.settings import ACTIVEMQ
from utils.project.structure import get_log_file
from utils.project.static_content import LOG_FORMAT

logging.basicConfig(filename=get_log_file('activemq_test.log'), level=logging.DEBUG,
                    format=LOG_FORMAT)


class MyListener(stomp.ConnectionListener):
    """
    prints output from errors and messages
    """
    def on_error(self, headers, body):
        """On an error being received"""
        print('received an error %s' % body)

    def on_message(self, headers, body):
        """On a message being received"""
        print('received a message %s' % body)


CONN = stomp.Connection(host_and_ports=ACTIVEMQ['broker'], use_ssl=ACTIVEMQ['SSL'], ssl_version=3)

CONN.set_listener('', MyListener())
CONN.start()
CONN.connect(ACTIVEMQ['username'], ACTIVEMQ['password'], wait=False)

CONN.subscribe(destination='/queue/test', id=1, ack='auto')
CONN.send(body=' '.join(sys.argv[1:]), destination='/queue/test')

time.sleep(2)
CONN.disconnect()
