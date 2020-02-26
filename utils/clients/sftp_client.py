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
            self._connection = pysftp.Connection(host=self.credentials.host,
                                                 username=self.credentials.username,
                                                 password=self.credentials.password,
                                                 port=self.credentials.port)
            self._test_connection()  # TODO: Currently just returns True
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
        :param server_path: The location of the file on the SFTP server
        :param local_path: The location to download the file to
        :return: True if there is a connection
        """
        if not os.path.isfile(server_path):
            # TODO: Tell user they need to provide server_path to file
            return
        elif not os.path.isfile(local_path):
            # TODO: Tell user they need to provide local_path to file
            # TODO: Might want to have this use the existing file name (from server_path) if pysftp requires name
            return
        else:
            self._connection.get(server_path, local_path)
