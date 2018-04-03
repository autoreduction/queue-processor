"""
Test class for sending messages to the ActiveMQ queue
"""
from __future__ import print_function
import json
import logging

import stomp
from testconfig import LOG_FILENAME, ACTIVEMQ

logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


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


def send(destination_queue, message, persistent='true'):
    """
    Send a message to a queue
    @param destination_queue: name of the queue
    @param message: message content
    @param persistent: message persistence
    """

    print("Before attempting to connect to ActiveMQ")
    conn = stomp.Connection(host_and_ports=ACTIVEMQ['broker'],
                            use_ssl=ACTIVEMQ['SSL'], ssl_version=3)
    print("After attempting to connect to ActiveMQ")

    print("Start")
    conn.set_listener('', MyListener())
    conn.start()
    print("Connect")
    conn.connect(ACTIVEMQ['username'], ACTIVEMQ['password'], wait=False)
    print("send")
    conn.send(destination_queue, message, persistent=persistent, priority='4')
    print("Message send with information:")
    print("%s: %s" % ("destination", destination_queue))
    print("%s: %s" % ("message", message))

    conn.disconnect()


DESTINATION = '/queue/ReductionPending'

# Example for testing
REDUCTION_SCRIPT = open('reduce.py').read()
TEST_DATA = '\\isis\\NDXGEM\\Instrument\\data\\cycle_15_1\\GEM75513.nxs'
MESSAGE = {"run_number": "75513", "rb_number": "1510188", "facility": "ISIS",
           "run_version": 0, "instrument": "GEM", "reduction_script": REDUCTION_SCRIPT,
           "data": TEST_DATA,
           "reduction_arguments": {"advanced_vars": {"var_6": [2, 0.5],
                                                     "var_5": [0, 7]},
                                   "standard_vars": {"var_4": [22413, 22450],
                                                     "var_3": [2.87],
                                                     "var_2": "5,2,4,30.0",
                                                     "var_1": "-3,-5,-4,-5.0"}}}

send(DESTINATION, json.dumps(MESSAGE))
