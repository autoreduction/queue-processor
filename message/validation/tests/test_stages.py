# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Exercise the functions that handle validating a message at each pipeline stage
"""
import unittest

from message.validation import stages
from message.job import Message


class TestStages(unittest.TestCase):
    """
    Assert the stages return the correct bool value based on if they are valid
    """

    def setUp(self):
        self.valid_message = Message(run_number=1234,
                                     instrument='GEM',
                                     rb_number=0,
                                     started_by=-1,
                                     data='test/file/path',
                                     )
        self.invalid_message = Message(run_number='12345',
                                       instrument='not inst',
                                       rb_number='0',
                                       started_by='test',
                                       data=123)

    def test_valid_validate_data_ready(self):
        """
        Test: validate_data_ready returns true
        When: supplied with a valid message
        """
        self.assertTrue(stages.validate_data_ready(self.valid_message))

    def test_invalid_validate_data_ready(self):
        """
        Test: validate_data_ready returns false
        When: supplied with an invalid message
        """
        self.assertFalse(stages.validate_data_ready(self.invalid_message))
