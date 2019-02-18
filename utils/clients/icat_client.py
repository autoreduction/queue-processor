"""
Module to perform ICAT client functionality
Functions for login and query available from class
"""

import icat

from utils.settings import ICAT_SETTINGS
from utils.clients.abstract_client import AbstractClient
from utils.clients.connection_exception import ConnectionException


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

    def refresh(self):
        """ Refreshes the ICAT session only if necessary """
        self.client.refresh()

    def disconnect(self):
        """ Disconnect the ICAT client """
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
