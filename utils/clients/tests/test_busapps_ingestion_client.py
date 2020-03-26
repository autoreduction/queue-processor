# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test BusApps ingestion client
"""
import unittest

from utils.clients.settings.client_settings_factory import ClientSettingsFactory


class TestBusAppsIngestionClient(unittest.TestCase):
    """
    Exercises the BusApps ingestion client
    """
    def setUp(self):
        pass

# TODO: Tests
#   - Default init:
#   invalid init: pass invalid credentials
#   - create_uows_client: _uows_client is of Client type
#   create_uows_client + invalid creds: raises Exception
#   create_scheduler_client: _scheduler_client is of Client type
#   create_scheduler_client + invalid creds: raises Exception
#   - connect with valid creds: return same id
#   connect with invalid creds: connectionException
#   - disconnect: _session_id is None
#   - _test_connection + both clients mocked valid: returns True
#   _test_connection + uows mocked invalid: TypeError("The UOWS Client
#   _test_connection + sched mocked invalid: TypeError("The Scheduler Client
#   _test_connection + session invalid: ConnectionException("BusApps
#   - ingest_cycle_dates + mocked return: return == mocked
#   ingest_maintenance_days + mocked return: return == mocked

