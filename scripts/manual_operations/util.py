# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
utility functions used in manual operations scripts
"""


def get_run_range(first_run, last_run=None):
    """
    Given a first_run number and optionally, a last run number return the range of runs including
    and between the run numbers. If last_run is not provided then the range will only include the
    first run
    :param first_run: (int) the first number
    :param last_run: (int) optional the second run number
    :return: (range) the range of runs including and between the first run
    """
    last_run = first_run if last_run is None else last_run
    if first_run > last_run:
        raise ValueError(f"first run: {first_run} is greater than last run: {last_run}")
    return range(first_run, last_run + 1)
