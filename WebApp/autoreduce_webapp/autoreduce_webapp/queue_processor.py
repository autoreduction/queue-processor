import stomp
from settings import ACTIVEMQ, BASE_DIR, LOGGING, EMAIL_HOST, EMAIL_PORT, EMAIL_ERROR_RECIPIENTS, EMAIL_ERROR_SENDER, BASE_URL
import logging
import logging.config
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("django")
import time, sys, os, json, glob, base64
from django.utils import timezone
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
sys.path.insert(0, BASE_DIR)
from reduction_viewer.models import ReductionRun, ReductionLocation, DataLocation, Experiment
from reduction_viewer.utils import StatusUtils, InstrumentUtils, ReductionRunUtils
from reduction_variables.utils import MessagingUtils
from icat_communication import ICATCommunication
from django.db import connection
import smtplib
import django
django.setup()

class Client(object):
    def __init__(self, brokers, user, password, topics=None, consumer_name='QueueProcessor', client_only=True, use_ssl=ACTIVEMQ['SSL']):
        self._brokers = brokers
        self._user = user
        self._password = password
        self._connection = None
        self._topics = topics
        self._consumer_name = consumer_name
        self._client_only = client_only
        self._use_ssl = use_ssl

    def get_connection(self):
        logger.info("[%s] Connecting to %s" % (self._consumer_name, str(self._brokers)))

        connection = stomp.Connection(host_and_ports=self._brokers, use_ssl=self._use_ssl, ssl_version=3)
        connection.start()
        connection.connect(self._user, self._password, wait=False)

        time.sleep(0.5)
        return connection

    def connect(self):
        if self._connection is None or not self._connection.is_connected():
            self._disconnect()
            self._connection = self.get_connection()
        for queue in self._topics:
            logger.info("[%s] Subscribing to %s" % (self._consumer_name, queue))
            self._connection.subscribe(destination=queue, id=1, ack='auto')

    def _disconnect(self):
        if self._connection is not None and self._connection.is_connected():
            self._connection.disconnect()
        self._connection = None
        logger.info("[%s] Disconnected" % (self._consumer_name))

    def stop(self):
        self._disconnect()
        if self._connection is not None:
            self._connection.stop()
        self._connection = None

    def send(self, destination, message, persistent='true', priority='4', delay=None):
        logger.info('SENDING MESSAGE to %s' % destination)
        logger.info(message)
        if self._connection is None or not self._connection.is_connected():
            self._disconnect()
            self._connection = self.get_connection()
            
        headers = {}
        if delay:
            headers['AMQ_SCHEDULED_DELAY'] = str(delay)
        self._connection.send(destination, message, persistent=persistent, priority=priority, headers=headers)
        logger.debug("[%s] send message to %s" % (self._consumer_name, destination))


def main():
    client = Client(ACTIVEMQ['broker'], ACTIVEMQ['username'], ACTIVEMQ['password'], ACTIVEMQ['topics'], 'Autoreduction_QueueProcessor', False, ACTIVEMQ['SSL'])
    client.connect()
    return client

if __name__ == '__main__':
    main()
