import time
import sys

import stomp

class MyListener(object):
    def on_error(self, headers, message):
        print 'listener received an error %s' % message

    def on_message(self, headers, message):
        print 'listener received a message %s' % message

print 'Starting connection'
connection = stomp.Connection(host_and_ports=[('localhost', 61613)])
connection.set_listener('', MyListener())
connection.start()
connection.connect()
print 'subscribing'
connection.subscribe(destination='/queue/test', id=1, ack='auto')
print 'sending'
connection.send('/queue/test', ' '.join(sys.argv[1:]))
print 'sent'
time.sleep(2)
connection.disconnect()