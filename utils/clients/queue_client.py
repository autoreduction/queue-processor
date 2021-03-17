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
import uuid

import stomp
from stomp.exception import ConnectFailedException

from model.message.message import Message
from utils.clients.abstract_client import AbstractClient
from utils.clients.connection_exception import ConnectionException
from utils.settings import ACTIVEMQ_SETTINGS


class QueueClient(AbstractClient):
    """
    Class for client to access messaging service via python
    """
    def __init__(self, credentials=None, consumer_name='queue_client'):
        if not credentials:
            credentials = ACTIVEMQ_SETTINGS
        super(QueueClient, self).__init__(credentials)  # pylint:disable=super-with-arguments
        self._connection = None
        self._consumer_name = consumer_name
        self._logger = logging.getLogger("queue_listener")

    # pylint:disable=arguments-differ
    def connect(self, listener=None):
        """
        Create the connection if the connection has not been created
        :param listener: A ConnectionListener object to assign to the stomp connection, optionally
        """
        if self._connection is None or not self._connection.is_connected():
            self.disconnect()
            self._create_connection(listener)

    def _test_connection(self):
        if not self._connection.is_connected():
            raise ConnectionException("ActiveMQ")
        return True

    def disconnect(self):
        """
        Disconnect from queue service
        """
        self._logger.info("Starting disconnect from ActiveMQ...")
        if self._connection is not None and self._connection.is_connected():
            # By passing a receipt Stomp will call stop on the transport layer
            # which causes it to wait on the listener thread (if it's still
            # running). Without this step we just drop out, so the behaviour
            # is not guaranteed. UUID is used by Stomp if we don't pass in
            # a receipt so this matches the behaviour under the hood
            self._connection.disconnect(receipt=str(uuid.uuid4()))
            self._logger.info("Disconnected from ActiveMQ.")
        self._connection = None

    def _create_connection(self, listener=None):
        """
        Create the connection to the queuing service and store as self._connection
        :param listener: A ConnectionListener object to assign to the stomp connection, optionally
        """
        if self._connection is None or not self._connection.is_connected():
            try:
                host_port = [(self.credentials.host, int(self.credentials.port))]
                connection = stomp.Connection(host_and_ports=host_port, use_ssl=False)
                if listener:
                    connection.set_listener('Autoreduction', listener)
                self._logger.info("Starting connection to %s", host_port)
                connection.connect(username=self.credentials.username, passcode=self.credentials.password, wait=True)
            except ConnectFailedException as exp:
                raise ConnectionException("ActiveMQ") from exp
            # Sleep required to avoid using the service too quickly after establishing connection
            # time.sleep(0.5)
            self._connection = connection

    def subscribe_queues(self, queue_list, consumer_name, listener):
        """
        Subscribe a listener to the provided queues
        :param queue_list: The queue(s) to subscribe to as a string or list of strings
        :param consumer_name: A name to assign to the consumer
        :param listener: A ConnectionListener object to assign to the stomp connection, optionally
        """
        if not isinstance(queue_list, list):
            queue_list = [queue_list]
        self._connection.set_listener(consumer_name, listener)
        for queue in queue_list:
            # prefetchSize limits the processing to 1 message at a time
            self._connection.subscribe(destination=queue,
                                       id=str(uuid.uuid4()),
                                       ack="client-individual",
                                       header={'activemq.prefetchSize': '1'})
            self._logger.info("[%s] Subscribing to %s", consumer_name, queue)
        self._logger.info("Successfully subscribed to all of the queues")

    def subscribe_autoreduce(self, consumer_name, listener):
        """
        Subscribe to queues including DataReady
        :param consumer_name: A name to assign to the consumer
        :param listener: A ConnectionListener object to assign to the stomp connection, optionally
        """
        self.subscribe_queues(queue_list=[self.credentials.data_ready], consumer_name=consumer_name, listener=listener)

    def ack(self, message_id, subscription):
        """
        Acknowledge receipt of a message
        :param message_id: The identifier of the message
        """
        # pylint:disable=no-value-for-parameter
        self._connection.ack(message_id, subscription)

    # pylint:disable=too-many-arguments
    def send(self, destination, message, persistent='true', priority='4', delay=None):
        """
        Send a message via the open connection to a queue
        :param destination: Queue to send to
        :param message: Message instance OR json dump of dict containing message payload
        :param persistent: should to message be persistent
        :param priority: priority rating of the message
        :param delay: time to wait before send
        """
        self.connect()

        if isinstance(message, Message):
            message_json_dump = message.serialize()
        else:
            message_json_dump = message

        self._connection.send(destination, message_json_dump, persistent=persistent, priority=priority, delay=delay)
