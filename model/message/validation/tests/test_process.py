# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Exercise the helper functions that process the validation results
"""
import unittest

from unittest.mock import patch
from model.message.validation import process


class TestProcess(unittest.TestCase):
    def setUp(self):
        self.true_validity_dict = {
            'check_1': True,
            'check_2': True,
        }
        self.mixed_validity_dict = {
            'check_1': True,
            'check_2': False,
        }
        self.false_validity_dict = {
            'check_1': False,
            'check_2': False,
        }

    def test_validity_dict_valid(self):
        """
        Test: The return values
        When: Different dicts are supplied to check_validity_dict (all true, mixed, all false)
        """
        self.assertTrue(process.check_validity_dict(self.true_validity_dict))
        self.assertFalse(process.check_validity_dict(self.mixed_validity_dict))
        self.assertFalse(process.check_validity_dict(self.false_validity_dict))

    @patch('model.message.validation.process.dict_to_string')
    @patch('logging.error')
    def test_validity_dict_log_when_false(self, mock_err_log, mock_dict_to_str):
        """
        Test: A logging error is called with output of dict_to_string
        When: check_validity_dict returns false
        """
        msg = 'Test string'
        mock_dict_to_str.return_value = msg
        self.assertFalse(process.check_validity_dict(self.false_validity_dict))
        mock_err_log.assert_called_once_with(msg)

    def test_dict_to_string(self):
        """
        Test: An expected string is returned
        When: dict_to_string is called with a valid dict
        """
        expected = "check_1 - True, check_2 - True"
        self.assertEqual(process.dict_to_string(self.true_validity_dict), expected)
