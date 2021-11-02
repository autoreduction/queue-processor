# ############################################################################ #
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################ #
"""Class to deal with reduction run variables."""
import logging
import traceback
from copy import deepcopy
import re
from typing import List

from autoreduce_qp.queue_processor.reduction.service import ReductionScript

logger = logging.getLogger(__file__)


class VariableUtils:
    @staticmethod
    def get_type_string(value):
        """
        Return a string representation of the type of the given value. If the
        type isn't supported, it defaults to text. Possible return strings:
        - text
        - number
        - list_text
        - list_number
        - boolean
        """
        var_type = type(value).__name__
        if var_type == 'str':
            return "text"
        elif var_type in ('int', 'float'):
            return "number"
        elif var_type == 'bool':
            return "boolean"
        elif var_type == 'list':
            list_type = "number"
            for val in value:
                if type(val).__name__ == 'str':
                    list_type = "text"
                    break
            return "list_" + list_type
        else:
            return "text"

    @staticmethod
    def _prepare_list(input_list: str) -> List[str]:
        if not isinstance(input_list, list):
            return input_list.replace("[", "").replace("]", "").split(",")
        else:
            return input_list

    @staticmethod
    def convert_variable_to_type(value, var_type):
        """
        Cast the given value to a type matching that of var_type.

        Args:
            value: A string of the value being casted to another type.
            var_type: Can be 'text', 'number', 'list_text', 'list_number',
            'boolean'.

        Returns:
            The value casted to the specified type. If the var_type is
            unrecognised, return the original value.
        """
        # pylint: disable=too-many-return-statements,too-many-branches
        if var_type == "text":
            return str(value)
        if var_type == "number":
            if not value or not re.match('(-)?[0-9]+', str(value)):
                return None
            if '.' in str(value):
                return float(value)
            return int(re.sub("[^0-9]+", "", str(value)))
        if var_type == "list_text":
            var_list = VariableUtils._prepare_list(value)
            list_text = []
            for list_val in var_list:
                item = list_val.strip().strip("'")
                if item:
                    list_text.append(item)
            return list_text
        if var_type == "list_number":
            var_list = VariableUtils._prepare_list(value)
            list_number = []
            for list_val in var_list:
                if list_val:
                    if '.' in str(list_val):
                        list_number.append(float(list_val))
                    else:
                        list_number.append(int(list_val))
            return list_number
        if var_type == "boolean":
            if isinstance(value, bool):
                return value
            else:
                return value.lower() == 'true'

        return value

    @staticmethod
    def get_default_variables(instrument_name) -> dict:
        """
        Create and return a list of variables from the reduction script on disk
        for the instrument. If reduce_script is supplied, return variables
        using that script instead of the one on disk.
        """
        arguments = {
            "standard_vars": {},
            "advanced_vars": {},
            "variable_help": {
                "standard_vars": {},
                "advanced_vars": {},
            }
        }

        reduce_vars = ReductionScript(instrument_name, 'reduce_vars.py')
        try:
            module = reduce_vars.load()

            for dict_name in ["standard_vars", "advanced_vars", "variable_help"]:
                if hasattr(module, dict_name):
                    arguments[dict_name] = getattr(module, dict_name)
        except (FileNotFoundError, ImportError, SyntaxError):
            logger.error(traceback.format_exc())

        return arguments


def merge_arguments(message_reduction_arguments: dict, reduce_vars_module):
    """
    Merge the reduction arguments provided from the message and from the
    reduce_vars module, with the ones from the message taking precedent.
    """
    def set_with_correct_type(message_reduction_arguments: dict, reduction_args: dict, dict_name: str):
        """
        Set the value of the variable with the correct type.

        It retrieves the type string of the value in reduce_vars.py (the
        reduction_args param), and converts the value to that type.

        This is done to enforce type consistency between reduce_vars.py and
        message_reduction_arguments.

        message_reduction_arguments can contain bad types when it gets sent from
        the web app - some values are incorrectly strings and they create extra
        duplicates.
        """
        if dict_name in message_reduction_arguments and dict_name in reduction_args:
            for name, value in message_reduction_arguments[dict_name].items():
                real_type = VariableUtils.get_type_string(reduction_args[dict_name][name])
                reduction_args[dict_name][name] = VariableUtils.convert_variable_to_type(value, real_type)

    reduction_args = {
        'standard_vars': deepcopy(getattr(reduce_vars_module, 'standard_vars', {})),
        'advanced_vars': deepcopy(getattr(reduce_vars_module, 'advanced_vars', {}))
    }
    set_with_correct_type(message_reduction_arguments, reduction_args, 'standard_vars')
    set_with_correct_type(message_reduction_arguments, reduction_args, 'advanced_vars')

    reduction_args["variable_help"] = getattr(reduce_vars_module, 'variable_help', {})
    return reduction_args
