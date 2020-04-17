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
import copy

from message.job import Message


class TestMessage(unittest.TestCase):
    """
    Test cases for the Message class used with AMQ
    """

    def setUp(self):
        self.empty_msg = Message()
        self.empty_dict = {'description': None,
                           'facility': None,
                           'run_number': None,
                           'instrument': None,
                           'rb_number': None,
                           'started_by': None,
                           'file_path': None,
                           'overwrite': None,
                           'run_version': None,
                           'job_id': None,
                           'reduction_script': None,
                           'reduction_arguments': None,
                           'reduction_log': None,
                           'admin_log': None,
                           'return_message': None,
                           'retry_in': None}
        self.populated_msg = Message(run_number=11111, rb_number=22222, description='test message')
        self.populated_dict = copy.deepcopy(self.empty_dict)
        self.populated_dict['run_number'] = self.populated_msg.run_number
        self.populated_dict['rb_number'] = self.populated_msg.rb_number
        self.populated_dict['description'] = self.populated_msg.description
        self.populated_keys = ['run_number', 'rb_number', 'description']

    def test_init(self):
        """ Test all the member variables are created """
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

    def test_to_dict_populated(self):
        """ Converted to a dictionary when attribute values set """
        actual = attr.asdict(self.populated_msg)
        self.assertEqual(actual, self.populated_dict)

    def test_serialize_populated(self):
        """ Serialized and retain the attributes values """
        serialized = self.populated_msg.serialize()
        actual = json.loads(serialized)
        self.assertEqual(actual, self.populated_dict)

    def test_deserialize_populated(self):
        """ Produce a deserialized object correctly for a populated serialized object """
        serialized = self.populated_msg.serialize()
        actual = self.populated_msg.deserialize(serialized)
        self.assertEqual(actual, self.populated_dict)

    def test_populate_from_dict_overwrite_true(self):
        """ Overwritten from a dictionary values"""
        actual = self.empty_msg
        actual.populate(self.populated_dict, overwrite=True)
        self.assertEqual(attr.asdict(actual), self.populated_dict)

    def test_populate_from_dict_overwrite_false(self):
        """ Do not overwrite from dictionary """
        self.populated_dict['job_id'] = 123
        self.populated_dict['rb_number'] = 33333
        actual = copy.deepcopy(self.populated_msg)
        actual.populate(self.populated_dict, overwrite=False)
        self.assertEqual(actual.rb_number, self.populated_msg.rb_number)
        self.assertEqual(actual.job_id, 123)

    def test_populate_from_serialized_overwrite_true(self):
        """ Overwrite with a serialized object """
        serialized = self.populated_msg.serialize()
        actual = self.empty_msg
        actual.populate(source=serialized, overwrite=True)
        self.assertEqual(attr.asdict(actual), self.populated_dict)

    def test_populate_from_serialized_overwrite_false(self):
        """ Do not overwrite from a serialized object """
        new_msg = copy.deepcopy(self.populated_msg)
        new_msg.job_id = 123
        new_msg.rb_number = 33333
        serialized = new_msg.serialize()
        actual = copy.deepcopy(self.populated_msg)
        actual.populate(source=serialized, overwrite=False)
        self.assertEqual(actual.rb_number, self.populated_msg.rb_number)
        self.assertEqual(actual.job_id, 123)

    def test_invalid_serialized(self):
        """ Test raise exception for invalid serialized object """
        serialized = 'test'
        self.assertRaises(ValueError, self.empty_msg.populate, serialized)
