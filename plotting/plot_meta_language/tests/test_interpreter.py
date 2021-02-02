# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test cases for the meta-language interpreter
"""
import unittest

from unittest.mock import MagicMock
from unittest.mock import patch
from plotting.plot_meta_language.interpreter import Interpreter


class TestInterpreter(unittest.TestCase):
    """
    Exercises the Interpreter
    """
    def setUp(self):
        self.valid_figure_dict = {"figure": {"key": "value"}}
        self.valid_minimal_dict = {"key": "value"}
        self.invalid_text = "invalid"

    @staticmethod
    def create_interpreter_with_mocked_read(read_return):
        """ Creates an interpreter instance with a mocked read method.
        :param read_return: The return value to be assigned to the read method
        :return: The interpreter with a mocked read method.
        """
        inter = Interpreter()
        inter.read = MagicMock()
        inter.read.return_value = read_return
        return inter

    def test_valid_figure_dict(self):
        """
        Test: interpret() outputs the dictionary value of the "figure" key
        When: The method is given a dictionary containing a key="figure" entry
        """
        inter = self.create_interpreter_with_mocked_read(self.valid_figure_dict)
        output = inter.interpret("")
        self.assertEqual(output, self.valid_figure_dict["figure"])

    def test_valid_dict(self):
        """
        Test: interpret() outputs the same (valid) dictionary that is read
        When: The method is given a dictionary which does NOT
        exclusively contain a key="figure" entry
        """
        inter = self.create_interpreter_with_mocked_read(self.valid_minimal_dict)
        output = inter.interpret("")
        self.assertEqual(output, self.valid_minimal_dict)

    def test_invalid_input(self):
        """
        Test: interpret() raises an error
        When: The argument provided is not a dictionary
        """
        inter = self.create_interpreter_with_mocked_read(self.invalid_text)
        with self.assertRaises(RuntimeError):
            inter.interpret("")

    @patch('yaml.full_load')
    def test_invalid_file_location(self, mocked_load):
        """
        Test: read() raises an error
        When: The plot-type file location does not point to a file
        """
        inter = Interpreter()
        mocked_load.side_effect = FileNotFoundError
        with self.assertRaises(RuntimeError):
            inter.read("")

    def test_empty_input(self):
        """
        Test: interpret() raises an error
        When: The plot-type file is empty
        """
        inter = self.create_interpreter_with_mocked_read("")
        with self.assertRaises(RuntimeError):
            inter.interpret("")
