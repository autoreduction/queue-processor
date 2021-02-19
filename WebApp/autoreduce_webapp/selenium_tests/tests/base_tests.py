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
from pathlib import Path

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls.base import reverse
from selenium_tests.configuration import set_url
from selenium_tests.driver import get_chrome_driver

from utils.project.structure import PROJECT_ROOT


class BaseTestCase(StaticLiveServerTestCase):
    """
    Base test class that provides setup and teardown of driver aswell as screenshotting capability
    on failed tests
    """
    fixtures = ["super_user_fixture", "status_fixture", "notification_fixture"]

    @classmethod
    def setUpClass(cls) -> None:
        """
        Obtain the webdriver to be used in a testcase
        """
        super().setUpClass()
        cls.driver = get_chrome_driver()
        set_url(cls.live_server_url)

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Quit the webdriver and screenshot the contents if there was a test failure
        """
        super().tearDownClass()
        cls.driver.quit()
        set_url("http://localhost:0000")

    def tearDown(self) -> None:
        if self._is_test_failure():
            self._screenshot_driver()

    def _screenshot_driver(self):
        now = datetime.datetime.now()
        screenshot_name = f"{self._testMethodName}-{now.strftime('%Y-%m-%d_%H-%M-%S')}.png"
        path = str(Path(PROJECT_ROOT, "WebApp", "autoreduce_webapp", "selenium_tests", "screenshots", screenshot_name))
        self.driver.save_screenshot(path)

    def _is_test_failure(self):
        if hasattr(self, '_outcome'):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
            return len(result.failures) > 0 or len(result.errors) > 0
        return False


class NavbarTestMixin:
    """
    Contains test cases for pages with the NavbarMixin
    """
    ADMIN_NOTIFICATION_MESSAGE = "This notification should only be visible to admins"
    NON_ADMIN_NOTIFICATION_MESSAGE = "This notification should be visible to everyone"

    def test_navbar_visible(self):
        """
        Test: Navbar is visible on current page
        """
        self.page.launch()
        self.assertTrue(self.page.is_navbar_visible())

    # add visibility tests for links and logo etc.

    def test_logo_returns_to_overview(self):
        """
        Test: driver navigates to overview page
        When: navbar logo is clicked
        """
        self.page.launch().click_navbar_logo()
        self.assertIn(reverse("overview"), self.driver.current_url)

    def test_all_instruments_goes_returns_to_overview(self):
        """
        Tests: driver navigates to overview page
        When: all instruments link is clicked
        """
        self.page.launch().click_navbar_all_instruments()
        self.assertIn(reverse("overview"), self.driver.current_url)

    def test_job_queue_goes_to_job_queue(self):
        """
        Test: driver navigates to job queue
        When: job queue link is clicked
        """
        self.page.launch().click_navbar_job_queue()
        self.assertIn(reverse("runs:queue"), self.driver.current_url)

    def test_failed_jobs_goes_to_failed_jobs(self):
        """
        Tests: driver navigates to failed jobs page
        When: failed jobs link is clicked
        """
        self.page.launch().click_navbar_failed_jobs()
        self.assertIn(reverse("runs:failed"), self.driver.current_url)

    def test_graphs_goes_to_graphs(self):
        """
        Test: driver navigates to graphs page
        When: Navbar graphs link is clicked
        """
        self.page.launch().click_navbar_graphs()
        self.assertIn(reverse("graph"), self.driver.current_url)

    def test_help_goes_to_help(self):
        """
        Test: driver goes to help page
        When: Help link is clicked
        """
        self.page.launch().click_navbar_help()
        self.assertIn(reverse("help"), self.driver.current_url)

    def test_admin_notification_visible_to_admins(self):
        """
        Tests: Admin notifications visible to admins
        """
        notifications = self.page.launch().get_notification_messages()
        self.assertIn(self.ADMIN_NOTIFICATION_MESSAGE, notifications)

    def test_non_admin_notifications_visible_to_admins(self):
        """
        Tests: non admin notifications visible to admins
        """
        notifications = self.page.launch().get_notification_messages()
        self.assertIn(self.NON_ADMIN_NOTIFICATION_MESSAGE, notifications)

    def test_admin_notifications_not_visible_to_non_admin(self):
        """
        Tests: Admin notifications not visible for non admins
        """
        self.driver.get(self.live_server_url + "/overview")  # We do this due to issues with logging in. see README
        notifications = self.page.get_notification_messages()
        self.assertNotIn(self.ADMIN_NOTIFICATION_MESSAGE, notifications)


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
        self.page.launch()
        self.assertTrue(self.page.is_footer_visible())

    def test_github_link_navigates_to_github(self):
        """
        Tests: Github link navigates to autoreduction github page
        When: Github link is clicked
        """
        self.page.launch().click_footer_github_link()
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.assertEqual(self.GITHUB_URL, self.driver.current_url)

    def test_help_link_navigates_to_help_page(self):
        """
        Tests: Help page link navigates to help page
        When: Help page link is clicked
        """
        self.page.launch().click_footer_help_link()
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.assertIn(reverse("help"), self.driver.current_url)

    def test_support_email_visible(self):
        """
        Test: Support email is displayed in footer
        When: Page has FooterMixin
        """
        self.page.launch()
        self.assertTrue(self.page.is_footer_email_visible())
