import icat
from settings import ICAT_SETTINGS


class ICAT():
    def get_client(self):
        icat_client = icat.client.Client(ICAT_SETTINGS['URL'])
        self.client_login(icat_client, ICAT_SETTINGS['AUTH'], ICAT_SETTINGS['USER'], ICAT_SETTINGS['PASSWORD'])
        return icat_client

    @staticmethod
    def client_login(icat_client, auth, username, password):
        return icat_client.login(auth, {'username': username, 'password': password})

    @staticmethod
    def execute_query(icat_client, query):
        icat_client.refresh()
        return icat_client.search(query)
