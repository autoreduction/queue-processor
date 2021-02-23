# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test the functionality of the project.structure package
"""
import os
import unittest

from utils.project.structure import get_project_root, get_log_file


# pylint:disable=missing-docstring
class TestStructure(unittest.TestCase):
    def test_get_project_root(self):
        path = get_project_root()
        expected = [
            'build', 'docker_reduction', 'documentation', 'scripts', 'queue_processors', 'utils', 'WebApp', 'monitors'
        ]
        actual = os.listdir(path)
        for directory in expected:
            self.assertIn(directory, actual)

    def test_get_log_file(self):
        actual = get_log_file('test.log')
        self.assertEqual(os.path.split(actual)[-1], 'test.log')
