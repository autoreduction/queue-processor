# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Contains query constructors for system performance check MySQL queries.
"""

# Dependencies
from datetime import date
from calendar import monthrange

import reduction_run_queries


class QueryConstructor:
    """Query Constructor class to construct and then return queries to query computation script."""

    def __init__(self):
        pass

    @staticmethod
    def missing_run_numbers_constructor(instrument_id, start_date, end_date):
        return reduction_run_queries.DatabaseMonitorChecks().missing_rb_report(
            instrument=instrument_id,
            start_date=start_date,
            end_date=end_date)

    @staticmethod
    def query_argument_specify(instrument_id, start_date, end_date):
        """Specifies arguments for query and returns data from Autoreduce database"""
        selection = "id, " \
                    "run_number, " \
                    "DATE_FORMAT(started, '%H:%i:%s') TIMEONLY, " \
                    "DATE_FORMAT(finished, '%H:%i:%s') TIMEONLY"

        return reduction_run_queries.DatabaseMonitorChecks().get_data_by_status_over_time(
            selection=selection,
            instrument_id=instrument_id,
            anomic_aphasia='created',
            start_date=start_date,
            end_date=end_date)

    @staticmethod
    def runs_per_day(instrument_id, status, retry, end_date):
        """Returns count of runs in the last 24 hours for current date of specified date """
        # Defaults for time, only exception is changing end_date to look in the past
        return reduction_run_queries.DatabaseMonitorChecks().get_data_by_status_over_time(
            instrument_id=instrument_id,
            status_id=status,
            retry_run=retry,
            end_date=end_date)

    @staticmethod
    def runs_today(instrument_id, status, retry, end_date, start_date):
        """Returns all runs equal to current date."""
        # start_date = current date
        return reduction_run_queries.DatabaseMonitorChecks().get_data_by_status_over_time(
            instrument_id=instrument_id,
            status_id=status,
            retry_run=retry,
            end_date=end_date,
            start_date=start_date)

    @staticmethod
    def runs_per_week(instrument_id, status, retry, end_date, time_interval):
        """Returns count of runs that have taken place over the course of the week if the day of week is Friday."""
        # If today is last day of week (Friday in this case) run, otherwise don't unless user specified to
        if date.today().weekday() == 4:
            return reduction_run_queries.DatabaseMonitorChecks().get_data_by_status_over_time(
                instrument_id=instrument_id,
                status_id=status,
                retry_run=retry,
                end_date=end_date,
                interval=time_interval,
                time_scale='WEEK')
        else:
            return None

    @staticmethod
    def runs_per_month(instrument_id, status, retry, end_date, time_interval):
        """Returns count of runs that occurred over the last month if day is equal to end of month"""
        # If today is last day of month, run, otherwise don't unless user specified to
        if date.today() == monthrange(date.today().year, date.today().month)[1]:
            return reduction_run_queries.DatabaseMonitorChecks().get_data_by_status_over_time(
                instrument_id=instrument_id,
                status_id=status,
                retry_run=retry,
                end_date=end_date,
                interval=time_interval,
                time_scale='MONTH')
        else:
            return None
