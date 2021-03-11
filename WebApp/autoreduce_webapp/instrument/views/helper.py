# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

from queue_processors.queue_processor.status_utils import STATUS


def get_last(runs_for_instrument):
    """
    Gets the last non-skipped run, unless all the runs are skipped.
    In that case it just gets the last skipped run.
    """
    # try to get the last non-skipped run
    last_run = runs_for_instrument.exclude(status=STATUS.get_skipped()).last()
    if not last_run:
        # if no non-skipped runs exist, just return the last skipped one
        last_run = runs_for_instrument.last()
    return last_run
