# ############################################################################
# Autoreduction Repository :
# https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################
"""
Contains various Utility classes for accessing the DB / message queue
which is used by the message handler
"""

from .queueproc_utils.instrument_variable_utils import InstrumentVariablesUtils
from .queueproc_utils.status_utils import StatusUtils
from .queueproc_utils.variable_utils import VariableUtils


class UtilsClasses:
    """
    Holds various util classes used by the Queue Processor, this can
    be replaced with a mock object at test time if required.
    """
    def __init__(self):
        self.status = StatusUtils()

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
