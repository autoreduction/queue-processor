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
        expected = ['build', 'Documentation', 'scripts', 'QueueProcessors', 'utils', 'WebApp']
        actual = os.listdir(path)
        for directory in expected:
            self.assertTrue(directory in actual)

    def test_get_log_file(self):
        actual = get_log_file('test.log')
        self.assertEqual(os.path.split(actual)[-1], 'test.log')
