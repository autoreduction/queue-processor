# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Validators to be used in the Message class
"""


def validate_run_number(run_number):
    """
    Assert a run number is valid
    :param run_number: The run number to validate
    """
    try:
        if int(run_number) > 0:
            return True
    except (ValueError, TypeError):
        return False
    return False


def validate_rb_number(rb_number):
    """
    Detects if the RB number is valid e.g. (above 0 and not a string)
    :param rb_number:
    :return: False If the RB is not valid, otherwise true
    """
    try:
        rb_number = int(rb_number)
    except (ValueError, TypeError):
        return False

    return 999999 < rb_number < 9999999
