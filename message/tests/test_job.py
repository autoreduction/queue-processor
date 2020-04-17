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

from mock import patch

from message.job import Message


class TestMessage(unittest.TestCase):
    """
    Test cases for the Message class used with AMQ
    """

    def setUp(self):
        self.msg = Message()
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

    @patch('message.job.Message.un_serialise')
    def test_init(self, mock_un_serialise):
        """
        Test all the member variables are created and we do not call
        un-serialise if no object is provided
        """
        self.assertIsNone(self.msg.description)
        self.assertIsNone(self.msg.facility)
        self.assertIsNone(self.msg.run_number)
        self.assertIsNone(self.msg.instrument)
        self.assertIsNone(self.msg.rb_number)
        self.assertIsNone(self.msg.started_by)
        self.assertIsNone(self.msg.file_path)
        self.assertIsNone(self.msg.overwrite)
        self.assertIsNone(self.msg.run_version)
        self.assertIsNone(self.msg.job_id)
        self.assertIsNone(self.msg.reduction_script)
        self.assertIsNone(self.msg.reduction_arguments)
        self.assertIsNone(self.msg.reduction_log)
        self.assertIsNone(self.msg.admin_log)
        self.assertIsNone(self.msg.return_message)
        self.assertIsNone(self.msg.retry_in)
        self.assertFalse(mock_un_serialise.called)

    # pylint:disable=no-self-use
    @patch('message.job.Message.un_serialise')
    def test_init_with_serialised_obj(self, mock_un_serialise):
        """
        Test that we call the unserialise function if a serialised object is provided on init
        """
        _ = Message(serialised_object='test', overwrite=False)
        mock_un_serialise.assert_called_once()

    def test_to_dict(self):
        """
        Test the class can be correctly converted to a dictionary
        """
        actual = self.msg.to_dict()
        for key, value in actual.items():
            self.assertIn(key, self.key_list)
            self.assertIsNone(value)

    def test_serialise(self):
        """
        Test the class can be serialised and retain the variables values
        """
        serialised = self.msg.serialise()
        actual = json.loads(serialised)
        for key, value in actual.items():
            self.assertIn(key, self.key_list)
            self.assertIsNone(value)

    def test_un_serialise_overwrite_true(self):
        """
        Test the class can be populated with a serialised object
        """
        serialised = self.populated_msg.serialise()
        actual = Message()
        actual.un_serialise(serialised)
        self.assertEqual(actual.run_number, self.populated_msg.run_number)
        self.assertEqual(actual.rb_number, self.populated_msg.rb_number)
        self.assertEqual(actual.description, self.populated_msg.description)
