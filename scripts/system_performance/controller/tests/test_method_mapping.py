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
from mock import Mock, MagicMock, patch

from scripts.system_performance.controller.method_mapping import MethodSelectorConfigurator, logging


class MockConnection(Mock):
    """Mock object class"""
    pass


class TestQueryHandler(unittest.TestCase):

    def setUp(self):

        self.invalid_method = 'invalid_method'
        self.valid_method = 'missing_run_numbers_report'
        self.instruments = ['GEM',
                            'WISH',
                            'OSIRIS',
                            'POLARIS',
                            'MUSR',
                            'POLREF',
                            'ENGINX',
                            'MARI',
                            'MAPS']

        self.arguments_dict = {'selection': 'run_number',
                               'status_id': 4,
                               'retry_run': '',
                               'run_state_column': 'finished',
                               'end_date': 'CURDATE()',
                               'interval': 1,
                               'time_scale': 'DAY',
                               'start_date': None,
                               'instrument_id': None}

    def tearDown(self):
        pass

    def test_create_method_mappings(self):

        # Assert return type is a dictionary
        self.assertIsInstance(MethodSelectorConfigurator().create_method_mappings(), dict)

        # Assert all items inside dicitonary of of type object
        for method_object in MethodSelectorConfigurator().create_method_mappings().keys():
            self.assertIsInstance(method_object, object)

    @patch('scripts.system_performance.controller.statistics_computation.QueryHandler.missing_run_numbers_report')
    def test_method_call_valid(self, mock_function):
        MethodSelectorConfigurator().method_call(self.valid_method,
                                                 {'instrument_id': 8})

        mock_function.assert_called_once_with(**{'instrument_id': 8})

    def test_method_call_invalid(self):

        actual = MethodSelectorConfigurator().method_call(self.invalid_method, {'instrument_id': 8})
        expected = None
        self.assertEqual(actual, expected)

    @patch('scripts.system_performance.controller.method_mapping.logging.warn')
    def test_method_call_log_invalid(self, mock_logger):

        MethodSelectorConfigurator().method_call(self.invalid_method, {'instrument_id': 8})

        mock_logger.assert_called_once_with("Invalid Input - method '%s' does not exist try -help "
                                            "to look at existing methods and arguments", self.invalid_method)

    def test_get_instrument_models(self):
        actual = MethodSelectorConfigurator().get_instrument_models()
        actual_instruments = []
        for index, instrument in actual:
            self.assertIsInstance(int(index), int)
            actual_instruments.append(instrument)

        for expected_instrument in self.instruments[:2]:
            self.assertIn(expected_instrument, actual_instruments)

    def test_run_every_instrument(self):
        # TODO need  to mock
        self.arguments_dict['start_date'] = '2019-12-12'
        self.arguments_dict['end_date'] = '2019-12-14'
        actual_output = MethodSelectorConfigurator().run_every_instrument({},
                                                                          self.valid_method,
                                                                          {'instrument_id': 8,
                                                                           'start_date': self.arguments_dict['start_date'],
                                                                           'end_date': self.arguments_dict['end_date']})
        actual_instruments = list(actual_output.keys())
        # actual_methods = set()

        for expected_instruments in self.instruments[0:2]:
            self.assertIn(expected_instruments, actual_instruments)

        # getting method names
        # for key, value in actual_output.items():
        #     if value:
        #         for key1, value1 in value.items():
        #             if value1 is not:
        #                 actual_methods.add(key1)
        #
        # print(list(actual_methods))

    @patch('scripts.system_performance.controller.method_mapping.logging.warn')
    def test_run_every_instrument_log_invalid(self, mock_logger):
        """Testing invalid method name logging takes place"""
        MethodSelectorConfigurator().run_every_instrument({},
                                                          self.invalid_method,
                                                          {'instrument_id': 8})

        mock_logger.assert_called_with("Invalid Input - method '%s' does not exist try -help "
                                       "to look at existing methods and arguments",
                                       self.invalid_method)

    @patch('scripts.system_performance.controller.method_mapping.MethodSelectorConfigurator.method_call')
    @patch('scripts.system_performance.controller.method_mapping.MethodSelectorConfigurator.user_instrument_list_validate')
    @patch('scripts.system_performance.controller.method_mapping.MethodSelectorConfigurator.run_every_instrument')
    def test_get_query_for_instruments_assert_methods(self, mock_rei, mock_uilv, mock_method_call):
        """Assert dictionary containing N instruments taken from valid instrument"""
        mock_rei.return_value = None
        mock_uilv.return_value = None

        MethodSelectorConfigurator().get_query_for_instruments(instrument_input=['MARI', 'MAPS'],
                                                               method_name='missing_run_numbers_report',
                                                               additional_method_arguments={
                                                                   'start_date':'2020-02-11',
                                                                   'end_date': '2020-02-19'})



        # mock methods
        # create list of methods to use
        # create list of instruments
        # create dictionary of additional arguments

        # tests:
        # test all methods are in dict
        #  test all instruments are in dict
        #  check return matches any additional arguments set.

        # expect a dictionary output {'instrument': []}
        # actual_output = MethodSelectorConfigurator().get_query_for_instruments(self.valid_method,
        #                                                                        8,
        #                                                                        self.arguments_dict)

        pass

    def test_get_query_for_instruments_assert_instruments_all(self):
        """Assert expected output for a given method and all instruments is returned"""
        # need to mock
        pass

    def test_get_query_for_instruments_assert_instruments_specific_instrument(self):
        """Assert expected output for a given method and instrument is returned"""
        # need to mock
        pass

    def test_get_query_for_instruments_invalid_instruments(self):
        """Assert that empty dictionary is returned if one invalid instrument is passed"""
        expected = {}
        actual = MethodSelectorConfigurator().get_query_for_instruments(instrument_input=['MARII'],
                                                                          method_name='execution_times',
                                                                          additional_method_arguments={
                                                                              'start_date': '2019-12-12',
                                                                              'end_date': '2019-12-14'})
        self.assertEqual(expected,actual)

    def test_get_query_for_instruments_invalid_methods(self):
        """Assert instrument returns none if method name is invalid"""
        expected = {'MARI': None}
        actual = MethodSelectorConfigurator().get_query_for_instruments(instrument_input=['MARI'],
                                                                          method_name='execution_times_invalid',
                                                                          additional_method_arguments={
                                                                              'start_date': '2019-12-12',
                                                                              'end_date': '2019-12-14'})

        self.assertEqual(expected, actual)

    def test_get_query_for_instruments_invalid_instrument_arg_format(self):
        """Assert instrument returns none if invalid additional argument is passed"""
        expected = {'MARI': None}
        actual = MethodSelectorConfigurator().get_query_for_instruments(instrument_input=['MARI'],
                                                                        method_name='execution_times',
                                                                        additional_method_arguments={
                                                                            'start_date': '2019-12-12',
                                                                            'end_invalid': '2019-12-14'})

        self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
