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

# pylint:disable=line-too-long
from scripts.system_performance.data_persistence.system_performance_queries import DatabaseMonitorChecks   # pylint: disable=line-too-long


def get_day_of_week():
    """ Retrieves numerical day of week
    =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

    :returns:
    ----------
    - date.today() (integer): Day of week as integer"""
    return date.today()


def get_instruments():
    """ Retrieve list of all existing instruments from Autoreduction Database
        =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

        :returns:
        ----------
        - RowProxy Object: RowProxy object containing instrument id and instrument
        names for all instruments"""

    return DatabaseMonitorChecks().get_instruments_from_database()


def runs_in_date_range(instrument_id, start_date, end_date):
    """ Specifies query arguments to retrieve run numbers from Autoreduction database
        between two specified dates ready
        =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

        :parameter
        ----------
        - instrument_id (int): instrument ID
        - start_date (string): start date formatted as string <"yyyy-mm-dd">
        - end_date (string): end date formatted as string <"yyyy-mm-dd">

        :returns:
        ----------
        RowProxy Object: RowProxy object of run_numbers between 2 dates for a given instrument id"""

    return DatabaseMonitorChecks().runs_by_instrument_over_date_range(
        instrument=instrument_id,
        start_date=start_date,
        end_date=end_date)


def start_and_end_times_by_instrument(instrument_id, start_date, end_date):
    """ Specifies query arguments to retrieves table ID, run_number, started and
        finished columns (time only) from Autoreduction Database
        =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

        :parameter
        ----------
        - instrument_id (int): (int): instrument ID
        - start_date (string): start date formatted as string <"yyyy-mm-dd">
        - end_date (string): end date formatted as string <"yyyy-mm-dd">

        :returns:
        ----------
        RowProxy Object: RowProxy object of ID, run_number, start and end times
        between two specified dates"""

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
    """ specifies query arguments and returns count of runs in the last 24 hours
        for current date of specified date
        =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

        :parameter
        ----------
        - instrument_id (int): instrument ID
        - status (int): run status ((1 : Error),
                                    (2 : Queued),
                                    (3 : Processing),
                                    (4 : Completed),
                                    (5 : Skipped))
        - retry ():
        - end_date (string): end date formatted as string <"yyyy-mm-dd">

        :returns:
        ----------
        RowProxy Object: RowProxy object of run numbers from end_date to end_date - 24 hours"""

    # Defaults for time, only exception is changing end_date to look in the past
    return DatabaseMonitorChecks().get_data_by_status_over_time(
        instrument_id=instrument_id,
        status_id=status,
        retry_run=retry,
        end_date=end_date)


def runs_today(instrument_id, status, retry, start_date, end_date):
    """ Specifies query arguments and returns all runs equal to current date.
        =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

        :parameter
        ----------
        - instrument_id (int): Instrument ID
        - status (int): run status ((1 : Error),
                                    (2 : Queued),
                                    (3 : Processing),
                                    (4 : Completed),
                                    (5 : Skipped))
        - retry ():
        - start_date (string): start date formatted as string <"yyyy-mm-dd">
        - end_date (string): end date formatted as string <"yyyy-mm-dd">

        :returns:
        ----------
        - RowProxy Object:  RowProxy object of run numbers where date is equal to
        current date/end_date"""

    # start_date = current date
    return DatabaseMonitorChecks().get_data_by_status_over_time(
        instrument_id=instrument_id,
        status_id=status,
        retry_run=retry,
        end_date=end_date,
        start_date=start_date)


def runs_per_week(instrument_id, status, retry, end_date, time_interval):
    """ Specifies query arguments and returns count of runs that have taken place
        over the course of the week by default (can return N weeks) if the day of week is Friday.
        =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

        :parameter
        ----------
        - instrument_id (int): Instrument ID
        - status (int): ((1 : Error),
                                    (2 : Queued),
                                    (3 : Processing),
                                    (4 : Completed),
                                    (5 : Skipped))
        - retry ():
        - end_date (string): start date formatted as string <"yyyy-mm-dd">
        - time_interval (int): number of days to retrieve

        :returns:
        ----------
        - RowProxy Object: RowProxy object of run numbers from the last week or N weeks"""

    todays_date = get_day_of_week()

    print(todays_date.weekday())

    # If today is last day of week (Friday) run, otherwise don't unless user specified to
    if todays_date.weekday() == 4:
        return DatabaseMonitorChecks().get_data_by_status_over_time(
            instrument_id=instrument_id,
            status_id=status,
            retry_run=retry,
            end_date=end_date,
            interval=time_interval,
            time_scale='WEEK')
    return None


def runs_per_month(instrument_id, status, retry, end_date, time_interval):
    """ Specifies query arguments and returns count of runs that occurred over the
        last month by default (can retrieve N months) if day is equal to end of month
        =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

        :parameter
        ----------
        - instrument_id (int):
        - status (int):
        - retry ():
        - end_date (string):
        - time_interval (int):

        :returns:
        ----------
        - RowProxy Object: RowProxy object of run numbers from the last month or N months"""

    # If today is last day of month, run, otherwise don't unless user specified to
    todays_date = get_day_of_week()
    # temp = todays_date.month
    if todays_date.day == monthrange(date.today().year, todays_date.month)[1]:
        return DatabaseMonitorChecks().get_data_by_status_over_time(
            instrument_id=instrument_id,
            status_id=status,
            retry_run=retry,
            end_date=end_date,
            interval=time_interval,
            time_scale='MONTH')
    return None
