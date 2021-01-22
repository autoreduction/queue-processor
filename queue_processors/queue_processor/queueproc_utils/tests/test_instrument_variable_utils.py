# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the messaging utils
"""
from mock import patch
from queue_processors.queue_processor.queueproc_utils.instrument_variable_utils import InstrumentVariablesUtils
import unittest

from model.database.records import create_reduction_run_record

import model.database.access

UTILS_PATH = "queue_processors.queue_processor.queueproc_utils"
MESSAGE_CLASS_PATH = UTILS_PATH + ".messaging_utils.MessagingUtils"


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


class TestInstrumentVariableUtils(unittest.TestCase):
    def __init__(self, methodName: str) -> None:
        super().__init__(methodName=methodName)
        db_handle = model.database.access.start_database()
        self.data_model = db_handle.data_model
        self.variable_model = db_handle.variable_model

    @patch(
        "queue_processors.queue_processor.queueproc_utils.instrument_variable_utils.import_module",
        return_value=FakeModule())
    def test_new_reduction_run(self, import_module):
        experiment = self.data_model.Experiment.objects.create(reference_number=1231231)
        instrument = self.data_model.Instrument.objects.create(name="MyInstrument",
                                                               is_active=1,
                                                               is_paused=0)
        status = self.data_model.Status.objects.get(value="q")
        fake_script_text = "scripttext"
        reduction_run = create_reduction_run_record(experiment, instrument, FakeMessage(), 0,
                                                    fake_script_text, status)
        reduction_run.save()

        before_creating_variables = self.variable_model.InstrumentVariable.objects.count()
        new_variables = InstrumentVariablesUtils().create_variables_for_run(reduction_run)
        after_creating_variables = self.variable_model.InstrumentVariable.objects.count()

        self.assertGreater(after_creating_variables, before_creating_variables)

        self.assertEqual(new_variables[0].variable.name, "standard_var1")
        self.assertEqual(new_variables[0].variable.value, "standard_value1")
        self.assertEqual(new_variables[1].variable.name, "advanced_var1")
        self.assertEqual(new_variables[1].variable.value, "advanced_value1")

        for var in new_variables:
            var.delete()

        reduction_run.delete()

    @patch(
        "queue_processors.queue_processor.queueproc_utils.instrument_variable_utils.import_module",
        return_value=FakeModule())
    def test_two_reduction_runs_only_creates_one_set_of_variables(self, import_module):
        """
        Tests that creating variables for a module that has the same variables will
        re-use the variables once they have been created
        """
        experiment = self.data_model.Experiment.objects.create(reference_number=1231231)
        instrument = self.data_model.Instrument.objects.create(name="MyInstrument",
                                                               is_active=1,
                                                               is_paused=0)
        status = self.data_model.Status.objects.get(value="q")
        fake_script_text = "scripttext"
        reduction_run = create_reduction_run_record(experiment, instrument, FakeMessage(), 0,
                                                    fake_script_text, status)
        reduction_run.save()

        before_creating_variables = self.variable_model.InstrumentVariable.objects.count()
        new_variables = InstrumentVariablesUtils().create_variables_for_run(reduction_run)
        after_creating_variables = self.variable_model.InstrumentVariable.objects.count()
        new_variables_again = InstrumentVariablesUtils().create_variables_for_run(reduction_run)
        after_creating_variables_again = self.variable_model.InstrumentVariable.objects.count()

        self.assertGreater(after_creating_variables, before_creating_variables)
        self.assertEqual(after_creating_variables, after_creating_variables_again)

        self.assertEqual(new_variables[0].variable, new_variables_again[0].variable)
        self.assertEqual(new_variables[1].variable, new_variables_again[1].variable)

        for var in new_variables:
            var.delete()

        reduction_run.delete()

    def test_imported_module_changed_one_variable_gets_a_new_variable(self):
        """
        Test that when the module gets only partially changed (e.g. 1 out of 2 variables)
        only the changed one gets a new Variable, but the other gets reused
        """
        pass
        # TODO copy test from above and change the Advanced variable in fake module