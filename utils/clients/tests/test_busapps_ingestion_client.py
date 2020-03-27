# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test BusApps ingestion client
"""
import unittest
from urllib.error import URLError

from mock import patch, MagicMock, Mock

from utils.clients.busapps_ingestion_client import BusAppsIngestionClient
from suds import Client, WebFault

from utils.clients.connection_exception import ConnectionException
from utils.clients.settings.client_settings_factory import ClientSettingsFactory


class TestBusAppsIngestionClient(unittest.TestCase):
    """
    Exercises the BusApps ingestion client
    """
    def setUp(self):
        self.valid_value = "valid"
        self.test_credentials = ClientSettingsFactory().create('busapps',
                                                                username='valid-user',
                                                                password='valid-pass',
                                                                host='',
                                                                port='',
                                                                uows_url='https://api.valid-uows.com/?wsdl',
                                                                scheduler_url='https://api.valid-scheduler.com/?wsdl')

    # TODO: Edward - make method to create client + options to mock things

    def test_invalid_init(self):
        """ Test initialisation raises TypeError when given invalid credentials """
        with self.assertRaises(TypeError):
            BusAppsIngestionClient("invalid")

    def test_default_init(self):
        """ Test initialisation values are set """
        client = BusAppsIngestionClient()
        self.assertIsNone(client._uows_client)
        self.assertIsNone(client._scheduler_client)
        self.assertIsNone(client._session_id)

    # TODO: Note - EO mentioned I shouldn't need to mock the Client as we assumed real credentials
    #  weren't need to instantiate a suds client. However, I later discovered they were needed,
    #  so I've mocked the __init__ so that I can give it fake credentials without causing an exception
    @patch('suds.client.Client.__init__')
    def test_create_uows_client_with_valid_credentials(self, mocked_suds_client):
        mocked_suds_client.return_value = None
        client = BusAppsIngestionClient(self.test_credentials)
        client.create_uows_client()
        mocked_suds_client.assert_called_with(self.test_credentials.uows_url)

    def test_create_uows_client_with_invalid_credentials(self):
        client = BusAppsIngestionClient()
        client.credentials.uows_url = "https://api.invalid.com/?wsdl"
        with self.assertRaises(URLError):
            client.create_uows_client()

    def test_create_scheduler_client_with_invalid_credentials(self):
        client = BusAppsIngestionClient()
        client.credentials.scheduler_url = "https://api.invalid.com/?wsdl"
        with self.assertRaises(URLError):
            client.create_scheduler_client()

    def test_connect_with_valid_credentials(self):
        client = BusAppsIngestionClient(self.test_credentials)
        client._uows_client = MagicMock()
        client._scheduler_client = MagicMock()

        client._uows_client.service.login.return_value = self.valid_value
        client.connect()

        client._uows_client.service.login.assert_called_with(Account=self.test_credentials.username,
                                                             Password=self.test_credentials.password)
        self.assertEqual(self.valid_value, client._session_id)

    def test_connect_with_invalid_credentials(self):
        client = BusAppsIngestionClient(self.test_credentials)
        client._uows_client = MagicMock()
        client._uows_client.service.login.side_effect = WebFault(fault=None, document=None)

        with self.assertRaises(ConnectionException):
            client.connect()
        client._uows_client.service.login.assert_called_with(Account=self.test_credentials.username,
                                                             Password=self.test_credentials.password)

    def test_disconnect(self):
        client = BusAppsIngestionClient()
        client._uows_client = MagicMock()
        self.assertEqual(None, client._session_id)

    # @patch('suds.client.Client.__init__')
    def test_test_connection_no_uows_client(self):
        client = BusAppsIngestionClient()
        client._uows_client = MagicMock()
        client._scheduler_client = MagicMock()

        client.connect()
        client._uows_client = None
        # TODO: note - I've used a more granular way of testing (rather than just testing for a general error type)
        with self.assertRaises(TypeError) as error:
            client._test_connection()
            self.assertEqual(error, client._errors["invalid_uows_client"])

    def test_test_connection_no_scheduler_client(self):
        client = BusAppsIngestionClient()
        client._uows_client = MagicMock()
        client._scheduler_client = MagicMock()

        client.connect()
        client._scheduler_client = None
        with self.assertRaises(TypeError) as error:
            client._test_connection()
            self.assertEqual(error, client._errors["invalid_scheduler_client"])

    def test_test_connection_no_invalid_session_id(self):
        client = BusAppsIngestionClient()
        client._uows_client = MagicMock()
        client._scheduler_client = MagicMock()
        client._scheduler_client.service.getFacilityList.side_effect = WebFault(fault=None, document=None)

        client.connect()
        client._session_id = None
        with self.assertRaises(ConnectionException) as error:
            client._test_connection()
            self.assertEqual(error, client._errors["invalid_session_id"])

    def test_ingest_cycle_dates(self):
        client = BusAppsIngestionClient()
        client._uows_client = MagicMock()
        client._scheduler_client = MagicMock()
        client.connect()
        client._scheduler_client.service.getCycles.return_value = self.valid_value

        ret = client.ingest_cycle_dates()
        self.assertEqual(ret, self.valid_value)
        client._scheduler_client.service.getCycles.assert_called_with(sessionId=client._session_id)

    def test_ingest_maintenance_days(self):
        client = BusAppsIngestionClient()
        client._uows_client = MagicMock()
        client._scheduler_client = MagicMock()
        client.connect()
        client._scheduler_client.service.getOfflinePeriods.return_value = self.valid_value

        ret = client.ingest_maintenance_days()
        self.assertEqual(ret, self.valid_value)
        client._scheduler_client.service.getOfflinePeriods.assert_called_with(sessionId=client._session_id,
                                                                              reason='Maintenance')


