# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for getting the reduction run statuses from the database.
"""
from model.database import access


class StatusUtils:
    # pylint: disable=missing-docstring
    @staticmethod
    def _get_status(status_value):
        """
        Attempt to get a status matching the given name or create one if it
        doesn't yet exist
        :param status_value: The value of the status record in the database
        """
        status_record = access.get_status(status_value, create=True)
        return status_record

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
