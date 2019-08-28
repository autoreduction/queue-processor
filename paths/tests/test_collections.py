# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test the collections classes
"""
import unittest
import os

from paths.path import Path, PathError
from paths.collections import (PathCollection, InputPaths, TemporaryPaths,
                               OutputPaths)


NOT_ABSOLUTE_FILE = 'not/absolute/path'
FILE_PATH = os.path.realpath(__file__)
DIR_PATH = os.path.dirname(FILE_PATH)


# pylint:disable=missing-docstring
class TestPathCollection(unittest.TestCase):

    def test_path_collection_generic_init_raises_exp(self):
        self.assertRaises(RuntimeError, PathCollection)


# pylint:disable=missing-docstring
class TestInputPaths(unittest.TestCase):

    def test_init_valid_paths(self):
        input_paths = InputPaths(data_path=FILE_PATH,
                                 reduction_script_path=FILE_PATH,
                                 reduction_variables_path=FILE_PATH)
        self.assertEqual(input_paths.data_path, Path(FILE_PATH, 'file'))
        self.assertEqual(input_paths.reduction_script_path, Path(FILE_PATH, 'file'))
        self.assertEqual(input_paths.reduction_variables_path, Path(FILE_PATH, 'file'))

    def test_init_with_invalid_path_types(self):
        self.assertRaisesRegexp(PathError, "Path is not a file", InputPaths, DIR_PATH,
                                DIR_PATH, DIR_PATH)


# pylint:disable=missing-docstring
class TestTemporaryPaths(unittest.TestCase):

    def test_init_valid_paths(self):
        temp_paths = TemporaryPaths(root_directory=DIR_PATH,
                                    data_directory=DIR_PATH,
                                    log_directory=DIR_PATH)
        self.assertEqual(temp_paths.root_directory, Path(DIR_PATH, 'directory'))
        self.assertEqual(temp_paths.data_directory, Path(DIR_PATH, 'directory'))
        self.assertEqual(temp_paths.log_directory, Path(DIR_PATH, 'directory'))

    def test_init_with_invalid_path_types(self):
        self.assertRaisesRegexp(PathError, "Path is not a directory", TemporaryPaths, FILE_PATH,
                                FILE_PATH, FILE_PATH)


# pylint:disable=missing-docstring
class TestOutputPaths(unittest.TestCase):

    def test_init_valid_paths(self):
        output_paths = OutputPaths(data_directory=DIR_PATH,
                                   log_directory=DIR_PATH)
        self.assertEqual(output_paths.data_directory, Path(DIR_PATH, 'directory'))
        self.assertEqual(output_paths.log_directory, Path(DIR_PATH, 'directory'))

    def test_init_with_invalid_path_types(self):
        self.assertRaisesRegexp(PathError, "Path is not a directory", OutputPaths, FILE_PATH,
                                FILE_PATH)
