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
from pathlib import Path

from autoreduce_webapp.settings import REDUCTION_DIRECTORY
from reduction_viewer.models import Instrument

LOGGER = logging.getLogger(__name__)


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
            instrument.is_active = Path(REDUCTION_DIRECTORY % instrument.name, 'reduce.py').exists()
            instrument.save()

        return func(request, *args, **kws)

    return request_processor
