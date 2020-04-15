# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test SFTP client
"""
import unittest
from unittest.mock import MagicMock

from mock import patch

from utils.clients.connection_exception import ConnectionException
from utils.clients.sftp_client import SFTPClient


class TestSFTPClient(unittest.TestCase):
    # pylint:disable=protected-access
    """
    Exercises the SFTP client
    """
    def setUp(self):
        self.valid_argument = "valid"

    def is_argument_valid(self, value):
        """ Checks whether the value is a valid argument """
        if value == self.valid_argument:
            return True
        return False

    def create_mocked_connection_client(self):
        """ Creates a client with a mocked connection
        which returns True when exists(arg) is called if 'arg' is recognised as valid
        :return: The client with a mocked connection """
        client = SFTPClient()
        client._connection = MagicMock()
        client._connection.exists.side_effect = self.is_argument_valid
        return client

    def test_invalid_init(self):
        """ Test initialisation raises TypeError when given invalid credentials """
        with self.assertRaises(TypeError):
            SFTPClient("invalid")

    def test_default_init(self):
        """ Test initialisation values are set """
        client = SFTPClient()
        self.assertIsNotNone(client.credentials)
        self.assertIsNone(client._connection)

    def test_invalid_connection(self):
        """ Test ConnectionException raised when access attempted without valid connection """
        client = SFTPClient()  # client initialised but no connection made
        with self.assertRaises(ConnectionException):
            client._test_connection()

    def test_valid_connection(self):
        """ Test that a valid connection results in a connection-test returning True """
        client = self.create_mocked_connection_client()
        self.assertTrue(client._test_connection())

    def test_server_path_is_invalid(self):
        """ Test RuntimeError raised when server_path invalid """
        client = self.create_mocked_connection_client()
        with self.assertRaises(RuntimeError):
            client.retrieve(server_path="invalid", local_path=self.valid_argument)

    def test_local_path_does_not_exist(self):
        """ Test RuntimeError raised when local_path does not exist """
        client = self.create_mocked_connection_client()
        client._connection.get.side_effect = FileNotFoundError()
        with self.assertRaises(RuntimeError):
            client.retrieve(server_path=self.valid_argument, local_path="invalid")

    def test_local_path_is_directory(self):
        """ Test RuntimeError raised when local_path is a directory """
        client = self.create_mocked_connection_client()
        client._connection.get.side_effect = PermissionError()
        with self.assertRaises(RuntimeError):
            client.retrieve(server_path=self.valid_argument, local_path="directory")

    def test_local_path_is_none(self):
        """ Test file retrieval called successfully when no local_path is given explicitly """
        client = self.create_mocked_connection_client()
        client.retrieve(server_path=self.valid_argument)
        client._connection.get.assert_called_with(self.valid_argument, "")

    def test_server_path_and_local_path_are_valid(self):
        """ Test file retrieval called successfully
        when a valid server_path and local_path are given """
        client = self.create_mocked_connection_client()
        client.retrieve(server_path=self.valid_argument, local_path=self.valid_argument)
        client._connection.get.assert_called_with(self.valid_argument, self.valid_argument)

    @patch('os.path.isfile')
    def test_override_is_false_and_local_path_exists(self, mocked_isfile):
        """ Test RuntimeError raised when local_path file exists and override is False """
        client = self.create_mocked_connection_client()
        mocked_isfile.return_value = True
        with self.assertRaises(RuntimeError):
            client.retrieve(server_path=self.valid_argument,
                            local_path=self.valid_argument, override=False)

    @patch('os.path.isfile')
    def test_override_is_false_and_local_path_does_not_exists(self, mocked_isfile):
        """ Test file retrieval called successfully
        when local_path file exists and override is True """
        client = self.create_mocked_connection_client()
        mocked_isfile.return_value = False
        client.retrieve(server_path=self.valid_argument,
                        local_path=self.valid_argument, override=False)
        client._connection.get.assert_called_with(self.valid_argument, self.valid_argument)
