# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for JobQueuePage
"""
from selenium_tests.pages.job_queue_page import JobQueuePage
from selenium_tests.tests.base_tests import (FooterTestMixin, BaseTestCase, NavbarTestMixin,
                                             AccessibilityTestMixin)


class TestJobQueuePage(NavbarTestMixin, BaseTestCase, FooterTestMixin, AccessibilityTestMixin):
    """
    Test cases for JobQueuePage
    """
    fixtures = BaseTestCase.fixtures + ["test_job_queue_fixture"]
    excluded_accessibility_rules = [["color-contrast", "*"]]

    def setUp(self):
        """
        Setup and launch job queue page
        """
        super().setUp()
        self.page = JobQueuePage(self.driver)
        self.page.launch()

    def test_runs_shown_in_table(self):
        """
        Test: All expected runs on table
        """
        expected_runs = ["123", "456"]
        self.assertCountEqual(expected_runs, self.page.get_run_numbers_from_table())

    def test_runs_have_correct_status(self):
        """
        Test runs have expected statuses
        """
        self.assertEqual("Processing", self.page.get_status_from_run(123))
        self.assertEqual("Queued", self.page.get_status_from_run(456))
