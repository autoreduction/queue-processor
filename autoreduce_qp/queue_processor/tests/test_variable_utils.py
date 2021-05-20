# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test utility functions for constructing run variables
"""

import datetime
from unittest.mock import patch
from parameterized import parameterized

from django.test import TestCase

from autoreduce_db.instrument.models import InstrumentVariable, Variable, ReductionRun

from autoreduce_qp.queue_processor.variable_utils import VariableUtils as vu


# pylint:disable=no-member
class TestVariableUtils(TestCase):
    fixtures = ["status_fixture"]

    def setUp(self):
        self.valid_variable = Variable(name='test',
                                       value='value',
                                       type='text',
                                       is_advanced=False,
                                       help_text='help text')
        self.valid_inst_var = InstrumentVariable(name='test',
                                                 value='value',
                                                 is_advanced=False,
                                                 type='text',
                                                 help_text='help test',
                                                 instrument_id=4,
                                                 experiment_reference=54321,
                                                 start_run=12345,
                                                 tracks_script=1)
        self.reduction_run = ReductionRun(run_number=1111,
                                          run_version=0,
                                          run_description='run name',
                                          hidden_in_failviewer=0,
                                          admin_log='admin log',
                                          reduction_log='reduction log',
                                          created=datetime.datetime.utcnow(),
                                          last_updated=datetime.datetime.utcnow(),
                                          experiment_id=222,
                                          instrument_id=3,
                                          status_id=4,
                                          script='script',
                                          started_by=1)

    def test_get_type_string(self):
        """
        Test: Python types are successfully recognised and converted to database input
        When: Calling get_type_string
        """
        self.assertEqual(vu.get_type_string('a string'), 'text')
        self.assertEqual(vu.get_type_string(1), 'number')
        self.assertEqual(vu.get_type_string(1.0), 'number')
        self.assertEqual(vu.get_type_string(True), 'boolean')
        self.assertEqual(vu.get_type_string([1, 2, 3]), 'list_number')
        self.assertEqual(vu.get_type_string(['s', 't', 'r']), 'list_text')

    def test_get_type_string_unknown_type(self):
        """
        Test: A value of unknown type is output as database type text
        When: Calling get_type_string
        """
        self.assertEqual(vu.get_type_string({'key': 'value'}), 'text')

    @parameterized.expand([["text", "text", str], ["", "text", str], ["None", "text", str], [None, "text", str],
                           ['1', 'number', int], ['1.0', 'number', float], ['True', 'boolean', bool],
                           ['False', 'boolean', bool], [1, 'number', int], [1.0, 'number', float],
                           [True, 'boolean', bool], [False, 'boolean', bool], [[1, 2, 3], 'list_number', list],
                           [['s', 't', 'r'], 'list_text', list]])
    def test_convert_variable_to_type(self, value, value_type, exp_type):
        """
        Test: database variables types are successfully recognised and converted into python
        single variable types
        When: calling convert_variable_to_type with valid arguments
        """
        self.assertIsInstance(vu.convert_variable_to_type(value, value_type), exp_type)

    @parameterized.expand([
        ["'s','t'", 'list_text', str],
        ['1,2', 'list_number', int],
        ['1.0,2.0', 'list_number', float],
        ["[1, 2]", 'list_number', int],
        ["[1.0,2.0]", 'list_number', float],
    ])
    def test_convert_variable_to_type_list_types(self, value, value_type, exp_type):
        """
        Test database variables types are successfully recognised and converted into python
        for list types
        """
        result_list = vu.convert_variable_to_type(value, value_type)
        self.assertIsInstance(result_list, list)
        self.assertIsInstance(result_list[0], exp_type)

    def test_convert_variable_unknown_type(self):
        """
        Test output variable type are unchanged if the target type is unrecognised
        """
        self.assertIsInstance(vu.convert_variable_to_type('value', 'unknown'), str)
        self.assertIsInstance(vu.convert_variable_to_type(1, 'unknown'), int)

    def test_convert_variable_mismatch_type(self):
        """
        Test: number type conversion with non number
        """
        self.assertIsNone(vu.convert_variable_to_type('string', 'number'))

    @staticmethod
    def test_make_dict_with_unsaved_variables():
        """
        Test: the unsaved variables are correctly made
        """
        some_vars = {"var1": 123, "var2": 432, "var3": 666}
        help_dict = {"var1": "help1", "var2": "help2", "var3": "help3"}
        result = vu.make_dict_with_unsaved_variables(some_vars, help_dict)

        assert len(result) == 3
        assert all(isinstance(var, Variable) for var in result.values())

        for name, value in some_vars.items():
            assert name == result[name].name
            assert value == result[name].value

        # make sure they're not in the DB
        assert Variable.objects.filter(name="var1").count() == 0
        assert Variable.objects.filter(name="var2").count() == 0
        assert Variable.objects.filter(name="var3").count() == 0

    @staticmethod
    @patch("autoreduce_qp.queue_processor.variable_utils.ReductionScript")
    def test_get_default_variables(reduction_script):
        """
        Test: Getting the default variables returns the expected keys
        """
        reduction_script.load.return_value = {
            "standard_vars": {
                "var1": 123,
                "var2": 432,
                "var3": 666
            },
            "advanced_vars": {
                "adv_var1": 123,
                "adv_var2": 432,
                "adv_var3": 666
            },
            "variable_help": {
                "var1": "test_help",
                "var2": "test_help",
                "var3": "test_help",
                "adv_var1": "test_help",
                "adv_var2": "test_help",
                "adv_var3": "test_help",
            }
        }
        result = vu.get_default_variables("TestInstrument")

        assert "standard_vars" in result
        assert "advanced_vars" in result
        assert "variable_help" in result

        # make sure they're not in the DB
        for name in ["var1", "var2", "var3", "adv_var1", "adv_var2", "adv_var3"]:
            assert Variable.objects.filter(name=name).count() == 0

        for _, variables in result.items():
            for var in variables:
                assert var.help_text == "test_help"

    @staticmethod
    @patch("autoreduce_qp.queue_processor.variable_utils.ReductionScript")
    def test_get_default_variables_empty_help(reduction_script):
        """
        Test: Getting the default variables returns the expected keys
        """
        reduction_script.load.return_value = {
            "standard_vars": {
                "var1": 123,
                "var2": 432,
                "var3": 666
            },
            "advanced_vars": {
                "adv_var1": 123,
                "adv_var2": 432,
                "adv_var3": 666
            },
            "variable_help": {}
        }
        result = vu.get_default_variables("TestInstrument")

        assert "standard_vars" in result
        assert "advanced_vars" in result
        assert "variable_help" in result

        # make sure they're not in the DB
        for name in ["var1", "var2", "var3", "adv_var1", "adv_var2", "adv_var3"]:
            assert Variable.objects.filter(name=name).count() == 0

        for _, variables in result.items():
            for var in variables:
                assert var.help_text == ""
