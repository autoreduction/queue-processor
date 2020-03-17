# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Client class for ingesting BusApps data via SOAP
"""
from scripts.scheduler_ingest import SchedulerDataProcessor
from utils.clients.abstract_client import AbstractClient
from utils.test_settings import BUSAPPS_SETTINGS

from suds import Client

class BusAppsIngestionClient(AbstractClient):
    """
    Class for client to ingest BusApps data via SOAP
    """
    def __init__(self, credentials=None):
        if not credentials:
            credentials = BUSAPPS_SETTINGS
            # print(f"credentials: {credentials.uows, credentials.scheduler}")
        super(BusAppsIngestionClient, self).__init__(credentials)
        self._uows_client = None
        self._scheduler_client = None
        self._session_id = None

    def create_uows_client(self):
        if self._uows_client is None:
            self._uows_client = Client(self.credentials.uows_url)
            print(type(self._uows_client))

    def create_scheduler_client(self):
        if self._scheduler_client is None:
            self._scheduler_client = Client(self.credentials.scheduler_url)

    def connect(self):
        """
        Login to User Office Web Service (UOWS)
        :return: UOWS connection session ID
        """
        if self._uows_client is None:
            self.create_uows_client()
        if self._session_id is None:
            self._session_id = self._uows_client.service.login(Account=self.credentials.username,
                                                               Password=self.credentials.password)
        if self._scheduler_client is None:
            self.create_scheduler_client()

        return self._session_id

    def disconnect(self):
        """
        Logout from the User Office Web Service (UOWS)
        """
        self._uows_client.service.logout(self._session_id)

    @staticmethod
    def test_client(client):
        if type(client) is not Client:
            raise AttributeError("The client instance is not of the expected type 'Client'")
        else:
            return True

    def _test_connection(self):
        try:
            self.test_client(self._uows_client)
        except AttributeError:
            raise TypeError("The UOWS Client does not exist or has not been initialised properly")
        try:
            self.test_client(self._scheduler_client)
        except AttributeError:
            raise TypeError("The Scheduler Client does not exist or has not been initialised properly")


baic = BusAppsIngestionClient()
baic.connect()
# baic._uows_client = None
baic._test_connection()
