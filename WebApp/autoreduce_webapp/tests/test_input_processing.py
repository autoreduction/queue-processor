# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for the input parser
"""
import string
import unittest

from utilities import input_processing


# pylint:disable=missing-docstring
class RunParsingTestCase(unittest.TestCase):
    def test_empty_input(self):
        input_value = ""
        with self.assertRaises(SyntaxError):
            input_processing.parse_user_run_numbers(input_value)

    def test_single_value_case(self):
        input_value = "101"
        expected_value = [int(input_value)]

        result = input_processing.parse_user_run_numbers(input_value)
        self.assertEqual(expected_value, result)

    def test_list_case(self):
        input_value = "10-20"
        # Returns inclusive values
        expected_value = list(range(10, 21))

        result = input_processing.parse_user_run_numbers(input_value)
        self.assertEqual(expected_value, result)

    def test_alpha_char_rejected(self):
        # Check the single case first
        with self.assertRaises(SyntaxError):
            input_processing.parse_user_run_numbers('a')

        # Check all individual characters
        for char in string.ascii_letters:
            with self.assertRaises(SyntaxError):
                input_processing.parse_user_run_numbers(char)

    def test_commas(self):
        input_string = "10,15,20"
        expected_vals = [10, 15, 20]

        result = input_processing.parse_user_run_numbers(input_string)
        self.assertEqual(expected_vals, result)

    def test_mixed_list(self):
        input_string = "10,20-22,30"
        expected_vals = [10, 20, 21, 22, 30]

        result = input_processing.parse_user_run_numbers(input_string)
        self.assertEqual(expected_vals, result)

    def test_negative_numbers(self):
        input_string = "-10"
        expected_val = [-10]

        result = input_processing.parse_user_run_numbers(input_string)
        self.assertEqual(expected_val, result)

    def test_negative_ranges(self):
        input_string = "-5-2"
        expected_val = list(range(-5, 2 + 1))

        result = input_processing.parse_user_run_numbers(input_string)
        self.assertEqual(expected_val, result)

    def test_excessive_range(self):
        input_string = "-5-2-3"
        with self.assertRaises(SyntaxError):
            input_processing.parse_user_run_numbers(input_string)
