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
from unittest.mock import patch

from autoreduce_db.reduction_viewer.models import Experiment, Instrument, Status
from autoreduce_db.instrument.models import InstrumentVariable, Variable
from django.test import TestCase
from parameterized import parameterized

from autoreduce_qp.model.database.records import create_reduction_run_record
from autoreduce_qp.queue_processor.instrument_variable_utils import InstrumentVariablesUtils

UTILS_PATH = "queue_processor."
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
        self.description = "This is a fake message"


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
class TestInstrumentVariableUtils(TestCase):
    fixtures = ["status_fixture"]

    def __init__(self, methodName: str) -> None:
        super().__init__(methodName=methodName)
        self.fake_script_text = "somescripttext"

    def setUp(self) -> None:
        self.experiment = Experiment.objects.get_or_create(reference_number=1231231)[0]
        self.instrument = Instrument.objects.get_or_create(name="MyInstrument", is_active=1, is_paused=0)[0]
        self.status = Status.objects.get_or_create(value="q")[0]

    @patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load", return_value=FakeModule())
    def test_new_reduction_run(self, _):
        """
        Tests with a never before seen Reduction Run
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        before_creating_variables = InstrumentVariable.objects.count()
        new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)
        after_creating_variables = InstrumentVariable.objects.count()

        self.assertGreater(after_creating_variables, before_creating_variables)

        self.assertEqual(new_variables[0].variable.name, "standard_var1")
        self.assertEqual(new_variables[0].variable.value, "standard_value1")
        self.assertEqual(new_variables[1].variable.name, "advanced_var1")
        self.assertEqual(new_variables[1].variable.value, "advanced_value1")

    @patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load", return_value=FakeModule())
    def test_new_reduction_run_with_message_reduction_args(self, _):
        """
        Tests with a never before seen Reduction Run
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        before_creating_variables = InstrumentVariable.objects.count()
        new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run,
                                                                        {"standard_vars": {
                                                                            "standard_var1": 123
                                                                        }})
        after_creating_variables = InstrumentVariable.objects.count()

        self.assertGreater(after_creating_variables, before_creating_variables)

        self.assertEqual(new_variables[0].variable.name, "standard_var1")
        self.assertEqual(new_variables[0].variable.value, "123")
        self.assertEqual(new_variables[1].variable.name, "advanced_var1")
        self.assertEqual(new_variables[1].variable.value, "advanced_value1")

    @patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load", return_value=FakeModule())
    def test_two_reduction_runs_only_creates_one_set_of_variables(self, _):
        """
        Tests that creating variables for a module that has the same variables will
        re-use the variables once they have been created
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        before_creating_variables = InstrumentVariable.objects.count()
        new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)
        after_creating_variables = InstrumentVariable.objects.count()
        new_variables_again = InstrumentVariablesUtils().create_run_variables(reduction_run)
        after_creating_variables_again = InstrumentVariable.objects.count()

        self.assertGreater(after_creating_variables, before_creating_variables)
        self.assertEqual(after_creating_variables, after_creating_variables_again)

        self.assertEqual(new_variables[0].variable, new_variables_again[0].variable)
        self.assertEqual(new_variables[1].variable, new_variables_again[1].variable)

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

        before_creating_variables = InstrumentVariable.objects.count()

        with patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load", return_value=FakeModule()):
            new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

        after_creating_variables = InstrumentVariable.objects.count()
        assert after_creating_variables > before_creating_variables

        new_variables_again = None
        # loop twice and check that no new variables are created
        for _ in range(2):
            # MODIFIES an advanced value so that they no longer match
            with patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load",
                       return_value=FakeModule(**param_variable_dict)):
                new_variables_again = InstrumentVariablesUtils().create_run_variables(reduction_run)

            after_creating_variables_again = InstrumentVariable.objects.count()

            assert after_creating_variables + 1 == after_creating_variables_again
            if "standard_vars" in param_variable_dict:
                ops = [operator.ne, operator.eq]
            else:
                ops = [operator.eq, operator.ne]
            assert ops[0](new_variables[0].variable, new_variables_again[0].variable)
            assert ops[1](new_variables[1].variable, new_variables_again[1].variable)

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

        before_creating_variables = InstrumentVariable.objects.count()

        with patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load", return_value=FakeModule()):
            new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

        after_creating_variables = InstrumentVariable.objects.count()
        assert after_creating_variables > before_creating_variables

        new_variables_again = None
        # loop twice and check that no new variables are created
        for _ in range(2):
            # MODIFIES an advanced value so that they no longer match
            with patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load",
                       return_value=FakeModule(**param_variable_dict)):
                new_variables_again = InstrumentVariablesUtils().create_run_variables(reduction_run)

            after_creating_variables_again = InstrumentVariable.objects.count()

            assert after_creating_variables + 1 == after_creating_variables_again

            # check that the previous variables are contained in the new ones
            assert new_variables[0].variable in [nv.variable for nv in new_variables_again]
            assert new_variables[1].variable in [nv.variable for nv in new_variables_again]

            # check that ONE variable (the new one) is not contained in the first variable creation
            assert len({nva.variable for nva in new_variables_again} - {nv.variable for nv in new_variables}) == 1

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

        before_creating_variables = InstrumentVariable.objects.count()

        with patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(**param_variable_dict)):
            new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

        after_creating_variables = InstrumentVariable.objects.count()
        assert after_creating_variables > before_creating_variables

        new_variables_again = None
        # loop twice and check that no new variables are created
        for _ in range(2):
            # MODIFIES an advanced value so that they no longer match
            with patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load",
                       return_value=FakeModule()):
                new_variables_again = InstrumentVariablesUtils().create_run_variables(reduction_run)

            after_creating_variables_again = InstrumentVariable.objects.count()

            assert after_creating_variables == after_creating_variables_again

            # check that the previous variables are contained in the new ones
            assert new_variables_again[0].variable in [nv.variable for nv in new_variables]
            assert new_variables_again[1].variable in [nv.variable for nv in new_variables]

            # check that ONE variable (the new one) is not contained in the first variable creation
            assert len({nva.variable for nva in new_variables} - {nv.variable for nv in new_variables_again}) == 1

    def test_imported_module_no_variables(self):
        """
        Test: that no variables get created
        When: the imported reduce_vars has no variables in it
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        before_creating_variables = InstrumentVariable.objects.count()

        with patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(standard_vars={}, advanced_vars={})):
            new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

        assert not new_variables
        after_creating_variables = InstrumentVariable.objects.count()
        assert after_creating_variables == before_creating_variables

    def test_variable_that_exists_and_tracks_script_gets_updated(self):
        """
        Test: Existing variable that tracks the script gets its value/type/help updated
        When: The variable was created for a previous reduction run, but the value was changed in reduce_vars
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        before_creating_variables = InstrumentVariable.objects.count()

        with patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(advanced_vars={})):
            InstrumentVariablesUtils().create_run_variables(reduction_run)

        after_creating_variables = InstrumentVariable.objects.count()
        assert after_creating_variables > before_creating_variables

        # change the VALUE and the TYPE of the variable
        with patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(
                       standard_vars={"standard_var1": 123},
                       advanced_vars={},
                       variable_help={"standard_vars": {
                           "standard_var1": "CHANGED HELP FOR VARIABLE"
                       }})):
            new_variables_again = InstrumentVariablesUtils().create_run_variables(reduction_run)

        var = new_variables_again[0].variable
        assert var.name == "standard_var1"
        assert var.value == 123
        assert var.type == "number"
        assert var.help_text == "CHANGED HELP FOR VARIABLE"

    def test_variable_that_exists_and_does_not_track_script_gets_ignored(self):
        """
        Test: Existing variable that tracks the script gets its value/type/help updated
        When: The variable was created for a previous reduction run, but the value was changed in reduce_vars
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        before_creating_variables = InstrumentVariable.objects.count()

        with patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(advanced_vars={})):
            new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

        new_variables[0].variable.tracks_script = False
        new_variables[0].variable.save()

        after_creating_variables = InstrumentVariable.objects.count()
        assert after_creating_variables > before_creating_variables

        # change the VALUE and the TYPE of the variable
        with patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load",
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

    def test_variable_changed_for_new_run_gets_copied(self):
        """
        Test: Existing variable that tracks the script gets copied when its
              value/type/help is updated and the run_number is different
        When: The variable was created for a previous reduction run, but the value was changed in reduce_vars
        """
        reduction_run = create_reduction_run_record(self.experiment, self.instrument, FakeMessage(), 0,
                                                    self.fake_script_text, self.status)
        reduction_run.save()

        with patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(advanced_vars={})):
            variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

        newer_reduction_run = create_reduction_run_record(self.experiment, self.instrument,
                                                          FakeMessage(run_number=7654321), 0, self.fake_script_text,
                                                          self.status)
        newer_reduction_run.save()

        with patch("autoreduce_qp.queue_processor.reduction.service.ReductionScript.load",
                   return_value=FakeModule(
                       standard_vars={"standard_var1": 123},
                       advanced_vars={},
                       variable_help={"standard_vars": {
                           "standard_var1": "CHANGED HELP FOR VARIABLE"
                       }})):
            newer_variables = InstrumentVariablesUtils().create_run_variables(newer_reduction_run)

        assert variables[0].variable != newer_variables[0].variable

    @staticmethod
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

        assert InstrumentVariablesUtils.merge_arguments(message_args, fakemod) == expected

    @staticmethod
    def test_get_help_module_dict_name_not_in_variable_help():
        """
        Test that empty string is returned
        When the variable name is not contained in the help
        """
        assert not InstrumentVariablesUtils.get_help_text(
            "apples", "123", {"variable_help": {
                "standard_args": {
                    "variable1": "help text 1"
                }
            }})

    @staticmethod
    def test_get_help():
        """
        Test that empty string is returned
        When the variable name is not contained in the help
        """
        assert InstrumentVariablesUtils.get_help_text(
            "standard_args", "variable1", {"variable_help": {
                "standard_args": {
                    "variable1": "help text 1"
                }
            }}) == "help text 1"

    def test_find_appropriate_var_chooses_experiment_vars_as_top_priority(self):
        """
        Test that find_appropriate_variable will prefer a variable with matching experiment number
        """
        start_run = 1234567
        exp_ref = 4321
        name = "test_variable1"

        var1 = InstrumentVariable.objects.create(name=name,
                                                 value="test_value1",
                                                 type="string",
                                                 is_advanced=False,
                                                 instrument=self.instrument,
                                                 start_run=start_run)
        var1.save()

        var2 = InstrumentVariable.objects.create(name=name,
                                                 value="test_value1",
                                                 type="string",
                                                 is_advanced=False,
                                                 instrument=self.instrument,
                                                 experiment_reference=exp_ref)

        var2.save()

        var3 = InstrumentVariable.objects.create(name=name,
                                                 value="test_value1",
                                                 type="string",
                                                 is_advanced=False,
                                                 instrument=self.instrument,
                                                 start_run=start_run + 10)
        var3.save()
        possible_variables = InstrumentVariable.objects.filter(instrument=self.instrument)
        assert len(possible_variables) == 3

        assert InstrumentVariablesUtils.find_appropriate_variable(possible_variables, name, exp_ref) == var2

    def test_find_appropriate_var_chooses_latest_var(self):
        """
        Test that, lacking a var with experiment number, find_appropriate_variable will prefer
        the variable with the latest start_run
        """
        start_run = 1234567
        exp_ref = 4321
        name = "test_variable1"

        var1 = InstrumentVariable.objects.create(name=name,
                                                 value="test_value1",
                                                 type="string",
                                                 is_advanced=False,
                                                 instrument=self.instrument,
                                                 start_run=start_run)
        var1.save()

        var2 = InstrumentVariable.objects.create(name=name,
                                                 value="test_value1",
                                                 type="string",
                                                 is_advanced=False,
                                                 instrument=self.instrument,
                                                 start_run=start_run + 10)
        var2.save()

        possible_variables = InstrumentVariable.objects.filter(instrument=self.instrument)
        assert len(possible_variables) == 2

        assert InstrumentVariablesUtils.find_appropriate_variable(possible_variables, name, exp_ref) == var2

    def test_find_or_make_overwrites_variable_for_experiment_reference(self):
        """
        Test that find_or_make will overwrite the variable saved for an experiment reference
        when the variable is provided a new value. (This behaviour is different than for start_run,
        as a new value for a start_run will COPY the variable instead, not overwrite)
        """
        exp_ref = 4321
        name = "test_variable1"
        red_args = {'standard_vars': {name: "test_value3"}, 'advanced_vars': {}, 'variable_help': {}}
        possible_variables = InstrumentVariable.objects.filter(instrument=self.instrument)

        variables = InstrumentVariablesUtils.find_or_make_variables(possible_variables,
                                                                    self.instrument.id,
                                                                    red_args,
                                                                    experiment_reference=exp_ref)

        assert variables[0].experiment_reference == exp_ref
        assert variables[0].name == name
        assert variables[0].value == "test_value3"
        assert variables[0].start_run is None

        red_args = {'standard_vars': {name: "test_value44"}, 'advanced_vars': {}, 'variable_help': {}}
        new_variables = InstrumentVariablesUtils.find_or_make_variables(possible_variables,
                                                                        self.instrument.id,
                                                                        red_args,
                                                                        experiment_reference=exp_ref)
        assert new_variables[0].value == "test_value44"
        assert new_variables[0].start_run is None

        assert variables[0] == new_variables[0]
        assert variables[0].name == new_variables[0].name
        assert variables[0].experiment_reference == new_variables[0].experiment_reference
        assert variables[0].value != new_variables[0].value

    def test_find_or_make_doesnt_update_without_changes(self):
        """
        Test that find_or_make will reuse the variable when the value of the experiment variable has not changed.
        """
        exp_ref = 4321
        name = "test_variable1"
        red_args = {'standard_vars': {name: "test_value3"}, 'advanced_vars': {}, 'variable_help': {}}
        possible_variables = InstrumentVariable.objects.filter(instrument=self.instrument)

        variables = InstrumentVariablesUtils.find_or_make_variables(possible_variables,
                                                                    self.instrument.id,
                                                                    red_args,
                                                                    experiment_reference=exp_ref)

        assert variables[0].experiment_reference == exp_ref
        assert variables[0].name == name
        assert variables[0].value == "test_value3"
        assert variables[0].start_run is None

        new_vars = InstrumentVariablesUtils.find_or_make_variables(possible_variables,
                                                                   self.instrument.id,
                                                                   red_args,
                                                                   experiment_reference=exp_ref)
        assert variables[0] == new_vars[0]

    @parameterized.expand([["text", "text"], ["", "text"], ["None", "text"], [None, "text"], [1, 'number'],
                           [1.0, 'number'], [True, 'boolean'], [False, 'boolean'], [[1, 2], 'list_number'],
                           [['s', 't', 'r'], 'list_text']])
    def test_variable_not_updated(self, var_value, var_type):  # pylint:disable=no-self-use
        """
        Test that the value does not get updated when it hasn't changed. Parameterized for all supported types
        """
        name = "test"
        new_var = Variable.objects.create(
            name=name,
            value=var_value,
            type=var_type,
            help_text="",
        )

        new_var = Variable.objects.get(pk=new_var.pk)
        assert not InstrumentVariablesUtils.variable_was_updated(new_var, var_value, var_type, "")


if __name__ == "__main__":
    unittest.main()
