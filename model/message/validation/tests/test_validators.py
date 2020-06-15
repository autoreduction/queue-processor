# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Exercise the validation functions
"""
import unittest

from model.message.validation import validators


class TestValidators(unittest.TestCase):
    """
    As the validators are simple bool returns,
    we are validating a function completely per test case
    """

    def test_validate_run_number(self):
        """
        Test: validate_run_number returns the expected result
        When: In valid and invalid cases
        """
        self.assertTrue(validators.validate_run_number(1))
        self.assertTrue(validators.validate_run_number('001'))

        self.assertFalse(validators.validate_run_number(0))
        self.assertFalse(validators.validate_run_number(-1))
        self.assertFalse(validators.validate_run_number('string'))

    def test_validate_instrument(self):
        """
        Test: validate_instrument returns the expected result
        When: In valid and invalid cases
        """
        self.assertTrue(validators.validate_instrument('GEM'))

        self.assertFalse(validators.validate_instrument('NOT INST'))
        self.assertFalse(validators.validate_instrument(1))
