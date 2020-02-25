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
            pass  # TODO: figure out how to write connection code

    def disconnect(self):
        """
        Disconnect from the SFTP server
        """
        # TODO: figure out how to write disconnection code
        self._connection = None

    def _test_connection(self):
        """
        Test whether there is a connection to the SFTP server
        :return: True if there is a connection
        """
        # TODO: figure out how to write test connection code
        if self._connection is not None:
            return True

    def retrieve(self, server_path, local_path):
        """
        Retrieves file from the given server_path and downloads it to the given local_path
        :param server_path: The location of the file on the SFTP server
        :param local_path: The location to download the file to
        :return: True if there is a connection
        """