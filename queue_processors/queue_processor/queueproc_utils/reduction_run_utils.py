# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module to deal with creating and caneling of reduction runs in the database.
"""

from ..queueproc_utils.variable_utils import VariableUtils



class ReductionRunUtils:
    """ Reduction run utils, deals with creating and canceling of runs. """
    @staticmethod
    def get_script_arguments(run_variables):
        """
        Converts the RunVariables that have been created into Python kwargs which can
        be passed as the script parameters at runtime.
        """
        standard_vars, advanced_vars = {}, {}
        for run_variable in run_variables:
            variable = run_variable.variable
            value = VariableUtils.convert_variable_to_type(variable.value, variable.type)
            if variable.is_advanced:
                advanced_vars[variable.name] = value
            else:
                standard_vars[variable.name] = value

        arguments = {'standard_vars': standard_vars, 'advanced_vars': advanced_vars}

        return arguments
