# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Utility functions for the view of django models
"""
import logging
import os

from autoreduce_webapp.settings import REDUCTION_DIRECTORY
from reduction_viewer.models import Instrument


LOGGER = logging.getLogger(__name__)


def deactivate_invalid_instruments(func):
    """
    Deactivate instruments if they are invalid
    """

    def request_processor(request, *args, **kws):
        """
        Function decorator that checks the reduction script for all active instruments
        and deactivates any that cannot be found
        """
        # pylint:disable=no-member
        instruments = Instrument.objects.filter(is_active=True)
        for instrument in instruments:
            reduction_path = os.path.join(REDUCTION_DIRECTORY % instrument.name, 'reduce.py')
            if not os.path.isfile(reduction_path):
                LOGGER.warn("Could not find reduction file: %s", reduction_path)
                instrument.is_active = False
                instrument.save()

        return func(request, *args, **kws)
    return request_processor
