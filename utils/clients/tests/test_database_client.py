# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the database client
"""
import unittest

from mock import patch
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.session import Session

from utils.clients.connection_exception import ConnectionException
from utils.clients.database_client import DatabaseClient
from utils.clients.settings.client_settings_factory import ClientSettingsFactory


# pylint:disable=missing-docstring,protected-access,invalid-name
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

    def test_valid_connection(self):
        """ Test access is established with valid connection """
        client = DatabaseClient()
        client.connect()
        self.assertTrue(client._test_connection())

    def test_get_connection(self):
        client = DatabaseClient()
        self.assertIsNone(client.get_connection())
        client.connect()
        self.assertIsInstance(client.get_connection(), Session)

    @patch('utils.clients.database_client.DatabaseClient._test_connection')
    def test_double_connect(self, mock_test_connection):
        client = DatabaseClient()
        connection_1 = client.connect()
        connection_2 = client.connect()
        # Test that we do not attempt to reconnect if a valid connection is already established
        mock_test_connection.assert_called_once()
        self.assertEqual(connection_1, connection_2)

    def test_invalid_connection(self):
        """ Test access is rejected with invalid credentials """
        client = DatabaseClient(self.incorrect_credentials)
        with self.assertRaises(ConnectionException):
            client.connect()

    def test_stop_connection(self):
        """ Test connection can be successfully stopped gracefully """
        client = DatabaseClient()
        client.connect()
        self.assertTrue(client._test_connection())
        client.disconnect()
        self.assertIsNone(client._connection)
        self.assertIsNone(client._engine)
        self.assertIsNone(client._meta_data)

    @patch('sqlalchemy.engine.result.ResultProxy.fetchall')
    def test_re_raise_unexpected_exception(self, mock_execute):
        client = DatabaseClient()
        client.connect()

        def raise_runtime_error():
            raise RuntimeError()
        mock_execute.side_effect = raise_runtime_error
        self.assertRaises(RuntimeError, client._test_connection)

    def test_instrument_table(self):
        client = DatabaseClient()
        client.connect()
        instrument_table = client.instrument()
        self.assertEqual(type(instrument_table.__bases__[0]), type(declarative_base()))
        self.assertIsNotNone(instrument_table.__table__)

    def test_reduction_run_table(self):
        client = DatabaseClient()
        client.connect()
        reduction_run_table = client.reduction_run()
        self.assertEqual(type(reduction_run_table.__bases__[0]), type(declarative_base()))
        self.assertIsNotNone(reduction_run_table.__table__)
