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

from unittest.mock import patch
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
        """
        Test: Class variables are created and set
        When: DatabaseClient is initialised with default credentials
        """
        client = DatabaseClient()
        self.assertIsNotNone(client.credentials)
        self.assertIsNone(client._connection)
        self.assertIsNone(client._meta_data)
        self.assertIsNone(client._engine)

    def test_invalid_init(self):
        """
        Test: A TypeError is raised
        When: DatabaseClient is initialised with invalid credentials
        """
        self.assertRaises(TypeError, DatabaseClient, 'string')

    def test_valid_connection(self):
        """
        Test: Access is established with a valid connection
        When: connect is called while valid credentials are held
        """
        client = DatabaseClient()
        client.connect()
        self.assertTrue(client._test_connection())

    def test_get_connection(self):
        """
        Test: get_connection returns the a connect Session or None
        (depending on whether connect has been called)
        When: get_connection is called
        """
        client = DatabaseClient()
        self.assertIsNone(client.get_connection())
        client.connect()
        self.assertIsInstance(client.get_connection(), Session)

    @patch('utils.clients.database_client.DatabaseClient._test_connection')
    def test_double_connect(self, mock_test_connection):
        """
        Test: The existing (rather than a new) connection is returned
        When: connect is called while a valid connection is currently established
        """
        client = DatabaseClient()
        connection_1 = client.connect()
        connection_2 = client.connect()
        mock_test_connection.assert_called_once()
        self.assertEqual(connection_1, connection_2)

    def test_invalid_connection(self):
        """
        Test: A ConnectionException is raised
        When: connect is called while invalid connection are held
        """
        client = DatabaseClient(self.incorrect_credentials)
        with self.assertRaises(ConnectionException):
            client.connect()

    def test_stop_connection(self):
        """
        Test: Connection is stopped and connection variables are set to None
        When: disconnect is called while a valid connection is currently established
        """
        client = DatabaseClient()
        client.connect()
        self.assertTrue(client._test_connection())
        client.disconnect()
        self.assertIsNone(client._connection)
        self.assertIsNone(client._engine)
        self.assertIsNone(client._meta_data)
        self.assertRaises(AttributeError, client._test_connection)

    @patch('sqlalchemy.engine.result.ResultProxy.fetchall')
    def test_re_raise_unexpected_exception(self, mock_execute):
        """
        Test: _test_connection re-raises an exception 'as is'
        When: The connection raises an exception that is not a connection related error
        (which is handled as a special case)
        """
        client = DatabaseClient()
        client.connect()

        def raise_runtime_error():
            raise RuntimeError()
        mock_execute.side_effect = raise_runtime_error
        self.assertRaises(RuntimeError, client._test_connection)

    def test_instrument_table(self):
        """
        Test: An Instrument object is created and returned with a Table object stored within
        When: instrument is called
        """
        client = DatabaseClient()
        client.connect()
        instrument_table = client.instrument()
        self.assertEqual(type(instrument_table.__bases__[0]), type(declarative_base()))
        self.assertIsNotNone(instrument_table.__table__)

    def test_reduction_run_table(self):
        """
        Test: A ReductionRun object is created and returned with a Table object stored within
        When: reduction_run is called
        """
        client = DatabaseClient()
        client.connect()
        reduction_run_table = client.reduction_run()
        self.assertEqual(type(reduction_run_table.__bases__[0]), type(declarative_base()))
        self.assertIsNotNone(reduction_run_table.__table__)
