# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test ICAT client
This performs a large amount of mocking of the actual ICAT functions.
This is because we can not connect to icat for testing and it is not feasible
to set up a local version for testing at this point.
"""
import unittest
from unittest.mock import patch

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
        """
        Test: Class variables are created and set
        When: ICATClient is initialised with default credentials
        """
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
        """
        Test: login is called on the stored client
        When: connect is called while valid credentials are held
        """
        client = ICATClient()
        mock_icat.assert_called_once()
        client.connect()
        mock_icat_login.assert_called_once_with(auth='simple',
                                                credentials={'username': 'YOUR-ICAT-USERNAME',
                                                             'password': 'YOUR-PASSWORD'})

    def test_invalid_connection(self):
        """
        Test: A ValueError is raised
        When: connect is called while invalid credentials are held
        """
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
        """
        Test: logout is called on the stored client
        When: disconnect is called
        """
        client = ICATClient()
        client.disconnect()
        mock_logout.assert_called_once()

    @patch('icat.Client.__init__', return_value=None)
    @patch('icat.Client.refresh')
    def test_refresh(self, mock_autorefresh, _):
        """
        Test: refresh is called on the stored client
        When: refresh is called
        """
        client = ICATClient()
        client.refresh()
        mock_autorefresh.assert_called_once()

    @patch('icat.Client.__init__', return_value=None)
    @patch('icat.Client.refresh')
    def test_valid_test_connection(self, mock_refresh, _):
        """
        Test: refresh is called on the stored client
        When: _test_connection is called
        """
        client = ICATClient()
        # pylint:disable=protected-access
        self.assertTrue(client._test_connection())
        mock_refresh.assert_called_once()

    @patch('icat.Client.__init__', return_value=None)
    @patch('icat.Client.refresh')
    def test_failing_test_connection(self, mock_refresh, _):
        """
        Test: A ConnectionException is raised
        When: _test_connection is called while an invalid connection is held
        """
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
        """
        Test: A query is executed
        When: execute_query is called without a connection having been established
        """
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
        """
        Test: A query is executed
        When: execute_query is called with a connection having been established
        """
        client = ICATClient()
        client.execute_query('icat query')
        mock_refresh.assert_called_once()
        mock_search.assert_called_once_with('icat query')
