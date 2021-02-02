# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests the functionality within scheduler_ingest.py
"""
import unittest
from datetime import datetime
from unittest.mock import patch

from dateutil.relativedelta import relativedelta

from scripts.scheduler_ingest import Cycle, MaintenanceDay, SchedulerDataProcessor


class TestCycle(unittest.TestCase):
    """
    Exercises the Cycle class
    """
    def setUp(self):
        """ Create example cycle and maintenance day data for testing with """
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
        """
        Test: Class variables are created and set
        When: Cycle is initialised
        """
        cycle = Cycle(self.test_cycle_values["name"],
                      self.test_cycle_values["start"],
                      self.test_cycle_values["end"])
        self.assertEqual(cycle.name, self.test_cycle_values["name"])
        self.assertEqual(cycle.start, self.test_cycle_values["start"])
        self.assertEqual(cycle.end, self.test_cycle_values["end"])
        self.assertEqual(0, len(cycle.maintenance_days))

    def test_add_maintenance_day(self):
        """
        Test: Cycle creates and stores a maintenance day based on the arguments given
        When: add_maintenance_day is called with valid arguments
        """
        cycle = Cycle(self.test_cycle_values["name"],
                      self.test_cycle_values["start"],
                      self.test_cycle_values["end"])
        cycle.add_maintenance_day(self.test_maintenance_day_values["start"],
                                  self.test_maintenance_day_values["end"])
        self.assertEqual(1, len(cycle.maintenance_days))
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

    @staticmethod
    def create_cycle_from_dict(cycle_dict):
        """ Creates a Cycle object from a dict containing the keys: name, start, end
        :param cycle_dict: a dict containing the keys: name, start, end
        :return: A Cycle object """
        return Cycle(cycle_dict["name"],
                     cycle_dict["start"],
                     cycle_dict["end"])

    def test_init(self):
        """
        Test: Class variables are created and set
        When: SchedulerDataProcessor is initialised
        """
        sdp = SchedulerDataProcessor()
        self.assertIsInstance(sdp._earliest_possible_date, datetime)
        self.assertIsInstance(sdp._cycle_name_regex, str)
        self.assertIsInstance(sdp._datetime_fields, list)
        self.assertIsInstance(sdp._sort_by_field, str)

    def test_sort_order(self):
        """
        Test: _sort_order orders a list of cycles by start date
        When: Called with a list of cycles
        """
        # Note: This test assumes self.test_cycle_data is ordered
        local_cycle_data = [
            self.test_cycle_data[1],
            self.test_cycle_data[2],
            self.test_cycle_data[0]
        ]
        sdp = SchedulerDataProcessor()
        result = sdp._sort_by_date(local_cycle_data)
        self.assertEqual(self.test_cycle_data, result)

    def test_clean_with_invalid_name(self):
        """
        Test: _clean_data removes the cycle with an invalid name
        When: Called with data containing a cycle with an invalid name
        """
        # Note: Assumes all other entries in test_cycle_data are valid
        local_cycle_data = self.test_cycle_data.copy()
        local_cycle_data[0]["name"] = "invalid"
        sdp = SchedulerDataProcessor()
        result = sdp._clean_data(local_cycle_data)
        self.assertEqual(len(local_cycle_data) - 1, len(result))

    def test_clean_with_invalid_date(self):
        """
        Test: _clean_data removes the cycle with an invalid date
        When: Called with data containing a cycle with a date 1 day
        before the earliest possible (specified by the SchedulerDataProcessor)
        """
        sdp = SchedulerDataProcessor()
        local_cycle_data = self.test_cycle_data.copy()
        earlier_than_possible = sdp._earliest_possible_date + relativedelta(days=-1)
        local_cycle_data[0]["start"] = earlier_than_possible
        result = sdp._clean_data(local_cycle_data)
        self.assertEqual(len(local_cycle_data) - 1, len(result))

    @patch('scripts.scheduler_ingest.SchedulerDataProcessor._clean_data')
    @patch('scripts.scheduler_ingest.SchedulerDataProcessor._sort_by_date')
    def test_pre_process_with_valid_data(self, mocked_sort_by_date, mocked_clean_data):
        """
        Test: _pre_process calls both _clean_data and _sort_by_date twice (once for each
        data-set given) and returns 2 lists
        When: Called with valid data-sets
        """
        sdp = SchedulerDataProcessor()
        result = sdp._pre_process(self.test_cycle_data,
                                  self.test_maintenance_dict.values())
        self.assertEqual(2, mocked_sort_by_date.call_count)
        self.assertEqual(2, mocked_clean_data.call_count)
        self.assertEqual(2, len(result))

    def check_process_output(self, _process_output, expected_length):
        """
        Checks all items in _process_output are Cycle objects, that they do not
        contain any maintenance days, and the number of cycles is as expected
        :param _process_output: A list of cycles retrieved as output from _process()
        :param expected_length: The expected number of cycles retrieved from _process()
        """
        self.assertEqual(len(_process_output), expected_length)
        for cycle in _process_output:
            self.assertIsInstance(cycle, Cycle)
            self.assertEqual(0, len(cycle.maintenance_days))

    @patch('scripts.scheduler_ingest.SchedulerDataProcessor._md_warning')
    def test_process_with_maintenance_before_cycles(self, mocked_md_warning):
        """
        Test: _process calls _md_warning, and doesn't add the current maintenance day to any cycle
        When: _process encounters a maintenance day start value *earlier* than any cycle start date
        """
        sdp = SchedulerDataProcessor()
        cycles = sdp._process(self.test_cycle_data,
                              [self.test_maintenance_dict["before_cycles"]])

        (_, kwargs) = mocked_md_warning.call_args
        self.assertEqual(kwargs["md_data"],
                         self.test_maintenance_dict["before_cycles"])
        self.assertIsNone(kwargs['cycle_before'])
        self.assertEqual(kwargs["cycle_after"],
                         self.create_cycle_from_dict(self.test_cycle_data[0]))

        self.check_process_output(cycles, len(self.test_cycle_data))

    @patch('scripts.scheduler_ingest.SchedulerDataProcessor._md_warning')
    def test_process_with_maintenance_after_cycles(self, mocked_md_warning):
        """
        Test: _process calls _md_warning, and doesn't add the current maintenance day to any cycle
        When: _process encounters a maintenance day start value *later* than any cycle end date
        """
        sdp = SchedulerDataProcessor()
        cycles = sdp._process(self.test_cycle_data,
                              [self.test_maintenance_dict["after_cycles"]])

        (_, kwargs) = mocked_md_warning.call_args
        self.assertEqual(kwargs["md_data"], self.test_maintenance_dict["after_cycles"])
        self.assertEqual(kwargs["cycle_before"],
                         self.create_cycle_from_dict(self.test_cycle_data[2]))
        self.assertIsNone(kwargs["cycle_after"])

        self.check_process_output(cycles, len(self.test_cycle_data))

    @patch('scripts.scheduler_ingest.SchedulerDataProcessor._md_warning')
    def test_process_with_maintenance_between_cycles(self, mocked_md_warning):
        """
        Test: _process calls _md_warning, and doesn't add the current maintenance day to any cycle
        When: _process encounters a maintenance day start value *in-between* the previous cycle end
        date and current cycle start date
        """
        local_cycle_data = self.test_cycle_data.copy()
        local_cycle_data[0]["end"] = local_cycle_data[0]["start"] + relativedelta(days=1)
        sdp = SchedulerDataProcessor()
        cycles = sdp._process(self.test_cycle_data,
                              [self.test_maintenance_dict["within_first_cycle"]])

        (_, kwargs) = mocked_md_warning.call_args
        self.assertEqual(kwargs["md_data"],
                         self.test_maintenance_dict["within_first_cycle"])
        self.assertEqual(kwargs["cycle_before"],
                         self.create_cycle_from_dict(self.test_cycle_data[0]))
        self.assertEqual(kwargs["cycle_after"],
                         self.create_cycle_from_dict(self.test_cycle_data[1]))

        self.check_process_output(cycles, len(self.test_cycle_data))

    @patch('scripts.scheduler_ingest.SchedulerDataProcessor._md_warning')
    def test_process_with_maintenance_within_cycles(self, mocked_md_warning):
        """
        Test: _process adds the current maintenance day to the appropriate cycle
        When: _process encounters a maintenance day which starts and ends within
        the given cycle's start and end dates
        """
        sdp = SchedulerDataProcessor()
        cycles = sdp._process(self.test_cycle_data,
                              [self.test_maintenance_dict["within_first_cycle"]])
        mocked_md_warning.assert_not_called()
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
        """
        Test: A KeyError is thrown
        When: convert_raw_to_structured is called and a cycle attribute is missing
        """
        local_cycle_data = self.test_cycle_data.copy()
        local_cycle_data[0].pop("start")
        sdp = SchedulerDataProcessor()
        with self.assertRaises(KeyError):
            sdp.convert_raw_to_structured(local_cycle_data,
                                          self.test_maintenance_dict.values())
