"""
Test the functionality of the project.structure package
"""
import os
import unittest

from utils.project.structure import get_project_root


# pylint:disable=missing-docstring
class TestStructure(unittest.TestCase):

    def test_get_project_root(self):
        path = get_project_root()
        expected = ['build', 'Documentation', 'scripts', 'QueueProcessors', 'utils', 'WebApp']
        actual = os.listdir(path)
        for directory in expected:
            self.assertTrue(directory in actual)
