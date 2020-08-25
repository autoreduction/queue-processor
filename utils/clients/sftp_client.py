# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Client class for retrieving files via SFTP from servers (e.g. CEPH)
"""
import os.path
import logging
import re

import pysftp
from utils.clients.abstract_client import AbstractClient
from utils.clients.connection_exception import ConnectionException
from utils.test_settings import SFTP_SETTINGS
from utils.project.structure import get_log_file
from utils.project.static_content import LOG_FORMAT


logging.basicConfig(filename=get_log_file('sftp_client.log'), level=logging.INFO,
                    format=LOG_FORMAT)


class SFTPClient(AbstractClient):
    """
    This class allows files to be retrieved from SFTP servers
    """
    def __init__(self, credentials=None):
        if not credentials:
            credentials = SFTP_SETTINGS
        super(SFTPClient, self).__init__(credentials)  # pylint:disable=super-with-arguments
        self._connection = None

    def connect(self):
        """
        Create the connection to the SFTP server
        :return: The connection object
        """
        if self._connection is None:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None
            self._connection = pysftp.Connection(host=self.credentials.host,
                                                 username=self.credentials.username,
                                                 password=self.credentials.password,
                                                 port=int(self.credentials.port),
                                                 cnopts=cnopts)
        self._test_connection()

        return self._connection

    def disconnect(self):
        """
        Disconnect from the SFTP server
        """
        if self._connection is not None:
            self._connection.close()
        self._connection = None

    def _test_connection(self):
        """
        Test whether there is a connection to the SFTP server
        :return: True if there is a connection.
        :raises ConnectionException: If there is no existing connection or it is not valid.
        """

        try:
            self._connection.pwd
        except AttributeError as exp:
            raise ConnectionException("SFTP") from exp
        return True

    def retrieve(self, server_file_path, local_file_path=None, override=True):
        """
        Retrieves file from the given server_path and downloads it to the given local_path
        :param server_file_path: The location of the file on the SFTP server.
        :param local_file_path:
            The location to download the file to, including filename with extension.
            If None, local_path is the local directory.
        :param override: If True and local_path points to an existing file, will override this file.
        :raises RuntimeError: If any of the following occur:
            1) The server_file_path does not exist on the SFTP server
            2) The local_file_path directory does not exist
            3) The local_file_path points to a directory instead of a file
            4) The local_file_path points to an existing file, and override is false
            Note: an error message will describe which of the 4 cases above has occurred.
        """

        self._server_path_check(server_file_path)

        if local_file_path is None:
            local_file_path = ""

        if not override and os.path.isfile(local_file_path):
            raise RuntimeError("The local_file_path points to a file which already exists. "
                               "Please provide a different filename in the local_path, "
                               "or set the override flag to True.")

        try:
            self._connection.get(server_file_path, local_file_path)
        except FileNotFoundError as exp:
            raise RuntimeError("The local_file_path does not exist.") from exp
        except PermissionError as exp:
            raise RuntimeError("The local_file_path is a directory. "
                               "Please ensure the local_path includes a full filename.") from exp

    def get_filenames(self, server_dir_path, regex=".*"):
        """
        Gets filenames from a given server directory which meet a regular expression
        :param server_dir_path: The server directory to get filenames from.
        :param regex: A regular expression for the files to meet (default allows for all files).
        :return: A list of filenames which match the regex within the server directory.
        """
        self._server_path_check(server_dir_path)
        with self._connection.cd(server_dir_path):
            filenames = self._connection.listdir()
        matches = []

        for name in filenames:
            if re.match(regex, name) is not None:
                matches.append(name)

        return matches

    def _server_path_check(self, server_path):
        """
        Checks the connection to the server (or establishes one if there isn't one yet)
        and that the given path exists.
        :param server_path: A location on the SFTP server.
            Note: Use server_path="." to reference the current working directory
        :raises RuntimeError: If the server_path does not exist on the SFTP server
        """
        if self._connection is None:
            self.connect()

        if not self._connection.exists(server_path):
            raise RuntimeError(f"The given server_path does not exist: '{server_path}'")
