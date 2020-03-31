# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test utility functions for constructing run variables
"""
import unittest

from mock import Mock, patch

from queue_processors.queue_processor.queueproc_utils.tests.\
    compare_db_object import compare_db_objects
from queue_processors.queue_processor.queueproc_utils.variable_utils import VariableUtils as vu
from queue_processors.queue_processor.orm_mapping import RunJoin, Variable, InstrumentJoin


# pylint:disable=missing-class-docstring
class TestVariableUtils(unittest.TestCase):

    def setUp(self):
        self.valid_variable = Variable(name='test',
                                       value='value',
                                       type='text',
                                       is_advanced=False,
                                       help_text='help text')
        self.valid_inst_var = InstrumentJoin(name='test',
                                             value='value',
                                             is_advanced=False,
                                             type='text',
                                             help_text='help test',
                                             instrument=4,
                                             experiment_reference=54321,
                                             start_run=12345,
                                             tracks_script=1)
        self.reduction_run = Mock()
        self.reduction_run.run_number = 12345

    def test_derive_run_variable(self):
        """
        Ensure that we are able to create a RunJoin variable from a variable
        and reduction run number
        """
        reduction_run_no = '12345'
        expected = RunJoin(name=self.valid_variable.name,
                           value=self.valid_variable.value,
                           is_advanced=self.valid_variable.is_advanced,
                           type=self.valid_variable.type,
                           help_text=self.valid_variable.help_text,
                           reduction_run=reduction_run_no)
        actual = vu.derive_run_variable(self.valid_variable, reduction_run_no)
        self.assertTrue(compare_db_objects(actual, expected))

    @patch('queue_processors.queue_processor.base.session.add')
    @patch('queue_processors.queue_processor.base.session.commit')
    @patch('queue_processors.queue_processor.queueproc_utils.variable_utils.'
           'VariableUtils.derive_run_variable')
    def test_save_run_variable(self, mock_derive_run_var, mock_session_commit, mock_session_add):
        """
        Ensure that the control method `save_run_variable` constructs run variables and
        Attempts to add these to the database
        :param mock_derive_run_var: Mock out the derive run as tested above
        :param mock_session_commit: Mock out session.commit to ensure we do not commit to database
        :param mock_session_add: Mock out session.add to ensure we do not add to the database
        :return:
        """
        var_utils = vu()
        var_utils.save_run_variables([self.valid_variable], self.reduction_run)
        mock_derive_run_var.assert_called_once()
        mock_session_add.assert_called_once()
        mock_session_commit.assert_called_once()

    def test_copy_variable(self):
        """
        Test that an InstrumentJoin database object can be copied
        """
        expected = InstrumentJoin(name=self.valid_inst_var.name,
                                  value=self.valid_inst_var.value,
                                  is_advanced=self.valid_inst_var.is_advanced,
                                  type=self.valid_inst_var.type,
                                  help_text=self.valid_inst_var.help_text,
                                  instrument=self.valid_inst_var.instrument,
                                  experiment_reference=self.valid_inst_var.experiment_reference,
                                  start_run=self.valid_inst_var.start_run,
                                  tracks_script=self.valid_inst_var.tracks_script)
        actual = vu.copy_variable(vu.copy_variable(self.valid_inst_var))
        self.assertTrue(compare_db_objects(actual, expected))

    def test_get_type_string(self):
        """
        Test that python types are successfully recognised and converted to database input
        """
        self.assertEqual(vu.get_type_string('a string'), 'text')
        self.assertEqual(vu.get_type_string(1), 'number')
        self.assertEqual(vu.get_type_string(1.0), 'number')
        self.assertEqual(vu.get_type_string(True), 'boolean')
        self.assertEqual(vu.get_type_string([1, 2, 3]), 'list_number')
        self.assertEqual(vu.get_type_string(['s', 't', 'r']), 'list_text')

    def test_get_type_string_unknown_type(self):
        """
        Test that a value of unknown type is output as database type text
        """
        self.assertEqual(vu.get_type_string({'key': 'value'}), 'text')

    def test_convert_variable_to_type(self):
        """
        Test database variables types are successfully recognised and converted into python
        single variable types
        """
        self.assertIsInstance(vu.convert_variable_to_type('text', 'text'), str)
        self.assertIsInstance(vu.convert_variable_to_type('1', 'number'), int)
        self.assertIsInstance(vu.convert_variable_to_type('1.0', 'number'), float)
        self.assertIsInstance(vu.convert_variable_to_type('True', 'boolean'), bool)
        self.assertIsInstance(vu.convert_variable_to_type('False', 'boolean'), bool)

    def test_convert_variable_to_type_list_types(self):
        """
        Test database variables types are successfully recognised and converted into python
        for list types
        """
        str_list = vu.convert_variable_to_type('[\'s\',\'t\'', 'list_text')
        self.assertIsInstance(str_list, list)
        self.assertIsInstance(str_list[0], str)
        int_list = vu.convert_variable_to_type('1,2', 'list_number')
        self.assertIsInstance(int_list, list)
        self.assertIsInstance(int_list[0], int)
        float_list = vu.convert_variable_to_type('1.0,2.0', 'list_number')
        self.assertIsInstance(float_list, list)
        self.assertIsInstance(float_list[0], float)

    def test_convert_variable_unknown_type(self):
        """
        Test output variable type are unchanged if the target type is unrecognised
        """
        self.assertIsInstance(vu.convert_variable_to_type('value', 'unknown'), str)
        self.assertIsInstance(vu.convert_variable_to_type(1, 'unknown'), int)

    def test_convert_variable_mismatch_type(self):
        """
        Test number type conversion with non number
        """
        self.assertIsNone(vu.convert_variable_to_type('string', 'number'))
