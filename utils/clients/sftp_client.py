# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Client class for retrieving files via SFTP from servers (e.g. CEPH)
"""
from utils.clients.abstract_client import AbstractClient
from utils.test_settings import SFTP_SETTINGS
import pysftp
import os.path
from utils.project.structure import get_log_file
from utils.project.static_content import LOG_FORMAT
import logging

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

        # TODO: do I need to check for existing connection? (like with queue & database clients)
        if self._connection is None:
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None  # TODO: ! This makes the connection vulnerable to man-in-the-middle attacks
                                    #   source: https://stackoverflow.com/questions/38939454/verify-host-key-with-pysftp
            self._connection = pysftp.Connection(host=self.credentials.host,
                                                 username=self.credentials.username,
                                                 password=self.credentials.password,
                                                 port=int(self.credentials.port),
                                                 cnopts=cnopts)
        if self._test_connection():  # TODO: Currently just returns True
            print("Connection Success")
        else:
            print("Connection Failure")
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
        # TODO: figure out how to write test connection code | Perhaps pwd, i.e. print to current dir?
        if self._connection is not None:
            return True

    def retrieve(self, server_path, local_path):
        """
        Retrieves file from the given server_path and downloads it to the given local_path
        :param server_path:
            The location of the file on the SFTP server.
        :param local_path:
            The location to download the file to.
            If a filename (with file extension) is provided at the end of the path,
            the file will be stored under this name and extension.
        """

        # TODO: Might consider adding the follow:
        #   (1) _test_connection, connect is False? BUT allows people to retrieve without connecting
        #   (2) check local_path exists
        #   (2b) offering to create directory if doesn't exist
        #   (3) warn user before overriding an existing file
        #   (3b) offering to rename "<filename> (2)"

        self._connection.get(server_path, local_path)
