# -*- coding: utf-8 -*-
"""
Created on Wed May 27 14:37:59 2015

@author: xxu30744
"""
import logging
import time

import stomp

from utils.settings import ACTIVEMQ


class QueueClient(object):
    """
    Class for client to access messaging service via python
    """
    # pylint: disable=too-many-arguments
    def __init__(self, brokers=None, user=None, password=None, consumer_name='QueueProcessor'):
        """
        Initialise variable, if input is None, values from the settings file are used
        """
        default_broker = [(ACTIVEMQ['brokers'].split(':')[0],
                           int(ACTIVEMQ['brokers'].split(':')[1]))]
        self._brokers = self._use_default_if_none(brokers, default_broker)
        self._user = self._use_default_if_none(user, ACTIVEMQ['amq_user'])
        self._password = self._use_default_if_none(password, ACTIVEMQ['amq_pwd'])
        self._connection = None
        self._consumer_name = consumer_name
        self._autoreduce_queues = [ACTIVEMQ['data_ready'],
                                   ACTIVEMQ['reduction_started'],
                                   ACTIVEMQ['reduction_complete'],
                                   ACTIVEMQ['reduction_error']]
        self._amq_queues = ACTIVEMQ['amq_queues']

    @staticmethod
    def _use_default_if_none(input_var, default):
        """
        :param input_var: Input to the class (could be None)
        :param default: The default value to use if input_var is None
        """
        if input_var is None:
            return default
        return input_var

    def get_connection(self):
        """
        Get the connection to the queuing service
        :return: The connection to the queue
        """
        if self._connection is None or not self._connection.is_connected():
            logging.info("connection =")
            connection = stomp.Connection(host_and_ports=self._brokers,
                                          use_ssl=False)
            logging.info("Starting connection")
            connection.start()
            logging.info("connection.connect")
            connection.connect(self._user, self._password,
                               wait=False,
                               header={'activemq.prefetchSize': '1'})
            time.sleep(0.5)
            self._connection = connection
        return self._connection

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
        self.subscribe_queues(self._autoreduce_queues, consumer_name, listener, ack)

    def subscribe_amq(self, consumer_name, listener, ack='auto'):
        """
        Subscribe to ReductionPending
        """
        self.subscribe_queues(self._amq_queues, consumer_name, listener, ack)

    def ack(self, frame):
        """
        Acknowledge receipt of a message
        """
        self._connection.ack(frame)

    def stop(self):
        """
        disconnect and stop the connection to the service
        """
        self._disconnect()
        if self._connection is not None:
            self._connection.stop()
        self._connection = None

    def send(self, destination, message, persistent='true', priority='4', delay=None):
        """
        Send a message via the open connection to a queue
        :param destination: Queue to send to
        :param message: contents of the message
        :param persistent: should to message be persistent
        :param priority: priority rating of the message
        """
        self.connect()
        self._connection.send(destination, message,
                              persistent=persistent,
                              priority=priority,
                              delay=delay)
