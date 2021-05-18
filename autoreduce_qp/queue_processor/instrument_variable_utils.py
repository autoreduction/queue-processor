# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for dealing with instrument reduction variables.
"""
import html
import logging
import logging.config
from copy import deepcopy
from typing import Any, List, Optional, Tuple

from django.db import transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.core.exceptions import ObjectDoesNotExist

from autoreduce_db.instrument.models import InstrumentVariable

from autoreduce_qp.queue_processor.variable_utils import VariableUtils
from autoreduce_qp.queue_processor.reduction.service import ReductionScript

# pylint:disable=too-many-locals,no-member


class DataTooLong(ValueError):
    """ Error class used for when reduction variables are too long. """


def _replace_special_chars(help_text):
    """ Remove any special chars in the help text. """
    help_text = html.escape(help_text)  # Remove any HTML already in the help string
    help_text = help_text.replace('\n', '<br>').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
    return help_text


class InstrumentVariablesUtils:
    """ Class used to parse and process instrument reduction variables. """
    @transaction.atomic
    def create_run_variables(self, reduction_run, message_reduction_arguments: dict = None) -> List:
        """
        Finds the appropriate InstrumentVariables for the given reduction run, and creates
        RunVariables from them.

        If the run is a re-run, use the previous run's variables.

        If instrument variables set for the run's experiment are found, they're used.

        Otherwise if variables set for the run's run number exist, they'll be used.

        If not, the instrument's default variables will be used.

        :param reduction_run: The reduction run object
        :param message_reduction_arguments: Preset arguments that will override whatever is in the
                                            reduce_vars.py script. They are passed in from the web app
                                            and have been acquired via direct user input
        """
        if message_reduction_arguments is None:
            message_reduction_arguments = {}
        instrument_name = reduction_run.instrument.name

        experiment_reference = reduction_run.experiment.reference_number
        run_number = reduction_run.run_number
        instrument_id = reduction_run.instrument.id
        possible_variables = InstrumentVariable.objects.filter(Q(experiment_reference=experiment_reference)
                                                               | Q(start_run__lte=run_number),
                                                               instrument_id=instrument_id)

        reduce_vars = ReductionScript(instrument_name, 'reduce_vars.py')
        reduce_vars_module = reduce_vars.load()

        final_reduction_arguments = self.merge_arguments(message_reduction_arguments, reduce_vars_module)

        variables = self.find_or_make_variables(possible_variables,
                                                instrument_id,
                                                final_reduction_arguments,
                                                run_number=run_number)

        logging.info('Creating RunVariables')
        # Create run variables from these instrument variables, and return them.
        return VariableUtils.save_run_variables(variables, reduction_run)

    @staticmethod
    def merge_arguments(message_reduction_arguments: dict, reduce_vars_module):
        """
        Merges the reduction arguments provided from the message and from the reduce_vars module,
        with the ones from the message taking precedent.
        """
        reduction_args = {
            'standard_vars': deepcopy(getattr(reduce_vars_module, 'standard_vars', {})),
            'advanced_vars': deepcopy(getattr(reduce_vars_module, 'advanced_vars', {}))
        }
        InstrumentVariablesUtils.set_with_correct_type(message_reduction_arguments, reduction_args, 'standard_vars')
        InstrumentVariablesUtils.set_with_correct_type(message_reduction_arguments, reduction_args, 'advanced_vars')

        reduction_args["variable_help"] = getattr(reduce_vars_module, 'variable_help', {})
        return reduction_args

    @staticmethod
    def set_with_correct_type(message_reduction_arguments: dict, reduction_args: dict, dict_name: str):
        """
        Set the value of the variable with the correct type.

        It retrieves the type string of the value in reduce_vars.py (the reduction_args param),
        and converts the value to that type.

        This is done to enforce type consistency between reduce_vars.py and message_reduction_arguments.

        message_reduction_arguments can contain bad types when it gets sent from the web app - some
        values are incorrectly strings and they create extra duplicates.
        """
        if dict_name in message_reduction_arguments and dict_name in reduction_args:
            for name, value in message_reduction_arguments[dict_name].items():
                real_type = VariableUtils.get_type_string(reduction_args[dict_name][name])
                reduction_args[dict_name][name] = VariableUtils.convert_variable_to_type(value, real_type)

    @staticmethod
    def find_or_make_variables(possible_variables: QuerySet,
                               instrument_id: int,
                               reduction_arguments: dict,
                               run_number: Optional[int] = None,
                               experiment_reference: Optional[int] = None,
                               from_webapp=False) -> List:
        """
        Find appropriate variables from the possible_variables QuerySet, or make the necessary variables

        :param possible_variables: A queryset holding the possible variables to be re-used
        :param instrument_id: ID of the instrument object
        :param reduction_arguments: A dictionary holding all required reduction arguments
        :param run_number: Optional, the run number from which these variables will be active
        :param expriment_reference: Optional, the experiment number for which these variables WILL ALWAYS be used.
                                    Variables set for experiment are treated as top-priority.
                                    They can only be changed or deleted from the web app.
                                    They will not be affected by variables for a run range or changing
                                    the values in reduce_vars.
        :param from_webapp: If the call is made from the web app we want to ignore the variable's own tracks_script flag
                            and ALWAYS overwrite the value of the variable with what has been passed in
        """
        all_vars: List[Tuple[str, Any, bool]] = [(name, value, False)
                                                 for name, value in reduction_arguments["standard_vars"].items()]
        all_vars.extend([(name, value, True) for name, value in reduction_arguments["advanced_vars"].items()])

        if len(all_vars) == 0:
            return []

        variables = []
        for name, value, is_advanced in all_vars:
            script_help_text = InstrumentVariablesUtils.get_help_text(
                'standard_vars' if not is_advanced else 'advanced_vars', name, reduction_arguments)
            new_type = VariableUtils.get_type_string(value)

            # Try to find a suitable variable to re-use from the ones that already exist
            variable = InstrumentVariablesUtils.find_appropriate_variable(possible_variables, name,
                                                                          experiment_reference)
            # if no suitable variable is found - create a new one
            if variable is None:
                var_kwargs = {
                    'name': name,
                    'value': value,
                    'type': new_type,
                    'help_text': script_help_text,
                    'is_advanced': is_advanced,
                    'instrument_id': instrument_id
                }
                variable = possible_variables.create(**var_kwargs)
                # if the variable was just created then set it to track the script
                # and that it starts on the current run
                # if it was found already existing just leave it as it is
                if experiment_reference:
                    variable.experiment_reference = experiment_reference
                else:
                    variable.start_run = run_number
                    variable.tracks_script = not from_webapp
                variable.save()
            else:
                InstrumentVariablesUtils.update_if_necessary(variable, experiment_reference, run_number, value,
                                                             new_type, script_help_text, from_webapp)
            variables.append(variable)
        return variables

    @staticmethod
    def update_if_necessary(variable, experiment_reference: Optional[int], run_number: Optional[int], new_value: Any,
                            new_type: str, script_help_text: str, from_webapp: bool):
        """
        Updates the variable if necessary:
            - Vars for experiment_reference are always updated in-place (i.e. a new variable is never made)
            - Vars for run ranges are updated in-place, if the current run is the same as the start_run.
              Otherwise the variable is copied, so that the original run can be re-reduced with it's original values
        """
        if experiment_reference is not None and variable.experiment_reference == experiment_reference:
            # we do not copy variables for an experiment_reference - we overwrite them to ensure only one exists
            if InstrumentVariablesUtils.variable_was_updated(variable, new_value, new_type, script_help_text):
                variable.save()
        elif from_webapp or variable.tracks_script:
            # if the variable is tracking the reduce_vars script
            # then update it's value to the one from the script. This is True
            # for variables that were created via manual_submission or run_detection.
            # "Configuring new Runs" from the web app will set it to False so that
            # the value always overrides the script, until changed back by the user or a later variable
            # takes priority.
            if InstrumentVariablesUtils.variable_was_updated(variable, new_value, new_type, script_help_text):
                # if the run number is different than what is already saved, then we will copy the
                # variable that contains the new values rather than overwriting the old variable
                # This allows the user to see the old run with the exact values that were used the first time
                if variable.start_run != run_number:
                    variable.pk = None
                    variable.id = None
                    # updates the effect of the new variable value to start from the current run
                    variable.start_run = run_number

                variable.save()

    @staticmethod
    def find_appropriate_variable(possible_variables, name, expriment_reference):
        """
        Find the appropriate variable that should be used.

        This function enforces the following priority:
        - Variables set for an Experiment number will ALWAYS be used - top priority
        - Next come variables set for specific run number ranges
        """
        # enforce a uniqueness using the (name, expriment_reference) fields
        # this will allow to only have 1 variable with that name for 1 experiment reference
        variable = None
        if expriment_reference is not None:
            try:
                variable = possible_variables.get(name=name, experiment_reference=expriment_reference)
            except ObjectDoesNotExist:
                pass

        if not variable:
            # if a variable set for the experiment was not found - then find the latest variable with that name
            return possible_variables.filter(name=name).last()

        return variable

    @staticmethod
    def variable_was_updated(variable, new_value: Any, new_type: str, new_help_text: str) -> bool:
        """
        Returns whether any of the variable's field was updated.
        """
        changed = False
        # compare the new value, which was converted earlier, to the original value in its real type
        real_type_value = VariableUtils.convert_variable_to_type(variable.value, variable.type)
        # special case for a None value - make it a None string
        if new_value is None:
            new_value = "None"

        if new_value != real_type_value:
            variable.value = new_value
            changed = True

        if new_type != variable.type:
            variable.type = new_type
            changed = True

        if new_help_text != variable.help_text:
            variable.help_text = new_help_text
            changed = True

        return changed

    @staticmethod
    def get_help_text(dict_name, key, reduction_arguments: dict):
        """ Get variable help text. """
        if dict_name in reduction_arguments["variable_help"]:
            if key in reduction_arguments["variable_help"][dict_name]:
                return _replace_special_chars(reduction_arguments["variable_help"][dict_name][key])
        return ""

    @staticmethod
    def get_current_script_text(instrument_name):
        """
        Fetches the reduction script and variables script for
        the given instrument, and returns each as a string.
        """
        return ReductionScript(instrument_name).text()
