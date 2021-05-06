# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Utility functions for the view of django models
"""
import functools
import logging
import os

from reduction_viewer.models import Instrument
from queue_processors.queue_processor.reduction.service import ReductionScript

LOGGER = logging.getLogger("app")


def deactivate_invalid_instruments(func):
    """
    Deactivate instruments if they are invalid
    """
    @functools.wraps(func)
    def request_processor(request, *args, **kws):
        """
        Function decorator that checks the reduction script for all active instruments
        and deactivates any that cannot be found
        """
        instruments = Instrument.objects.all()
        for instrument in instruments:
            script_path = ReductionScript(instrument.name)
            if instrument.is_active != script_path.exists():
                instrument.is_active = script_path.exists()
                instrument.save(update_fields=['is_active'])

        return func(request, *args, **kws)

    return request_processor


def get_interactive_plot_data(plot_locations):
    """
    Get the data for the interactive plots from the saved JSON files
    """
    # get only JSON files
    json_files = [location for location in plot_locations if location.endswith(".json")]

    output = {}

    for filepath in json_files:
        name = os.path.basename(filepath)
        with open(filepath, 'r') as file:
            data = file.read()
        output[name] = data
    return output
