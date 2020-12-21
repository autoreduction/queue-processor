# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for dealing with instrument reduction variables.
"""
import importlib.util as imp
import io
import logging.config
import os
import html
from typing import Any, Dict, List, Tuple

import chardet

# pylint:disable=no-name-in-module,import-error
from queue_processors.queue_processor.settings import REDUCTION_DIRECTORY, LOGGING
from queue_processors.queue_processor.queueproc_utils.variable_utils import VariableUtils

from model.database import access as db

# Set up logging and attach the logging to the right part of the config.
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor")  # pylint: disable=invalid-name


class DataTooLong(ValueError):
    """ Error class used for when reduction variables are too long. """


class InstrumentVariablesUtils:
    """ Class used to parse and process instrument reduction variables. """
    def __init__(self) -> None:
        self.model = db.start_database()

    @staticmethod
    def log_error_and_notify(message):
        """
        Helper method to log an error and save a notification
        """
        logger.error(message)
        model = db.start_database().data_model
        notification = model.Notification(is_active=True, is_staff_only=True, severity='e', message=message)
        db.save_record(notification)

    def create_variables_for_run(self, reduction_run):
        """
        Finds the appropriate InstrumentVariables for the given reduction run, and creates
        RunVariables from them.

        If the run is a re-run, use the previous run's variables.

        If instrument variables set for the run's experiment are found, they're used.

        Otherwise if variables set for the run's run number exist, they'll be used.

        If not, the instrument's default variables will be used.
        """
        instrument_name = reduction_run.instrument.name
        # Find if any variables exist. This happens when:
        # - This is a re-run
        # - There are variables configured for future runs
        variables = self.find_existing_variables(instrument_name, reduction_run)
        reduce_vars_file = os.path.join(self._reduction_script_location(instrument_name), 'reduce_vars.py')
        reduce_vars_module = self._import_module(reduce_vars_file)

        final_variables = self.get_variables(reduce_vars_module, 'standard_vars', variables, reduction_run, False)

        final_variables.extend(self.get_variables(reduce_vars_module, 'advanced_vars', variables, reduction_run, True))

        logger.info('Creating RunVariables')
        # Create run variables from these instrument variables, and return them.
        return VariableUtils().save_run_variables(variables, reduction_run)

    def get_variables(self, reduce_vars_module, vars_type, variables, reduction_run, is_advanced):
        # Match variables found for this experiment/run number, with the variables that are currently
        # in the reduce_vars script.
        final_variables, missing_variables = self.match_variables_with_script_vars(reduce_vars_module, vars_type,
                                                                                   variables, reduction_run.run_number)

        final_variables.extend(
            self.make_missing_variables(missing_variables, reduce_vars_module, vars_type, reduction_run.run_number,
                                        reduction_run.instrument.id, is_advanced))
        return final_variables

    def make_missing_variables(self, missing_variables: Dict, reduce_vars_module, dict_name: str, run_number: int,
                               instrument_id: int, is_advanced: bool) -> List:
        """
        Makes any variables that were found missing when matched against the database variables.

        The Variables get created in the database with values from the current reduce_vars script.

        :returns: List of created variables
        """
        # Process any variables left in the dictionary from the script
        final_reduction_variables = []
        for name, value in missing_variables.items():
            help_text = self._get_help_text(dict_name, name, reduce_vars_module)
            new_var = self._create_new_var(name, value, help_text, run_number, instrument_id, is_advanced)
            final_reduction_variables.append(new_var)

        return final_reduction_variables

    def match_variables_with_script_vars(self, reduce_vars_module, dict_name: str, variables: List,
                                         run_number: int) -> Tuple[List, Dict]:
        """
        Match variables found for this experiment/run number, with the variables that are currently in the reduce_vars script.

        Variables that match will be checked for changes, if changed will be copied and updated.

        Variables that don't match will be returned to be processed further.

        :return: List of matching variables, and a dict of ones that don't exist yet
        """
        dictionary = getattr(reduce_vars_module, dict_name, None)
        if dictionary is None:
            return [], {}

        final_reduction_variables = []
        for var in variables:
            # if the variable is still used within the reduce_vars script
            if var.name in dictionary:
                # if the variable is tracking the script, then we make sure that it's value is up to date
                # - if changed a new variable will be made, and the fields updated
                # - if NOT changed the same variable object will be used
                if var.tracks_script:
                    help_text = self._get_help_text(dict_name, var.name, reduce_vars_module)
                    var = self._create_new_var_if_changed(var, dictionary[var.name], help_text, run_number)
                final_reduction_variables.append(var)

                # remove from the dictionary, so it's not processed further as a missing variable
                del dictionary[var.name]

        return final_reduction_variables, dictionary

    def find_existing_variables(self, instrument_name, reduction_run):
        logger.info('Finding variables from experiment')
        variables = self.find_variables_for_experiment(instrument_name, reduction_run.experiment.reference_number)

        if not variables:  # if none were found from experiment ref number, then use the run number
            logger.info('Finding variables from run number')
            # No experiment-specific variables, so let's look for variables set by run number.
            variables = self.find_variables_for_run(instrument_name, reduction_run.run_number)
        return variables

    def find_variables_for_experiment(self, instrument_name, experiment_reference):
        """
        Look for currently set variables for the experiment.
        If none are set, return an empty list (or QuerySet) anyway.
        """
        instrument = db.get_instrument(instrument_name)
        model = self.model.variable_model
        ins_vars = model.InstrumentVariable.objects \
            .filter(instrument_id=instrument.id) \
            .filter(experiment_reference=experiment_reference)
        return [VariableUtils().copy_variable(ins_var) for ins_var in ins_vars]

    def find_variables_for_run(self, instrument_name, run_number=None):
        """
        Look for the applicable variables for the given run number. If none are set, return an empty
        list (or QuerySet)
        """
        instrument = db.get_instrument(instrument_name)
        var_model = self.model.variable_model
        if not run_number:
            # If we haven't been given a run number, assume the variables are from the latest run available
            return var_model.InstrumentVariable.objects.filter(instrument_id=instrument.id).last()
        else:
            return var_model.InstrumentVariable.objects.filter(instrument_id=instrument.id, start_run=run_number)

    def _create_new_var(self, name, value, help_text: str, run_number: int, instrument_id: int, is_advanced: bool):
        new_var = self.model.variable_model.InstrumentVariable(name=name,
                                                               value=str(value).replace('[', '').replace(']', ''),
                                                               type=VariableUtils().get_type_string(value),
                                                               help_text=help_text,
                                                               is_advanced=is_advanced,
                                                               start_run=run_number,
                                                               instrument_id=instrument_id,
                                                               tracks_script=1)
        return new_var.save()

    def _create_new_var_if_changed(self, variable, dict_value: Any, help_text: str, run_number: int):
        new_value = str(dict_value).replace('[', '').replace(']', '')
        new_type = VariableUtils().get_type_string(dict_value)
        new_help_text = help_text
        changed = False

        if new_value != variable.value:
            variable.value = new_value
            changed = True

        if new_type != variable.type:
            variable.type = new_type
            changed = True

        if new_help_text != variable.help_text:
            variable.help_text = new_help_text
            changed = True

        if changed:
            # forces a new object to be made
            variable.pk = None
            variable.id = None
            # updates the effect of the new variable value to start from the current run
            variable.start_run = run_number
            variable.save()
        return variable

    @staticmethod
    def _reduction_script_location(instrument_name):
        """ Get reduction script location. """
        return REDUCTION_DIRECTORY % instrument_name

    def _import_module(self, script_path):
        """
        Takes a python script as a text string, and returns it loaded as a module.
        Failure will return None, and notify.
        """
        # file name without extension
        module_name = os.path.basename(script_path).split(".")[0]
        try:
            spec = imp.spec_from_file_location(module_name, script_path)
            module = imp.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except ImportError as exp:
            self.log_error_and_notify("Unable to load reduction script %s due to missing import. (%s)" %
                                      (script_path, exp))
            return None
        except SyntaxError:
            self.log_error_and_notify("Syntax error in reduction script %s" % script_path)
            return None

    def _get_help_text(self, dict_name, key, reduce_vars_module):
        """ Get variable help text. """
        if not dict_name or not key:
            return ""
        if 'variable_help' in dir(reduce_vars_module):
            if dict_name in reduce_vars_module.variable_help:
                if key in reduce_vars_module.variable_help[dict_name]:
                    return self._replace_special_chars(reduce_vars_module.variable_help[dict_name][key])
        return ""

    @staticmethod
    def _replace_special_chars(help_text):
        """ Remove any special chars in the help text. """
        help_text = html.escape(help_text)  # Remove any HTML already in the help string
        help_text = help_text.replace('\n', '<br>').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        return help_text

     def get_current_script_text(self, instrument_name):
        """
        Fetches the reduction script and variables script for the given
        instrument, and returns each as a string.
        """
        script_text = self._load_reduction_script(instrument_name)
        script_vars_text = self._load_reduction_vars_script(instrument_name)
        return script_text, script_vars_text
