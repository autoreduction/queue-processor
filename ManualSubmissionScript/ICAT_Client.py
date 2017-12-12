import icat
from settings import ICAT_SETTINGS
from time import gmtime, strftime

class ICAT():
    def get_client(self):
        icat_client = icat.client.Client(ICAT_SETTINGS['URL'])
        session_id = self.client_login(icat_client, ICAT_SETTINGS['AUTH'], ICAT_SETTINGS['USER'], ICAT_SETTINGS['PASSWORD'])
        return icat_client

    def client_login(self, icat_client, auth, username, password):
        return icat_client.login(auth, {'username': username, 'password': password})

    def execute_query(self, icat_client, query):
        icat_client.refresh
        return icat_client.search(query)


