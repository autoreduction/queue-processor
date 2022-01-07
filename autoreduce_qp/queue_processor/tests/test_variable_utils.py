# ############################################################################### #
# Autoreduction Repository : https://github.com/autoreduction/autoreduce
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

from autoreduce_qp.queue_processor.variable_utils import VariableUtils as vu


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

    @staticmethod
    @patch("autoreduce_qp.queue_processor.variable_utils.ReductionScript")
    def test_get_default_variables(reduction_script):
        """
        Test: Getting the default variables returns the expected keys
        """

        class ReduceVars:
            standard_vars = {
                "var1": 123,
                "var2": 432,
                "var3": 666,
            }
            advanced_vars = {
                "adv_var1": 123,
                "adv_var2": 432,
                "adv_var3": 666,
            }
            variable_help = {
                "standard_vars": {
                    "var1": "test_help",
                    "var2": "test_help",
                    "var3": "test_help",
                },
                "advanced_vars": {
                    "adv_var1": "test_help",
                    "adv_var2": "test_help",
                    "adv_var3": "test_help",
                },
            }

        reduction_script.return_value.load.return_value = ReduceVars()
        result = vu.get_default_variables("TESTINSTRUMENT")

        assert "standard_vars" in result
        assert "var1" in result["standard_vars"]
        assert "advanced_vars" in result
        assert "adv_var1" in result["advanced_vars"]
        assert "variable_help" in result
        assert "standard_vars" in result["variable_help"]
        assert "advanced_vars" in result["variable_help"]

    @parameterized.expand([
        [FileNotFoundError],
        [ImportError],
        [SyntaxError],
        [Exception],
    ])
    @patch("autoreduce_qp.queue_processor.variable_utils.ReductionScript")
    def test_get_default_variables_raises(self, exception_class, reduction_script):
        """
        Test: Getting the default variables re-raises the exception when raise_exc parameter is given
        """
        reduction_script.return_value.load.side_effect = exception_class("msg")

        with self.assertRaises(exception_class):
            vu.get_default_variables("TESTINSTRUMENT", raise_exc=True)

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
        result = vu.get_default_variables("TESTINSTRUMENT")

        assert "standard_vars" in result
        assert "advanced_vars" in result
        assert "variable_help" in result

        for _, variables in result.items():
            for var in variables:
                assert var.help_text == ""
