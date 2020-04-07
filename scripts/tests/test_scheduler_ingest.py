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
        """ Test initialisation values are set """
        cycle = Cycle(self.test_cycle_values["name"],
                      self.test_cycle_values["start"],
                      self.test_cycle_values["end"])
        self.assertEqual(cycle.name, self.test_cycle_values["name"])
        self.assertEqual(cycle.start, self.test_cycle_values["start"])
        self.assertEqual(cycle.end, self.test_cycle_values["end"])
        self.assertTrue(len(cycle.maintenance_days) == 0)

    def test_add_maintenance_day(self):
        """ Test cycle stores a given maintenance day properly when
        it received through the add_maintenance_day method. """
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
        """ Creates fake cycle data where each cycle is exactly 1 month
        and there are no gaps between cycles
        :param length: The number of cycles to create test data for
        :param initial_start: The date to start the initial cycle from
        :return: The fake cycle data """
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
        """ Creates a fake maintenance day data entry (minus an id) from a start_date
        :param start_date: The start date of the maintenance day
        :return: The fake maintenance day data entry """
        return {
            "start": start_date,
            "end": start_date + relativedelta(days=1),
            "reason": "Maintenance",
            "facility": "Test"
        }

    def test_init(self):
        """ Test initialisation values are set """
        sdp = SchedulerDataProcessor()
        self.assertIsInstance(sdp._earliest_possible_date, datetime)
        self.assertIsInstance(sdp._cycle_name_regex, str)
        self.assertIsInstance(sdp._datetime_fields, list)
        self.assertIsInstance(sdp._sort_by_field, str)

    def test_sort_order(self):
        """ Test _sort_order by providing it an unordered list of cycles.
         Assumes test_cycle_data is already ordered """
        local_cycle_data = [
            self.test_cycle_data[1],
            self.test_cycle_data[2],
            self.test_cycle_data[0]
        ]
        sdp = SchedulerDataProcessor()
        result = sdp._sort_by_date(local_cycle_data)
        self.assertEqual(self.test_cycle_data, result)

    def test_clean_with_invalid_name(self):
        """ Test _clean_data by providing it data containing a cycle with an invalid name.
         Assumes all other entries in test_cycle_data are valid """
        local_cycle_data = self.test_cycle_data.copy()
        local_cycle_data[0]["name"] = "invalid"
        sdp = SchedulerDataProcessor()
        result = sdp._clean_data(local_cycle_data)
        self.assertTrue(len(result) == len(local_cycle_data)-1)

    def test_clean_with_invalid_date(self):
        """ Test _clean_data by providing it data containing a cycle with an date
         1 day before the earliest possible (specified by the SchedulerDataProcessor).
         Assumes all other entries in test_cycle_data are valid """
        sdp = SchedulerDataProcessor()
        local_cycle_data = self.test_cycle_data.copy()
        earlier_than_possible = sdp._earliest_possible_date + relativedelta(days=-1)
        local_cycle_data[0]["start"] = earlier_than_possible
        result = sdp._clean_data(local_cycle_data)
        self.assertTrue(len(result) == len(local_cycle_data)-1)

    def test_pre_process_with_valid_data(self):
        """ Test _pre_process calls the internal methods the expected number of times
        and returns the expected number of lists """
        sdp = SchedulerDataProcessor()
        sdp._sort_by_date = MagicMock()
        sdp._clean_data = MagicMock()
        result = sdp._pre_process(self.test_cycle_data,
                                  self.test_maintenance_dict.values())
        self.assertTrue(sdp._sort_by_date.call_count == 2)
        self.assertTrue(sdp._clean_data.call_count == 2)
        self.assertTrue(len(result) == 2)

    def test_process_with_maintenance_before_cycles(self):
        """ Test _process calls _unexpected_maintenance_day_warning when
        it encounters a maintenance day start value *earlier* than any cycle start date,
        and doesn't add this maintenance day to any cycle. """
        sdp = SchedulerDataProcessor()
        sdp._unexpected_maintenance_day_warning = MagicMock()
        cycles = sdp._process(self.test_cycle_data, [self.test_maintenance_dict["before_cycles"]])
        sdp._unexpected_maintenance_day_warning.assert_called_once()
        self.assertTrue(len(cycles) == len(self.test_cycle_data))
        for cycle in cycles:
            self.assertIsInstance(cycle, Cycle)
            self.assertTrue(len(cycle.maintenance_days) == 0)

    def test_process_with_maintenance_after_cycles(self):
        """ Test _process calls _unexpected_maintenance_day_warning when
        it encounters a maintenance day start value *later* than any cycle end date,
        and doesn't add this maintenance day to any cycle. """
        sdp = SchedulerDataProcessor()
        sdp._unexpected_maintenance_day_warning = MagicMock()
        cycles = sdp._process(self.test_cycle_data, [self.test_maintenance_dict["after_cycles"]])
        sdp._unexpected_maintenance_day_warning.assert_called_once()
        for cycle in cycles:
            self.assertIsInstance(cycle, Cycle)
            self.assertTrue(len(cycle.maintenance_days) == 0)

    def test_process_with_maintenance_between_cycles(self):
        """ Test _process calls _unexpected_maintenance_day_warning when it encounters
        a maintenance day start value *in-between* the previous and cycle end date and
        current cycle start date, and ensures it doesn't add this maintenance day to any cycle. """
        local_cycle_data = self.test_cycle_data.copy()
        local_cycle_data[0]["end"] = local_cycle_data[0]["start"] + relativedelta(days=1)
        sdp = SchedulerDataProcessor()
        sdp._unexpected_maintenance_day_warning = MagicMock()
        cycles = sdp._process(self.test_cycle_data,
                              [self.test_maintenance_dict["within_first_cycle"]])
        sdp._unexpected_maintenance_day_warning.assert_called_once()
        for cycle in cycles:
            self.assertIsInstance(cycle, Cycle)
            self.assertTrue(len(cycle.maintenance_days) == 0)

    def test_process_with_maintenance_within_cycles(self):
        """ Test _process adds a maintenance day to the appropriate cycle when said
        maintenance day starts and ends within the given cycle's start and end dates. """
        sdp = SchedulerDataProcessor()
        sdp._unexpected_maintenance_day_warning = MagicMock()
        cycles = sdp._process(self.test_cycle_data,
                              [self.test_maintenance_dict["within_first_cycle"]])
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
        """ Test a KeyError is thrown if a cycle attribute is missing when
         convert_raw_to_structured is called """
        local_cycle_data = self.test_cycle_data.copy()
        local_cycle_data[0].pop("start")
        sdp = SchedulerDataProcessor()
        with self.assertRaises(KeyError):
            sdp.convert_raw_to_structured(local_cycle_data,
                                          self.test_maintenance_dict.values())
