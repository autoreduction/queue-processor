# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Handles colouring table rows
"""
from django.template import Library

# pylint:disable=invalid-name
register = Library()


@register.simple_tag
def colour_table_row(status):
    """
    Switch statement for defining table colouring
    """
    if status == 'Error':
        return 'danger'
    if status == 'Processing':
        return 'warning'
    if status == 'Queued':
        return 'info'
    if status == 'Completed':
        return 'success'
    if status == 'Skipped':
        return 'dark'
    return status
