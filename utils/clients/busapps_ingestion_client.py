# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Client class for ingesting BusApps data via SOAP
"""
from suds import Client, WebFault
from utils.clients.abstract_client import AbstractClient
from utils.clients.connection_exception import ConnectionException
from utils.test_settings import BUSAPPS_SETTINGS


class BusAppsIngestionClient(AbstractClient):
    """
    Class for client to ingest BusApps data via SOAP
    """
    def __init__(self, credentials=None):
        if not credentials:
            credentials = BUSAPPS_SETTINGS
        super(BusAppsIngestionClient, self).__init__(credentials)
        self._uows_client = None
        self._scheduler_client = None
        self._session_id = None
        # TODO: Note - I've used an error dictionary (for reuse and more granular testing)  # pylint:disable=fixme,line-too-long
        self._errors = {
            "invalid_uows_client": TypeError("The UOWS Client does not exist"
                                             "or has not been initialised properly"),
            "invalid_scheduler_client": TypeError("The Scheduler Client does not exist"
                                                  "or has not been initialised properly"),
            "invalid_session_id": ConnectionException("BusApps Ingestion")
        }

    def create_uows_client(self):
        """ Creates a User Office Web Service Client is one does not exist """
        if self._uows_client is None:
            self._uows_client = Client(self.credentials.uows_url)
            # print(type(self._uows_client))

    def create_scheduler_client(self):
        """ Creates a Scheduler Client is one does not exist """
        if self._scheduler_client is None:
            self._scheduler_client = Client(self.credentials.scheduler_url)

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
            except WebFault:
                raise self._errors["invalid_session_id"]

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
        except AttributeError:
            raise self._errors["invalid_uows_client"]

        try:
            self._scheduler_client.service.getFacilityList(self._session_id)
        except AttributeError:
            raise self._errors["invalid_scheduler_client"]
        except WebFault:    # Raised by suds if the session id is not valid
            raise self._errors["invalid_session_id"]

        return True

    def ingest_cycle_dates(self):
        """ Ingests cycles dates from the Scheduler client.
        :return: Cycle data as a list of 'sudsobject's """
        return self._scheduler_client.service.getCycles(sessionId=self._session_id)

    def ingest_maintenance_days(self):
        """ Ingests maintenance day dates from the Scheduler client.
        :return: Maintenance day data as a list of 'sudsobject's """
        return self._scheduler_client.service.getOfflinePeriods(sessionId=self._session_id,
                                                                reason='Maintenance')


# TODO: Please note - all of the code below is for testing purposes only.    # pylint:disable=fixme

# baic = BusAppsIngestionClient()
# baic.connect()
# cycles = baic.ingest_cycle_dates()
# maintn = baic.ingest_maintenance_days()
#
# sdp = SchedulerDataProcessor()
#
# def print_all_dates(cycle_objs):
#     for c in cycle_objs:
#         print(f"Cycle: {c.start} - {c.end}")
#         for m in c.maintenance_days:
#             print(f"\tM Day: {m.start} - {m.end}")
#
# print("\n\t=====AS SEPARATE=====\n")
# cycle_list = sdp.convert_raw_to_structured_as_separate(cycles, maintn)
# print_all_dates(cycle_list)
#
# # print("\n\t=====AS COMBINED=====\n")
# # cycle_list = sdp.convert_raw_to_structured(cycles, maintn)
# # print_all_dates(cycle_list)
