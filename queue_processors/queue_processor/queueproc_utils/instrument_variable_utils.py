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
        RunVariables from them. If the run is a re-run, use the previous run's variables.
        If instrument variables set for the run's experiment are found, they're used.
        Otherwise if variables set for the run's run number exist, they'll be used.
        If not, the instrument's default variables will be used.
        """
        """
        PATHS

        Input: Run Number

        Distinction is made with `tracks_script`
        QP should only handle:
            - Already exists (reruns should be modified by webapp)
                - Reruns
                - Scheduled ahead
            - New

        For this Run Number:

        - If new run number = no variables -> create and set value from script
            -> Return new instrument variables that `tracks_script`

        - Existing variables
            - Rerun (this should be handled by the webapp)
            - Scheduled ahead
            - They look the same, we query for Variable where Run number = parameter

            -> Depending on tracks_script
                -> IF existing variables == what's in the script -> return the same instrument variables
                -> IF existing variables != what's in the script -> make new instrument variables, and return those


        AT END -> Reference the InstVars received via RunVariable(variable=instvar, run=...)

        """

        # Check for existing variables. This is the case when:
        # - This is a rerun
        #   - There's 2 entrypoints for a rerun:
        #       -> Via manual_submission
        #       -> Via rerun from the web-app
        # - The variables are scheduled ahead via "Configure new jobs"
        #   - In this case the variable's new values should have been set from the web app

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

        # Find variable records associated with instrument variables
        # variables = self.find_var_records_for_inst_vars(instrument.id, variable_run_number)

        # If we have found some variables then we want to use them by first making copies of them
        # and sending them back to be used. This means we don't alter the previous set of variables.
        # If we haven't found any variables, just return an empty list.
        # if variables:
        #     new_variables = []
        #     for variable in variables:
        #         new_variables.append(VariableUtils().copy_variable(variable))
        #         self._update_variables(inst_vars)
        #     return new_variables
        # return []

    def _update_variables_with_default_values(self, variables, reduce_vars_module):
        """
        Updates ONLY variables that are tracking the script, to have the current value from the script.
        """
        for variable in variables:
            if variable.tracks_script:
                logger.info("Updating variable id: %i name: %s", variable.id, variable.name)
                if not variable.is_advanced:
                    self._update_single_variable(variable, reduce_vars_module, 'standard_vars')
                else:
                    self._update_single_variable(variable, reduce_vars_module, 'advanced_vars')

    def _update_single_variable(self, variable, reduce_vars_module, dictionary):
        value_in_script = getattr(reduce_vars_module, dictionary)[variable.name]
        variable.pk = None  # this creates a new variable on save
        variable.value = str(value_in_script).replace('[', '').replace(']', '')
        variable.type = VariableUtils().get_type_string(value_in_script)
        variable.help_text = self._get_help_text(dictionary, variable.name, reduce_vars_module)
        return variable.save()

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

    def make_new_variables_with_defaults(self, instrument_name, reduce_vars_module, run_number):
        """
        Creates new variables using the default values from the reduce_vars.py file
        """
        instrument = db.get_instrument(instrument_name)
        variables = []
        # pylint:disable=no-member
        if 'standard_vars' in dir(reduce_vars_module):
            variables.extend(
                self._create_variables(instrument,
                                       reduce_vars_module,
                                       reduce_vars_module.standard_vars,
                                       is_advanced=False,
                                       start_run=run_number))

        if 'advanced_vars' in dir(reduce_vars_module):
            variables.extend(
                self._create_variables(instrument,
                                       reduce_vars_module,
                                       reduce_vars_module.advanced_vars,
                                       is_advanced=True,
                                       start_run=run_number))
        return variables

    # def find_var_records_for_inst_vars(self,instrument_id, start_run):
    #     """
    #     Returns a list of the variables that are associated with a given instrument instance
    #     e.g. return all the Variable objects that are associated with a given set of
    #          InstrumentVariables with a start run of 123
    #     :param instrument_id: (int) The id of the instrument to use
    #     :param start_run: (int) The start run of the instrument variable
    #     :return: (list) of all Variable objects matching the criteria
    #     """
    #     model = self.model.variable_model
    #     instrument_var_records = model.InstrumentVariable.objects \
    #         .filter(instrument_id=instrument_id) \
    #         .filter(start_run=start_run)
    #     return [record.variable_ptr for record in instrument_var_records]

    def _update_variables(self, variables, save=True):
        """
        Updates all variables with tracks_script to their value in the script, and append any new
        ones. This assumes that the variables all belong to the same instrument, and that the list
        supplied is complete. If no variables have tracks_script set, we won't do anything at all.
        variables should be a list; it needs to be mutable so that this function can add/remove
        variables. If the 'save' option is true, it will save/delete the variables from the
        database as required.
        """
        if not any([hasattr(var, "tracks_script") and var.tracks_script for var in variables]):
            return

        # New variable set from the script
        defaults = self.make_new_variables_with_defaults(variables[0].instrument.name) if variables else []

        def update_variable(old_var):
            """ Update the existing variables. """
            old_var.keep = True
            # Find the new variable from the script.
            matching_vars = [variable for variable in defaults if old_var.name == variable.name]

            # Check whether we should and can update the old one.
            if matching_vars and old_var.tracks_script:
                new_var = matching_vars[0]
                map(lambda name: setattr(old_var, name, getattr(new_var, name)),
                    ["value", "type", "is_advanced", "help_text"
                     ])  # Copy the new one's important attributes onto the old variable.
                if save:
                    db.save_record(old_var)
            elif not matching_vars:
                # Or remove the variable if it doesn't exist any more.
                if save:
                    db.save_record(old_var)
                old_var.keep = False
            return old_var

        variables = list(map(update_variable, variables))
        variables[:] = [var for var in variables if var.keep]

        # Add any new ones
        current_names = [var.name for var in variables]
        new_vars = [var for var in defaults if var.name not in current_names]

        def copy_metadata(new_var):
            """ Copy the source variable's metadata to the new one. """
            source_var = variables[0]
            model = self.model.variable_model
            if isinstance(source_var, model.InstrumentVariable):
                map(lambda name: setattr(new_var, name, getattr(source_var, name)),
                    ["instrument", "experiment_reference", "start_run"])
            elif isinstance(source_var, model.RunVariable):
                # Create a run variable.
                VariableUtils().derive_run_variable(new_var, source_var.reduction_run)
            else:
                return
            db.save_record(new_var)

        map(copy_metadata, new_vars)
        variables += list(new_vars)

    @staticmethod
    def _reduction_script_location(instrument_name):
        """ Get reduction script location. """
        return REDUCTION_DIRECTORY % instrument_name

    def _load_reduction_script(self, instrument_name):
        """ Loads reduction script. """
        return self._load_script(os.path.join(self._reduction_script_location(instrument_name), 'reduce.py'))

    def _load_reduction_vars_script(self, instrument_name):
        """ Loads reduction variables script. """
        return self._load_script(os.path.join(self._reduction_script_location(instrument_name), 'reduce_vars.py'))

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

    def _create_variables(self, instrument, reduce_vars_module, variable_dict, is_advanced: bool, start_run: int):
        """ Create variables in the database. """
        variables = []
        for key, value in list(variable_dict.items()):
            str_value = str(value).replace('[', '').replace(']', '')
            if len(str_value) > 300:
                raise DataTooLong
            model = self.model.variable_model
            help_text = self._get_help_text('standard_vars', key, reduce_vars_module)
            var_type = VariableUtils().get_type_string(value)
            # Please note: As instrument_variable inherits from Variable, the below creates BOTH an
            # an InstrumentVariable and Variable record in the database when saved. As such,
            # both sets of fields are required for initialisation.
            instrument_variable = model.InstrumentVariable(name=key,
                                                           value=str_value,
                                                           type=var_type,
                                                           is_advanced=is_advanced,
                                                           help_text=help_text,
                                                           start_run=start_run,
                                                           instrument_id=instrument.id,
                                                           tracks_script=1)

            instrument_variable.save()
            variables.append(instrument_variable)
        return variables

    def get_current_script_text(self, instrument_name):
        """
        Fetches the reduction script and variables script for the given
        instrument, and returns each as a string.
        """
        script_text = self._load_reduction_script(instrument_name)
        script_vars_text = self._load_reduction_vars_script(instrument_name)
        return script_text, script_vars_text

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
