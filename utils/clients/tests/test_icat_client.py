# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test ICAT client
This performs a large amount of mocking of the actual ICAT functions.
This is because we can not connect to icat for testing and it is not feasible
to set up a local version for testing at this point.
"""
import unittest
from mock import patch

import icat

from utils.clients.icat_client import ICATClient
from utils.clients.settings.client_settings_factory import ClientSettingsFactory
from utils.clients.connection_exception import ConnectionException


def raise_icat_session_error():
    """ function required to raise ICATSessionErrors in mocks """
    raise icat.ICATSessionError('ICAT session error raised from mock')


# pylint:disable=missing-docstring,no-self-use
class TestICATClient(unittest.TestCase):

    @patch('icat.Client.__init__', return_value=None)
    def test_default_init(self, mock_icat,):
        client = ICATClient()
        self.assertEqual(client.credentials.username, 'YOUR-ICAT-USERNAME')
        self.assertEqual(client.credentials.password, 'YOUR-PASSWORD')
        self.assertEqual(client.credentials.host, 'YOUR-ICAT-WSDL-URL')
        self.assertEqual(client.credentials.port, '')
        self.assertEqual(client.credentials.auth, 'simple')
        mock_icat.assert_called_once_with('YOUR-ICAT-WSDL-URL')

    @patch('icat.Client.__init__', return_value=None)
    @patch('icat.Client.login')
    def test_valid_connection(self, mock_icat_login, mock_icat):
        client = ICATClient()
        mock_icat.assert_called_once()
        client.connect()
        mock_icat_login.assert_called_once()
        mock_icat_login.assert_called_once_with(auth='simple',
                                                credentials={'username': 'YOUR-ICAT-USERNAME',
                                                             'password': 'YOUR-PASSWORD'})

    def test_invalid_connection(self):
        invalid_settings = ClientSettingsFactory().create('icat',
                                                          username='user',
                                                          password='pass',
                                                          host=r'www.fake-url.com',
                                                          port='',
                                                          authentication_type='none')
        self.assertRaises(ValueError, ICATClient, invalid_settings)

    @patch('icat.Client.__init__', return_value=None)
    @patch('icat.Client.logout')
    def test_disconnect(self, mock_logout, _):
        client = ICATClient()
        client.disconnect()
        mock_logout.assert_called_once()

    @patch('icat.Client.__init__', return_value=None)
    @patch('icat.Client.refresh')
    def test_refresh(self, mock_autorefresh, _):
        client = ICATClient()
        client.refresh()
        mock_autorefresh.assert_called_once()

    @patch('icat.Client.__init__', return_value=None)
    @patch('icat.Client.refresh')
    def test_valid_test_connection(self, mock_refresh, _):
        client = ICATClient()
        # pylint:disable=protected-access
        self.assertTrue(client._test_connection())
        mock_refresh.assert_called_once()

    @patch('icat.Client.__init__', return_value=None)
    @patch('icat.Client.refresh')
    def test_failing_test_connection(self, mock_refresh, _):
        mock_refresh.side_effect = raise_icat_session_error
        client = ICATClient()
        # pylint:disable=protected-access
        self.assertRaisesRegex(ConnectionException, 'ICAT', client._test_connection)

    @patch('icat.Client.__init__', return_value=None)
    @patch('icat.Client.__setattr__')
    @patch('utils.clients.icat_client.ICATClient.connect')
    @patch('icat.Client.refresh')
    @patch('icat.Client.search')
    def test_query_without_conn(self, mock_search, mock_refresh, mock_connect, mock_set_attr, _):
        # Add side effect to raise exception with icat.refresh
        mock_refresh.side_effect = raise_icat_session_error
        client = ICATClient()
        client.execute_query('icat query')
        mock_refresh.assert_called_once()
        mock_set_attr.assert_called_once()
        mock_connect.assert_called_once()
        mock_search.assert_called_once_with('icat query')

    @patch('icat.Client.__init__', return_value=None)
    @patch('icat.Client.search')
    @patch('icat.Client.refresh', return_value=None)
    def test_query_icat(self, mock_refresh, mock_search, _):
        client = ICATClient()
        client.execute_query('icat query')
        mock_refresh.assert_called_once()
        mock_search.assert_called_once_with('icat query')
