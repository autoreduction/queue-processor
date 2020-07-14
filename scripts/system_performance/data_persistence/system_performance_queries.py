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


class DatabaseMonitorChecks:
    """Class to query system performance"""

    def __init__(self):
        """ Initialisation of database client and database connection
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=
         """
        self.database = DatabaseClient()
        self.connection = self.database.connect()
        self.table = "reduction_viewer_reductionrun"

    def query_log_and_execute(self, constructed_query):
        """ Logs and executes all queries ran in script
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - constructed_query (string): Query in string format to be executed and logged

            :returns:
            ----------
            RowProxy Object: RowProxy object of database query return"""

        logging.info('SQL QUERY: %s', constructed_query)
        print(constructed_query)
        return self.connection.execute(constructed_query).fetchall()

    def get_instruments_from_database(self):
        """ Retrieve current list of instruments from database
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :returns:
            ----------
            - RowProxy Object: RowProxy object containing query output of all instrument id's and
            names for autoreduction database"""

        all_instruments = "SELECT id, name "\
                          "FROM reduction_viewer_instrument"
        return self.query_log_and_execute(all_instruments)

    def runs_by_instrument_over_date_range(self, instrument, start_date, end_date):
        """ Retrieves run_numbers as longs for a given instrument
            between two dates as a list of integers
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - instrument (int): Instrument ID
            - start_date (string): start date formatted as string <"yyyy-mm-dd">
            - end_date (string): end date formatted as string <"yyyy-mm-dd">

            :returns:
            ----------
            - List: List containing query output of run numbers as integers"""

        missing_rb_calc_vars = {}

        missing_rb_query = "SELECT run_number "\
                           "FROM {} " \
                           "WHERE instrument_id = {} " \
                           "AND created " \
                           "BETWEEN '{}' " \
                           "AND '{}'".format(self.table,
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
        """ Construct a subsection of the last query segment based on argument input
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - query_arguments (dictionary): Dictionary of query arguments

            :returns:
            ----------
            - query_sub_segment (string): A modular sub-segment of larger query being constructed"""

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
    def construct_date_segment(arguments_dictionary):
        """ Called when start and end dates are equivalent
            - By default, end_date is set to CURDATE if not specified otherwise by user.
            - Sets date segment within query to CURDATE if start date is CURDATE meaning end_date
              is also set the CURDATE()
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - arguments_dictionary (dictionary): Dictionary of query arguments

            :returns:
            ----------
            - date_segment_string_format (string): Modular sub-segment of query being constructed"""

        if arguments_dictionary['start_date'] == 'CURDATE()':  # pylint disable=no-else-return
            date_segment_string_format = "= {}".format(arguments_dictionary['end_date'])
        else:
            arguments_dictionary['run_state_column'] = "CAST({} AS DATE) =".format(arguments_dictionary['run_state_column'])  # pylint: disable=line-too-long
            date_segment_string_format = "DATE('{}')".format(arguments_dictionary['end_date'])

        return date_segment_string_format

    def query_segment_replace(self, query_arguments):
        """ Handles the interchangeable segment of query to return either intervals of
            time or a period of time between two user specified dates and whether or not to
            include a filter by retry run or not.
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - query_arguments (dictionary): dictionary of query arguments

            :returns:
            ----------
            - returned_args (list): list of modular query_segments to be used in query
            construction"""

        returned_args = []

        # If end date is None, query only for rows created on or up to current date
        if query_arguments['start_date'] == query_arguments['end_date']:
            query_segment = self.construct_date_segment(query_arguments)

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
        return [returned_args]

    def query_construction(self, arguments, instrument_id_arg, query_type_segment):
        """ Constructs query as a string ready for execution
            =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - arguments (dictionary): Dictionary of query arguments
            - instrument_id_arg (int): Instrument ID
            - query_type_segment (string): Constructed query segment

            :returns:
            ----------
            String: Constructed query in string format"""

        return "SELECT {} " \
                         "FROM {} " \
                         "WHERE (status_id {}) = ({} {}) {} " \
                         "AND {} {}".format(arguments['selection'],
                                            self.table,
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
        """ Construct final query to be executed in string format to retrieve database
            return value from query_log_and_execute
             =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=

            :parameter
            ----------
            - selection (string) Default; 'run_number' : Column you would like to select or all
            columns by default
            - status_id (int) Default; 4 : Interchangeable id to look at different run status's
            - retry_run (string) Default; '' : Whether or not a user is looking for runs that have
            been retried
            - run_state_column (string) Default; 'finished' : DateTime column in
            database (created,
                     last_updated,
                     started,
                     finished)
            - end_date (string) Default; 'CURDATE()' : Most recent date you wish to query up too.
            - interval (int) Default; 1 : Interval for time_scale
            - time_scale (string) Default; 'DAY' : Expected inputs include DAY, Month or YEAR
            - start_date (None/string) Default; None : The furthest date from today you wish to
            query from e.g the start of cycle.
            - instrument_id (None/int) Default; None : Instrument id of the instrument to query

            :returns:
            ----------
            List : List of queried data returned from autoreduction database"""

        arguments = locals()  # Retrieving user specified variables
        # Determining query segment to use
        interchangeable_query_args = self.query_segment_replace(arguments)[0]
        # Constructing Query
        constructed_query = self.query_construction(
            arguments=arguments,
            instrument_id_arg=interchangeable_query_args[1],
            query_type_segment=interchangeable_query_args[0])

        return [list(elem) for elem in self.query_log_and_execute(constructed_query)]
