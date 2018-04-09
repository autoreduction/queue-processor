""" Module for getting the reduction run statuses from the database. """
import sys
sys.path.append("..")  # Adds parent directory to python path, until we decide how to package this.
import logging.config
from settings import LOGGING  # pylint: disable=import-error,no-name-in-module
from orm_mapping import Status, InstrumentVariable  # pylint: disable=import-error,
from base import session  # pylint: disable=import-error,
# Set up logging and attach the logging to the right part of the config.
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("queue_processor") # pylint: disable=invalid-name


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
