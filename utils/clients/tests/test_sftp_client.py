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

from unittest.mock import patch

from utils.clients.connection_exception import ConnectionException
from utils.clients.sftp_client import SFTPClient


class TestSFTPClient(unittest.TestCase):
    # pylint:disable=protected-access
    """
    Exercises the SFTP client
    """
    def setUp(self):
        self.valid_argument = "valid"
        self.filenames = ["textfile.txt", "nexusfile.nxs", "image.png"]
        self.textfile_regex = r".*\.txt"

    def is_argument_valid(self, value):
        """ Checks whether the value is a valid argument
        :return: True if value is valid """
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
        """
        Test: A TypeError is raised
        When: SFTPClient is initialised with invalid credentials
        """
        with self.assertRaises(TypeError):
            SFTPClient("invalid")

    def test_default_init(self):
        """
        Test: Class variables are created and set
        When: SFTPClient is initialised with default credentials
        """
        client = SFTPClient()
        self.assertIsNotNone(client.credentials)
        self.assertIsNone(client._connection)

    def test_invalid_connection(self):
        """
        Test: A ConnectionException raised
        When: _test_connection is called without a valid connection
        """
        client = SFTPClient()  # client initialised but no connection made
        with self.assertRaises(ConnectionException):
            client._test_connection()

    def test_valid_connection(self):
        """
        Test: _test_connection returns True
        When: _test_connection is called on an SFTPClient with a valid connection
        """
        client = self.create_mocked_connection_client()
        self.assertTrue(client._test_connection())

    def test_server_path_check_with_invalid_path(self):
        """
        Test: A RuntimeError is raised
        When: _server_path_check is called with an invalid server path
        """
        client = self.create_mocked_connection_client()
        with self.assertRaises(RuntimeError):
            client._server_path_check(server_path="invalid")

    def test_server_path_check_with_valid_path(self):
        """
        Test: pysftp.Connection.exists is called, but no errors are raised
        When: _server_path_check is called with a valid server path
        """
        client = self.create_mocked_connection_client()
        client._server_path_check(server_path=self.valid_argument)
        client._connection.exists.assert_called_with(self.valid_argument)

    def test_server_file_path_is_invalid(self):
        """
        Test: A RuntimeError is raised
        When: retrieve is called with an invalid server path
        """
        client = self.create_mocked_connection_client()
        with self.assertRaises(RuntimeError):
            client.retrieve(server_file_path="invalid", local_file_path=self.valid_argument)

    def test_local_file_path_does_not_exist(self):
        """
        Test: A RuntimeError is raised
        When: retrieve is called with an invalid file path
        """
        client = self.create_mocked_connection_client()
        client._connection.get.side_effect = FileNotFoundError()
        with self.assertRaises(RuntimeError):
            client.retrieve(server_file_path=self.valid_argument, local_file_path="invalid")

    def test_local_file_path_is_directory(self):
        """
        Test: A RuntimeError is raised
        When: retrieve is called with a local path that points to a directory
        """
        client = self.create_mocked_connection_client()
        client._connection.get.side_effect = PermissionError()
        with self.assertRaises(RuntimeError):
            client.retrieve(server_file_path=self.valid_argument, local_file_path="directory")

    def test_local_file_path_is_none(self):
        """
        Test: retrieve uses the current directory as the local_file_path
        When: retrieve is called with no local_file_path argument
        """
        client = self.create_mocked_connection_client()
        client.retrieve(server_file_path=self.valid_argument)
        client._connection.get.assert_called_with(self.valid_argument, "")

    def test_server_file_path_and_local_file_path_are_valid(self):
        """
        Test: retrieve finds a file from a given server_file_path and puts a copy in local_file_path
        When: retrieve is called with a valid server_file_path
        (i.e. a path which point to a real file)
        and a valid local_file_path (i.e. a local path which exists)
        """
        client = self.create_mocked_connection_client()
        client.retrieve(server_file_path=self.valid_argument, local_file_path=self.valid_argument)
        client._connection.get.assert_called_with(self.valid_argument, self.valid_argument)

    @patch('os.path.isfile', return_value=True)
    def test_override_is_false_and_local_file_path_exists(self, _):
        """
        Test: A RuntimeError is raised
        When: A file at local_file_path exists and override is False
        """
        client = self.create_mocked_connection_client()
        with self.assertRaises(RuntimeError):
            client.retrieve(server_file_path=self.valid_argument, local_file_path=self.valid_argument, override=False)

    @patch('os.path.isfile', return_value=False)
    def test_override_is_false_and_local_file_path_does_not_exists(self, _):
        """
        Test: retrieve does not encounter an error
        When: A file at local_file_path exists and override is True
        """
        client = self.create_mocked_connection_client()
        client.retrieve(server_file_path=self.valid_argument, local_file_path=self.valid_argument, override=False)
        client._connection.get.assert_called_with(self.valid_argument, self.valid_argument)

    def test_get_filenames_valid_path(self):
        """
        Test: The output from pysftp.Connection.listdir is returned
        When: get_filenames is called with a valid server directory path
        """
        client = self.create_mocked_connection_client()
        client._connection.listdir.return_value = self.filenames
        filenames_returned = client.get_filenames(server_dir_path=self.valid_argument)
        self.assertEqual(filenames_returned, self.filenames)

    def test_get_filenames_invalid_path(self):
        """
        Test: A RuntimeError is raised
        When: get_filenames is called with an invalid server directory path
        """
        client = self.create_mocked_connection_client()
        with self.assertRaises(RuntimeError):
            client.get_filenames(server_dir_path="invalid")

    def test_get_filenames_regex(self):
        """
        Test: The output from pysftp.Connection.listdir is returned
        When: get_filenames is called with a valid server directory path
        """
        client = self.create_mocked_connection_client()
        client._connection.listdir.return_value = self.filenames
        filenames_returned = client.get_filenames(server_dir_path=self.valid_argument, regex=self.textfile_regex)
        self.assertEqual(filenames_returned, [self.filenames[0]])
