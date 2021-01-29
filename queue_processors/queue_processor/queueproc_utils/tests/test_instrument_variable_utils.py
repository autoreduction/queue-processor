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
import pytest
from mock import patch

import model.database.access
from model.database.records import create_reduction_run_record
from queue_processors.queue_processor.queueproc_utils.instrument_variable_utils import \
    InstrumentVariablesUtils

UTILS_PATH = "queue_processors.queue_processor.queueproc_utils"
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
    started_by = 0
    run_number = 1234567


class FakeModule:
    standard_vars = {"standard_var1": "standard_value1"}
    advanced_vars = {"advanced_var1": "advanced_value1"}

    variable_help = {
        "standard_vars": {
            "standard_var1": "This is help for standard_value1"
        },
        "advanced_vars": {
            "advanced_var1": "This is help for advanced_value1"
        }
    }

    def __init__(self, standard_vars=None, advanced_vars=None) -> None:
        """
        Allows overwriting the advanced vars
        """
        super().__init__()
        if standard_vars is not None:
            self.standard_vars = standard_vars
        if advanced_vars is not None:
            self.advanced_vars = advanced_vars


class TestInstrumentVariableUtils(unittest.TestCase):
    def __init__(self, methodName: str) -> None:
        super().__init__(methodName=methodName)
        db_handle = model.database.access.start_database()
        self.data_model = db_handle.data_model
        self.variable_model = db_handle.variable_model

        self.delete_on_teardown = []

    def tearDown(self) -> None:
        delete_objects(self.delete_on_teardown)
        self.delete_on_teardown = []

    @patch("queue_processors.queue_processor.queueproc_utils.instrument_variable_utils.import_module",
           return_value=FakeModule())
    def test_new_reduction_run(self, _):
        """
        Tests with a never before seen Reduction Run
        """
        experiment = self.data_model.Experiment.objects.create(reference_number=1231231)
        instrument = self.data_model.Instrument.objects.create(name="MyInstrument", is_active=1, is_paused=0)
        status = self.data_model.Status.objects.get(value="q")
        fake_script_text = "scripttext"
        reduction_run = create_reduction_run_record(experiment, instrument, FakeMessage(), 0, fake_script_text, status)
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

    @patch("queue_processors.queue_processor.queueproc_utils.instrument_variable_utils.import_module",
           return_value=FakeModule())
    def test_two_reduction_runs_only_creates_one_set_of_variables(self, _):
        """
        Tests that creating variables for a module that has the same variables will
        re-use the variables once they have been created
        """
        experiment = self.data_model.Experiment.objects.create(reference_number=1231231)
        instrument = self.data_model.Instrument.objects.create(name="MyInstrument", is_active=1, is_paused=0)
        status = self.data_model.Status.objects.get(value="q")
        fake_script_text = "scripttext"
        reduction_run = create_reduction_run_record(experiment, instrument, FakeMessage(), 0, fake_script_text, status)
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


# Annoying mix of unittest and pytest... but the parametrise is worth it to avoid doubling the tests


def with_db(func):
    """
    Sets up the DB access and passes it into the func. Workaround having no setUp
    """
    def inner(type_of_variable):
        db_handle = model.database.access.start_database()
        data_model = db_handle.data_model
        variable_model = db_handle.variable_model

        return func(data_model, variable_model, type_of_variable)

    return inner


def delete_returned(inner_from_with_db):
    """
    :param inner_from_with_db: This function is actually the inner function in the with_db decorator
                               because that got executed first.
    """

    # this inner needs the argument so that it matches the pytest parametrize param
    def inner(type_of_variable):
        retval = inner_from_with_db(type_of_variable)
        delete_objects(retval)

    return inner


@pytest.mark.parametrize('type_of_variable', [{
    'standard_vars': {
        'new_standard_var': 'new_standard_value'
    }
}, {
    'advanced_vars': {
        'new_advanced_var': 'new_advanced_value'
    }
}])
@delete_returned
@with_db
def test_imported_module_variable_dict_changed(data_model, variable_model, type_of_variable):
    """
    Test that when the variable module dict gets changed a new variable is created.
    """
    experiment = data_model.Experiment.objects.create(reference_number=1231231)
    instrument = data_model.Instrument.objects.create(name="MyInstrument", is_active=1, is_paused=0)
    status = data_model.Status.objects.get(value="q")
    fake_script_text = "scripttext"
    reduction_run = create_reduction_run_record(experiment, instrument, FakeMessage(), 0, fake_script_text, status)
    reduction_run.save()

    before_creating_variables = variable_model.InstrumentVariable.objects.count()

    with patch("queue_processors.queue_processor.queueproc_utils.instrument_variable_utils.import_module",
               return_value=FakeModule()):
        new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

    after_creating_variables = variable_model.InstrumentVariable.objects.count()
    assert after_creating_variables > before_creating_variables

    new_variables_again = None
    # loop twice and check that no new variables are created
    for _ in range(2):
        # MODIFIES an advanced value so that they no longer match
        with patch("queue_processors.queue_processor.queueproc_utils.instrument_variable_utils.import_module",
                   return_value=FakeModule(**type_of_variable)):
            new_variables_again = InstrumentVariablesUtils().create_run_variables(reduction_run)

        after_creating_variables_again = variable_model.InstrumentVariable.objects.count()

        assert after_creating_variables + 1 == after_creating_variables_again
        if "standard_vars" in type_of_variable:
            ops = [operator.ne, operator.eq]
        else:
            ops = [operator.eq, operator.ne]
        assert ops[0](new_variables[0].variable, new_variables_again[0].variable)
        assert ops[1](new_variables[1].variable, new_variables_again[1].variable)

    return reduction_run, new_variables, new_variables_again


@pytest.mark.parametrize('type_of_variable', [{
    'standard_vars': {
        "standard_var1": "standard_value1",
        'new_standard_var': 'new_standard_value'
    }
}, {
    'advanced_vars': {
        "advanced_var1": "advanced_value1",
        'new_advanced_var': 'new_advanced_value'
    }
}])
@delete_returned
@with_db
def test_imported_module_one_dict_gets_a_new_variable(data_model, variable_model, type_of_variable):
    """
    Test that when the variable module has a new variable added it gets created correctly.
    """
    experiment = data_model.Experiment.objects.create(reference_number=1231231)
    instrument = data_model.Instrument.objects.create(name="MyInstrument", is_active=1, is_paused=0)
    status = data_model.Status.objects.get(value="q")
    fake_script_text = "scripttext"
    reduction_run = create_reduction_run_record(experiment, instrument, FakeMessage(), 0, fake_script_text, status)
    reduction_run.save()

    before_creating_variables = variable_model.InstrumentVariable.objects.count()

    with patch("queue_processors.queue_processor.queueproc_utils.instrument_variable_utils.import_module",
               return_value=FakeModule()):
        new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

    after_creating_variables = variable_model.InstrumentVariable.objects.count()
    assert after_creating_variables > before_creating_variables

    new_variables_again = None
    # loop twice and check that no new variables are created
    for _ in range(2):
        # MODIFIES an advanced value so that they no longer match
        with patch("queue_processors.queue_processor.queueproc_utils.instrument_variable_utils.import_module",
                   return_value=FakeModule(**type_of_variable)):
            new_variables_again = InstrumentVariablesUtils().create_run_variables(reduction_run)

        after_creating_variables_again = variable_model.InstrumentVariable.objects.count()

        assert after_creating_variables + 1 == after_creating_variables_again

        # check that the previous variables are contained in the new ones
        assert new_variables[0].variable in [nv.variable for nv in new_variables_again]
        assert new_variables[1].variable in [nv.variable for nv in new_variables_again]

        # check that ONE variable (the new one) is not contained in the first variable creation
        assert len({nva.variable for nva in new_variables_again} - {nv.variable for nv in new_variables}) == 1

    return reduction_run, new_variables, new_variables_again


@pytest.mark.parametrize('type_of_variable', [{
    'standard_vars': {
        "standard_var1": "standard_value1",
        'new_standard_var': 'new_standard_value'
    }
}, {
    'advanced_vars': {
        "advanced_var1": "advanced_value1",
        'new_advanced_var': 'new_advanced_value'
    }
}])
@delete_returned
@with_db
def test_imported_module_one_dict_loses_a_new_variable(data_model, variable_model, type_of_variable):
    """
    Test that when the variable module has lost a variable it is not used.

    """
    experiment = data_model.Experiment.objects.create(reference_number=1231231)
    instrument = data_model.Instrument.objects.create(name="MyInstrument", is_active=1, is_paused=0)
    status = data_model.Status.objects.get(value="q")
    fake_script_text = "scripttext"
    reduction_run = create_reduction_run_record(experiment, instrument, FakeMessage(), 0, fake_script_text, status)
    reduction_run.save()

    before_creating_variables = variable_model.InstrumentVariable.objects.count()

    with patch("queue_processors.queue_processor.queueproc_utils.instrument_variable_utils.import_module",
               return_value=FakeModule(**type_of_variable)):
        new_variables = InstrumentVariablesUtils().create_run_variables(reduction_run)

    after_creating_variables = variable_model.InstrumentVariable.objects.count()
    assert after_creating_variables > before_creating_variables

    new_variables_again = None
    # loop twice and check that no new variables are created
    for _ in range(2):
        # MODIFIES an advanced value so that they no longer match
        with patch("queue_processors.queue_processor.queueproc_utils.instrument_variable_utils.import_module",
                   return_value=FakeModule()):
            new_variables_again = InstrumentVariablesUtils().create_run_variables(reduction_run)

        after_creating_variables_again = variable_model.InstrumentVariable.objects.count()

        assert after_creating_variables == after_creating_variables_again

        # check that the previous variables are contained in the new ones
        assert new_variables_again[0].variable in [nv.variable for nv in new_variables]
        assert new_variables_again[1].variable in [nv.variable for nv in new_variables]

        # check that ONE variable (the new one) is not contained in the first variable creation
        assert len({nva.variable for nva in new_variables} - {nv.variable for nv in new_variables_again}) == 1

    return reduction_run, new_variables, new_variables_again
