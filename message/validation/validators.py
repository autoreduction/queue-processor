# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Validators to be used in the Message class
"""
from utils.settings import VALID_INSTRUMENTS


def validate_run_number(run_number):
    """
    Assert a run number is valid
    :param run_number: The run numebr to validate
    """
    return isinstance(run_number, int) and run_number > 0


def validate_instrument(instrument):
    """
    Assert an instrument exists in the valid set of instruemnts
    :param instrument: The instrument to validate
    """
    return isinstance(instrument, str) and instrument in VALID_INSTRUMENTS
