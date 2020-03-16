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


class BusAppsIngestionClient(AbstractClient):
    """
    Class for client to ingest BusApps data via SOAP
    """
    def __init__(self, credentials=None):
        if not credentials:
            credentials = BUSAPPS_SETTINGS
            # print(f"credentials: {credentials.uows, credentials.scheduler}")
        super(BusAppsIngestionClient, self).__init__(credentials)


        scheduler_data = SchedulerDataProcessor(self.credentials.username,
                                                self.credentials.password,
                                                self.credentials.uows,
                                                self.credentials.scheduler)
        scheduler_data.get_data()
        print(scheduler_data.raw_cycle_data)
        print(scheduler_data.raw_maintenance_data)


baic = BusAppsIngestionClient()
