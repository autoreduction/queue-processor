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

from autoreduce_db.reduction_viewer.models import ReductionArguments, ReductionRun, ReductionScript

from autoreduce_qp.queue_processor.variable_utils import VariableUtils as vu, merge_arguments


class FakeModule:
    def __init__(self, standard_vars=None, advanced_vars=None, variable_help=None) -> None:
        """
        Allows overwriting the advanced vars
        """
        self.standard_vars = {"standard_var1": "standard_value1"}
        self.advanced_vars = {"advanced_var1": "advanced_value1"}

        self.variable_help = {
            "standard_vars": {
                "standard_var1": "This is help for standard_value1"
            },
            "advanced_vars": {
                "advanced_var1": "This is help for advanced_value1"
            }
        }
        if standard_vars is not None:
            self.standard_vars = standard_vars
        if advanced_vars is not None:
            self.advanced_vars = advanced_vars
        if variable_help is not None:
            self.variable_help.update(variable_help)


# pylint:disable=no-member
class TestVariableUtils(TestCase):
    fixtures = ["status_fixture"]

    def setUp(self):
        script = ReductionScript(text="def main(input_file, output_dir): print(123)")
        arguments = ReductionArguments(raw="{}")
        self.reduction_run = ReductionRun(run_version=0,
                                          run_description='run name',
                                          hidden_in_failviewer=0,
                                          admin_log='admin log',
                                          reduction_log='reduction log',
                                          created=datetime.datetime.utcnow(),
                                          last_updated=datetime.datetime.utcnow(),
                                          experiment_id=222,
                                          instrument_id=3,
                                          status_id=4,
                                          started_by=1,
                                          script=script,
                                          arguments=arguments)

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

        for _, variables in result.items():
            for var in variables:
                assert var.help_text == ""


def test_merge_arguments():
    """
    Tests that the arguments are merged correctly when both standard and advanced are being replaced
    """
    message_args = {
        "standard_vars": {
            "standard_var1": 123,
            "none_var": None,
            "int_var": 123,
            "float_var": 123.0,
            "bool_var": False,
            "num_list_var": [1, 2, 3],
            "str_list_var": ["1", "2", "3"]
        },
        "advanced_vars": {
            "advanced_var1": "321"
        }
    }
    fakemod = FakeModule(
        standard_vars={
            "standard_var1": "standard_value1",
            "none_var": None,
            "int_var": 123,
            "float_var": 123.0,
            "bool_var": False,
            "num_list_var": [1, 2, 3],
            "str_list_var": ["1", "2", "3"],
        })

    expected = {
        "standard_vars": {
            "standard_var1": '123',
            "none_var": "None",
            "int_var": 123,
            "float_var": 123.0,
            "bool_var": False,
            "num_list_var": [1, 2, 3],
            "str_list_var": ["1", "2", "3"]
        },
        "advanced_vars": {
            "advanced_var1": "321"
        },
        "variable_help": fakemod.variable_help
    }

    assert merge_arguments(message_args, fakemod) == expected
