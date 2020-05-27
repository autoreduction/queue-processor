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

from mock import patch, Mock

from utils.clients.connection_exception import ConnectionException
from utils.clients.django_database_client import DatabaseClient


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
        self.assertIsNotNone(client.data_model.Instrument.objects.first())
        self.assertIsNotNone(client.variable_model.Variable.objects.first())

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

    def test_get_instrument_valid(self):
        """
        Test: The correct instrument object is returned
        When: get_instrument is called on a valid database connection
        """
        client = DatabaseClient()
        client.connect()
        actual = client.get_instrument('GEM')
        self.assertIsNotNone(actual)
        self.assertEqual('GEM', actual.name)

    @patch('utils.clients.django_database_client.DatabaseClient.save_record')
    def test_get_instrument_does_not_exist(self, mock_save):
        """
        Test: A new instrument record is created
        When: create is true and no matching instrument can be found in the database

        Note: As we do not actually save the object, we cannot assert values of it
        These are only stored when it enters the database
        """
        client = DatabaseClient()
        client.connect()
        actual = client.get_instrument('Not an instrument', create=True)
        self.assertIsNotNone(actual)
        self.assertIsInstance(actual, client.data_model.Instrument)
        mock_save.assert_called_once()

    def test_get_instrument_invalid(self):
        """
        Test: None is returned
        When: get_instrument is called with an instrument that does not exist
        """
        client = DatabaseClient()
        client.connect()
        actual = client.get_instrument('Fake instrument')
        self.assertIsNone(actual)

    def test_save_record(self):
        """
        Test: .save() is called on the provided object
        When: Calling save_record()
        """
        mock_record = Mock()
        DatabaseClient.save_record(mock_record)
        mock_record.save.assert_called_once()

    # pylint:disable=no-self-use
    def test_get_reduction_run_valid(self):
        """
        Test: A ReductionRun record is returned
        When: get_reduction_run is called with values that match a database record
        """
        mock_data_model = Mock()
        client = DatabaseClient()
        client.connect()
        client.data_model = mock_data_model
        client.get_reduction_run('GEM', 1)
        mock_data_model.ReductionRun.objects.filter.assert_called_once()

    def test_get_reduction_run_invalid(self):
        """
        Test: None is returned
        When: get_reduction_run is called values not in the database
        """
        client = DatabaseClient()
        client.connect()
        actual = client.get_reduction_run('GEM', 0)
        self.assertIsNone(actual.first())
