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

        reduce_vars_file = os.path.join(self._reduction_script_location(instrument_name), 'reduce_vars.py')
        reduce_vars_module = self._import_module(reduce_vars_file)

        variables = self.find_or_make_variables(reduction_run, reduce_vars_module, 'standard_vars', False)
        variables.extend(self.find_or_make_variables(reduction_run, reduce_vars_module, 'advanced_vars', True))

        logger.info('Creating RunVariables')
        # Create run variables from these instrument variables, and return them.
        return VariableUtils().save_run_variables(variables, reduction_run)

    @transaction.atomic
    def find_or_make_variables(self, reduction_run, reduce_vars_module, vars_type, is_advanced) -> List:
        dictionary = getattr(reduce_vars_module, vars_type, None)
        if dictionary is None:
            return []
        model = self.model.variable_model
        experiment_reference = reduction_run.experiment.reference_number
        run_number = reduction_run.run_number
        instrument_id = reduction_run.instrument.id

        possible_variables = model.InstrumentVariable.objects.filter(Q(experiment_reference=experiment_reference)
                                                                     | Q(start_run__lte=run_number),
                                                                     instrument_id=instrument_id)
        variables = []
        for name, value in dictionary.items():
            script_help_text = self._get_help_text(vars_type, name, reduce_vars_module)
            script_value = str(value).replace('[', '').replace(']', '')
            script_type = VariableUtils().get_type_string(value)

            variable, created = possible_variables.get_or_create(name=name,
                                                                 value=script_value,
                                                                 type=script_type,
                                                                 help_text=script_help_text,
                                                                 is_advanced=is_advanced,
                                                                 instrument_id=instrument_id)

            if created:
                # if the variable was just created then set it to track the script and that it starts on the current run
                # if it was found already existing just leave it as it is
                variable.tracks_script = True
                variable.start_run = run_number
                variable.save()

            variables.append(variable)
        return variables

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

    def _load_reduction_script(self, instrument_name):
        """ Loads reduction script. """
        return self._load_script(os.path.join(self._reduction_script_location(instrument_name), 'reduce.py'))

    def _load_reduction_vars_script(self, instrument_name):
        """ Loads reduction variables script. """
        return self._load_script(os.path.join(self._reduction_script_location(instrument_name), 'reduce_vars.py'))

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