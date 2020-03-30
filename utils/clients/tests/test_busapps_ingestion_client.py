# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test BusApps ingestion client
"""

from urllib.error import URLError

import unittest

from mock import patch, MagicMock

from suds import WebFault

from utils.clients.busapps_ingestion_client import BusAppsIngestionClient
from utils.clients.connection_exception import ConnectionException
from utils.clients.settings.client_settings_factory import ClientSettingsFactory


class TestBusAppsIngestionClient(unittest.TestCase):
    """
    Exercises the BusApps ingestion client
    """
    def setUp(self):
        self.valid_value = "valid"
        self.test_credentials =\
            ClientSettingsFactory().create('busapps',
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
        client = BusAppsIngestionClient(credentials)
        if to_mock and "_uows_client" in to_mock:               # pylint: disable=protected-access
            client._uows_client = MagicMock()       # pylint: disable=protected-access
        if to_mock and "_scheduler_client" in to_mock:          # pylint: disable=protected-access
            client._scheduler_client = MagicMock()  # pylint: disable=protected-access
        return client

    def test_invalid_init(self):
        """ Test initialisation raises TypeError when given invalid credentials """
        with self.assertRaises(TypeError):
            BusAppsIngestionClient("invalid")

    def test_default_init(self):
        """ Test initialisation values are set """
        client = BusAppsIngestionClient()
        self.assertIsNone(client._uows_client)          # pylint: disable=protected-access
        self.assertIsNone(client._scheduler_client)     # pylint: disable=protected-access
        self.assertIsNone(client._session_id)           # pylint: disable=protected-access

    # TODO: Note - EO mentioned I shouldn't need to mock the Client as we assumed   # pylint: disable=fixme
    #  real credentials weren't need to instantiate a suds client. However, I later
    #  discovered they were needed, so I've mocked the __init__ so that I can give
    #  it fake credentials without causing an exception
    @patch('suds.client.Client.__init__')
    def test_create_uows_client_with_valid_credentials(self, mocked_suds_client):
        """ Test the User Office Web Service client is initialised with the uows_url """
        mocked_suds_client.return_value = None  # Avoids Client.__init__() being called
        client = self.create_client()
        client.create_uows_client()
        mocked_suds_client.assert_called_with(self.test_credentials.uows_url)

    def test_create_uows_client_with_invalid_credentials(self):
        """ Test a URLError is raised if the User Office Web Service client
        is initialised with an invalid uows_url """
        client = BusAppsIngestionClient()
        client.credentials.uows_url = "https://api.invalid.com/?wsdl"
        with self.assertRaises(URLError):
            client.create_uows_client()

    @patch('suds.client.Client.__init__')
    def test_create_scheduler_client_with_valid_credentials(self, mocked_suds_client):
        """ Test the Scheduler client is initialised with the scheduler_url """
        mocked_suds_client.return_value = None  # Avoids Client.__init__() being called
        client = self.create_client()
        client.create_scheduler_client()
        mocked_suds_client.assert_called_with(self.test_credentials.scheduler_url)

    def test_create_scheduler_client_with_invalid_credentials(self):
        """ Test a URLError is raised if the Scheduler client
        is initialised with an invalid scheduler_url """
        client = BusAppsIngestionClient()
        client.credentials.scheduler_url = "https://api.invalid.com/?wsdl"
        with self.assertRaises(URLError):
            client.create_scheduler_client()

    def test_connect_with_valid_credentials(self):
        """ Test UOWS login with valid credentials populates _session_id  """
        client = self.create_client(["_uows_client", "_scheduler_client"])
        client._uows_client.service.login.return_value = self.valid_value                               # pylint: disable=protected-access
        client.connect()
        client._uows_client.service.login.assert_called_with(Account=self.test_credentials.username,    # pylint: disable=protected-access,line-too-long
                                                             Password=self.test_credentials.password)   # pylint: disable=protected-access,line-too-long
        self.assertEqual(self.valid_value, client._session_id)                                          # pylint: disable=protected-access

    def test_connect_with_invalid_credentials(self):
        """ Test UOWS login with invalid credentials raises a ConnectionException """
        client = self.create_client(["_uows_client"])
        client._uows_client.service.login.side_effect = WebFault(fault=None, document=None) # pylint: disable=protected-access

        with self.assertRaises(ConnectionException):
            client.connect()
        client._uows_client.service.login.assert_called_with(Account=self.test_credentials.username,    # pylint: disable=protected-access,line-too-long
                                                             Password=self.test_credentials.password)   # pylint: disable=protected-access,line-too-long

    def test_disconnect(self):
        """ Test disconnection from a session sets _session_id = None"""
        client = self.create_client(["_uows_client", "_scheduler_client"])
        client.connect()
        client.disconnect()
        self.assertEqual(None, client._session_id)  # pylint: disable=protected-access

    def test_test_connection_no_uows_client(self):
        """ Test the connection test throws the TypeError: "invalid_uows_client"
        When the _uows_client is invalid """
        client = self.create_client(["_uows_client", "_scheduler_client"])
        client.connect()
        client._uows_client = None  # pylint: disable=protected-access
        # TODO: note - I've used a more granular way of testing     # pylint: disable=fixme
        #  (rather than just testing for a general error type)
        with self.assertRaises(TypeError) as error:
            client._test_connection()                                       # pylint: disable=protected-access
            self.assertEqual(error, client._errors["invalid_uows_client"])  # pylint: disable=protected-access,line-too-long

    def test_test_connection_no_scheduler_client(self):
        """ Test the connection test throws the TypeError: "invalid_scheduler_client"
        When the _scheduler_client is invalid """
        client = self.create_client(["_uows_client", "_scheduler_client"])
        client.connect()
        client._scheduler_client = None                                             # pylint: disable=protected-access
        with self.assertRaises(TypeError) as error:
            client._test_connection()                                               # pylint: disable=protected-access
            self.assertEqual(error, client._errors["invalid_scheduler_client"])     # pylint: disable=protected-access,line-too-long

    def test_test_connection_no_invalid_session_id(self):
        """ Test the connection test throws the ConnectionException: "invalid_session_id"
        When the _session_id is invalid """
        client = self.create_client(["_uows_client", "_scheduler_client"])
        client._scheduler_client.service.getFacilityList.side_effect = WebFault(fault=None, document=None)  # pylint: disable=protected-access,line-too-long
        client.connect()
        client._session_id = None                                           # pylint: disable=protected-access
        with self.assertRaises(ConnectionException) as error:
            client._test_connection()                                       # pylint: disable=protected-access
            self.assertEqual(error, client._errors["invalid_session_id"])   # pylint: disable=protected-access

    def test_ingest_cycle_dates(self):
        """ Test the cycle ingestion returns the output received from the Scheduler Client
        and uses the _session_id to do so"""
        client = self.create_client(["_uows_client", "_scheduler_client"])
        client.connect()
        client._scheduler_client.service.getCycles.return_value = self.valid_value  # pylint: disable=protected-access
        ret = client.ingest_cycle_dates()
        self.assertEqual(ret, self.valid_value)
        client._scheduler_client.service.getCycles.assert_called_with(sessionId=client._session_id)  # pylint: disable=protected-access,line-too-long

    def test_ingest_maintenance_days(self):
        """ Test the maintenance-days ingestion returns the output received
        from the Scheduler Client and uses the _session_id to do so"""
        client = self.create_client(["_uows_client", "_scheduler_client"])
        client.connect()
        client._scheduler_client.service.getOfflinePeriods.return_value = self.valid_value  # pylint: disable=protected-access,line-too-long

        ret = client.ingest_maintenance_days()
        self.assertEqual(ret, self.valid_value)
        client._scheduler_client.service.getOfflinePeriods.assert_called_with(sessionId=client._session_id,     # pylint: disable=protected-access,line-too-long
                                                                              reason='Maintenance')             # pylint: disable=line-too-long
