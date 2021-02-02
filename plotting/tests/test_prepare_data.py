# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the data preparation class
"""
import os
import unittest
from unittest.mock import patch

import pandas as pd

from plotting.prepare_data import PrepareData


class TestPrepareData(unittest.TestCase):
    # pylint:disable=protected-access
    """
    Exercises the PrepareData class
    """
    def setUp(self):
        self.valid_first_row = "first"
        self.valid_data = (
            f"{self.valid_first_row}\n"
            f"2\n"
            f"3.1, 3.2, 3.3"
        )
        self.test_file_name = "test_data.csv"
        with open(self.test_file_name, 'w') as file:
            file.write(self.valid_data)

    def tearDown(self):
        os.remove(self.test_file_name)

    def test_default_init(self):
        """
        Test: Class variables are created and set
        When: PrepareData is initialised
        """
        prep = PrepareData()
        self.assertIsNotNone(prep.expected_first_row)
        self.assertIsNotNone(prep.columns)

    def test_invalid_first_row(self):
        """
        Test: _check_first_row() raises a RuntimeError
        When: The argument given does not match PrepareData.expected_first_row
        """
        prep = PrepareData()
        valid_string = "0"
        prep.expected_first_row = valid_string
        invalid_first_row = self.valid_data.split("\n")[0]
        with self.assertRaises(RuntimeError):
            prep._check_first_row(invalid_first_row)

    def test_valid_first_row(self):
        """
        Test: _check_first_row() returns True
        When: The argument given matches PrepareData.expected_first_row,
        despite the argument containing additional appended whitespace.
        """
        prep = PrepareData()
        prep.expected_first_row = self.valid_first_row
        first_row = self.valid_data.split("\n")[0]
        self.assertTrue(prep._check_first_row(first_row))

    def test_invalid_second_row(self):
        """
        Test: _check_second_row() raises a RuntimeError
        When : The argument given cannot be cast to an integer
        """
        prep = PrepareData()
        with self.assertRaises(RuntimeError):
            prep._check_second_row("invalid")

    def test_valid_second_row(self):
        """
        Test: _check_second_row() returns the argument given as an integer type
        When: The argument given is a string representation of an integer
        """
        prep = PrepareData()
        second_row = self.valid_data.split("\n")[1]
        expected_return = int(second_row)
        self.assertEqual(prep._check_second_row(second_row),
                         expected_return)

    def test_invalid_path(self):
        """
        Test: prepare_data raises a FileNotFoundError
        When: An invalid path is given
        """
        prep = PrepareData()
        with self.assertRaises(FileNotFoundError):
            prep.prepare_data("invalid_path")

    @patch('plotting.prepare_data.PrepareData._check_second_row')
    @patch('plotting.prepare_data.PrepareData._check_first_row', return_value=True)
    def test_valid_path(self, mocked_check_first_row, mocked_check_second_row):
        """
        Test: prepare_data() validates the first and second rows of the data pointed to,
        and returns a panda.DataFrame 2 rows less than the data
        When: A valid path to valid data is given
        """
        split_data = self.valid_data.split("\n")
        first_row_with_newline = split_data[0] + "\n"
        second_row_with_newline = split_data[1] + "\n"

        prep = PrepareData()
        mocked_check_second_row.return_value = int(second_row_with_newline)
        data_frame = prep.prepare_data(self.test_file_name)

        mocked_check_first_row.assert_called_with(first_row_with_newline)
        mocked_check_second_row.assert_called_with(second_row_with_newline)
        self.assertIsInstance(data_frame, pd.DataFrame)
        self.assertEqual(len(data_frame), (len(split_data) - 2))
