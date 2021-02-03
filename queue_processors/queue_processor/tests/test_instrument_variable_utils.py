# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the messaging utils
"""
import operator
import unittest
from collections.abc import Iterable
from typing import Any, List, Union
from parameterized import parameterized
from unittest.mock import patch

import model.database.access
from model.database.records import create_reduction_run_record
from queue_processors.queue_processor.instrument_variable_utils import \
    InstrumentVariablesUtils

UTILS_PATH = "queue_processors.queue_processor."
MESSAGE_CLASS_PATH = UTILS_PATH + ".messaging_utils.MessagingUtils"


def delete_objects(objects: List[Union[list, Any]]):
    """
    Deletes the list of objects
    """
    for val in objects:
        if isinstance(val, Iterable):
            for obj in val:
                obj.delete()
        else:
            val.delete()


class FakeMessage:
    def __init__(self, run_number=None) -> None:
        super().__init__()
        self.started_by = 0
        self.run_number = run_number if run_number else 1234567


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


class TestInstrumentVariableUtils(unittest.TestCase):
    def __init__(self, methodName: str) -> None:
        super().__init__(methodName=methodName)
        db_handle = model.database.access.start_database()
        self.data_model = db_handle.data_model
        self.variable_model = db_handle.variable_model
        self.fake_script_text = "somescripttext"

        self.delete_on_teardown = []

    def setUp(self) -> None:
        self.experiment = self.data_model.Experiment.objects.get_or_create(reference_number=1231231)[0]
        self.instrument = self.data_model.Instrument.objects.get_or_create(name="MyInstrument",
                                                                           is_active=1,
                                                                           is_paused=0)[0]
        self.status = self.data_model.Status.objects.get(value="q")

    def tearDown(self) -> None:
        self.experiment.delete()
        self.instrument.delete()
        delete_objects(self.delete_on_teardown)
        self.delete_on_teardown = []

    @patch("queue_processors.queue_processor.reduction.service.ReductionScript.load", return_value=FakeModule())
    def test_new_reduction_run(self, _):
        """
        Tests with a never before seen Reduction Run
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        before_creating_variables = self.variable_model.InstrumentVariable.objects.count()
        new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)
        after_creating_variables = self.variable_model.InstrumentVariable.objects.count()

        self.assertGreater(after_creating_variables, before_creating_variables)

        self.assertEqual(new_variables[0].variable.name, "standard_var1")
        self.assertEqual(new_variables[0].variable.value, "standard_value1")
        self.assertEqual(new_variables[1].variable.name, "advanced_var1")
        self.assertEqual(new_variables[1].variable.value, "advanced_value1")

        self.delete_on_teardown = [reduction_run, new_variables]

    @patch("queue_processors.queue_processor.reduction.service.ReductionScript.load", return_value=FakeModule())
    def test_two_reduction_runs_only_creates_one_set_of_variables(self, _):
        """
        Tests that creating variables for a module that has the same variables will
        re-use the variables once they have been created
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        before_creating_variables = self.variable_model.InstrumentVariable.objects.count()
        new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)
        after_creating_variables = self.variable_model.InstrumentVariable.objects.count()
        new_variables_again = InstrumentVariablesUtils().create_run_variables(reduction_run)
        after_creating_variables_again = self.variable_model.InstrumentVariable.objects.count()

        self.assertGreater(after_creating_variables, before_creating_variables)
        self.assertEqual(after_creating_variables, after_creating_variables_again)

        self.assertEqual(new_variables[0].variable, new_variables_again[0].variable)
        self.assertEqual(new_variables[1].variable, new_variables_again[1].variable)

        self.delete_on_teardown = [reduction_run, new_variables]

    @parameterized.expand([[{
        'standard_vars': {
            'new_standard_var': 'new_standard_value'
        }
    }], [{
        'advanced_vars': {
            'new_advanced_var': 'new_advanced_value'
        }
    }]])
    def test_imported_module_variable_dict_changed(self, param_variable_dict):
        """
        Test that only the current variables in reduce_vars are created
        When: the reduce_vars module gets changed
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        before_creating_variables = self.variable_model.InstrumentVariable.objects.count()

        with patch("queue_processors.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule()):
            new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

        after_creating_variables = self.variable_model.InstrumentVariable.objects.count()
        assert after_creating_variables > before_creating_variables

        new_variables_again = None
        # loop twice and check that no new variables are created
        for _ in range(2):
            # MODIFIES an advanced value so that they no longer match
            with patch("queue_processors.queue_processor.reduction.service.ReductionScript.load",
                       return_value=FakeModule(**param_variable_dict)):
                new_variables_again = InstrumentVariablesUtils().create_run_variables(reduction_run)

            after_creating_variables_again = self.variable_model.InstrumentVariable.objects.count()

            assert after_creating_variables + 1 == after_creating_variables_again
            if "standard_vars" in param_variable_dict:
                ops = [operator.ne, operator.eq]
            else:
                ops = [operator.eq, operator.ne]
            assert ops[0](new_variables[0].variable, new_variables_again[0].variable)
            assert ops[1](new_variables[1].variable, new_variables_again[1].variable)

        self.delete_on_teardown = [reduction_run, new_variables, new_variables_again]

    @parameterized.expand([[{
        'standard_vars': {
            "standard_var1": "standard_value1",
            'new_standard_var': 'new_standard_value'
        }
    }], [{
        'advanced_vars': {
            "advanced_var1": "advanced_value1",
            'new_advanced_var': 'new_advanced_value'
        }
    }]])
    def test_imported_module_one_dict_gets_a_new_variable(self, param_variable_dict):
        """
        Test that new variables get created correctly.
        When: the variable module has a new variable added
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        before_creating_variables = self.variable_model.InstrumentVariable.objects.count()

        with patch("queue_processors.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule()):
            new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

        after_creating_variables = self.variable_model.InstrumentVariable.objects.count()
        assert after_creating_variables > before_creating_variables

        new_variables_again = None
        # loop twice and check that no new variables are created
        for _ in range(2):
            # MODIFIES an advanced value so that they no longer match
            with patch("queue_processors.queue_processor.reduction.service.ReductionScript.load",
                       return_value=FakeModule(**param_variable_dict)):
                new_variables_again = InstrumentVariablesUtils().create_run_variables(reduction_run)

            after_creating_variables_again = self.variable_model.InstrumentVariable.objects.count()

            assert after_creating_variables + 1 == after_creating_variables_again

            # check that the previous variables are contained in the new ones
            assert new_variables[0].variable in [nv.variable for nv in new_variables_again]
            assert new_variables[1].variable in [nv.variable for nv in new_variables_again]

            # check that ONE variable (the new one) is not contained in the first variable creation
            assert len({nva.variable for nva in new_variables_again} - {nv.variable for nv in new_variables}) == 1

        self.delete_on_teardown = [reduction_run, new_variables, new_variables_again]

    @parameterized.expand([[{
        'standard_vars': {
            "standard_var1": "standard_value1",
            'new_standard_var': 'new_standard_value'
        }
    }], [{
        'advanced_vars': {
            "advanced_var1": "advanced_value1",
            'new_advanced_var': 'new_advanced_value'
        }
    }]])
    def test_imported_module_one_dict_loses_a_new_variable(self, param_variable_dict):
        """
        Test: removed variables are not used accidentally
        when the variable module has less variables a variable (e.g. one has been removed)

        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        before_creating_variables = self.variable_model.InstrumentVariable.objects.count()

        with patch("queue_processors.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(**param_variable_dict)):
            new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

        after_creating_variables = self.variable_model.InstrumentVariable.objects.count()
        assert after_creating_variables > before_creating_variables

        new_variables_again = None
        # loop twice and check that no new variables are created
        for _ in range(2):
            # MODIFIES an advanced value so that they no longer match
            with patch("queue_processors.queue_processor.reduction.service.ReductionScript.load",
                       return_value=FakeModule()):
                new_variables_again = InstrumentVariablesUtils().create_run_variables(reduction_run)

            after_creating_variables_again = self.variable_model.InstrumentVariable.objects.count()

            assert after_creating_variables == after_creating_variables_again

            # check that the previous variables are contained in the new ones
            assert new_variables_again[0].variable in [nv.variable for nv in new_variables]
            assert new_variables_again[1].variable in [nv.variable for nv in new_variables]

            # check that ONE variable (the new one) is not contained in the first variable creation
            assert len({nva.variable for nva in new_variables} - {nv.variable for nv in new_variables_again}) == 1

        self.delete_on_teardown = [reduction_run, new_variables, new_variables_again]

    def test_imported_module_no_variables(self):
        """
        Test: that no variables get created
        When: the imported reduce_vars has no variables in it
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        before_creating_variables = self.variable_model.InstrumentVariable.objects.count()

        with patch("queue_processors.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(standard_vars={}, advanced_vars={})):
            new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

        assert not new_variables
        after_creating_variables = self.variable_model.InstrumentVariable.objects.count()
        assert after_creating_variables == before_creating_variables

    def test_variable_that_exists_and_tracks_script_gets_updated(self):
        """
        Test: Existing variable that tracks the script gets its value/type/help updated
        When: The variable was created for a previous reduction run, but the value was changed in reduce_vars
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        before_creating_variables = self.variable_model.InstrumentVariable.objects.count()

        with patch("queue_processors.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(advanced_vars={})):
            new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

        after_creating_variables = self.variable_model.InstrumentVariable.objects.count()
        assert after_creating_variables > before_creating_variables

        # change the VALUE and the TYPE of the variable
        with patch("queue_processors.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(
                       standard_vars={"standard_var1": 123},
                       advanced_vars={},
                       variable_help={"standard_vars": {
                           "standard_var1": "CHANGED HELP FOR VARIABLE"
                       }})):
            new_variables_again = InstrumentVariablesUtils().create_run_variables(reduction_run)

        var = new_variables_again[0].variable
        assert var.name == "standard_var1"
        assert var.value == "123"
        assert var.type == "number"
        assert var.help_text == "CHANGED HELP FOR VARIABLE"

        self.delete_on_teardown = [reduction_run, new_variables, new_variables_again]

    def test_variable_that_exists_and_does_not_track_script_gets_ignored(self):
        """
        Test: Existing variable that tracks the script gets its value/type/help updated
        When: The variable was created for a previous reduction run, but the value was changed in reduce_vars
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        before_creating_variables = self.variable_model.InstrumentVariable.objects.count()

        with patch("queue_processors.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(advanced_vars={})):
            new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

        new_variables[0].variable.tracks_script = False
        new_variables[0].variable.save()

        after_creating_variables = self.variable_model.InstrumentVariable.objects.count()
        assert after_creating_variables > before_creating_variables

        # change the VALUE and the TYPE of the variable
        with patch("queue_processors.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(
                       standard_vars={"standard_var1": 123},
                       advanced_vars={},
                       variable_help={"standard_vars": {
                           "standard_var1": "CHANGED HELP FOR VARIABLE"
                       }})):
            new_variables_again = InstrumentVariablesUtils().create_run_variables(reduction_run)

        var = new_variables_again[0].variable
        assert var.name == "standard_var1"
        assert var.value == "standard_value1"
        assert var.type == "text"
        assert var.help_text == "This is help for standard_value1"
        self.delete_on_teardown = [reduction_run, new_variables, new_variables_again]

    def test_variable_changed_for_new_run_gets_copied(self):
        """
        Test: Existing variable that tracks the script gets copied when its
              value/type/help is updated and the run_number is different
        When: The variable was created for a previous reduction run, but the value was changed in reduce_vars
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        with patch("queue_processors.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(advanced_vars={})):
            variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

        newer_reduction_run = create_reduction_run_record(self.experiment, self.instrument,
                                                          FakeMessage(run_number=7654321), 0, self.fake_script_text,
                                                          self.status)
        newer_reduction_run.save()

        with patch("queue_processors.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(
                       standard_vars={"standard_var1": 123},
                       advanced_vars={},
                       variable_help={"standard_vars": {
                           "standard_var1": "CHANGED HELP FOR VARIABLE"
                       }})):
            newer_variables = InstrumentVariablesUtils().create_run_variables(newer_reduction_run)

        assert variables[0].variable != newer_variables[0].variable
        self.delete_on_teardown = [reduction_run, variables, newer_reduction_run, newer_variables]


def test_get_help_module_dict_name_not_in_variable_help():
    """
    Test that empty string is returned
    When the variable name is not contained in the help
    """
    assert not InstrumentVariablesUtils.get_help_text("apples", "123", FakeModule())


def test_get_help_module_no_variable_help():
    """
    Test that empty string is returned
    When there is no variable_help in reduce_vars
    """
    assert not InstrumentVariablesUtils.get_help_text("apples", "123", {})


if __name__ == '__main__':
    unittest.main()
