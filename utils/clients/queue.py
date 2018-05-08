"""
Used to create a connection to the queue system
Current implementation is ActiveMQ
"""
import stomp
from utils.clients.test_settings import ACTIVEMQ


def make_queue_session():
    """
    Create an activeMq session
    :return: the connection to the queueing system
    """
    brokers = [(ACTIVEMQ['brokers'].split(':')[0],
                int(ACTIVEMQ['brokers'].split(':')[1]))]
    connection = stomp.Connection(host_and_ports=brokers, use_ssl=False)
    connection.start()
    connection.connect(ACTIVEMQ['amq_user'],
                       ACTIVEMQ['amq_pwd'],
                       wait=False,
                       header={'activemq.prefetchSize': '1'})
    return connection
