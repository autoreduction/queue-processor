# -*- coding: utf-8 -*-
"""
Created on Wed May 27 14:37:59 2015

@author: xxu30744
"""
import time
import stomp
import logging

class StompClient(object):
    def __init__(self, brokers, user, password, topics=None, consumer_name='QueueProcessor'):
        self._brokers = brokers
        self._user = user
        self._password = password
        self._connection = None
        self._topics = topics
        self._consumer_name = consumer_name
        self._listener = None

    def get_connection(self):
        logging.info("connection =")
        connection = stomp.Connection(host_and_ports=self._brokers, use_ssl=True, ssl_version=3)
        logging.info("Starting connection")
        connection.start()
        logging.info("connection.connect")
        connection.connect(self._user, self._password, wait=False)

        time.sleep(0.5)
        return connection

    def connect(self):
        if self._connection is None or not self._connection.is_connected():
            logging.info("Disconnect")
            self._disconnect()
            logging.info("Connect")
            self._connection = self.get_connection()

    def _disconnect(self):
        if self._connection is not None and self._connection.is_connected():
            self._connection.disconnect()
        self._connection = None

    def stop(self):
        self._disconnect()
        if self._connection is not None:
            self._connection.stop()
        self._connection = None

    def send(self, destination, message, persistent='true', priority='4'):
        self.connect()
        self._connection.send(destination, message, persistent=persistent, priority=priority)
