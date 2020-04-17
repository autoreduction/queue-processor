# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test the Message class
"""
import unittest
import json
import attr

from message.job import Message


class TestMessage(unittest.TestCase):
    """
    Test cases for the Message class used with AMQ
    """

    def setUp(self):
        self.empty_msg = Message()
        # Ensure the list below is up to date if member variables are added/removed/renamed
        self.key_list = ['description', 'facility', 'run_number', 'instrument',
                         'rb_number', 'started_by', 'file_path', 'overwrite',
                         'run_version', 'job_id', 'reduction_script',
                         'reduction_arguments', 'reduction_log', 'admin_log',
                         'return_message', 'retry_in']
        self.populated_msg = Message()
        self.populated_msg.run_number = 11111
        self.populated_msg.rb_number = 22222
        self.populated_msg.description = 'test message'

    def test_init(self):
        """
        Test all the member variables are created and we do not call
        un-serialise if no object is provided
        """
        self.assertIsNone(self.empty_msg.description)
        self.assertIsNone(self.empty_msg.facility)
        self.assertIsNone(self.empty_msg.run_number)
        self.assertIsNone(self.empty_msg.instrument)
        self.assertIsNone(self.empty_msg.rb_number)
        self.assertIsNone(self.empty_msg.started_by)
        self.assertIsNone(self.empty_msg.file_path)
        self.assertIsNone(self.empty_msg.overwrite)
        self.assertIsNone(self.empty_msg.run_version)
        self.assertIsNone(self.empty_msg.job_id)
        self.assertIsNone(self.empty_msg.reduction_script)
        self.assertIsNone(self.empty_msg.reduction_arguments)
        self.assertIsNone(self.empty_msg.reduction_log)
        self.assertIsNone(self.empty_msg.admin_log)
        self.assertIsNone(self.empty_msg.return_message)
        self.assertIsNone(self.empty_msg.retry_in)

    def test_to_dict(self):
        """
        Test the class can be correctly converted to a dictionary
        """
        actual = attr.asdict(self.empty_msg)
        for key, value in actual.items():
            self.assertIn(key, self.key_list)
            self.assertIsNone(value)

    def test_serialise(self):
        """
        Test the class can be serialised and retain the variables values
        """
        serialised = self.empty_msg.serialise()
        actual = json.loads(serialised)
        for key, value in actual.items():
            self.assertIn(key, self.key_list)
            self.assertIsNone(value)

    def test_un_serialise_overwrite_true(self):
        """
        Test the class can be populated with a serialised object
        """
        serialised = self.populated_msg.serialise()
        actual = self.empty_msg
        actual.un_serialise(serialised)
        self.assertEqual(actual.run_number, self.populated_msg.run_number)
        self.assertEqual(actual.rb_number, self.populated_msg.rb_number)
        self.assertEqual(actual.description, self.populated_msg.description)
