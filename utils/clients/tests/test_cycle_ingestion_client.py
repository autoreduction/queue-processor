# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test Cycle ingestion client
"""

from urllib.error import URLError

import unittest

from unittest.mock import patch, MagicMock

import suds

from utils.clients.cycle_ingestion_client import CycleIngestionClient
from utils.clients.connection_exception import ConnectionException
from utils.clients.settings.client_settings_factory import ClientSettingsFactory


class TestCycleIngestionClient(unittest.TestCase):
    # pylint: disable=protected-access
    """
    Exercises the Cycle ingestion client
    """
    def setUp(self):
        self.valid_value = "valid"
        self.test_credentials =\
            ClientSettingsFactory().create('cycle',
                                           username='valid-user',
                                           password='valid-pass',
                                           host='',
                                           port='',
                                           uows_url='https://api.valid-uows.com/?wsdl',
                                           scheduler_url='https://api.valid-scheduler.com/?wsdl')

    def create_client(self, to_mock=None, credentials=None):
        """ Returns a client with 0 or more mocked instance variables
        :param to_mock: A list of client instance variables to mock
        :param credentials: The credentials to initialise the client with
                            (test credentials used if none supplied)
        :return: A client with 0 or more mocked instance variables """
        if not credentials:
            credentials = self.test_credentials
        client = CycleIngestionClient(credentials)
        if to_mock and "_uows_client" in to_mock:
            client._uows_client = MagicMock()
        if to_mock and "_scheduler_client" in to_mock:
            client._scheduler_client = MagicMock()
        return client

    def test_invalid_init(self):
        """
        Test: A TypeError is raised
        When: CycleIngestionClient is initialised with invalid credentials
        """
        with self.assertRaises(TypeError):
            CycleIngestionClient("invalid")

    def test_default_init(self):
        """
        Test: Class variables are created and set
        When: CycleIngestionClient is initialised with default credentials
        """
        client = CycleIngestionClient()
        self.assertIsNone(client._uows_client)
        self.assertIsNone(client._scheduler_client)
        self.assertIsNone(client._session_id)

    @patch('suds.client.Client.__init__', return_value=None)
    def test_create_uows_client_with_valid_credentials(self, mock_suds_client):
        """
        Test: The User Office Web Service (UOWS) client is initialised with credentials.uows_url
        When: create_uows_client is called while a valid uows_url is held
        """
        client = self.create_client()
        client.create_uows_client()
        mock_suds_client.assert_called_with(self.test_credentials.uows_url)

    def test_create_uows_client_with_invalid_credentials(self):
        """
        Test: A URLError is raised
        When: create_uows_client is called while an invalid uows_url is held
        """
        client = CycleIngestionClient()
        client.credentials.uows_url = "https://api.invalid.com/?wsdl"
        with self.assertRaises(URLError):
            client.create_uows_client()

    @patch('suds.client.Client.__init__', return_value=None)
    def test_create_scheduler_client_with_valid_credentials(self, mock_suds_client):
        """
        Test: The Scheduler client is initialised with credentials.scheduler_url
        When: create_scheduler_client is called while a valid scheduler_url is held
        """
        client = self.create_client()
        client.create_scheduler_client()
        mock_suds_client.assert_called_with(self.test_credentials.scheduler_url)

    def test_create_scheduler_client_with_invalid_credentials(self):
        """
        Test: A URLError is raised
        When: create_scheduler_client is called while an invalid scheduler_url is held
        """
        client = CycleIngestionClient()
        client.credentials.scheduler_url = "https://api.invalid.com/?wsdl"
        with self.assertRaises(URLError):
            client.create_scheduler_client()

    def test_connect_with_valid_credentials(self):
        # pylint: disable=line-too-long
        """
        Test: The CycleIngestionClient connects to the UOWS Client using the
        credentials held, and a valid session_id is stored
        When: connect is called while a valid username and password is held
        """
        client = self.create_client(["_uows_client", "_scheduler_client"])
        client._uows_client.service.login.return_value = self.valid_value
        client.connect()
        client._uows_client.service.login.assert_called_with(Account=self.test_credentials.username,
                                                             Password=self.test_credentials.password)
        self.assertEqual(self.valid_value, client._session_id)

    def test_connect_with_invalid_credentials(self):
        # pylint: disable=line-too-long
        """
        Test: A ConnectionException is raised
        When: connect is called while an invalid username and password is held
        """
        client = self.create_client(["_uows_client"])
        client._uows_client.service.login.side_effect = suds.WebFault(fault=None, document=None)

        with self.assertRaises(ConnectionException):
            client.connect()
        client._uows_client.service.login.assert_called_with(Account=self.test_credentials.username,
                                                             Password=self.test_credentials.password)

    def test_disconnect(self):
        """
        Test: _session_id is set to None
        When: disconnect is called after a connection has been established
        """
        client = self.create_client(["_uows_client", "_scheduler_client"])
        client.connect()
        client.disconnect()
        self.assertEqual(None, client._session_id)

    def test_test_connection_no_uows_client(self):
        """
        Test: The TypeError: "invalid_uows_client" is raised
        When: test_connection is called with an invalid _uows_client
        """
        client = self.create_client(["_uows_client", "_scheduler_client"])
        client.connect()
        client._uows_client = None
        with self.assertRaises(TypeError) as error:
            client._test_connection()
            self.assertEqual(error, client._errors["invalid_uows_client"])

    def test_test_connection_no_scheduler_client(self):
        """
        Test: The TypeError: "invalid_scheduler_client" is raised
        When: test_connection is called with an invalid _scheduler_client
        """
        client = self.create_client(["_uows_client", "_scheduler_client"])
        client.connect()
        client._scheduler_client = None
        with self.assertRaises(TypeError) as error:
            client._test_connection()
            self.assertEqual(error, client._errors["invalid_scheduler_client"])

    def test_test_connection_no_invalid_session_id(self):
        # pylint: disable=line-too-long
        """
        Test: The ConnectionException: "invalid_session_id" is raised
        When: test_connection is called with an invalid _session_id
        """
        client = self.create_client(["_uows_client", "_scheduler_client"])
        client._scheduler_client.service.getFacilityList.side_effect = suds.WebFault(fault=None, document=None)
        client.connect()
        client._session_id = None
        with self.assertRaises(ConnectionException) as error:
            client._test_connection()
            self.assertEqual(error, client._errors["invalid_session_id"])

    def test_ingest_cycle_dates(self):
        # pylint: disable=line-too-long
        """
        Test: _session_id is used to retrieve cycle-dates data from the _scheduler_client
        When: ingest_cycle_dates is called while a valid _session_id is held
        """
        client = self.create_client(["_uows_client", "_scheduler_client"])
        client.connect()
        client._scheduler_client.service.getCycles.return_value = self.valid_value
        ret = client.ingest_cycle_dates()
        self.assertEqual(ret, self.valid_value)
        client._scheduler_client.service.getCycles.assert_called_with(sessionId=client._session_id)

    def test_ingest_maintenance_days(self):
        # pylint: disable=line-too-long
        """
        Test: _session_id is used to retrieve maintenance-day-dates data from the _scheduler_client
        When: ingest_maintenance_days is called while a valid _session_id is held
        """
        client = self.create_client(["_uows_client", "_scheduler_client"])
        client.connect()
        client._scheduler_client.service.getOfflinePeriods.return_value = self.valid_value

        ret = client.ingest_maintenance_days()
        self.assertEqual(ret, self.valid_value)
        client._scheduler_client.service.getOfflinePeriods.assert_called_with(sessionId=client._session_id,
                                                                              reason='Maintenance')
