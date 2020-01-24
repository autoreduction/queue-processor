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
        try:
            self.connection = self.database.connect()
        except ConnectionException:
            raise ConnectionException('database')

    def query_log_and_execute(self, constructed_query):
        """Logs and executes all queries ran in script"""
        logging.info('SQL QUERY: %s', constructed_query)
        print(constructed_query)
        return self.connection.execute(constructed_query).fetchall()

    def instruments_list(self):
        """Retrieve current list of instruments"""
        all_instruments = "SELECT id, name "\
                          "FROM reduction_viewer_instrument"
        return self.query_log_and_execute(all_instruments)

    def rb_range_by_instrument(self, instrument, start_date, end_date):
        """Retrieves run_number column and return missing sequential values """
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
        missing_rb_calc_vars['run_numbers'] = self.query_log_and_execute(missing_rb_query)
        # pylint: disable=line-too-long
        # Converts list of run number sets containing longs into list of integers [(123L), (456L)] -> [123, 456]
        return [int(elem) for elem in list(itertools.chain.from_iterable(missing_rb_calc_vars['run_numbers']))]
        # pylint: enable=line-too-long

    @staticmethod
    def query_sub_segment_replace(query_arguments):
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
    def set_date_segment(start_date, end_date):
        """Set date segment within query"""
        if start_date == 'CURDATE()':
            date_segment = 'CURDATE()'
        else:
            date_segment = end_date
        return "= '{}'".format(date_segment)

    def query_segment_replace(self, query_arguments):
        """Handles the interchangeable segment of query to return either intervals of
        time or period between two user specified dates and whether or not to
        include a filter by retry run or not."""

        returned_args = []

        # If end date is None, query only for rows created on or up to current date
        if query_arguments['start_date'] == query_arguments['end_date']:
            query_segment = self.set_date_segment(start_date=query_arguments['start_date'],
                                                  end_date=query_arguments['end_date'])
            query_arguments['start_date'] = ''
            returned_args.append(query_segment)
        else:
            # Determining which sub query segment to place in query.
            query_segment = self.query_sub_segment_replace(query_arguments,)
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

    # pylint: disable=too-many-arguments
    def get_data_by_status_over_time(self, selection='run_number', status_id=4, retry_run='',
                                     anomic_aphasia='finished', end_date='CURDATE()', interval=1,
                                     time_scale='DAY', start_date=None, instrument_id=None):
        """
        Default Variables
        :param selection : * Which column you would like to select or all columns
        by default
        :param status_id : 1 Interchangeable id to look at different run status's
        :param retry_run : Whether or not a user is looking for runs that have
        been retried
        :param instrument_id : the instrument id of the instrument to be queried.
        :param anomic_aphasia : "finished" DateTime column in database (created,
        last_updated, started, finished)
        :param end_date : Most recent date you wish to query up too. By default
        this is the current date.
        :param interval : 1 Interval for time_scale
        :param time_scale : "DAY" Expected inputs include DAY, Month or YEAR
        :param start_date : The furthest date from today you wish to query from
        e.g the start of start of cycle.
        """
        # pylint: disable=unused-argument

        def _query_out(instrument_id_arg, query_type_segment):
            """Executes and returns built query as list"""
            query_argument = "SELECT {} " \
                 "FROM {} " \
                 "WHERE (status_id {}) = ({} {}) {} " \
                 "AND {} {}".format(arguments['selection'],
                                    DatabaseMonitorChecks.table,
                                    instrument_id_arg,
                                    arguments['status_id'],
                                    arguments['instrument_id'],
                                    arguments['retry_run'],
                                    arguments['anomic_aphasia'],
                                    query_type_segment)

            return [list(elem) for elem in self.query_log_and_execute(query_argument)]

        arguments = locals()  # Retrieving user specified variables
        # Determining query segment to use
        interchangeable_query_args = self.query_segment_replace(arguments)
        return _query_out(interchangeable_query_args[0][1], interchangeable_query_args[0][0])
