# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Client class for ingesting BusApps data via SOAP
"""
import json
from datetime import datetime

from scripts.scheduler_ingest import SchedulerDataProcessor
from utils.clients.abstract_client import AbstractClient
from utils.clients.connection_exception import ConnectionException
from utils.test_settings import BUSAPPS_SETTINGS

from suds import Client, WebFault


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

    def create_uows_client(self):
        if self._uows_client is None:
            self._uows_client = Client(self.credentials.uows_url)
            # print(type(self._uows_client))

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
        # self.credentials.password = "1"
        if self._session_id is None:
            try:
                self._session_id = self._uows_client.service.login(Account=self.credentials.username,
                                                               Password=self.credentials.password)
            except WebFault:
                raise ConnectionException("BusApps Ingestion")

        if self._scheduler_client is None:
            self.create_scheduler_client()

        return self._session_id

    def disconnect(self):
        """
        Logout from the User Office Web Service (UOWS)
        """
        self._uows_client.service.logout(self._session_id)
        self._session_id = None

    def _test_connection(self):  # 'getAllFacilityNames' and 'getFacilityList' chosen as arbitrary test methods
        try:
            self._uows_client.service.getAllFacilityNames()
        except AttributeError:
            raise TypeError("The UOWS Client does not exist or has not been initialised properly")

        try:
            self._scheduler_client.service.getFacilityList(self._session_id)
        except AttributeError:
            raise TypeError("The Scheduler Client does not exist or has not been initialised properly")
        except WebFault:    # Raised by suds if the session id is not valid
            raise ConnectionException("BusApps Ingestion")

        return True

    def ingest_cycle_dates(self):
        return self._scheduler_client.service.getCycles(sessionId=self._session_id)

    def ingest_maintenance_days(self):
        return self._scheduler_client.service.getOfflinePeriods(sessionId=self._session_id,
                                                                reason='Maintenance')


#TODO: Please note - all of the code below is for testing purposes only.

# TODO: Note - the commented-out code below dumps data locally
#   Only need to run if want to update local version

baic = BusAppsIngestionClient()
baic.connect()
cycles = baic.ingest_cycle_dates()
maintn = baic.ingest_maintenance_days()

# cycles_dict_items = [dict(item) for item in cycles]
# maintn_dict_items = [dict(item) for item in maintn]
#
# print(repr(cycles[0].start))
#
# with open("ingested_cycle_dates", "w") as fh:
#     json.dump(cycles_dict_items, fh, default=str)
#
# with open("ingested_maintn_dates", "w") as fh:
#     json.dump(maintn_dict_items, fh, default=str)
#

# def change_datetime_format(list):
#     keys_to_convert = ["start", "end"]
#     # print(list[0])
#     for item in list:
#         for key in keys_to_convert:
#             if key in item:
#                 without_timezone = item[key].split("+")[0]
#                 item[key] = datetime.strptime(without_timezone, "%Y-%m-%d %H:%M:%S")
#     # print(list[0])
#     return list

# with open("ingested_cycle_dates", "r") as fh:
#     cycles = json.load(fh)
#
# with open("ingested_maintn_dates", "r") as fh:
#     maintn = json.load(fh)
#
# # print(f"c: {cycles[0]}, m: {maintn[0]}")
# cycles = to_datetime(cycles)
# maintn = to_datetime(maintn)

# print(f"c: {cycles[0]}, m: {maintn[0]}")
# exit()

sdp = SchedulerDataProcessor()

# print(f"normal: type={type(cycles)}, itemtype={type(cycles[0])},some data=\n{cycles[:3]}")
# sdp.print_start_dates(cycles[:3])
#
# cycles_dict = []
# for item in cycles[:3]:
#     cycles_dict.append(dict(item))
#
# print(f"dict items: type={type(cycles_dict)}, itemtype={type(cycles_dict[0])},some data=\n{cycles_dict[:3]}")


# sdp.print_start_dates()
cycle_list = sdp.convert_raw_to_structured(cycles, maintn)

for c in cycle_list:
    print(c)
    for m in c.maintenance_days:
        print(f"    {m}")



# TODO: To Test
#   - Client (uows) null
#   - Client exists, session_id doesn't?
