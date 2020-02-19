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
from datetime import date, datetime
from calendar import monthrange

from scripts.system_performance.data_persistence.system_performance_queries import DatabaseMonitorChecks


def get_day_of_week():
    return date.today()


def get_list_of_instruments():
    return DatabaseMonitorChecks().get_instruments_from_database()


def missing_run_numbers_constructor(instrument_id, start_date, end_date):

    return DatabaseMonitorChecks().runs_by_instrument_over_date_range(
        instrument=instrument_id,
        start_date=start_date,
        end_date=end_date)


def start_and_end_times_by_instrument(instrument_id, start_date, end_date):
    """Specifies arguments for query and returns data from Autoreduce database"""
    selection = "id, " \
                "run_number, " \
                "DATE_FORMAT(started, '%H:%i:%s') TIMEONLY, " \
                "DATE_FORMAT(finished, '%H:%i:%s') TIMEONLY"

    return DatabaseMonitorChecks().get_data_by_status_over_time(
        selection=selection,
        instrument_id=instrument_id,
        run_state_column='created',
        start_date=start_date,
        end_date=end_date)


def runs_per_day(instrument_id, status, retry, end_date):
    """Returns count of runs in the last 24 hours for current date of specified date """
    # Defaults for time, only exception is changing end_date to look in the past
    print('per day')
    return DatabaseMonitorChecks().get_data_by_status_over_time(
        instrument_id=instrument_id,
        status_id=status,
        retry_run=retry,
        end_date=end_date)


def runs_today(instrument_id, status, retry, start_date, end_date):
    """Returns all runs equal to current date."""
    # start_date = current date
    print('today')
    return DatabaseMonitorChecks().get_data_by_status_over_time(
        instrument_id=instrument_id,
        status_id=status,
        retry_run=retry,
        end_date=end_date,
        start_date=start_date)


def runs_per_week(instrument_id, status, retry, end_date, time_interval):
    """Returns count of runs that have taken place over the course of the week if the day of
    week is Friday."""

    todays_date = get_day_of_week()

    print(todays_date.weekday())

    # If today is last day of week (Friday) run, otherwise don't unless user specified to
    if todays_date.weekday() == 4:
        print('week')
        return DatabaseMonitorChecks().get_data_by_status_over_time(
            instrument_id=instrument_id,
            status_id=status,
            retry_run=retry,
            end_date=end_date,
            interval=time_interval,
            time_scale='WEEK')
    else:
        return None


def runs_per_month(instrument_id, status, retry, end_date, time_interval):
    """Returns count of runs that occurred over the last month if day is equal to end of month"""
    # If today is last day of month, run, otherwise don't unless user specified to
    todays_date = get_day_of_week()
    # temp = todays_date.month
    if todays_date.day == monthrange(date.today().year, date.today().month)[1]:
        print('month')
        return DatabaseMonitorChecks().get_data_by_status_over_time(
            instrument_id=instrument_id,
            status_id=status,
            retry_run=retry,
            end_date=end_date,
            interval=time_interval,
            time_scale='MONTH')
    else:
        return None
