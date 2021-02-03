# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for DataArchiveCreator class
"""
import os
import unittest
import tempfile

from utils.data_archive.data_archive_creator import DataArchiveCreator


class TestDataArchiveCreatorOverwrite(unittest.TestCase):
    """
    Can't use standard setup so requires a separate class
    """
    def test_valid_overwrite_init(self):
        """
        Test that the init can overwrite successfully if overwrite=True
        """
        test_output_directory = tempfile.mkdtemp()
        os.mkdir(os.path.join(test_output_directory, 'data-archive'))
        try:
            _ = DataArchiveCreator(test_output_directory, overwrite=True)
        except OSError as os_err:
            self.fail('The overwrite functionality didn\'t work: {}'.format(os_err))

    def test_invalid_overwrite_init(self):
        """
        Test that the init will throw if directory exists but no overwrite used
        """
        test_output_directory = tempfile.mkdtemp()
        os.mkdir(os.path.join(test_output_directory, 'data-archive'))
        self.assertRaises(OSError, DataArchiveCreator, test_output_directory, False)


# pylint:disable=missing-docstring, protected-access, invalid-name, too-many-public-methods
class TestDataArchiveCreator(unittest.TestCase):
    def setUp(self):
        self.test_output_directory = tempfile.mkdtemp()
        self.dac = DataArchiveCreator(self.test_output_directory)

    def test_valid_init(self):
        self.assertEqual(self.dac._base_dir, self.test_output_directory)
        archive_dir = os.path.join(self.test_output_directory, 'data-archive')
        self.assertEqual(self.dac._archive_dir, archive_dir)
        self.assertTrue(os.path.isdir(archive_dir))
        self.assertEqual(self.dac.data_files, [])
        self.assertFalse(self.dac.archive_deleted)

    def test_invalid_init(self):
        self.assertRaisesRegex(RuntimeError, 'Unable to find base_directory not a directory', DataArchiveCreator,
                               'not a directory')

    def test_valid_make_data_archive(self):
        self.dac.make_data_archive(['GEM'], 17, 18, 2)
        ndx_dir_path = os.path.join(self.test_output_directory, 'data-archive', 'NDXGEM')
        instrument_dir_path = os.path.join(ndx_dir_path, 'Instrument')
        logs_dir_path = os.path.join(instrument_dir_path, 'logs')
        user_dir_path = os.path.join(ndx_dir_path, 'user')
        data_dir_path = os.path.join(instrument_dir_path, 'data')
        cycle_dir_path = os.path.join(data_dir_path, 'cycle_{}_{}')
        jrnl_dir_path = os.path.join(logs_dir_path, 'journal')
        self.assertTrue(os.path.isdir(ndx_dir_path))
        self.assertTrue(os.path.isdir(instrument_dir_path))
        self.assertTrue(os.path.isdir(logs_dir_path))
        self.assertTrue(os.path.isdir(user_dir_path))
        self.assertTrue(os.path.isdir(data_dir_path))
        self.assertTrue(os.path.isdir(jrnl_dir_path))
        self.assertTrue(os.path.isdir(cycle_dir_path.format('17', '1')))
        self.assertTrue(os.path.isdir(cycle_dir_path.format('17', '2')))
        self.assertTrue(os.path.isdir(cycle_dir_path.format('17', '3')))
        self.assertTrue(os.path.isdir(cycle_dir_path.format('17', '4')))
        self.assertTrue(os.path.isdir(cycle_dir_path.format('18', '1')))
        self.assertTrue(os.path.isdir(cycle_dir_path.format('18', '2')))
        self.assertTrue(os.path.isdir(logs_dir_path.format('17', '1')))
        self.assertTrue(os.path.isdir(logs_dir_path.format('17', '2')))
        self.assertTrue(os.path.isdir(logs_dir_path.format('17', '3')))
        self.assertTrue(os.path.isdir(logs_dir_path.format('17', '4')))
        self.assertTrue(os.path.isdir(logs_dir_path.format('18', '1')))
        self.assertTrue(os.path.isdir(logs_dir_path.format('18', '2')))

    def test_under_single_digit_year(self):
        self.dac.make_data_archive(['GEM'], 1, 1, 1)
        self.assertTrue(
            os.path.isdir(
                os.path.join(self.test_output_directory, 'data-archive', 'NDXGEM', 'Instrument', 'data', 'cycle_01_1')))

    def test_add_data_to_recent(self):
        self.dac.make_data_archive(['GEM'], 17, 18, 2)
        self.dac.add_data_to_most_recent_cycle('GEM', ['test-file.nxs'])
        expected_file_path = os.path.join(self.test_output_directory, 'data-archive', 'NDXGEM', 'Instrument', 'data',
                                          'cycle_18_2', 'test-file.nxs')
        self.assertTrue(os.path.isfile(expected_file_path))

    def test_add_data_to_recent_single_digit(self):
        self.dac.make_data_archive(['GEM'], 1, 1, 2)
        self.dac.add_data_to_most_recent_cycle('GEM', ['test-file.nxs'])
        expected_file_path = os.path.join(self.test_output_directory, 'data-archive', 'NDXGEM', 'Instrument', 'data',
                                          'cycle_01_2', 'test-file.nxs')
        self.assertTrue(os.path.isfile(expected_file_path))

    def test_add_dat_files_invalid_type(self):
        self.dac.make_data_archive(['GEM'], 17, 18, 2)
        self.assertRaisesRegex(TypeError, "data_files is of: <class 'NoneType'>.",
                               self.dac.add_data_to_most_recent_cycle, 'GEM', None)

    def test_add_data_to_recent_invalid_inst(self):
        self.dac.make_data_archive(['GEM'], 17, 18, 2)
        self.assertRaisesRegex(RuntimeError, "Unable to create file at ", self.dac.add_data_to_most_recent_cycle,
                               'POLARIS', 'test-file.nxs')

    def test_add_journal_file_without_archive(self):
        self.assertRaisesRegex(RuntimeError, "Unable to create file at ", self.dac.add_journal_file, 'GEM', 'test')

    def test_add_journal_file_valid(self):
        self.dac.make_data_archive(['GEM'], 18, 18, 1)
        self.dac.add_journal_file('GEM', 'test')
        expected_file_path = os.path.join(self.test_output_directory, 'data-archive', 'NDXGEM', 'Instrument', 'logs',
                                          'journal', 'summary.txt')
        self.assertTrue(os.path.isfile(expected_file_path))

    def test_add_reduce_script_valid(self):
        self.dac.make_data_archive(['GEM'], 18, 18, 1)
        self.dac.add_reduce_script('GEM', 'test')
        expected_file_path = os.path.join(self.test_output_directory, 'data-archive', 'NDXGEM', 'user', 'scripts',
                                          'autoreduction', 'reduce.py')
        self.assertTrue(os.path.isfile(expected_file_path))

    def test_add_reduce_vars_script_valid(self):
        self.dac.make_data_archive(['GEM'], 18, 18, 1)
        self.dac.add_reduce_vars_script('GEM', 'test')
        expected_file_path = os.path.join(self.test_output_directory, 'data-archive', 'NDXGEM', 'user', 'scripts',
                                          'autoreduction', 'reduce_vars.py')
        self.assertTrue(os.path.isfile(expected_file_path))

    def test_add_last_run_without_archive(self):
        self.assertRaisesRegex(RuntimeError, "Unable to create file at ", self.dac.add_last_run_file, 'GEM', 'test')

    def test_add_last_run_valid(self):
        self.dac.make_data_archive(['GEM'], 18, 18, 1)
        self.dac.add_last_run_file('GEM', 'test')
        expected_file_path = os.path.join(self.test_output_directory, 'data-archive', 'NDXGEM', 'Instrument', 'logs',
                                          'lastrun.txt')
        self.assertTrue(os.path.isfile(expected_file_path))
        self.assertTrue(expected_file_path in self.dac.data_files)

    def test_overwrite_file_content_valid(self):
        self.dac.make_data_archive(['GEM'], 18, 18, 1)
        self.dac.add_last_run_file('GEM', 'test')
        expected_file_path = os.path.join(self.test_output_directory, 'data-archive', 'NDXGEM', 'Instrument', 'logs',
                                          'lastrun.txt')
        expected_file_content = 'new file content'
        self.dac.overwrite_file_content(expected_file_path, expected_file_content)
        self.assertTrue(os.path.isfile(expected_file_path))
        self.assertTrue(expected_file_path in self.dac.data_files)
        with open(expected_file_path, 'r') as actual_file:
            actual = actual_file.readline()
        self.assertEqual(actual, expected_file_content)

    def test_overwrite_file_content_not_a_file(self):
        self.assertRaises(ValueError, self.dac.overwrite_file_content, 'not a file path', 'content')

    def test_overwrite_file_content_unknown_file(self):
        # create test file that is unkown to the DAC
        temp_path = os.path.join(self.test_output_directory, 'temp.txt')
        with open(temp_path, 'w') as temp_file:
            temp_file.write('test')
        self.assertRaises(ValueError, self.dac.overwrite_file_content, temp_path, 'content')
        os.remove(temp_path)

    def test_delete_file_invalid_file_path(self):
        self.assertRaises(ValueError, self.dac.delete_file, 'not/a/real/file path .u')

    def test_delete_file_unknown_file(self):
        temp_path = os.path.join(self.test_output_directory, 'temp.txt')
        with open(temp_path, 'w') as temp_file:
            temp_file.write('test')
        self.assertRaises(ValueError, self.dac.delete_file, temp_path)
        os.remove(temp_path)

    def test_delete_file_valid(self):
        self.dac.make_data_archive(['WISH'], 18, 18, 1)
        self.dac.add_last_run_file('WISH', 'test')
        last_run_file_path = os.path.join(self.test_output_directory, 'data-archive', 'NDXWISH', 'Instrument', 'logs',
                                          'lastrun.txt')
        self.dac.delete_file(last_run_file_path)
        self.assertFalse(last_run_file_path in self.dac.data_files)
        self.assertFalse(os.path.exists(last_run_file_path))

    def test_delete_all_files_with_none(self):
        self.dac.make_data_archive(['GEM'], 18, 18, 1)
        self.dac.delete_all_files()

    def test_delete_all_with_files(self):
        self.dac.make_data_archive(['GEM'], 18, 18, 1)
        self.dac.add_last_run_file('GEM', 'test')
        self.dac.add_journal_file('GEM', 'test')
        self.dac.add_data_to_most_recent_cycle('GEM', ['test.nxs', 'test1.nxs'])
        self.dac.delete_all_files()
        self.assertFalse(
            os.path.isfile(
                os.path.join(self.test_output_directory, 'data-archive', 'NDXGEM', 'Instrument', 'logs',
                             'last_run.txt')))
        self.assertFalse(
            os.path.isfile(
                os.path.join(self.test_output_directory, 'data-archive', 'NDXGEM', 'Instrument', 'logs', 'journal',
                             'summary.txt')))
        self.assertFalse(
            os.path.isfile(
                os.path.join(self.test_output_directory, 'data-archive', 'NDXGEM', 'Instrument', 'data', 'cycle_18_1',
                             'test.nxs')))
        self.assertFalse(
            os.path.isfile(
                os.path.join(self.test_output_directory, 'data-archive', 'NDXGEM', 'Instrument', 'data', 'cycle_18_1',
                             'test1.nxs')))

    def test_delete_uncreated_archive(self):
        self.dac.delete_archive()

    def test_double_delete_archive(self):
        self.dac.delete_archive()
        self.dac.delete_archive()

    def test_delete_empty_archive(self):
        self.dac.make_data_archive(['GEM'], 18, 18, 1)
        self.dac.delete_archive()
        self.assertFalse(os.path.isdir(os.path.join(self.test_output_directory, 'data-archive')))

    def test_delete_full_archive(self):
        self.dac.make_data_archive(['GEM'], 18, 18, 1)
        self.dac.add_last_run_file('GEM', 'test')
        self.dac.add_journal_file('GEM', 'test')
        self.dac.add_data_to_most_recent_cycle('GEM', ['test.nxs', 'test1.nxs'])
        self.dac.delete_archive()
        self.assertFalse(os.path.isdir(os.path.join(self.test_output_directory, 'data-archive')))

    def tearDown(self):
        del self.dac
