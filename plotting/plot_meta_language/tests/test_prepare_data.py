# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the data preparation class
"""
import csv
import unittest
from mock import patch, mock_open, MagicMock

from plotting.prepare_data import PrepareData


class TestPrepareData(unittest.TestCase):
    """
    Exercises the PrepareData class
    """
    def setUp(self):
        self.valid_first_row = "first"
        self.valid_data = [
            [self.valid_first_row + " "],
            ["2"],
            ["3.1", "3.2", "3.3"]
        ]
        self.valid_data = (
            f"{self.valid_first_row}\n"
            f"2\n"
            f"3.1, 3.2, 3.3"
        )
        self.real_data = (
            "# X , Y , E\n"
            "1\n"
            "100.25,8210,90.6091"
        )

    def test_default_init(self):
        """ Test initialisation values are set """
        prep = PrepareData()
        self.assertIsNotNone(prep.expected_first_row)
        self.assertIsNotNone(prep.columns)

    def test_invalid_first_row(self):
        prep = PrepareData()
        valid_string = "0"
        prep.expected_first_row = valid_string
        first_row = self.valid_data.split("\n")[0]
        with self.assertRaises(RuntimeError):
            prep._check_first_row(first_row)

    def test_valid_first_row(self):
        """ Test _check_first_row removes appended whitespace
        and returns True if matches expected_first_row """
        prep = PrepareData()
        prep.expected_first_row = self.valid_first_row
        first_row = self.valid_data.split("\n")[0]
        self.assertTrue(prep._check_first_row(first_row))

    def test_invalid_second_row(self):
        prep = PrepareData()
        with self.assertRaises(RuntimeError):
            prep._check_second_row("invalid")

    def test_valid_second_row(self):
        prep = PrepareData()
        second_row = self.valid_data.split("\n")[1]
        expected_return = int(second_row)
        self.assertEqual(prep._check_second_row(second_row),
                         expected_return)

    def test_invalid_path(self):
        prep = PrepareData()
        with patch("builtins.open", side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                prep.prepare_data("")

    def test_valid_path(self):
        first_row_with_newline = self.valid_data.split("\n")[0] + "\n"
        second_row_with_newline = self.valid_data.split("\n")[1] + "\n"

        prep = PrepareData()
        prep._check_first_row = MagicMock(return_value=True)
        second_row_check_return = int(second_row_with_newline)
        prep._check_second_row = MagicMock(return_value=second_row_check_return)
        with patch("builtins.open", mock_open(read_data=self.valid_data)):
            prep.prepare_data("")

        prep._check_first_row.assert_called_with(first_row_with_newline)
        prep._check_second_row.assert_called_with(second_row_with_newline)
