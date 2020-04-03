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
from mock import MagicMock

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
        self.test_maintenance_dict = {
            "before_cycles": self.create_maintenance_day_from_start_date(
                cycles_start + relativedelta(days=-1)),
            "within_first_cycle": self.create_maintenance_day_from_start_date(
                cycles_start + relativedelta(weeks=2)),
            "after_cycles": self.create_maintenance_day_from_start_date(
                cycles_start + relativedelta(months=number_of_cycles, days=1))
        }

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
        self.assertIsInstance(sdp._datetime_fields, list)
        self.assertIsInstance(sdp._sort_by_field, str)

    def test_sort_order(self):
        local_cycle_data = [
            self.test_cycle_data[1],
            self.test_cycle_data[2],
            self.test_cycle_data[0]
        ]
        sdp = SchedulerDataProcessor()
        result = sdp._sort_by_date(local_cycle_data)
        self.assertEqual(self.test_cycle_data, result)

    def test_clean_with_invalid_name(self):
        local_cycle_data = self.test_cycle_data.copy()
        local_cycle_data[0]["name"] = "invalid"
        sdp = SchedulerDataProcessor()
        result = sdp._clean_data(local_cycle_data)
        self.assertTrue(len(result) == len(local_cycle_data)-1)

    def test_clean_with_invalid_date(self):
        sdp = SchedulerDataProcessor()
        local_cycle_data = self.test_cycle_data.copy()
        earlier_than_possible = sdp._earliest_possible_date + relativedelta(days=-1)
        local_cycle_data[0]["start"] = earlier_than_possible
        result = sdp._clean_data(local_cycle_data)
        self.assertTrue(len(result) == len(local_cycle_data)-1)

    def test_pre_process_with_valid_data(self):
        sdp = SchedulerDataProcessor()
        sdp._sort_by_date = MagicMock()
        sdp._clean_data = MagicMock()
        result = sdp._pre_process(self.test_cycle_data,
                         self.test_maintenance_dict.values())
        sdp._sort_by_date.assert_called()
        sdp._clean_data.assert_called()
        self.assertTrue(len(result) == 2)

    def test_process_with_maintenance_before_cycle(self):
        sdp = SchedulerDataProcessor()
        sdp._unexpected_maintenance_day_warning = MagicMock()
        sdp._process(self.test_cycle_data, [self.test_maintenance_dict["before_cycles"]])
        sdp._unexpected_maintenance_day_warning.assert_called_with(
            self.test_maintenance_dict["before_cycles"],
            self.test_cycle_data[0],
            self.test_cycle_data[1]
        )

    def test_process_with_maintenance_before_cycles(self):
        sdp = SchedulerDataProcessor()
        sdp._unexpected_maintenance_day_warning = MagicMock()
        cycles = sdp._process(self.test_cycle_data, [self.test_maintenance_dict["before_cycles"]])
        sdp._unexpected_maintenance_day_warning.assert_called_with(
            self.test_maintenance_dict["before_cycles"],
            self.test_cycle_data[0],
            self.test_cycle_data[1]
        )
        self.assertTrue(len(cycles) == len(self.test_cycle_data))
        for cycle in cycles:
            self.assertIsInstance(cycle, Cycle)
            self.assertTrue(len(cycle.maintenance_days) == 0)

    def test_process_with_maintenance_after_cycles(self):
        sdp = SchedulerDataProcessor()
        sdp._unexpected_maintenance_day_warning = MagicMock()
        cycles = sdp._process(self.test_cycle_data, [self.test_maintenance_dict["after_cycles"]])
        sdp._unexpected_maintenance_day_warning.assert_called_with(
            self.test_maintenance_dict["after_cycles"],
            self.test_cycle_data[2],
            None
        )
        self.assertTrue(len(cycles) == len(self.test_cycle_data))
        for cycle in cycles:
            self.assertIsInstance(cycle, Cycle)
            self.assertTrue(len(cycle.maintenance_days) == 0)

    def test_process_with_maintenance_within_cycles(self):
        sdp = SchedulerDataProcessor()
        sdp._unexpected_maintenance_day_warning = MagicMock()
        cycles = sdp._process(self.test_cycle_data, [self.test_maintenance_dict["within_first_cycle"]])
        sdp._unexpected_maintenance_day_warning.assert_not_called()
        self.assertTrue(len(cycles) == len(self.test_cycle_data))
        for cycle in cycles:
            self.assertIsInstance(cycle, Cycle)
            if cycle is not cycles[0]:
                self.assertTrue(len(cycle.maintenance_days) == 0)
        self.assertTrue(len(cycles[0].maintenance_days) == 1)
        m_day = cycles[0].maintenance_days.pop()
        self.assertTrue(m_day.start == self.test_maintenance_dict["within_first_cycle"]["start"]
                        and m_day.end == self.test_maintenance_dict["within_first_cycle"]["end"])

    def test_conversion_with_invalid_args(self):
        local_cycle_data = self.test_cycle_data.copy()
        local_cycle_data[0].pop("start")
        sdp = SchedulerDataProcessor()
        with self.assertRaises(KeyError):
            sdp.convert_raw_to_structured(local_cycle_data,
                                      self.test_maintenance_dict.values())

