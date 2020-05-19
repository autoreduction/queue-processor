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

from utils.clients.connection_exception import ConnectionException
from utils.clients.database_client import DatabaseClient


# pylint:disable=missing-docstring,protected-access,invalid-name
class TestDatabaseClient(unittest.TestCase):
    """
    Exercises the database client
    """

    def test_default_init(self):
        """
        Test: Class variables are created and set
        When: DatabaseClient is initialised with default credentials
        """
        client = DatabaseClient()
        self.assertIsNone(client.data_model)
        self.assertIsNone(client.variable_model)

    def test_valid_connection(self):
        """
        Test: Access is established with a valid connection
        When: connect is called while valid credentials are held
        """
        client = DatabaseClient()
        client.connect()
        self.assertTrue(client._test_connection())

    def test_model_access_after_connect(self):
        """
        Test: Models variables can be accessed
        When: connect has been called successfully
        """
        client = DatabaseClient()
        client.connect()
        self.assertIsNotNone(client.data_model)
        self.assertIsNotNone(client.variable_model)
        self.assertIsNotNone(client.data_model.Instrument.objects.first())
        self.assertIsNotNone(client.variable_model.Variable.objects.first())

    @patch('utils.clients.database_client.DatabaseClient.data_model')
    @patch('utils.clients.database_client.DatabaseClient.variable_model')
    def test_invalid_connection(self, mock_var_query, mock_data_query):
        """
        Test: A ConnectionException is raised
        When: connect is called while invalid connection are held
        """
        mock_data_query.Instrument.objects.first.side_effect = RuntimeError
        mock_var_query.Instrument.objects.first.side_effect = RuntimeError
        client = DatabaseClient()
        self.assertRaises(ConnectionException, client._test_connection)

    def test_stop_connection(self):
        """
        Test: Connection is stopped and connection variables are set to None
        When: disconnect is called while a valid connection is currently established
        """
        client = DatabaseClient()
        client.connect()
        self.assertTrue(client._test_connection())
        client.disconnect()
        self.assertIsNone(client.data_model)
        self.assertIsNone(client.variable_model)
