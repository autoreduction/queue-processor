# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module to deal with creating and caneling of reduction runs in the database.
"""
import logging.config

from queue_processors.queue_processor.settings import LOGGING

from ..queueproc_utils.variable_utils import VariableUtils

logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor")


class ReductionRunUtils:
    """ Reduction run utils, deals with creating and canceling of runs. """
    @staticmethod
    def get_script_and_arguments(reduction_run):
        """
        MISLEADING just get the script from the reduction run? Why have a function that
        does both when one is just reduction_run.script

        TODO with queue processor PR

        ~~Fetch the reduction script from the given run and return it as a string, along with a
        dictionary of arguments.~~
        """
        standard_vars, advanced_vars = {}, {}
        for run_variable in reduction_run.run_variables.all():
            variable = run_variable.variable
            value = VariableUtils.convert_variable_to_type(variable.value, variable.type)
            if variable.is_advanced:
                advanced_vars[variable.name] = value
            else:
                standard_vars[variable.name] = value

        arguments = {'standard_vars': standard_vars, 'advanced_vars': advanced_vars}

        return reduction_run.script, arguments
