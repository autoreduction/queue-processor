# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Asserts the variable type of tables
"""
from django.template import Library

# pylint:disable=invalid-name
register = Library()


@register.simple_tag
def variable_type(var_type):
    """
    :return: variable type expected deepening on table element
    """
    if var_type == 'boolean':
        return 'checkbox'
    if var_type == 'list_number' or var_type == 'list_text':
        return 'text'
    return var_type
