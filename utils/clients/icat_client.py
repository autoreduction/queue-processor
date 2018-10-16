"""
Module to perform ICAT client functionality
Functions for login and query available from class
"""
import logging

import icat

from utils.settings import ICAT_SETTINGS
from utils.clients.abstract_client import AbstractClient
from utils.clients.connection_exception import ConnectionException
from utils.project.structure import get_log_file
from utils.project.static_content import LOG_FORMAT

logging.basicConfig(filename=get_log_file('icat_client.log'), level=logging.INFO,
                    format=LOG_FORMAT)


class ICATClient(AbstractClient):
    """
    This class provides a layer of abstraction from Python ICAT.
    Only allowing logging in and querying.
    """

    def __init__(self, credentials=None):
        if not credentials:
            credentials = ICAT_SETTINGS
        super(ICATClient, self).__init__(credentials)
        self.client = icat.Client(self.credentials.host)
        self.connect()

    def connect(self):
        """
        Log in to ICAT using the details provided in the test_settings.py file
        """
        self.client.login(auth=self.credentials.auth,
                          credentials={'username': self.credentials.username,
                                       'password': self.credentials.password})

    def _test_connection(self):
        """
        Test that the connection has been successful
        """
        try:
            self.client.refresh()
        except icat.exception.ICATSessionError:
            raise ConnectionException("ICAT")
        return True

    def disconnect(self):
        """ Log out of icat """
        self.client.logout()

    def execute_query(self, query):
        """
        Runs a query on ICAT - assumes a valid login has already been obtained
        :param query: The query to run
        :return: The result of the query
        """
        try:
            self.client.refresh()
        except icat.exception.ICATSessionError:
            # Session has most likely expired, try and log in again.
            # Have to set sessionId to None otherwise python ICAT attempts
            # to log out with an expired sessionId
            self.client.sessionId = None
            self.connect()
        return self.client.search(query)
