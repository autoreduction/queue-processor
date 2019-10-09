"""
Test cases of path handling helper in autoreduction processor
"""
import os
import unittest

from queue_processors.autoreduction_processor.settings import MISC
import queue_processors.autoreduction_processor.path_handling as path_handler


# pylint:disable=missing-docstring
class TestPathHandling(unittest.TestCase):

    def test_reduction_script_location(self):
        # ToDo: Should use archive explorer
        location = path_handler.reduction_script_location('WISH')
        self.assertEqual(location, MISC['scripts_directory'] % 'WISH')

    def test_load_reduction_script(self):
        file_path = path_handler.get_reduction_script('WISH')
        self.assertEqual(file_path, os.path.join(MISC['scripts_directory'] % 'WISH',
                                                 'reduce.py'))

    def test_is_excitations_instrument(self):
        excitation_inst = 'MARI'
        non_excitations_inst = 'POLARIS'
        self.assertTrue(path_handler.is_excitations_instrument(excitation_inst))
        self.assertFalse(path_handler.is_excitations_instrument(non_excitations_inst))

    def test_manipulate_excitations_output_dir(self):
        test_dir = '/test/path/with/many/folders'
        expected = '/test/path/with/many/'
        self.assertEqual(expected, path_handler.manipulate_excitations_output_dir(test_dir))

    def test_construct_log_directory(self):
        expected = '/test/dir/reduction_log/'
        self.assertEqual(expected, path_handler.construct_log_directory('/test/dir'))

    def test_construct_log_files(self):
        """
        Function uses os.path.join hence need windows / linux variant
        """
        if os.name == 'nt':
            expected_script = 'test\\RB123Run321Script.out'
            expected_mantid = 'test\\RB123Run321Mantid.log'
        else:
            expected_script = 'test/RB123Run321Script.out'
            expected_mantid = 'test/RB123Run321Mantid.log'
        expected = (expected_script, expected_mantid)
        self.assertEqual(expected, path_handler.construct_log_file_paths('test', '123', '321'))

    def test_construct_files_non_excitations(self):
        instrument = 'POLARIS'
        rb_num = '123'
        run = '321'
        expected_result_dir = MISC["ceph_directory"] % (instrument, rb_num, run)
        expected_log_dir = MISC["ceph_directory"] % (instrument, rb_num, run) + '/reduction_log/'
        expected_temp_result_dir = MISC["temp_root_directory"] + expected_result_dir
        expected_temp_log_dir = MISC["temp_root_directory"] + expected_log_dir
        expected = (expected_result_dir, expected_log_dir,
                    expected_temp_result_dir, expected_temp_log_dir)
        self.assertEqual(expected, path_handler.construct_file_paths(instrument, rb_num, run))
