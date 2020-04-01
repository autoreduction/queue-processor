# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests the functionality within scheduler_ingest.py
"""
from datetime import datetime

import unittest

from dateutil.relativedelta import relativedelta

from scripts.scheduler_ingest import Cycle, MaintenanceDay, SchedulerDataProcessor


class TestCycle(unittest.TestCase):
    """
    Exercises the Cycle class
    """
    def setUp(self):
        self.test_cycle_values = {
            "name": "test_cycle_name",
            "start": datetime(2020, 1, 1, tzinfo=None),
            "end": datetime(2020, 2, 1, tzinfo=None)
        }
        self.test_maintenance_day_values = {
            "start": datetime(2020, 1, 2, tzinfo=None),
            "end": datetime(2020, 1, 3, tzinfo=None)
        }

    def test_init(self):
        cycle = Cycle(self.test_cycle_values["name"],
                      self.test_cycle_values["start"],
                      self.test_cycle_values["end"])
        self.assertEqual(cycle.name, self.test_cycle_values["name"])
        self.assertEqual(cycle.start, self.test_cycle_values["start"])
        self.assertEqual(cycle.end, self.test_cycle_values["end"])
        self.assertTrue(len(cycle.maintenance_days) == 0)

    def test_add_maintenance_day(self):
        cycle = Cycle(self.test_cycle_values["name"],
                      self.test_cycle_values["start"],
                      self.test_cycle_values["end"])
        cycle.add_maintenance_day(self.test_maintenance_day_values["start"],
                                  self.test_maintenance_day_values["end"])
        self.assertTrue(len(cycle.maintenance_days) == 1)
        self.assertIsInstance(cycle.maintenance_days[0], MaintenanceDay)
        self.assertEqual(cycle.maintenance_days[0].start,
                         self.test_maintenance_day_values["start"])
        self.assertEqual(cycle.maintenance_days[0].end,
                         self.test_maintenance_day_values["end"])


class TestSchedulerDataProcessor(unittest.TestCase):
    # pylint: disable=protected-access
    """
    Exercises the scheduler data processor
    """
    def setUp(self):
        cycles_start = datetime(2020, 1, 1, tzinfo=None)
        number_of_cycles = 3
        self.test_cycle_data = self.create_cycle_data(length=number_of_cycles,
                                                      initial_start=cycles_start)
        self.test_maintenance_data = {
            "before_cycles": self.create_maintenance_day_from_start_date(
                cycles_start + relativedelta(days=-1)),
            "within_first_cycle": self.create_maintenance_day_from_start_date(
                cycles_start + relativedelta(weeks=2)),
            "within_second_cycle": self.create_maintenance_day_from_start_date(
                cycles_start + relativedelta(months=1, weeks=2)),
            "after_cycles": self.create_maintenance_day_from_start_date(
                cycles_start + relativedelta(months=number_of_cycles, days=1))
        }
        # for m in self.test_maintenance_data.values():
        #     print(m)

    @staticmethod
    def create_cycle_data(length, initial_start):
        cycles = []
        start_date = initial_start
        for index in range(length):
            end_date = start_date + relativedelta(months=1, days=-1)
            id_ = str(index+1)
            cycles.append({
                "id": id_,
                "name": f"000{id_}/x",
                "start": start_date,
                "end": end_date
            })
            start_date = end_date + relativedelta(days=1)
        return cycles

    @staticmethod
    def create_maintenance_day_from_start_date(start_date):
        return {
            "start": start_date,
            "end": start_date + relativedelta(days=1),
            "reason": "Maintenance",
            "facility": "Test"
        }

    def test_init(self):
        sdp = SchedulerDataProcessor()
        self.assertIsInstance(sdp._earliest_possible_date, datetime)
        self.assertIsInstance(sdp._cycle_name_regex, str)
        self.assertIsInstance(sdp._maintenance_specific_key, str)
        self.assertIsInstance(sdp._datetime_fields, list)
        self.assertIsInstance(sdp._sort_by_field, str)

    # def test_sort_order(self):

# TODO:
#   X* init values set
#   * _sort_by_date --> returns sort list
#   * _clean_data ; unexpected name ; removed
#    _clean_data ; unexpected date ; removed
#   * _maintenance_before_cycle_warning ; next_cycle=None   [perhaps mock print to see if called with?]
#    _maintenance_before_cycle_warning ; next_cycle=something
#   * _pre_process ; check output as expected
#   * _process ; 1 cycle day + EARLIER maintenance day --> warning printed
#    _process ; 1 cycle day + WITHIN maintenance day --> maintenance added ; cycle type, maintnn type
#    _process ; 1 cycle day + LATER maintenance day --> warning printed
#    _process ; 1 cycle day + LATER maintenance day --> warning printed

TestSchedulerDataProcessor()