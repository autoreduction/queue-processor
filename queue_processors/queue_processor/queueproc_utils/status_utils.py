# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for getting the reduction run statuses from the database.
"""
import logging.config

from queue_processors.queue_processor.base import session
from queue_processors.queue_processor.orm_mapping import Status, InstrumentVariable
# pylint:disable=no-name-in-module,import-error
from queue_processors.queue_processor.settings import LOGGING

# Set up logging and attach the logging to the right part of the config.
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor")  # pylint: disable=invalid-name


class StatusUtils(object):
    # pylint: disable=missing-docstring
    @staticmethod
    def _get_status(status_value):
        """
        Helper method that will try to get a status matching the given name or create one if it
        doesn't yet exist
        """
        status = session.query(Status).filter_by(value=status_value)[0]
        if status is None:
            new_status = Status(value=status_value)
            session.add(new_status)
            session.commit()
            status = session.query(InstrumentVariable).filter_by(value=status_value)[0]
            logger.warn("%s status was not found, created it.", status_value)
        return status

    def get_error(self):
        return self._get_status("Error")

    def get_completed(self):
        return self._get_status("Completed")

    def get_processing(self):
        return self._get_status("Processing")

    def get_queued(self):
        return self._get_status("Queued")

    def get_skipped(self):
        return self._get_status("Skipped")
