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
from django.db import transaction
from django.db.models import Q

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
        notification = model.Notification(is_active=True,
                                          is_staff_only=True,
                                          severity='e',
                                          message=message)
        db.save_record(notification)

    @transaction.atomic
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

        reduce_vars_file = os.path.join(self._reduction_script_location(instrument_name),
                                        'reduce_vars.py')
        reduce_vars_module = self._import_module(reduce_vars_file)
        model = self.model.variable_model
        experiment_reference = reduction_run.experiment.reference_number
        run_number = reduction_run.run_number
        instrument_id = reduction_run.instrument.id
        possible_variables = model.InstrumentVariable.objects.filter(
            Q(experiment_reference=experiment_reference)
            | Q(start_run__lte=run_number),
            instrument_id=instrument_id)

        variables = self._find_or_make_variables(possible_variables, run_number, instrument_id,
                                                 reduce_vars_module)

        logger.info('Creating RunVariables')
        # Create run variables from these instrument variables, and return them.
        return VariableUtils().save_run_variables(variables, reduction_run)

    def _find_or_make_variables(self, possible_variables, run_number, instrument_id,
                                reduce_vars_module) -> List:
        standard_vars = getattr(reduce_vars_module, 'standard_vars', None)
        advanced_vars = getattr(reduce_vars_module, 'advanced_vars', None)

        all_vars: List[Tuple[str, Any, bool]] = [(name, value, False)
                                                 for name, value in standard_vars.items()]
        all_vars.extend([(name, value, True) for name, value in advanced_vars.items()])

        if len(all_vars) == 0:
            return []

        variables = []
        for name, value, is_advanced in all_vars:
            script_help_text = self._get_help_text(
                'standard_vars' if not is_advanced else 'advanced_vars', name, reduce_vars_module)
            script_value = str(value).replace('[', '').replace(']', '')
            script_type = VariableUtils().get_type_string(value)

            var_kwargs = {
                'name': name,
                'value': script_value,
                'type': script_type,
                'help_text': script_help_text,
                'is_advanced': is_advanced,
                'instrument_id': instrument_id
            }

            variable = possible_variables.filter(name=name).order_by("-start_run").first()

            if variable is None:
                variable = possible_variables.create(**var_kwargs)
                # if the variable was just created then set it to track the script
                # and that it starts on the current run
                # if it was found already existing just leave it as it is
                variable.tracks_script = True
                variable.start_run = run_number
                variable.save()
            elif variable.tracks_script:
                # if the variable is tracking the reduce_vars script
                # then update it's value to the one from the script. This is True
                # for variables that were created via manual_submission or run_detection.
                # "Configuring new jobs" from the web app will set it to False so that
                # the value always overrides the script, until changed back by the user
                self._update_or_copy_if_changed(variable, script_value, script_type,
                                                script_help_text, run_number)

            variables.append(variable)
        return variables

    @staticmethod
    def _update_or_copy_if_changed(variable, new_value, new_type, new_help_text, run_number: int):
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
            # if the run number is different than what is already saved, then we will copy the
            # variable that contains the new values. Otherwise just overwrite them
            if variable.start_run != run_number:
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
            self.log_error_and_notify(
                "Unable to load reduction script %s due to missing import. (%s)" %
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
                    return self._replace_special_chars(
                        reduce_vars_module.variable_help[dict_name][key])
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

    def _load_reduction_script(self, instrument_name):
        """ Loads reduction script. """
        return self._load_script(
            os.path.join(self._reduction_script_location(instrument_name), 'reduce.py'))

    def _load_reduction_vars_script(self, instrument_name):
        """ Loads reduction variables script. """
        return self._load_script(
            os.path.join(self._reduction_script_location(instrument_name), 'reduce_vars.py'))

    def _load_script(self, path):
        """
        First detect the file encoding using chardet.
        Then load the relevant reduction script and return back the text of the script.
        If the script cannot be loaded, None is returned.
        """
        try:
            # Read raw bytes and determine encoding
            f_raw = io.open(path, 'rb')
            encoding = chardet.detect(f_raw.read(32))["encoding"]

            # Read the file in decoded; io is used for the encoding kwarg
            f_decoded = io.open(path, 'r', encoding=encoding)
            script_text = f_decoded.read()
            return script_text
        except Exception as exp:  # pylint: disable = broad-except
            self.log_error_and_notify("Unable to load reduction script %s - %s" % (path, exp))
            return None
