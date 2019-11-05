# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
This module is used to find an instrument and create it if it doesn't exist.
"""
import logging.config

from queue_processors.queue_processor.base import session
from queue_processors.queue_processor.orm_mapping import Instrument
# pylint:disable=no-name-in-module,import-error
from queue_processors.queue_processor.settings import LOGGING

# Set up logging and attach the logging to the right part of the config.
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor")  # pylint: disable=invalid-name


# pylint: disable=missing-docstring
# pylint: disable=too-few-public-methods
class InstrumentUtils:
    @staticmethod
    def get_instrument(instrument_name):
        """
        Helper method that will try to get an instrument matching the given name or create one if it
        doesn't yet exist
        """
        instrument = session.query(Instrument).filter_by(name=instrument_name).first()
        if instrument is None:
            instrument = Instrument(name=instrument_name, is_active=1, is_paused=0)
            session.add(instrument)
            session.commit()
            logger.warning("%s instrument was not found, created it.", instrument_name)
        return instrument
