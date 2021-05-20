# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Unit tests for manual submission utility functions
"""

from unittest import TestCase

from autoreduce_qp.scripts.manual_operations.util import get_run_range


class TestUtil(TestCase):
    """
    Test util.py
    """
    def test_get_run_numbers_one_run_returns_correct_range(self):
        """
        Test: Correct range is returned
        When: second_run is None
        """
        self.assertEqual(range(1, 2), get_run_range(1))

    def test_get_run_numbers_valid_input_returns_valid_range(self):
        """
        Test: Correct range is returned
        When: second_run is provided
        """
        self.assertEqual(range(1, 5), get_run_range(first_run=1, last_run=4))

    def test_get_run_numbers_invalid_input_raises_value_error(self):
        """
        Test: ValueError is raised
        When: first_run is greater than last_run
        """
        with self.assertRaises(ValueError):
            get_run_range(first_run=5, last_run=2)
