# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Class to deal with reduction run variables
"""
import re
import logging

from model.database import access


class VariableUtils:
    @staticmethod
    def save_run_variables(variables, reduction_run):
        """ Save reduction run variables in the database. """
        model = access.start_database().variable_model
        logging.info('Saving run variables for %s', str(reduction_run.run_number))
        run_variables = []
        for variable in variables:
            run_var = model.RunVariable(variable=variable, reduction_run=reduction_run)
            run_var.save()
            run_variables.append(run_var)
        return run_variables

    @staticmethod
    def get_type_string(value):
        """
        Returns a textual representation of the type of the given value.
        The possible returned types are: text, number, list_text, list_number, boolean
        If the type isn't supported, it defaults to text.
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
    def convert_variable_to_type(value, var_type):
        """
        Convert the given value a type matching that of var_type.
        Options for var_type: text, number, list_text, list_number, boolean
        If the var_type isn't recognised, the value is returned unchanged
        :param value: A string of the value to convert
        :param var_type: The desired type to convert the value to
        :return: The value as the desired type,
                 or if failed to convert the original value as string
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
            var_list = str(value).split(',')
            list_text = []
            for list_val in var_list:
                item = list_val.strip().strip("'")
                if item:
                    list_text.append(item)
            return list_text
        if var_type == "list_number":
            var_list = value.split(',')
            list_number = []
            for list_val in var_list:
                if list_val:
                    if '.' in str(list_val):
                        list_number.append(float(list_val))
                    else:
                        list_number.append(int(list_val))
            return list_number
        if var_type == "boolean":
            return value.lower() == 'true'
        return value
