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


class TestIntepreter(unittest.TestCase):
    """
    Exercises the Interpreter
    """
    def setUp(self):
        self.figure_dict = {"figure": {"key": "value"}}
        self.dict = {"key": "value"}
        self.invalid = "invalid"

    # TODO: Test cases
    #   NOTE: mock read() to return one of the dicts above
    #   - valid file, returns dict
    #   - empty file, runtime error
    #   - yaml with no dictionary, runtime error