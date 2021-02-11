# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Selenium tests for the overview page
"""

from webtests.pages.run_summary_page import RunSummaryPage
from webtests.tests.base_tests import BaseTestCase


class TestRunSummaryPage(BaseTestCase):
    """
    Test cases for the overview page
    """
    def setUp(self) -> None:
        """
        Sets up the OverviewPage object
        """
        super().setUp()
        self.page = RunSummaryPage(self.driver)
        self.page.launch()

    def test_re_reduction_visible(self):
        rerun = self.page.get_rerun_elem()
        assert rerun.text == "Re-run reduction job"

    def test_reduction_job_panel_visible(self):
        assert self.page.get_reduction_job_panel()
