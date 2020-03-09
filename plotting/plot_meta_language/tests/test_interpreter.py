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
from mock import patch
from plotting.plot_meta_language.interpreter import Interpreter


class TestInterpreter(unittest.TestCase):
    """
    Exercises the Interpreter
    """
    def setUp(self):
        self.valid_figure_dict = {"figure": {"key": "value"}}
        self.valid_minimal_dict = {"key": "value"}
        self.invalid_text = "invalid"

    def create_interpreter_with_mocked_read(self, read_return):
        """ Creates an interpreter instance with a mocked read method.
        :param read_return: The return value to be assigned to the read method
        :return: The interpreter with a mocked read method.
        """
        inter = Interpreter()
        inter.read = MagicMock()
        inter.read.return_value = read_return
        return inter

    def test_valid_figure_dict(self):
        """ Test the interpret method outputs the inner dictionary when given
        a dictionary exclusively containing a key="figure" entry """
        inter = self.create_interpreter_with_mocked_read(self.valid_figure_dict)
        output = inter.interpret("")
        self.assertEqual(output, self.valid_figure_dict["figure"])

    def test_valid_dict(self):
        """ Test the interpret method outputs the same (valid) dictionary that is read """
        inter = self.create_interpreter_with_mocked_read(self.valid_minimal_dict)
        output = inter.interpret("")
        self.assertEqual(output, self.valid_minimal_dict)

    def test_invalid_input(self):
        """ Test the interpret method raises an error if the data provided is not a dictionary """
        inter = self.create_interpreter_with_mocked_read(self.invalid_text)
        with self.assertRaises(RuntimeError):
            inter.interpret("")

    @patch('yaml.full_load')
    def test_invalid_file_location(self, mocked_load):
        """ Test the read method raises an error
        if the plot type file location does not point to a file """
        inter = Interpreter()
        mocked_load.side_effect = FileNotFoundError
        with self.assertRaises(RuntimeError):
            inter.read("")

    def test_empty_input(self):
        """ Test the interpret method raises an error if the plot type file is empty """
        inter = self.create_interpreter_with_mocked_read("")
        with self.assertRaises(RuntimeError):
            inter.interpret("")
