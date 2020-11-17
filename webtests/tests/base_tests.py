# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module containing the base test cases for a page and componenets
"""

import datetime
import functools
import unittest
from pathlib import Path

from utils.project.structure import get_project_root
from webtests import configuration
from webtests.driver import get_chrome_driver

def local_only(method):
    """
    Decorator to mark tests as local_only, meaning they will only run if the environment_type is set
    to local within the config.
    :param method: The test method to wrap
    :return: The wrapped test method
    """

    @functools.wraps(method)
    def wrapper_local_only(*args, **kwargs):
        if not configuration.is_local_environment():
            args[0].skipTest("Test is local only")
            return
        method(*args, **kwargs)

    return wrapper_local_only


class BaseTestCase(unittest.TestCase):
    """
    Base test class that provides setup and teardown of driver aswell as screenshotting capability
    on failed tests
    """

    def setUp(self) -> None:
        """
        Obtain the webdriver to be used in a testcase
        """
        self.driver = get_chrome_driver()

    def tearDown(self) -> None:
        """
        Quit the webdriver and screenshot the contents if there was a test failure
        """
        if self._is_test_failure():
            self._screenshot_driver()
        self.driver.quit()

    def _screenshot_driver(self):
        now = datetime.datetime.now()
        screenshot_name = f"{self._testMethodName}-{now.strftime('%Y-%m-%d_%H-%M-%S')}.png"
        path = str(Path(get_project_root(), "webtests", "screenshots", screenshot_name))
        self.driver.save_screenshot(path)

    def _is_test_failure(self):
        if hasattr(self, '_outcome'):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
            return len(result.failures) > 0
        return False
