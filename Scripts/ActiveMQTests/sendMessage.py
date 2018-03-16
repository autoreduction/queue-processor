import sys
import stomp
import json
import time

from testconfig import LOG_FILENAME, ACTIVEMQ

import logging
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


class MyListener(stomp.ConnectionListener):
    def on_error(self, headers, message):
        print('received an error %s' % message)
    def on_message(self, headers, message):
        print('received a message %s' % message)


def send(destination, message, persistent='true'):
    """
    Send a message to a queue
    @param destination: name of the queue
    @param message: message content
    """

    print("Before attempting to connect to ActiveMQ")
    conn = stomp.Connection(host_and_ports=ACTIVEMQ['broker'], use_ssl=ACTIVEMQ['SSL'], ssl_version=3)
    print("After attempting to connect to ActiveMQ")

    print("Start")
    conn.set_listener('', MyListener())
    conn.start()
    print("Connect")
    conn.connect(ACTIVEMQ['username'], ACTIVEMQ['password'], wait=False)
    print("send")
    conn.send(destination, message, persistent='true', priority='4')
    print("Message send with information:")
    print("%s: %s" % ("destination", destination))
    print("%s: %s" % ("message", message))

    conn.disconnect()

destination = '/queue/ReductionPending'

# Example for testing
reduction_script=open('reduce.py').read()
testdata='\\isis\\NDXGEM\\Instrument\\data\\cycle_15_1\\GEM75513.nxs'
message2={"run_number": "75513", "rb_number": "1510188", "facility": "ISIS", "run_version": 0, "instrument": "GEM", "reduction_script": reduction_script, "data": testdata, "reduction_arguments": {"advanced_vars": {"var_6": [2, 0.5], "var_5": [0, 7]}, "standard_vars": {"var_4": [22413, 22450], "var_3": [2.87], "var_2": "5,2,4,30.0", "var_1": "-3,-5,-4,-5.0"}}}

send(destination, json.dumps(message2))
