# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Client class for accessing queuing service
"""
import logging
import time

import stomp
from stomp.exception import ConnectFailedException

from utils.clients.abstract_client import AbstractClient
from utils.clients.connection_exception import ConnectionException
from utils.settings import ACTIVEMQ_SETTINGS
from utils.project.structure import get_log_file
from utils.project.static_content import LOG_FORMAT

logging.basicConfig(filename=get_log_file('queue_client.log'), level=logging.INFO,
                    format=LOG_FORMAT)


class QueueClient(AbstractClient):
    """
    Class for client to access messaging service via python
    """
    def __init__(self, credentials=None, consumer_name='QueueProcessor'):
        if not credentials:
            credentials = ACTIVEMQ_SETTINGS
        super(QueueClient, self).__init__(credentials)
        self._connection = None
        self._consumer_name = consumer_name
        self._autoreduce_queues = self.credentials.all_subscriptions

    def connect(self):
        """
        Create the connection if the connection has not been created
        :return: connection object
        """
        if self._connection is None or not self._connection.is_connected():
            self.disconnect()
            return self._create_connection()
        return self._connection

    def _test_connection(self):
        if not self._connection.is_connected():
            raise ConnectionException("ActiveMQ")
        return True

    def disconnect(self):
        """
        disconnect from queue service
        """
        logging.info("Disconnecting from activemq")
        if self._connection is not None and self._connection.is_connected():
            self._connection.disconnect()
        self._connection = None

    def _create_connection(self):
        """
        Get the connection to the queuing service
        :return: The connection to the queue
        """
        if self._connection is None or not self._connection.is_connected():
            try:
                host_port = [(self.credentials.host, int(self.credentials.port))]
                connection = stomp.Connection(host_and_ports=host_port,
                                              use_ssl=False)

                logging.info("Starting connection to %s", host_port)
                connection.connect(username=self.credentials.username,
                                   passcode=self.credentials.password,
                                   wait=False,
                                   header={'activemq.prefetchSize': '1'})
            except ConnectFailedException:
                raise ConnectionException("ActiveMQ")
            # Sleep required to avoid using the service too quickly after establishing connection
            time.sleep(0.5)
            self._connection = connection
        return self._connection

    def subscribe_queues(self, queue_list, consumer_name, listener, ack='auto'):
        """
        Subscribe a listener to the provided queues
        """
        self._connection.set_listener(consumer_name, listener)
        for queue in queue_list:
            self._connection.subscribe(destination=queue,
                                       id='1',
                                       ack=ack,
                                       header={'activemq.prefetchSize': '1'})
            logging.info("[%s] Subscribing to %s", consumer_name, queue)
        logging.info("Successfully subscribed to all of the queues")

    def subscribe_autoreduce(self, consumer_name, listener, ack='auto'):
        """
        Subscribe to queues including DataReady
        """
        self.subscribe_queues(queue_list=self.credentials.all_subscriptions,
                              consumer_name=consumer_name,
                              listener=listener,
                              ack=ack)

    def subscribe_amq(self, consumer_name, listener, ack='auto'):
        """
        Subscribe to ReductionPending
        """
        self.subscribe_queues(queue_list=self.credentials.reduction_pending,
                              consumer_name=consumer_name,
                              listener=listener,
                              ack=ack)

    def ack(self, frame):
        """
        Acknowledge receipt of a message
        """
        # pylint:disable=no-value-for-parameter
        self._connection.ack(frame)

    @staticmethod
    def serialise_data(rb_number, instrument, location, run_number, started_by):
        """
        Packs the specified data into a dictionary ready to send to a processor queue
        """
        return {'rb_number': rb_number,
                'instrument': instrument,
                'data': location,
                'run_number': run_number,
                'facility': 'ISIS',
                'started_by': started_by}

    # pylint:disable=too-many-arguments
    def send(self, destination, message, persistent='true', priority='4', delay=None):
        """
        Send a message via the open connection to a queue
        :param destination: Queue to send to
        :param message: contents of the message
        :param persistent: should to message be persistent
        :param priority: priority rating of the message
        :param delay: time to wait before send
        """
        self.connect()
        self._connection.send(destination, message,
                              persistent=persistent,
                              priority=priority,
                              delay=delay)
