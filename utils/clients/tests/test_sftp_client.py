# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test SFTP client
"""
import unittest
from unittest.mock import Mock, MagicMock

from mock import patch

from utils.clients.connection_exception import ConnectionException
from utils.clients.settings.client_settings_factory import ClientSettingsFactory
from utils.clients.sftp_client import SFTPClient

class MockConnection(Mock):
    """Mock object class"""
    pass

class TestSFTPClient(unittest.TestCase):
    """
    Exercises the database client
    """
    def setUp(self):
        self.incorrect_credentials = ClientSettingsFactory().create('sftp',
                                                                    username='not-user',
                                                                    password='not-pass',
                                                                    host='not-host',
                                                                    port='1234')

    def test_default_init(self):
        """ Test default values for initialisation """
        client = SFTPClient()
        self.assertIsNotNone(client.credentials)
        self.assertIsNone(client._connection)

    def test_invalid_init(self):
        """ Test invalid values for initialisation """
        self.assertRaises(TypeError, SFTPClient, 'string')

    def test_valid_connection(self):
        """ Test access is established with valid connection """
        client = SFTPClient()
        client.connect()
        self.assertTrue(client._test_connection())

    # TODO: Add docstrings for tests
    def test_invalid_connection(self):
        client = SFTPClient()   # client initialised but no connection made
        with self.assertRaises(ConnectionException):
            client._test_connection()

    @patch('utils.clients.database_client.SFTPClient.connect', return_value=MockConnection())
    def test_valid_retrieve(self, mock_connection):
         magicmock_connecion = MagicMock(mock_connection)


    # def test_local_path_is_none(self, path):
    #     client = SFTPClient()
    #     path.return_value = True
    #     client.retrieve("mountisiscommand.txt", None)

    # TODO: Tests for following
    #   - local path None -> saves to local
    #   - local_path == "" -> saves to local
    #   - override false + existing file -> Error
    #   - invalid connection, test -> Error
    #   - invalid local_path -> Error
    #   - no filename + not "" -> Error
    #   - valid path + override false, no dup -> saves
    #   - valid path + override true, dup -> saves
