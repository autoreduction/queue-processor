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
    def __init__(self) -> None:
        self._cached_statuses = {}

    def _get_status(self, status_value: str):
        """
        Attempt to get a status matching the given name or create one if it
        doesn't yet exist
        :param status_value: The value of the status record in the database
        """
        if status_value in self._cached_statuses:
            return self._cached_statuses[status_value]
        else:
            status_record = access.get_status(status_value, create=True)
            self._cached_statuses[status_value] = status_record
        return status_record

    def get_error(self):
        return self._get_status('e')

    def get_completed(self):
        return self._get_status('c')

    def get_processing(self):
        return self._get_status('p')

    def get_queued(self):
        return self._get_status('q')

    def get_skipped(self):
        return self._get_status('s')
