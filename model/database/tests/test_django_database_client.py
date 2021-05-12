# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the django database client
"""
import unittest

from unittest.mock import patch
from autoreduce_utils.clients.connection_exception import ConnectionException

from model.database.django_database_client import DatabaseClient


# pylint:disable=protected-access
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
        self.assertIsNotNone(client.data_model.Instrument.objects.all())
        self.assertIsNotNone(client.variable_model.Variable.objects.all())

    @patch('utils.clients.django_database_client.DatabaseClient.data_model')
    @patch('utils.clients.django_database_client.DatabaseClient.variable_model')
    def test_invalid_connection(self, mock_var_query, mock_data_query):
        """
        Test: A ConnectionException is raised
        When: connect is called while invalid connection are held
        """
        mock_data_query.Instrument.objects.first.side_effect = RuntimeError
        mock_var_query.Instrument.objects.first.side_effect = RuntimeError
        client = DatabaseClient()
        self.assertRaises(ConnectionException, client._test_connection)

    def test_disconnect_client(self):
        """
        Test: Connection is stopped and connection variables are set to None
        When: disconnect is called while a valid connection is currently established
        """
        django_client = DatabaseClient()
        django_client.connect()
        self.assertTrue(django_client._test_connection())
        django_client.disconnect()
        self.assertIsNone(django_client.data_model)
        self.assertIsNone(django_client.variable_model)
