# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Unit tests for statistics_computation script
"""

# Dependencies
import unittest
from mock import Mock, patch, call

from scripts.system_performance.controller.method_mapping import MethodSelectorConfigurator, logging


class MockConnection(Mock):
    """Mock object class"""
    pass


class MockInstrumentModels:
    """"""

    def __init__(self, name, inst_id):
        self.name = name
        self.id = inst_id


class TestQueryHandler(unittest.TestCase):
    """"""

    def setUp(self):
        """The setup of variables used in many test cases.
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        self.invalid_method = 'invalid_method'
        self.valid_method = 'missing_run_numbers_report'

        # List of instrument to evaluate against db returned row proxy objects
        self.instruments = [MockInstrumentModels('GEM', 1),
                            MockInstrumentModels('WISH', 2),
                            MockInstrumentModels('OSIRIS', 3),
                            MockInstrumentModels('POLARIS', 4),
                            MockInstrumentModels('MUSR', 5),
                            MockInstrumentModels('POLREF', 6),
                            MockInstrumentModels('ENGINX', 7),
                            MockInstrumentModels('MARI', 8),
                            MockInstrumentModels('MAPS', 9)]

        # Default arguments for test cases
        self.arguments_dict = {'selection': 'run_number',
                               'status_id': 4,
                               'retry_run': '',
                               'run_state_column': 'finished',
                               'end_date': 'CURDATE()',
                               'interval': 1,
                               'time_scale': 'DAY',
                               'start_date': None,
                               'instrument_id': None}

        # Missing_run_numbers_report expected method return
        self.missing_run_numbers_report_mock_return = {'GEM': {'Count_of_runs': 101,
                                                               'Missing_runs_count': 0,
                                                               'Missing_runs': []},
                                                       'WISH': {'Count_of_runs': 295,
                                                                'Missing_runs_count': 2,
                                                                'Missing_runs': [47173, 47174]}}

    def test_create_method_mappings_dict_assertion(self):
        """Asserting that the return type of create_method_mappings is a dictionary and method
        objects are of object type.
        =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_= """

        # Assert dictionary data type is returned
        self.assertIsInstance(MethodSelectorConfigurator().create_method_mappings(), dict)

    def test_create_method_mappings_dict_value_assertion(self):
        """Asserting that the return type of values associated to keys inside the dictionary
        returned by create_method_mappings are objects
        =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        # Assert all items inside dictionary are of of type object
        for method_object in MethodSelectorConfigurator().create_method_mappings().keys():
            self.assertIsInstance(method_object, object)

    @patch('scripts.system_performance.controller.statistics_computation.QueryHandler.missing_run_numbers_report')  # pylint: line-too-long
    def test_method_call_valid(self, mock_function):
        """Asserting that a valid method call is called for a given instrument
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        MethodSelectorConfigurator().method_call(self.valid_method,
                                                 {'instrument_id': 8})

        mock_function.assert_called_once_with(**{'instrument_id': 8})

    def test_method_call_invalid(self):
        """Assert None is returned when trying to call method_call with invalid method
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        actual = MethodSelectorConfigurator().method_call(self.invalid_method, {'instrument_id': 8})
        expected = None
        self.assertEqual(actual, expected)

    @patch('scripts.system_performance.controller.method_mapping.logging.warning')
    def test_method_call_log_invalid(self, mock_logger):
        """Assert logger is invoked when invalid method is passed to method_call
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        MethodSelectorConfigurator().method_call(self.invalid_method, {'instrument_id': 8})

        mock_logger.assert_called_once_with("Invalid Input - method '%s' does not exist try -help "
                                            "to look at existing methods and arguments",
                                            self.invalid_method)

    @patch('scripts.system_performance.models.query_argument_constructor.get_list_of_instruments')
    def test_get_instrument_models(self, mock_gli):
        """Assert get_instrument_models correctly returns valid instruments
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        mock_gli.return_value = [(1, 'GEM'), (2, 'WISH')]

        actual = MethodSelectorConfigurator().get_instrument_models()
        actual_instruments = []

        # Asserting instrument index is of type int
        for index, instrument in actual:
            self.assertIsInstance(int(index), int)
            actual_instruments.append(instrument)

        # Assert actual and expected instruments match
        for expected_instrument in self.instruments[0:2]:
            self.assertIn(expected_instrument.name, actual_instruments)

    @patch('scripts.system_performance.data_persistence.system_performance_queries.DatabaseMonitorChecks.query_log_and_execute')  # pylint: line-too-long
    @patch('scripts.system_performance.controller.method_mapping.MethodSelectorConfigurator.get_instrument_models')  # pylint: line-too-long
    def test_run_every_instrument(self, mock_gim, mock_qle):
        """Assert that expected instruments are keys in dictionary returned
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        mock_gim.return_value = self.instruments[0:2]

        self.arguments_dict['start_date'] = '2019-12-12'
        self.arguments_dict['end_date'] = '2019-12-14'

        MethodSelectorConfigurator().run_every_instrument(
            instrument_dict={},
            method_name=self.valid_method,
            method_arguments={'start_date': '2020-02-11', 'end_date': '2020-02-19'})

        mock_qle.assert_has_calls([call("SELECT run_number "
                                    "FROM reduction_viewer_reductionrun "
                                    "WHERE instrument_id = 1 "
                                    "AND created "
                                    "BETWEEN '2020-02-11' AND '2020-02-19'"),
                                   call("SELECT run_number "
                                    "FROM reduction_viewer_reductionrun "
                                    "WHERE instrument_id = 2 "
                                    "AND created "
                                    "BETWEEN '2020-02-11' AND '2020-02-19'")], any_order=True)

    # @patch('scripts.system_performance.data_persistence.system_performance_queries.DatabaseMonitorChecks.query_log_and_execute')
    @patch('scripts.system_performance.controller.method_mapping.MethodSelectorConfigurator.get_instrument_models')  # pylint: line-too-long
    @patch('scripts.system_performance.controller.method_mapping.logging.warning')
    def test_run_every_instrument_log_invalid(self, mock_logger, mock_gim):
        """Testing invalid method name logging takes place
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        mock_gim.return_value = self.instruments

        MethodSelectorConfigurator().run_every_instrument(instrument_dict={},
                                                          method_name=self.invalid_method,
                                                          method_arguments={'instrument_id': 8})

        mock_logger.assert_called_with("Invalid Input - method '%s' does not exist try -help "
                                       "to look at existing methods and arguments",
                                       self.invalid_method)

    @patch('scripts.system_performance.controller.method_mapping.MethodSelectorConfigurator.get_instrument_models')  # pylint: line-too-long
    def test_user_instrument_list_validate(self, mock_uilv):
        """Test to filter down valid instruments
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        mock_uilv.return_value = self.instruments

        instrument = ['MARI']
        expected = self.instruments[7:8]
        actual = MethodSelectorConfigurator().user_instrument_list_validate(instrument)

        self.assertEqual(expected, actual)

    @patch('scripts.system_performance.data_persistence.system_performance_queries.DatabaseMonitorChecks.query_log_and_execute')  # pylint: line-too-long
    @patch('scripts.system_performance.controller.method_mapping.MethodSelectorConfigurator.method_call')  # pylint: line-too-long
    @patch('scripts.system_performance.controller.method_mapping.MethodSelectorConfigurator.user_instrument_list_validate')  # pylint: line-too-long
    def test_get_query_for_instruments_assert_methods(self, mock_uilv, mock_method_call, mock_qle):
        """Assert dictionary containing N instruments taken from valid instrument
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        mock_uilv.return_value = self.instruments[7:]

        actual = MethodSelectorConfigurator().get_query_for_instruments(
            instrument_input=['MARI', 'MAPS'],
            method_name='missing_run_numbers_report',
            additional_method_arguments={
                'start_date': '2020-02-11',
                'end_date': '2020-02-19'})

        instrument_count = 2
        actual_instrument_count = len(actual.keys())

        self.assertEqual(instrument_count, actual_instrument_count)

    @patch('scripts.system_performance.controller.method_mapping.MethodSelectorConfigurator.get_instrument_models')  # pylint: line-too-long
    def test_get_query_for_instruments_invalid_instruments(self, mock_gim):
        """Assert that empty dictionary is returned if one invalid instrument is passed
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        mock_gim.return_value = self.instruments

        expected = {}
        actual = MethodSelectorConfigurator().get_query_for_instruments(
            instrument_input=['MARII'],
            method_name='execution_times',
            additional_method_arguments={
                'start_date': '2019-12-12',
                'end_date': '2019-12-14'})

        self.assertEqual(expected, actual)

    @patch('scripts.system_performance.controller.method_mapping.MethodSelectorConfigurator.get_instrument_models')  # pylint: line-too-long
    def test_get_query_for_instruments_invalid_methods(self, mock_gim):
        """Assert instrument returns none if method name is invalid
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        mock_gim.return_value = self.instruments

        expected = {'MARI': None}
        actual = MethodSelectorConfigurator().get_query_for_instruments(
            instrument_input=['MARI'],
            method_name='execution_times_invalid',
            additional_method_arguments={
                'start_date': '2019-12-12',
                'end_date': '2019-12-14'})

        self.assertEqual(expected, actual)

    @patch('scripts.system_performance.controller.method_mapping.MethodSelectorConfigurator.get_instrument_models')  # pylint: line-too-long
    def test_get_query_for_instruments_invalid_instrument_arg_format(self, mock_gim):
        """Assert instrument returns none if invalid additional argument is passed
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        mock_gim.return_value = self.instruments

        expected = {'MARI': None}
        actual = MethodSelectorConfigurator().get_query_for_instruments(
            instrument_input=['MARI'],
            method_name='execution_times',
            additional_method_arguments={
                'start_date': '2019-12-12',
                'end_invalid': '2019-12-14'})

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
