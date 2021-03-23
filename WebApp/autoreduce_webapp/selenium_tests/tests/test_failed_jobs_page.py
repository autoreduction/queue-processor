# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Selenium tests for failed jobs page
"""
from selenium_tests.pages.failed_jobs_page import FailedJobsPage
from selenium_tests.tests.base_tests import FooterTestMixin, BaseTestCase, NavbarTestMixin


class TestFailedJobsPage(NavbarTestMixin, BaseTestCase, FooterTestMixin):
    """
    Test cases for Failed Jobs Page
    """
    fixtures = BaseTestCase.fixtures + ["failed_jobs_fixture"]

    def setUp(self) -> None:
        """
        Sets up Failed Jobs Page model
        """
        super().setUp()
        self.page = FailedJobsPage(self.driver)
        self.page.launch()

    def test_failed_runs_visible(self):
        """
        Test: Correct runs shown on table
        """
        self.assertCountEqual(["99999"], self.page.get_failed_run_numbers())

    def test_hide_run_hides_run(self):
        """
        Test hide option hides run from page
        """
        self.page.toggle_run("99999").hide_runs()
        self.assertEqual([], self.page.get_failed_run_numbers())
