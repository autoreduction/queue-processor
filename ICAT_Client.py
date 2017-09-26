import icat
from settings import ICAT_SETTINGS

"""
This class provides a layer of abstraction from Python ICAT. Only allowing logging in and querying.
"""


class ICAT:

    def __init__(self):
        self.client = icat.Client(ICAT_SETTINGS['URL'])
        self.client_login()

    def client_login(self):
        self.client.login(ICAT_SETTINGS['AUTH'], {'username': ICAT_SETTINGS['USER'], 'password': ICAT_SETTINGS['PASSWORD']})

    def execute_query(self, query):
        try:
            self.client.refresh()
        except icat.exception.ICATSessionError:
            # Session has most likely expired, try and log in again.
            self.client_login()
        return self.client.search(query)
