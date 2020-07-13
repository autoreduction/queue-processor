# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the manual job submission script
"""
import builtins
import unittest

from mock import patch, call, Mock

from scripts.manual_operations.manual_remove import ManualRemove, main, remove, user_input_check
from utils.clients.django_database_client import DatabaseClient


# pylint:disable=invalid-name,too-many-public-methods
class TestManualRemove(unittest.TestCase):
    """
    Test manual_remove.py
    """
    def setUp(self):
        self.manual_remove = ManualRemove(instrument='GEM')
        # Setup database connection so it is possible to use
        # ReductionRun objects with valid meta data
        self.database_client = DatabaseClient()
        self.database_client.connect()

        # Fake ReductionRun objects for testing
        self.gem_object_1 = self.database_client.data_model.ReductionRun(run_number='123',
                                                                         run_name='v1 of GEM123',
                                                                         run_version='1')

        self.gem_object_2 = self.database_client.data_model.ReductionRun(run_number='123',
                                                                         run_name='v2 of GEM123',
                                                                         run_version='2')

    @staticmethod
    def _run_variable(reduction_run_id=None, variable_ptr_id=None):
        """
        Create a mock object that represents a RunVariable object from the database
        """
        mock = Mock()
        mock.reduction_run_id = reduction_run_id
        mock.variable_ptr_id = variable_ptr_id
        return mock

    def test_find_run(self):
        """
        Test: The correct number of runs are discovered
        When: find_runs_in_database is called
        """
        actual = self.manual_remove.find_runs_in_database(run_number='001')
        self.assertEqual(2, len(actual))

    def test_find_run_invalid(self):
        """
        Test: An empty list is returned
        When find_runs_in_database does not find any runs
        """
        actual = self.manual_remove.find_runs_in_database(run_number='000')
        self.assertEqual(0, len(actual))

    @patch('scripts.manual_operations.manual_remove.ManualRemove.run_not_found')
    def test_process_results_not_found(self, mock_not_found):
        """
        Test: run_not_found is called
        When: No matching records are found in the database
        """
        self.manual_remove.to_delete['123'] = []
        self.manual_remove.process_results()
        mock_not_found.assert_called_once()

    @patch('scripts.manual_operations.manual_remove.ManualRemove.run_not_found')
    @patch('scripts.manual_operations.manual_remove.ManualRemove.multiple_versions_found')
    def test_process_results_single(self, mock_multi, mock_not_found):
        """
        Test: That the code falls through to multiple_version_found
        When If the results only contain single runs (not multiple versions)
        """
        self.manual_remove.to_delete['123'] = ['test']
        self.manual_remove.process_results()
        mock_multi.assert_not_called()
        mock_not_found.assert_not_called()

    @patch('scripts.manual_operations.manual_remove.ManualRemove.multiple_versions_found')
    def test_process_results_multi(self, mock_multi_version):
        """
        Test: process_results function routes to correct function if the run has multiple versions
        When: Multiple runs / versions are found in the database

        Note: for this test the content of results[key] list does not have to be Run objects
        """
        self.manual_remove.to_delete['123'] = ['test', 'test2']
        self.manual_remove.process_results()
        mock_multi_version.assert_called_once()

    def test_run_not_found(self):
        """
        Test: The correct corresponding key is deleted
        When: The value of the key is empty
        """
        self.manual_remove.to_delete['123'] = []
        self.manual_remove.run_not_found('123')
        self.assertEqual(0, len(self.manual_remove.to_delete))

    @patch('scripts.manual_operations.manual_remove.ManualRemove.validate_csv_input')
    @patch.object(builtins, 'input')
    def test_multiple_versions_found_single_input(self, mock_input, mock_validate_csv):
        """
        Test: That the user is not asked more than once for input
        When: The input is valid
        """
        self.manual_remove.to_delete['123'] = [self.gem_object_1,
                                               self.gem_object_2]
        self.assertEqual(2, len(self.manual_remove.to_delete['123']))
        mock_input.return_value = '2'
        mock_validate_csv.return_value = (True, [2])
        self.manual_remove.multiple_versions_found('123')
        # We said to delete version 2 so it should be the only entry for that run number
        self.assertEqual(1, len(self.manual_remove.to_delete['123']))
        self.assertEqual('2', self.manual_remove.to_delete['123'][0].run_version)

    @patch('scripts.manual_operations.manual_remove.ManualRemove.validate_csv_input')
    @patch.object(builtins, 'input')
    def test_multiple_versions_retry_user_input(self, mock_input, mock_validate_csv):
        """
        Test: Input is re-validated
        When: the user initially gives incorrect input
        """
        self.manual_remove.to_delete['123'] = [self.gem_object_1,
                                               self.gem_object_2]
        self.assertEqual(2, len(self.manual_remove.to_delete['123']))
        mock_input.side_effect = ['invalid', '2']
        mock_validate_csv.side_effect = [(False, []), (True, [2])]
        self.manual_remove.multiple_versions_found('123')
        self.assertEqual(2, mock_validate_csv.call_count)
        mock_validate_csv.assert_has_calls([call('invalid'), call('2')])

    @patch('scripts.manual_operations.manual_remove.ManualRemove.validate_csv_input')
    @patch.object(builtins, 'input')
    def test_multiple_versions_found_list_input(self, mock_input, mock_validate_csv):
        """
        Test: The correct version is delete
        When: The user asks to delete the second run version
        """
        self.manual_remove.to_delete['123'] = [self.gem_object_1,
                                               self.gem_object_2]
        self.assertEqual(2, len(self.manual_remove.to_delete['123']))
        mock_input.return_value = '1,2'
        mock_validate_csv.return_value = (True, [1, 2])
        self.manual_remove.multiple_versions_found('123')
        # We said to delete version 2 so it should be the only entry for that run number
        self.assertEqual(2, len(self.manual_remove.to_delete['123']))

    def test_validate_csv_single_val(self):
        """
        Test: For expected validation result
        When: user input contains a single run
        """
        actual = self.manual_remove.validate_csv_input('1')
        self.assertEqual((True, [1]), actual)

    def test_validate_csv_single_val_invalid(self):
        """
        Test: For expected validation result (False, [])
        When: user input validation with single value that is invalid
        """
        actual = self.manual_remove.validate_csv_input('a')
        self.assertEqual((False, []), actual)

    def test_validate_csv_list(self):
        """
        Test: For expected validation result
        When: user input contains multiple runs
        """
        actual = self.manual_remove.validate_csv_input('1,2,3')
        self.assertEqual((True, [1, 2, 3]), actual)

    def test_validate_csv_invalid(self):
        """
        Test: For expected validation result (False, [])
        When: User input is invalid type and multiple
        """
        actual = self.manual_remove.validate_csv_input('t,e,s,t')
        self.assertEqual((False, []), actual)

    # pylint:disable=no-self-use
    @patch('scripts.manual_operations.manual_remove.ManualRemove.find_runs_in_database')
    @patch('scripts.manual_operations.manual_remove.ManualRemove.process_results')
    @patch('scripts.manual_operations.manual_remove.ManualRemove.delete_records')
    def test_main(self, mock_delete, mock_process, mock_find):
        """
        Test: The correct control functions are called
        When: The main() function is called
        """
        main(instrument='GEM', first_run=1)
        mock_find.assert_called_once_with(1)
        mock_process.assert_called_once()
        mock_delete.assert_called_once()

    # pylint:disable=no-self-use
    @patch('scripts.manual_operations.manual_remove.ManualRemove.find_runs_in_database')
    @patch('scripts.manual_operations.manual_remove.ManualRemove.process_results')
    @patch('scripts.manual_operations.manual_remove.ManualRemove.delete_records')
    @patch('scripts.manual_operations.manual_remove.user_input_check')
    def test_main_range(self, mock_delete, mock_process, mock_find, mock_uic):
        """
        Test: The correct control functions are called including handle_input for many runs
        When: The main() function is called
        """
        main(instrument='GEM', first_run=1, last_run=11)
        mock_uic.assert_called()
        mock_find.assert_called()
        mock_process.assert_called()
        mock_delete.assert_called()

    # pylint:disable=no-self-use
    @patch('scripts.manual_operations.manual_remove.ManualRemove.find_runs_in_database')
    @patch('scripts.manual_operations.manual_remove.ManualRemove.process_results')
    @patch('scripts.manual_operations.manual_remove.ManualRemove.delete_records')
    def test_run(self, mock_delete, mock_process, mock_find):
        """
        Test: The correct control functions are called
        When: The run() function is called
        """
        remove('GEM', 1)
        mock_find.assert_called_once_with(1)
        mock_process.assert_called_once()
        mock_delete.assert_called_once()

    def test_delete_data_location(self):
        """
        Test: The correct query is run and associated records are removed
        When: calling delete_data_location
        """
        mock_data_model = Mock()
        self.manual_remove.database.data_model = mock_data_model
        self.manual_remove.delete_data_location(123)
        mock_data_model.DataLocation.objects.filter.\
            assert_called_once_with(reduction_run_id=123)

    def test_delete_reduction_location(self):
        """
        Test: The correct query is run and associated records are removed
        When: calling delete_reduction_location
        """
        mock_data_model = Mock()
        self.manual_remove.database.data_model = mock_data_model
        self.manual_remove.delete_reduction_location(123)
        mock_data_model.ReductionLocation.objects.filter.\
            assert_called_once_with(reduction_run_id=123)

    def test_delete_reduction_run_location(self):
        """
        Test: The correct query is run and associated records are removed
        When: calling delete_reduction_run_location
        """
        mock_data_model = Mock()
        self.manual_remove.database.data_model = mock_data_model
        self.manual_remove.delete_reduction_run(123)
        mock_data_model.ReductionRun.objects.filter.assert_called_once_with(id=123)

    @patch('scripts.manual_operations.manual_remove.ManualRemove.delete_reduction_location')
    @patch('scripts.manual_operations.manual_remove.ManualRemove.delete_data_location')
    @patch('scripts.manual_operations.manual_remove.ManualRemove.delete_variables')
    @patch('scripts.manual_operations.manual_remove.ManualRemove.delete_reduction_run')
    def test_delete_records(self, mock_rr, mock_rv, mock_dl, mock_rl):
        """
        Test: The appropriate functions are called with expected variables
        When: delete_records is called while self.to_delete is populated
        """
        mock_record = Mock()
        mock_record.id = 12
        self.manual_remove.to_delete = {'1234': [mock_record]}
        self.manual_remove.delete_records()
        mock_rr.assert_called_once_with(12)
        mock_rv.assert_called_once_with(12)
        mock_dl.assert_called_once_with(12)
        mock_rl.assert_called_once_with(12)

    def test_find_variables(self):
        """
        Test: The correct query is run
        When: calling find_variables_of_reduction
        """
        mock_variable_model = Mock()
        self.manual_remove.database.variable_model = mock_variable_model
        self.manual_remove.find_variables_of_reduction(123)
        mock_variable_model.RunVariable.objects.filter \
            .assert_called_once_with(reduction_run_id=123)

    @patch('scripts.manual_operations.manual_remove.ManualRemove.find_variables_of_reduction')
    def test_delete_variables(self, mock_find_vars):
        """
        Test: ALL variable records are successfully deleted from the database
        When: delete_variables function is called.
        """
        mock_run_variables = [self._run_variable(variable_ptr_id=3),
                              self._run_variable(variable_ptr_id=5)]
        mock_find_vars.return_value = mock_run_variables
        mock_variable_model = Mock()
        self.manual_remove.database.variable_model = mock_variable_model
        self.manual_remove.delete_variables(20)
        mock_find_vars.assert_called_once_with(20)
        mock_variable_model.RunVariable.objects.filter \
            .assert_has_calls(([call(variable_ptr_id=3), call().delete(),
                                call(variable_ptr_id=5), call().delete()]))

    def test_user_input_check(self):
        """
           Test: user_input_check() returns True of false
           When based on user input if range of runs to remove is larger than 10
        """
        with patch.object(builtins, 'input', lambda _: 'Y'):
            self.assertEqual(user_input_check(range(1, 11), 'GEM'), True)

        with patch.object(builtins, 'input', lambda _: 'N'):
            self.assertEqual(user_input_check(range(1, 11), 'GEM'), False)
