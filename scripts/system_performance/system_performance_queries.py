# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

"""
The purpose of this script is for performing MySQL queries to monitor system state
performance and health.
"""
from __future__ import print_function
import itertools
import logging
from utils.clients.database_client import DatabaseClient
from utils.clients.connection_exception import ConnectionException


class DatabaseMonitorChecks(object):
    """Class to query system performance"""
    table = "reduction_viewer_reductionrun"

    # Establishing a connection with Database using Database Client
    def __init__(self):
        self.database = DatabaseClient()
        self.connection = self.database.connect()

    def query_log_and_execute(self, constructed_query):
        """Logs and executes all queries ran in script"""
        logging.info('SQL QUERY: %s', constructed_query)
        print(constructed_query)
        return self.connection.execute(constructed_query).fetchall()

    def get_instruments_from_database(self):
        """Retrieve current list of instruments from database"""
        all_instruments = "SELECT id, name "\
                          "FROM reduction_viewer_instrument"
        return self.query_log_and_execute(all_instruments)

    def rb_range_by_instrument(self, instrument, start_date, end_date):
        """Retrieves run_numbers as longs for a given instrument
        between two dates as a list of integers"""
        missing_rb_calc_vars = {}

        missing_rb_query = "SELECT run_number "\
                           "FROM {} " \
                           "WHERE instrument_id = {} " \
                           "AND created " \
                           "BETWEEN '{}' " \
                           "AND '{}'".format(DatabaseMonitorChecks.table,
                                             instrument,
                                             start_date,
                                             end_date)
        # Execute query and append to dictionary
        missing_rb_calc_vars['run_numbers'] = self.query_log_and_execute(missing_rb_query)

        # Converts list of run number sets containing longs into list of integers
        # [(123L), (456L)] -> [123, 456]
        return [int(elem) for elem in list(itertools.chain.from_iterable(missing_rb_calc_vars['run_numbers']))]  # pylint: disable=line-too-long

    @staticmethod
    def time_scale_format_segment_replace(query_arguments):
        """Select last query argument based on argument input - sub_segment selection"""
        if not query_arguments['start_date']:
            interval_range = "INTERVAL {} {}".format(query_arguments['interval'],
                                                     query_arguments['time_scale'])

            query_sub_segment = ">= DATE_SUB('{}', {})".format(query_arguments['end_date'],
                                                               interval_range)
        else:
            # When both start and end date inputs are populated, query between those dates.
            query_sub_segment = "BETWEEN '{}' AND '{}'".format(query_arguments['start_date'],
                                                               query_arguments['end_date'])
        return query_sub_segment

    @staticmethod
    def construct_date_segment(start_date, end_date):
        """Set date segment within query"""
        return "= '{}'".format('CURDATE()' if start_date == 'CURDATE()' else end_date)

    def query_segment_replace(self, query_arguments):
        """Handles the interchangeable segment of query to return either intervals of
        time or period between two user specified dates and whether or not to
        include a filter by retry run or not."""

        returned_args = []

        # If end date is None, query only for rows created on or up to current date
        if query_arguments['start_date'] == query_arguments['end_date']:
            query_segment = self.construct_date_segment(start_date=query_arguments['start_date'],
                                                        end_date=query_arguments['end_date'])
            query_arguments['start_date'] = ''
            returned_args.append(query_segment)
        else:
            # Determining which sub query segment to place in query.
            query_segment = self.time_scale_format_segment_replace(query_arguments, )
            returned_args.append(query_segment)

        if query_arguments['instrument_id'] is not None:
            # Applying instrument_id query argument segments when instrument_id argument
            # populated as method arg
            instrument_id_arg = ", instrument_id"
            query_arguments['instrument_id'] = ', {}'.format(query_arguments['instrument_id'])
        else:
            query_arguments['instrument_id'] = ''
            instrument_id_arg = ''

        returned_args.append(instrument_id_arg)  # Appending instrument_id_arg
        print(returned_args)
        return [returned_args]

    @staticmethod
    def query_construction(arguments, instrument_id_arg, query_type_segment):
        """Constructs query ready for execution"""
        return "SELECT {} " \
                         "FROM {} " \
                         "WHERE (status_id {}) = ({} {}) {} " \
                         "AND {} {}".format(arguments['selection'],
                                            DatabaseMonitorChecks.table,
                                            instrument_id_arg,
                                            arguments['status_id'],
                                            arguments['instrument_id'],
                                            arguments['retry_run'],
                                            arguments['run_state_column'],
                                            query_type_segment)

    # pylint: disable=too-many-arguments, unused-argument
    def get_data_by_status_over_time(self, selection='run_number', status_id=4, retry_run='',
                                     run_state_column='finished', end_date='CURDATE()', interval=1,
                                     time_scale='DAY', start_date=None, instrument_id=None):
        """
        Default Variables
        :param selection : * Which column you would like to select or all columns
        by default
        :param status_id : 1 Interchangeable id to look at different run status's
        :param retry_run : Whether or not a user is looking for runs that have
        been retried
        :param instrument_id : the instrument id of the instrument to be queried.
        :param run_state_column : "finished" DateTime column in database (created,
        last_updated, started, finished)
        :param end_date : Most recent date you wish to query up too. By default
        this is the current date.
        :param interval : 1 Interval for time_scale
        :param time_scale : "DAY" Expected inputs include DAY, Month or YEAR
        :param start_date : The furthest date from today you wish to query from
        e.g the start of start of cycle.
        """
        arguments = locals()  # Retrieving user specified variables
        # Determining query segment to use
        interchangeable_query_args = self.query_segment_replace(arguments)[0]
        # Constructing Query
        constructed_query = self.query_construction(
            arguments=arguments,
            instrument_id_arg=interchangeable_query_args[1],
            query_type_segment=interchangeable_query_args[0])

        return [list(elem) for elem in self.query_log_and_execute(constructed_query)]
