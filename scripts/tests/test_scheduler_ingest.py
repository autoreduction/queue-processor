# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests the functionality within scheduler_ingest.py
"""
# TODO: Question - should I do separate classes for each class(3) within scheduler_ingest.py?
from datetime import datetime

import unittest

from scripts.scheduler_ingest import Cycle, MaintenanceDay


class TestCycle(unittest.TestCase):

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

# class TestSchedulerDataProcessor:
