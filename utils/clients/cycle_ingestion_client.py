# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Client class for ingesting cycle data from ISIS Business Applications (BusApps) via SOAP
"""
import suds
from utils.clients.abstract_client import AbstractClient
from utils.clients.connection_exception import ConnectionException
from utils.settings import CYCLE_SETTINGS


class CycleIngestionClient(AbstractClient):
    """
    Class for client to ingest cycle data from ISIS Business Applications (BusApps) via SOAP
    """

    # pylint:disable=super-with-arguments
    def __init__(self, credentials=None):
        if not credentials:
            credentials = CYCLE_SETTINGS
        super(CycleIngestionClient, self).__init__(credentials)
        self._uows_client = None
        self._scheduler_client = None
        self._session_id = None
        self._errors = {
            "invalid_uows_client":
            TypeError("The UOWS Client does not exist"
                      "or has not been initialised properly"),
            "invalid_scheduler_client":
            TypeError("The Scheduler Client does not exist"
                      "or has not been initialised properly"),
            "invalid_session_id":
            ConnectionException("Cycle Ingestion")
        }

    def create_uows_client(self):
        """ Creates a User Office Web Service Client is one does not exist """
        if self._uows_client is None:
            self._uows_client = suds.Client(self.credentials.uows_url)

    def create_scheduler_client(self):
        """ Creates a Scheduler Client is one does not exist """
        if self._scheduler_client is None:
            self._scheduler_client = suds.Client(self.credentials.scheduler_url)

    def connect(self):
        """ Login to User Office Web Service (UOWS)
        :return: UOWS connection session ID """
        if self._uows_client is None:
            self.create_uows_client()
        if self._session_id is None:
            try:
                self._session_id = \
                    self._uows_client.service.login(Account=self.credentials.username,
                                                    Password=self.credentials.password)
            except suds.WebFault as exp:
                raise self._errors["invalid_session_id"] from exp

        if self._scheduler_client is None:
            self.create_scheduler_client()

        return self._session_id

    def disconnect(self):
        """ Logout from the User Office Web Service (UOWS) """
        self._uows_client.service.logout(self._session_id)
        self._session_id = None

    def _test_connection(self):
        """ Test whether there is a connection to the User Office Web Service (UOWS)
        :return: True if there is a connection.
        :raises TypeError:
            If the UOWS or Scheduler client does not exist or has not been initialised properly.
            Note: an error message will describe which client is at fault.
        :raises ConnectionException: If the session id is not valid. """
        # 'getAllFacilityNames' and 'getFacilityList' chosen as arbitrary test methods
        try:
            self._uows_client.service.getAllFacilityNames()
        except AttributeError as exp:
            raise self._errors["invalid_uows_client"] from exp

        try:
            self._scheduler_client.service.getFacilityList(self._session_id)
        except AttributeError as exp:
            raise self._errors["invalid_scheduler_client"] from exp
        except suds.WebFault as exp:  # Raised by suds if the session id is not valid
            raise self._errors["invalid_session_id"] from exp

        return True

    def ingest_cycle_dates(self):
        """ Ingests cycles dates from the Scheduler client.
        :return: Cycle data as a list of 'sudsobject's """
        return self._scheduler_client.service.getCycles(sessionId=self._session_id)

    def ingest_maintenance_days(self):
        """ Ingests maintenance day dates from the Scheduler client.
        :return: Maintenance day data as a list of 'sudsobject's """
        return self._scheduler_client.service.getOfflinePeriods(sessionId=self._session_id, reason='Maintenance')
