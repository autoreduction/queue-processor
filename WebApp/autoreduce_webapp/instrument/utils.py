# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Utility functions for reduction variables
"""
import cgi
import importlib.util as imp
import io
import logging
import os
import re

import chardet
from autoreduce_webapp.icat_communication import ICATCommunication

from reduction_viewer.models import Notification, ReductionRun
from reduction_viewer.utils import InstrumentUtils
from instrument.models import InstrumentVariable, RunVariable
from queue_processors.queue_processor.reduction.service import ReductionScript
from queue_processors.queue_processor.status_utils import StatusUtils

STATUS = StatusUtils()

LOGGER = logging.getLogger('app')


class InstrumentVariablesUtils(object):
    """
    Instrument variable specific helper functions
    """
    @staticmethod
    def get_current_script_text(instrument_name):
        """
        Fetches the reduction script and variables script for
        the given instrument, and returns each as a string.
        """
        reduce_vars = ReductionScript(instrument_name)
        # TODO handle raises
        return reduce_vars.text()

    @staticmethod
    def _replace_special_chars(help_text):
        help_text = cgi.escape(help_text)  # Remove any HTML already in the help string
        help_text = help_text.replace('\n', '<br>').replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')
        return help_text