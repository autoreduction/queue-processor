"""
Unit tests for the service helpers
"""
import unittest
import datetime

from monitors.service_helpers import compare_time


# pylint:disable=missing-docstring
class TestServiceHelpers(unittest.TestCase):

    def test_time_check_true(self):
        # 01/01/2018 00:00:00
        previous = datetime.datetime(2018, 1, 1, 0, 0, 0)
        # 01/01/2018 00:10:00
        current = datetime.datetime(2018, 1, 1, 0, 0, 10)
        self.assertTrue(compare_time(current, previous, 10))

    def test_time_check_false(self):
        # 01/01/2018 00:00:00
        previous = datetime.datetime(2018, 1, 1, 0, 0, 0)
        # 01/01/2018 00:00:05
        current = datetime.datetime(2018, 1, 1, 0, 0, 5)
        self.assertFalse(compare_time(current, previous, 10))

    def test_time_check_in_the_past(self):
        """ Check that this function still works if current is less than previous """
        # 01/01/2018 00:10:00
        previous = datetime.datetime(2018, 1, 1, 0, 0, 10)
        # 01/01/2018 00:00:00
        current = datetime.datetime(2018, 1, 1, 0, 0, 0)
        self.assertFalse(compare_time(current, previous, 10))
