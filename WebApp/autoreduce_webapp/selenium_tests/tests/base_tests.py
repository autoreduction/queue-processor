# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module containing the base test cases for a page and components
"""

import datetime
from pathlib import Path

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls.base import reverse
from selenium_tests.configuration import set_url
from selenium_tests.driver import get_chrome_driver
from axe_selenium_python import Axe

from queue_processors.queue_processor.settings import PROJECT_ROOT


class BaseTestCase(StaticLiveServerTestCase):
    """
    Base test class that provides setup and teardown of driver as well as screenshotting capability
    on failed tests
    """
    fixtures = ["super_user_fixture", "status_fixture", "notification_fixture"]

    def setUp(self) -> None:
        """
        Obtain the webdriver to be used in a testcase
        """
        self.driver = get_chrome_driver()
        set_url(self.live_server_url)

    def tearDown(self) -> None:
        """
        Quit the webdriver and screenshot the contents if there was a test failure
        """
        if self._is_test_failure():
            self._screenshot_driver()
        self.driver.quit()
        set_url("http://localhost:0000")

    def _screenshot_driver(self):
        now = datetime.datetime.now()
        screenshot_name = f"{type(self).__name__}-{self._testMethodName}-{now.strftime('%Y-%m-%d_%H-%M-%S')}.png"
        screenshot_path = str(
            Path(PROJECT_ROOT, "WebApp", "autoreduce_webapp", "selenium_tests", "screenshots", screenshot_name))
        self.driver.save_screenshot(screenshot_path)

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
        Test: driver navigates to overview page
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
        Test: driver navigates to failed jobs page
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
        Test: Admin notifications visible to admins
        """
        notifications = self.page.launch().get_notification_messages()
        self.assertIn(self.ADMIN_NOTIFICATION_MESSAGE, notifications)

    def test_non_admin_notifications_visible_to_admins(self):
        """
        Test: non admin notifications visible to admins
        """
        notifications = self.page.launch().get_notification_messages()
        self.assertIn(self.NON_ADMIN_NOTIFICATION_MESSAGE, notifications)

    def test_admin_notifications_not_visible_to_non_admin(self):
        """
        Test: Admin notifications not visible for non admins
        """
        self.driver.get(f"{self.live_server_url}{reverse('logout')}")
        # Go directly to the /overview page to avoid the logging in that happens at the index view
        self.driver.get(f"{self.live_server_url}{reverse('overview')}")
        notifications = self.page.get_notification_messages()
        self.assertNotIn(self.ADMIN_NOTIFICATION_MESSAGE, notifications)


class FooterTestMixin:
    """
    Contains test cases for pages with the FooterMixin
    """
    GITHUB_URL = "https://github.com/ISISScientificComputing/autoreduce"

    def test_footer_visible(self):
        """
        Test: Footer is visible
        When: Page has FooterMixin
        """
        self.page.launch()
        self.assertTrue(self.page.is_footer_visible())

    def test_github_link_navigates_to_github(self):
        """
        Test: Github link navigates to autoreduction github page
        When: Github link is clicked
        """
        self.page.launch().click_footer_github_link()
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.assertEqual(self.GITHUB_URL, self.driver.current_url)

    def test_help_link_navigates_to_help_page(self):
        """
        Test: Help page link navigates to help page
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


class AccessibilityTestMixin:
    """
    Contains axe accessibility test
    """
    # A dict of {rules.id: rules.selector, ...} to be ignored from the a11y test.
    # Reference: https://www.deque.com/axe/core-documentation/api-documentation/#parameters-1
    accessibility_test_ignore_rules = {}

    # A shared dict of {rules.id: rules.selector, ...} to also be ignored from the a11y test.
    # Reference: https://www.deque.com/axe/core-documentation/api-documentation/#parameters-1
    _shared_accessibility_test_ignore_rules = {
        # https://github.com/ISISScientificComputing/autoreduce/issues/790
        "color-contrast": "*",
    }

    # A list of axe tags to be run in the test.
    # Reference: https://www.deque.com/axe/core-documentation/api-documentation/#axe-core-tags
    accessibility_test_tags = ['wcag2a', 'wcag2aa', 'wcag21aa']

    # The axe reporter name. By default the reporter only reports violations results.
    # Reference: https://www.deque.com/axe/core-documentation/api-documentation/#api-name-axeconfigure
    accessibility_reporter_name = "no-passes"

    def test_accessibility(self):
        """
        Test: Page contains no axe accessibility violations for tags accessibility_test_tags and
        excluding the rules in accessibility_test_ignore_rules
        When: Page has AccessibilityMixin
        """
        self.page.launch()
        axe = Axe(self.driver)
        axe.inject()
        results = axe.run(options=self._build_axe_options())

        now = datetime.datetime.now()
        report_name = f"{type(self.page).__name__}-{now.strftime('%Y-%m-%d_%H-%M-%S')}.json"
        report_path = str(
            Path(PROJECT_ROOT, "WebApp", "autoreduce_webapp", "selenium_tests", "a11y_reports", report_name))

        axe.write_results(results, report_path)
        self.assertEqual(len(results['violations']), 0, axe.report(results["violations"]))

    def _build_axe_options(self) -> str:
        """
        Create the axe options JSON using accessibility_test_ignore_rules and
        accessibility_test_tags
        :return: (str) A JSON string which is used for axe options
        """
        def build_rules(rules):
            if rules == {}:
                return ""

            return ', '.join(
                [f"'{rule}': {{enabled: false, selector: '{selector}'}}" for rule, selector in rules.items()])

        all_rules = {**self._shared_accessibility_test_ignore_rules, **self.accessibility_test_ignore_rules}

        return f'''
        {{
            'runOnly': {{
                type: 'tag',
                values: {self.accessibility_test_tags}
            }},
            'rules': {{
                {build_rules(all_rules)}
            }},
            'reporter': '{self.accessibility_reporter_name}'
        }}
        '''
