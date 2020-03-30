# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
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


class StatusUtils:
    # pylint: disable=missing-docstring
    @staticmethod
    def _get_status(status_value):
        """
        Attempt to get a status matching the given name or create one if it
        doesn't yet exist
        :param status_value: The value of the status record in the database

        """
        status = session.query(Status).filter_by(value=status_value)[0]
        if status is None:
            status = StatusUtils._create_new_status(status_value)
            logger.warning("%s status was not found, created it.", status_value)
        return status

    @staticmethod
    def _create_new_status(status_value):
        """
        Create a new Status record in the database
        """
        new_status = Status(value=status_value)
        session.add(new_status)
        session.commit()
        status = session.query(InstrumentVariable).filter_by(value=status_value)[0]
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
