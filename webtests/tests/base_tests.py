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
from webtests.pages.page import OverviewPage, HelpPage


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


class NavbarTestMixin:
    """
    Contains test cases for pages with the NavbarMixin
    """
    def test_navbar_visible(self):
        """
        Test: Navbar is visible on current page
        """
        self.page \
            .go()
        self.assertTrue(self.page
                        .is_navbar_visible())

    # add visibility tests for links and logo etc.

    def test_logo_returns_to_overview(self):
        """
        Test: driver navigates to overview page
        When: navbar logo is clicked
        """
        self.page \
            .go() \
            .click_navbar_logo()
        self.assertEqual(OverviewPage.url(), self.driver.current_url)


class FooterTestMixin:
    """
    Contains test cases for pages with the FooterMixin
    """
    GITHUB_URL = "https://github.com/ISISScientificComputing/autoreduce"

    def test_footer_visible(self):
        """
        Tests: Footer is visible
        When: Page has FooterMixin
        """
        self.page.go()
        self.assertTrue(self.page.is_footer_visible())

    def test_github_link_navigates_to_github(self):
        """
        Tests: Github link navigates to autoreduction github page
        When: Github link is clicked
        """
        self.page \
            .go() \
            .click_footer_github_link()
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.assertEqual(self.GITHUB_URL, self.driver.current_url)

    def test_help_link_navigates_to_help_page(self):
        """
        Tests: Help page link navigates to help page
        When Help page link is clicked
        """
        self.page \
            .go() \
            .click_footer_help_link()
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.assertEqual(HelpPage.url(), self.driver.current_url)
