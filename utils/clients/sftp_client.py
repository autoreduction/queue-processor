# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Client class for retrieving files via SFTP from servers (e.g. CEPH)
"""
import os.path
import logging
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
    This class allows files to be retrieved via SFTP from servers (e.g. CEPH)
    """
    def __init__(self, credentials=None):
        if not credentials:
            credentials = SFTP_SETTINGS
        super(SFTPClient, self).__init__(credentials)
        self._connection = None

    def connect(self):
        """
        Create the connection to the SFTP server
        :return: connection object
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
        :return: True if there is a connection
        """

        try:
            self._connection.pwd
        except AttributeError:
            raise ConnectionException("SFTP")
        print("Connection Valid")   # TODO: Remove before final commit
        return True

    def retrieve(self, server_path, local_path=None, override=True):
        """
        Retrieves file from the given server_path and downloads it to the given local_path
        :param server_path: The location of the file on the SFTP server.
        :param local_path:
            The location to download the file to, including filename with extension.
            If None, local_path is the local directory.
        :param override: If True and local_path points to an existing file, will override this file.
        """

        if local_path is None:
            local_path = ""

        if not os.path.isfile(server_path): # TODO: Replace this - it won't work over sftp
            raise RuntimeError("The server_path does not point to a file. "
                               "Please provide a server_path which points to a file.")

        if not override and os.path.isfile(local_path):
            raise RuntimeError("The local_path points to a file which already exists. "
                               "Please provide a different filename in the local_path, "
                               "or set the override flag to True.")

        if self._connection is None:
            self.connect()

        try:
            self._connection.get(server_path, local_path)
        except FileNotFoundError:
            raise RuntimeError("The local_path does not exist.")
        except PermissionError:  # Raised when local_path points to directory
            raise RuntimeError("The local_path does not exist. "
                               "Please ensure the local_path includes a full filename.")
