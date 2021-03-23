# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for failed jobs page
"""
from __future__ import annotations
from typing import List, Union

from django.urls.base import reverse
from selenium.webdriver.support.select import Select

from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from slenium_tests.pages.page import Page


class FailedJobsPage(Page, NavbarMixin, FooterMixin):
    @staticmethod
    def url_path() -> str:
        """
        Return the path section of the failed job url
        :return: (str) path section of failed job url
        """
        return reverse("runs:failed")

    def get_failed_run_numbers(self) -> List[str]:
        """
        Get a list of the failed runs from the table
        :return: (List) list of failed runs
        """
        return [run.text for run in self.driver.find_elements_by_class_name("run-num-link")]

    def get_message_from_run(self, run_number: Union[str, int], version: int = None) -> str:
        """
        Get the message of a given run from the table
        :param run_number: The run number of the run
        :param version: Optionally run version
        :return: The message from the table
        """
        element_id = f"message-{run_number}-{version}" if version else f"message-{run_number}"
        return self.driver.find_element_by_id(element_id).text

    def toggle_run(self, run_number: Union[str, int], run_version: int = None) -> FailedJobsPage:
        """
        Toggle the checkbox for a given run number
        :param run_number: The run number to toggle for
        :param run_version: Optionally run version else 0 will be selected
        """
        element_id = f"selectRun{run_number}-{run_version}" if run_version else f"selectRun{run_number}-0"
        self.driver.find_element_by_id(element_id).click()
        return self

    def _get_select(self) -> Select:
        return Select(self.driver.find_element_by_id("runAction"))

    def hide_runs(self) -> FailedJobsPage:
        """
        Click to hide the toggled runs
        """
        self._get_select().select_by_value("hide")
        self.driver.find_element_by_id("runActionButton").click()
        return self

    def retry_runs(self) -> FailedJobsPage:
        """
        Click to retry toggled runs
        """
        self._get_select().select_by_value("rerun")
        self.driver.find_element_by_id("runActionButton").click()
        return self
