# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

"""
The purpose of this script is for performing MySQL queries to monitor system state performance and health.
"""

# sys.path.append(os.path.join(os.path.dirname(__file__), '../..', 'utils'))
# from scripts.system_performance.beam_status_webscraper import Data_Clean, TableWebScraper
from utils.clients.database_client import DatabaseClient
import requests
import itertools


class DatabaseMonitorChecks:
    """Class to query system performance"""
    table = "reduction_viewer_reductionrun"

    # Establishing a connection with Database using Database Client
    def __init__(self, credentials=None):
        if credentials:
            self.database = DatabaseClient(credentials)
        else:
            self.database = DatabaseClient()
        self.database.connect()

    def establish_connection(self):
        """Established connection ready to perform queries"""
        try:
            return self.database.get_connection()
        except requests.exceptions.ConnectionError:
            print "Unable to connect to database"

    def instruments_list(self):
        """Retrieve current list of instruments"""
        connection = self.establish_connection()
        result = connection.execute("SELECT id, name "
                                    "FROM reduction_viewer_instrument").fetchall()
        return result

    def missing_rb_report(self, instrument):
        """Retrieves run_number column and return missing sequential values """
        connection = self.establish_connection()
        missing_rb_calc_vars = {}

        missing_rb_calc_vars['run_numbers'] = \
            connection.execute("SELECT run_number "
                               "FROM {} "
                               "WHERE instrument_id = {}".format(DatabaseMonitorChecks.table,
                                                                 instrument)).fetchall()

        # Converts list of run number sets containing longs into list of integers [(123L), (456L)] -> [123, 456]
        return [int(elem) for elem in list(itertools.chain.from_iterable(missing_rb_calc_vars['run_numbers']))]

    def run_times(self, instrument):
        """
        Get the start and end times of a run for a given instrument separated into sub lists by status_id
        :returns run times in nested list formatted as: [[id, run_number, start time, end time], [...]...]"""
        connection = self.establish_connection()

        statuses = [4]  # add status id's of interest to list for be returned as nested lists in output

        nested_list_of_tuples_of_times_by_id = []
        for status_id in statuses:
            nested_list_of_tuples_of_times_by_id.append(connection.execute(
                "SELECT id,"
                " run_number,"
                " DATE_FORMAT(started, '%H:%i:%s') TIMEONLY,"
                " DATE_FORMAT(finished, '%H:%i:%s') TIMEONLY "
                "FROM {} Where instrument_id = {} AND status_id = {}".format(DatabaseMonitorChecks.table,
                                                                             instrument,
                                                                             status_id)).fetchall())  # works

        # Converting tuples to list items
        nested_list_of_times_by_id = []
        for i in range(len(nested_list_of_tuples_of_times_by_id)):
            temp_list = [list(elem) for elem in nested_list_of_tuples_of_times_by_id[i]]
            nested_list_of_times_by_id.append(temp_list)

        return nested_list_of_times_by_id

    def get_data_by_status_over_time(self, selection=None, status_id=None, retry_run=None, instrument_id=None,
                                     anomic_aphasia=None, end_date=None, interval=None, time_scale=None,
                                     start_date=None):
        """
        Default Variables
        :param selection : * Which column you would like to select or all columns by default
        :param status_id : 1 Interchangeable id to look at different run status's
        :param retry_run : Whether or not a user is looking for runs that have been retried
        :param instrument_id : the instrument id of the instrument to be queried.
        :param anomic_aphasia : "finished" DateTime column in database (created, last_updated, started, finished)
        :param end_date : Most recent date you wish to query up too. By default this is the current date.
        :param interval : 1 Interval for time_scale
        :param time_scale : "DAY" Expected inputs include DAY, Month or YEAR
        :param start_date : The furthest date from today you wish to query from e.g the start of start of cycle.
        """

        def _key_value_replace(key_to_find, definition, dictionary):
            """ Update arguments == to None with default variables """
            for key in dictionary.keys():
                if key == key_to_find:
                    dictionary[key] = definition
                    yield True
            yield False

        def _default_argument_assign(user_defined_arguments):
            # To assign all variables of type None a default variable
            defaults = {'selection': 'run_number',
                        'status_id': 4,
                        'retry_run': '',
                        'anomic_aphasia': 'finished',
                        'end_date': 'CURDATE()',
                        'interval': 1,
                        'time_scale': 'DAY',
                        'start_date': None,
                        'instrument_id': None}
            # reassigning None values to defaults.
            for argument in user_defined_arguments:
                if not user_defined_arguments[argument]:
                    found = False
                    while not found:
                        found = next(_key_value_replace(argument, defaults[argument], user_defined_arguments))

        def _dynamic_query_segment_replace(query_arguments):
            """Handles the interchangeable segment of query to return either intervals of time or period between two
            user specified dates and whether or not to include a filter by retry run or not."""
            returned_args = []
            # Interchangeable last query argument
            interval_range = "INTERVAL {} {}".format(query_arguments['interval'], query_arguments['time_scale'])
            date_range = "{}".format(start_date)

            # Select last query argument based on argument input
            if not query_arguments['start_date']:
                query_type_segment = interval_range
            else:
                query_type_segment = date_range
            returned_args.append(query_type_segment)
            # Allows for retry run column to be introduced into query when needed
            if query_arguments['retry_run']:
                query_arguments['retry_date'] = 'AND retry_run_id IS NOT NULL'

            if not query_arguments['instrument_id']:
                instrument_id_arg = ""
                query_arguments['instrument_id'] = ''
            else:
                instrument_id_arg = ", instrument_id"
                query_arguments['instrument_id'] = ', {}'.format(query_arguments['instrument_id'])
            returned_args.append(instrument_id_arg)
            return returned_args

        def _query_out(connection, instrument_id_arg, query_type_segment):
            # Generic Dynamic Query to handle most queries for data between two dates/time periods
            query_argument = "SELECT {} "\
                             "FROM {} "\
                             "WHERE (status_id {}) = ({} {}) {} "\
                             "AND {} >= {} - {}".format(arguments['selection'],
                                                        DatabaseMonitorChecks.table,
                                                        instrument_id_arg,
                                                        arguments['status_id'],
                                                        arguments['instrument_id'],
                                                        arguments['retry_run'],
                                                        arguments['anomic_aphasia'],
                                                        arguments['end_date'],
                                                        query_type_segment)
            return [list(elem) for elem in connection.execute(query_argument).fetchall()]

        arguments = locals()  # Retrieving user specified variables
        _default_argument_assign(arguments)  # Setting default variables
        interchangeable_query_args = _dynamic_query_segment_replace(arguments)  # Determining query segment to use

        return _query_out(self.establish_connection(), interchangeable_query_args[1], interchangeable_query_args[0])

# print(DatabaseMonitorChecks().get_data_by_status_over_time(instrument_id=7))
# print(DatabaseMonitorChecks().get_data_by_status_over_time(selection='COUNT(id)', instrument_id=8))
