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

from model.message.message import Message


class TestMessage(unittest.TestCase):
    """
    Test cases for the Message class used with AMQ
    """
    @staticmethod
    def _empty():
        """ Create and return an empty message object and corresponding dictionary"""
        empty_msg = Message()
        empty_dict = {
            'description': None,
            'facility': "ISIS",
            'run_number': None,
            'instrument': None,
            'rb_number': None,
            'started_by': None,
            'file_path': None,
            'overwrite': None,
            'run_version': None,
            'job_id': None,
            'reduction_script': None,
            'reduction_arguments': {},
            'reduction_log': "",
            'admin_log': "",
            'return_message': None,
            'retry_in': None,
            'software': None
        }
        return empty_msg, empty_dict

    @staticmethod
    def _populated():
        """ Create and return a populated message object and corresponding dictionary """
        run_number = 11111
        rb_number = 2222222
        description = 'test message'
        populated_msg = Message(run_number=run_number, rb_number=rb_number, description=description)
        populated_dict = {
            'description': description,
            'facility': "ISIS",
            'run_number': run_number,
            'instrument': None,
            'rb_number': rb_number,
            'started_by': None,
            'data': None,
            'overwrite': None,
            'run_version': None,
            'job_id': None,
            'reduction_script': None,
            'reduction_arguments': {},
            'reduction_log': "",
            'admin_log': "",
            'message': None,
            'retry_in': None,
            'reduction_data': None,
            'software': None,
        }
        return populated_msg, populated_dict

    def test_init(self):
        """
        Test: All the expected member variables are created
        When: The class is initialised
        """
        empty_msg, _ = self._empty()
        self.assertIsNone(empty_msg.description)
        self.assertEqual(empty_msg.facility, "ISIS")
        self.assertIsNone(empty_msg.run_number)
        self.assertIsNone(empty_msg.instrument)
        self.assertIsNone(empty_msg.rb_number)
        self.assertIsNone(empty_msg.started_by)
        self.assertIsNone(empty_msg.data)
        self.assertIsNone(empty_msg.overwrite)
        self.assertIsNone(empty_msg.run_version)
        self.assertIsNone(empty_msg.job_id)
        self.assertIsNone(empty_msg.reduction_script)
        self.assertEqual(empty_msg.reduction_arguments, {})
        self.assertEqual(empty_msg.reduction_log, "")
        self.assertEqual(empty_msg.admin_log, "")
        self.assertIsNone(empty_msg.message)
        self.assertIsNone(empty_msg.retry_in)
        self.assertIsNone(empty_msg.reduction_data)
        self.assertIsNone(empty_msg.software)

    def test_to_dict_populated(self):
        """
        Test: A dictionary with populated values in produced
        When: attr.asdict() is called on a Message with populated values
        """
        populated_msg, populated_dict = self._populated()
        actual = attr.asdict(populated_msg)
        self.assertEqual(actual, populated_dict)

    def test_serialize_populated(self):
        """
        Test: An expected JSON object is produced
        When: The Message class is serialised
        """
        populated_msg, populated_dict = self._populated()
        serialized = populated_msg.serialize()
        actual = json.loads(serialized)
        self.assertEqual(actual, populated_dict)

    def test_deserialize_populated(self):
        """
        Test: A Dictionary with all the expected value is produced
        When: A populated serialized object is deserialized
        """
        populated_msg, populated_dict = self._populated()
        serialized = populated_msg.serialize()
        actual = populated_msg.deserialize(serialized)
        self.assertEqual(actual, populated_dict)

    def test_populate_from_dict_overwrite_true(self):
        """
        Test: Values are added and overwritten in the member variables
        When: Message.populate() is called with a non-empty dictionary and overwrite is True
        """
        _, populated_dict = self._populated()
        actual, _ = self._empty()
        actual.populate(source=populated_dict, overwrite=True)
        self.assertEqual(attr.asdict(actual), populated_dict)

    def test_populate_from_dict_overwrite_false(self):
        """
        Test: Values are added but NOT overwritten in the member variables
        When: Message.populate() is called with a non-empty dictionary and overwrite is False
        """
        populated_msg, populated_dict = self._populated()
        populated_dict['job_id'] = 123
        populated_dict['rb_number'] = 33333
        actual, _ = self._populated()
        actual.populate(source=populated_dict, overwrite=False)
        self.assertEqual(actual.rb_number, populated_msg.rb_number)
        self.assertEqual(actual.job_id, 123)

    def test_populate_from_serialized_overwrite_true(self):
        """
        Test: Values are added and overwritten in the member variables
        When: Message.populate() called with a non-empty serialized object and overwrite is True
        """
        populated_msg, populated_dict = self._populated()
        serialized = populated_msg.serialize()
        actual, _ = self._empty()
        actual.populate(source=serialized, overwrite=True)
        self.assertEqual(attr.asdict(actual), populated_dict)

    def test_populate_from_serialized_overwrite_false(self):
        """
        Test: Values are added but NOT overwritten in the member variables
        When: Message.populate() called with a non-empty serialized object and overwrite is False
        """
        new_msg, _ = self._populated()
        new_msg.job_id = 123
        new_msg.rb_number = 33333
        serialized = new_msg.serialize()
        actual, _ = self._populated()
        original, _ = self._populated()
        actual.populate(source=serialized, overwrite=False)
        self.assertEqual(actual.rb_number, original.rb_number)
        self.assertEqual(actual.job_id, 123)

    def test_invalid_serialized(self):
        """
        Test: A ValueError is raised
        When: An invalid serialized object is supplied to Message.populate()
        """
        serialized = 'test'
        empty_msg, _ = self._empty()
        self.assertRaises(ValueError, empty_msg.populate, serialized)

    def test_populate_with_invalid_key(self):
        """
        Test: A warning is logged
        When: An unknown key is used to populate the Message
        """
        args = {'unknown': True}
        msg = Message()
        with self.assertRaises(ValueError):
            msg.populate(args)

    def test_validate_data_ready_valid(self):
        """
        Test: No exception is raised
        When: Calling validate for data_ready with a valid message
        """
        message = Message(instrument='GEM',
                          run_number=111,
                          rb_number=2222222,
                          data='file/path',
                          facility="ISIS",
                          started_by=0)
        try:
            self.assertIsNone(message.validate('/queue/DataReady'))
        except RuntimeError:
            self.fail()

    def test_validate_data_ready_invalid(self):
        """
        Test: An exception is raised
        When: An invalid Message is validated
        """
        message = Message(instrument='Not an inst')
        self.assertRaises(RuntimeError, message.validate, '/queue/DataReady')
