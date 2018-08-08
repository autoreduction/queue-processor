"""
Test cases for the database client
"""
import unittest

from utils.clients.connection_exception import ConnectionException
from utils.clients.database_client import DatabaseClient
from utils.clients.settings.client_settings_factory import ClientSettingsFactory


class TestDatabaseClient(unittest.TestCase):
    """
    Exercises the database client
    """

    def setUp(self):
        self.incorrect_credentials = ClientSettingsFactory().create('database',
                                                                    username='not-user-name',
                                                                    password='not-password',
                                                                    host='not-host',
                                                                    port='not-port',
                                                                    database_name='not-db')

    # pylint:disable=protected-access
    def test_default_init(self):
        """ Test default values for initialisation """
        client = DatabaseClient()
        self.assertIsNotNone(client.credentials)
        self.assertIsNone(client._connection)
        self.assertIsNone(client._meta_data)
        self.assertIsNone(client._engine)

    def test_invalid_init(self):
        """ Test invalid values for initialisation """
        self.assertRaises(TypeError, DatabaseClient, 'string')

    # pylint:disable=protected-access
    def test_valid_connection(self):
        """ Test access is established with valid connection """
        client = DatabaseClient()
        client.connect()
        self.assertTrue(client._test_connection())

    def test_invalid_connection(self):
        """ Test access is rejected with invalid credentials """
        client = DatabaseClient(self.incorrect_credentials)
        with self.assertRaises(ConnectionException):
            client.connect()

    # pylint:disable=protected-access
    def test_stop_connection(self):
        """ Test connection can be successfully stopped gracefully """
        client = DatabaseClient()
        client.connect()
        self.assertTrue(client._test_connection())
        client.disconnect()
        self.assertIsNone(client._connection)
        self.assertIsNone(client._engine)
        self.assertIsNone(client._meta_data)
