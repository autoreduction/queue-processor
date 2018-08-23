"""
Test functionality for the activemq client
"""
import unittest

from utils.clients.connection_exception import ConnectionException
from utils.clients.queue_client import QueueClient
from utils.clients.settings.client_settings_factory import ClientSettingsFactory


class TestQueueClient(unittest.TestCase):
    """
    Exercises the queue client
    """
    def setUp(self):
        self.incorrect_credentials = ClientSettingsFactory().create('queue',
                                                                    username='not-user',
                                                                    password='not-pass',
                                                                    host='not-host',
                                                                    port='1234')

    # pylint:disable=protected-access
    def test_default_init(self):
        """ Test default values for initialisation """
        client = QueueClient()
        self.assertIsNotNone(client.credentials)
        self.assertIsNone(client._connection)
        self.assertEqual('QueueProcessor', client._consumer_name)

    def test_invalid_init(self):
        """ Test invalid values for initialisation """
        self.assertRaises(TypeError, QueueClient, 'string')

    # pylint:disable=protected-access
    def test_valid_connection(self):
        """
        Test connection with valid credentials
        This by proxy will also test the get_connection function
        """
        client = QueueClient()
        client.connect()
        self.assertTrue(client._connection.is_connected())

    def test_invalid_connection(self):
        """ Test connection with invalid credentials """
        client = QueueClient(self.incorrect_credentials)
        with self.assertRaises(ConnectionException):
            client.connect()

    # pylint:disable=protected-access
    def test_stop_connection(self):
        """ Test connection can be stopped gracefully """
        client = QueueClient()
        client.connect()
        self.assertTrue(client._connection.is_connected())
        client.disconnect()
        self.assertIsNone(client._connection)

    # pylint:disable=no-self-use
    def test_send_data(self):
        """ Test data can be sent without error """
        client = QueueClient()
        client.send('dataready', 'test-message')
