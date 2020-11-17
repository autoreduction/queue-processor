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
from webtests.pages.page import OverviewPage, HelpPage, JobQueuePage, FailedJobsPage, GraphsPage


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
            .launch()
        self.assertTrue(self.page.is_navbar_visible())

    # add visibility tests for links and logo etc.

    def test_logo_returns_to_overview(self):
        """
        Test: driver navigates to overview page
        When: navbar logo is clicked
        """
        self.page \
            .launch() \
            .click_navbar_logo()
        self.assertEqual(OverviewPage.url(), self.driver.current_url)

    def test_all_instruments_goes_returns_to_overview(self):
        """
        Tests: driver navigates to overview page
        When: all instruments link is clicked
        """
        self.page \
            .launch() \
            .click_navbar_all_instruments()
        self.assertEqual(OverviewPage.url(), self.driver.current_url)

    def test_job_queue_goes_to_job_queue(self):
        """
        Test: driver navigates to job queue
        When: job queue link is clicked
        """
        self.page \
            .launch() \
            .click_navbar_job_queue()
        self.assertEqual(JobQueuePage.url(), self.driver.current_url)

    def test_failed_jobs_goes_to_failed_jobs(self):
        """
        Tests: driver navigates to failed jobs page
        When: failed jobs link is clicked
        """
        self.page \
            .launch() \
            .click_navbar_failed_jobs()
        self.assertEqual(FailedJobsPage.url(), self.driver.current_url)

    def test_graphs_goes_to_graphs(self):
        """
        Test: driver navigates to graphs page
        When: Navbar graphs link is clicked
        """
        self.page \
            .launch() \
            .click_navbar_graphs()
        self.assertEqual(GraphsPage.url(), self.driver.current_url)

    def test_help_goes_to_help(self):
        """
        Test: driver goes to help page
        When: Help link is clicked
        """
        self.page \
            .launch() \
            .click_navbar_help()
        self.assertEqual(HelpPage.url(), self.driver.current_url)
