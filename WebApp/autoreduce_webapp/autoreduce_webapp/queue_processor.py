"""
Handles QueueProcessor interactions from the WebApp
"""
import time
import sys
import os
import logging.config

import django
import stomp
from WebApp.autoreduce_webapp.autoreduce_webapp.settings import ACTIVEMQ, BASE_DIR, LOGGING

logging.config.dictConfig(LOGGING)
LOGGER = logging.getLogger("django")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
sys.path.insert(0, BASE_DIR)

django.setup()


class Client(object):
    """
    Client for ActiveMQ connection
    """
    # pylint: disable=too-many-instance-attributes, too-many-arguments
    def __init__(self, brokers, user, password, topics=None,
                 consumer_name='QueueProcessor', client_only=True,
                 use_ssl=ACTIVEMQ['SSL']):
        self._brokers = brokers
        self._user = user
        self._password = password
        self._connection = None
        self._topics = topics
        self._consumer_name = consumer_name
        self._client_only = client_only
        self._use_ssl = use_ssl

    def get_connection(self):
        """
        Create the connection to ActiveMQ
        :return: a connection to the ActiveMQ service
        """
        LOGGER.info("[%s] Connecting to %s", self._consumer_name, str(self._brokers))

        connection = stomp.Connection(host_and_ports=self._brokers,
                                      use_ssl=self._use_ssl, ssl_version=3)
        connection.start()
        connection.connect(self._user, self._password, wait=False)

        time.sleep(0.5)
        return connection

    def connect(self):
        """
        Start connection to activeMQ
        """
        if self._connection is None or not self._connection.is_connected():
            self._disconnect()
            self._connection = self.get_connection()
        for queue in self._topics:
            LOGGER.info("[%s] Subscribing to %s", self._consumer_name, queue)
            self._connection.subscribe(destination=queue, id="1", ack='auto')

    def _disconnect(self):
        """
        disconnect the connection to the queue
        :return:
        """
        if self._connection is not None and self._connection.is_connected():
            self._connection.disconnect()
        self._connection = None
        LOGGER.info("[%s] Disconnected", self._consumer_name)

    def stop(self):
        """
        Stop the current connection to queue
        :return:
        """
        self._disconnect()
        if self._connection is not None:
            self._connection.stop()
        self._connection = None

    def send(self, destination, message, persistent='true', priority='4', delay=None):
        """
        Send a message to a given Queue
        :param destination: The queue to send to
        :param message: the message content
        :param persistent: persistence of the message
        :param priority: message priority
        :param delay: delay in message sending
        """
        LOGGER.info('SENDING MESSAGE to %s', destination)
        LOGGER.info(message)
        if self._connection is None or not self._connection.is_connected():
            self._disconnect()
            self._connection = self.get_connection()

        headers = {}
        if delay:
            headers['AMQ_SCHEDULED_DELAY'] = str(delay)
        self._connection.send(destination, message, persistent=persistent,
                              priority=priority, headers=headers)
        LOGGER.debug("[%s] send message to %s", self._consumer_name, destination)


def main():
    """
    Run the client to start the connection to ActiveMQ
    """
    client = Client(ACTIVEMQ['broker'], ACTIVEMQ['username'],
                    ACTIVEMQ['password'], ACTIVEMQ['topics'],
                    'Autoreduction_QueueProcessor', False,
                    ACTIVEMQ['SSL'])
    client.connect()
    return client


if __name__ == '__main__':
    main()
