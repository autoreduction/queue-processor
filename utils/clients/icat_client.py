"""
Module to perform ICAT client functionality
Functions for login and query available from class
"""

import icat

# pylint: disable=import-error
from utils.clients.settings import ICAT


class ICATClient(object):
    """
    This class provides a layer of abstraction from Python ICAT.
    Only allowing logging in and querying.
    """

    def __init__(self):
        self.client = icat.Client(ICAT['URL'])
        self.client_login()

    def client_login(self):
        """
        Log in to ICAT using the details provided in the test_settings.py file
        """
        self.client.login(ICAT['AUTH'],
                          {'username': ICAT['USER'],
                           'password': ICAT['PASSWORD']})

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
            self.client_login()
        return self.client.search(query)
