import sys
import stomp
import json
import time

def send(destination, message, persistent='true'):
    """
    Send a message to a queue
    @param destination: name of the queue
    @param message: message content
    """

    # specify ActiveMQ address
    brokers = [("localhost", 61613)]

    conn = stomp.Connection(host_and_ports=brokers)

    conn.start()
    conn.connect()
    conn.send(destination=destination, message=message, persistent=persistent)
    print "%s: %s" % ("destination", destination)
    print "%s: %s" % ("message", message)

    conn.disconnect()

destination = '/queue/REDUCTION.DATA_READY'

message1={"proposal": "RB-1310123", "instrument": "HRPD", "data_file": "/home/ajm64/tmp/testdata/testData.txt", "run_number": 39592, "facility": "ISIS"}

send(destination, json.dumps(message1))
