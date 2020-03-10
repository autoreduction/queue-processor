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

from scripts.system_performance.controller.method_mapping import MethodSelectorConfigurator
from scripts.system_performance.test_setup.test_setup_default_mock_variables import SetupVariables


class MockConnection(Mock):
    """Mock object class"""
    pass  # pylint: disable=unnecessary-pass


class MockInstrumentModels:  # pylint: disable=too-few-public-methods
    """Mocking instrument models name and id properties"""

    def __init__(self, name, inst_id):
        self.name = name
        self.id = inst_id  # pylint: disable=invalid-name


class TestQueryHandler(unittest.TestCase):
    """Test query handler class methods"""

    def setUp(self):
        """The setup of variables used in many test cases.
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        self.invalid_method = 'invalid_method'
        self.valid_method = 'missing_run_numbers_report'

        # List of instrument to evaluate against db returned row proxy objects
        self.instruments = SetupVariables().instruments

        # Default arguments for test cases
        self.arguments_dict = SetupVariables().arguments_dict

        # Missing_run_numbers_report expected method return
        self.missing_run_numbers_report_mock_return = SetupVariables().missing_run_numbers_report_mock_return  # pylint: disable=line-too-long

    @patch('scripts.system_performance.controller.statistics_computation.QueryHandler.missing_run_numbers_report')  # pylint: disable=line-too-long
    def test_method_call_with_args_valid(self, mock_function):
        """Asserting that a valid method call is called for a given instrument
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        MethodSelectorConfigurator().call_method_with_args(self.valid_method,
                                                           {'instrument_id': 8})

        mock_function.assert_called_once_with(**{'instrument_id': 8})

    def test_method_call_with_args_invalid(self):
        """Assert None is returned when trying to call call_method_with_args with invalid method
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        actual = MethodSelectorConfigurator().call_method_with_args(self.invalid_method, {'instrument_id': 8})  # pylint: disable=line-too-long
        expected = None
        self.assertEqual(actual, expected)

    @patch('scripts.system_performance.controller.method_mapping.logging.warning')
    def test_method_call_with_args_log_invalid(self, mock_logger):
        """Assert logger is invoked when invalid method is passed to call_method_with_args
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        MethodSelectorConfigurator().call_method_with_args(self.invalid_method, {'instrument_id': 8})  # pylint: disable=line-too-long

        mock_logger.assert_called_once_with("Invalid Input - method '%s' does not exist try -help "
                                            "to look at existing methods and arguments",
                                            self.invalid_method)

    @patch('scripts.system_performance.data_persistence.system_performance_queries.DatabaseMonitorChecks.query_log_and_execute')  # pylint: disable=line-too-long
    @patch('scripts.system_performance.models.query_argument_constructor.get_instruments')
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

    @patch('scripts.system_performance.models.query_argument_constructor.get_instruments')
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

    @patch('scripts.system_performance.models.query_argument_constructor.get_instruments')
    def test_validate_instrument_list(self, mock_uilv):
        """Test to filter down valid instruments
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""

        mock_uilv.return_value = self.instruments

        instrument = ['MARI']
        expected = self.instruments[7:8]
        actual = MethodSelectorConfigurator().validate_instrument_list(instrument)

        self.assertEqual(expected, actual)

    # pylint: disable=line-too-long
    @patch('scripts.system_performance.data_persistence.system_performance_queries.DatabaseMonitorChecks.query_log_and_execute')
    @patch('scripts.system_performance.controller.method_mapping.MethodSelectorConfigurator.call_method_with_args')
    @patch('scripts.system_performance.controller.method_mapping.MethodSelectorConfigurator.validate_instrument_list')
    def test_get_query_for_instruments_assert_methods(self, mock_uilv, mock_method_call, mock_qle):  # pylint: disable=unused-argument
        """Assert dictionary containing N instruments taken from valid instrument
         =_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_=_="""
        # pyint: enable=line-too-long

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

    @patch('scripts.system_performance.models.query_argument_constructor.get_instruments')
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

    @patch('scripts.system_performance.models.query_argument_constructor.get_instruments')
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

    @patch('scripts.system_performance.models.query_argument_constructor.get_instruments')
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
