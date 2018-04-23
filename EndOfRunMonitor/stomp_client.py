# -*- coding: utf-8 -*-
"""
Created on Wed May 27 14:37:59 2015

@author: xxu30744
"""
import logging
import time
import stomp


class StompClient(object):
    """
    Class for client to access messaging service via python
    """
    # pylint: disable=too-many-arguments
    def __init__(self, brokers, user, password, topics=None, consumer_name='QueueProcessor'):
        self._brokers = brokers
        self._user = user
        self._password = password
        self._connection = None
        self._topics = topics
        self._consumer_name = consumer_name
        self._listener = None

    def get_connection(self):
        """
        Get the connection to the queuing service
        :return: The connection to the queue
        """
        logging.info("connection =")
        connection = stomp.Connection(host_and_ports=self._brokers, use_ssl=True, ssl_version=3)
        logging.info("Starting connection")
        connection.start()
        logging.info("connection.connect")
        connection.connect(self._user, self._password, wait=False)

        time.sleep(0.5)
        return connection

    def connect(self):
        """
        Start the connection to the queue
        Will disconnect first if already connected
        """
        if self._connection is None or not self._connection.is_connected():
            logging.info("Disconnect")
            self._disconnect()
            logging.info("Connect")
            self._connection = self.get_connection()

    def _disconnect(self):
        """
        disconnect from queue service
        """
        if self._connection is not None and self._connection.is_connected():
            self._connection.disconnect()
        self._connection = None

    def stop(self):
        """
        disconnect and stop the connection to the service
        """
        self._disconnect()
        if self._connection is not None:
            self._connection.stop()
        self._connection = None

    def send(self, destination, message, persistent='true', priority='4'):
        """
        Send a message via the open connection to a queue
        :param destination: Queue to send to
        :param message: contents of the message
        :param persistent: should to message be persistent
        :param priority: priority rating of the message
        """
        self.connect()
        self._connection.send(destination, message, persistent=persistent, priority=priority)
