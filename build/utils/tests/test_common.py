"""
Test common functions for commands
"""
import os
import unittest

from build.utils.build_logger import BuildLogger
from build.utils.common import build_logger, validate_user_input
from utils.project.structure import get_project_root


# pylint:disable=missing-docstring,invalid-name
class TestCommon(unittest.TestCase):

    def test_build_logger_init(self):
        self.assertIsInstance(build_logger(), BuildLogger)
        self.assertEqual(build_logger().location,
                         os.path.join(get_project_root(), 'build.log'))

    def test_validate_user_input_invalid_input(self):
        self.assertRaisesRegexp(ValueError, "Expected user_input to be of type list not:",
                                validate_user_input, 'string', [])
        self.assertRaisesRegexp(ValueError, "Expected expected to be of type list not:",
                                validate_user_input, [], 'string')

    def test_validate_user_input(self):
        self.assertTrue(validate_user_input(['test'], ['test']))
        self.assertTrue(validate_user_input(['TEST'], ['test']))

    def test_validate_user_input_invalid(self):
        self.assertRaisesRegexp(RuntimeError, "Input: \'invalid\' is not valid.",
                                validate_user_input, ['invalid'], ['valid'])
