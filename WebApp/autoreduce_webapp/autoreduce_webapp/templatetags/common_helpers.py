# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Common helper functions for templatetags
"""
from django.template import VariableDoesNotExist


def get_var(variable, context):
    """
    Obtain a variable from the context
    """
    try:
        return variable.resolve(context)
    except VariableDoesNotExist:
        return variable.var
