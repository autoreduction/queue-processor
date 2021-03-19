# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for the job queue page model
"""
from typing import Union, List

from django.urls.base import reverse
from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.page import Page


class JobQueuePage(Page, NavbarMixin, FooterMixin):
    @staticmethod
    def url_path() -> str:
        """
        Return the path section of the job queue url
        :return: (str) path section of job queue url
        """
        return reverse("runs:queue")

    def get_run_numbers_from_table(self) -> List[str]:
        """
        Return a list of run numbers from the table
        :return: (List) list of string run numbers from table
        """
        return [run.text for run in self.driver.find_elements_by_class_name("run-link")]

    def get_status_from_run(self, run_number: Union[str, int]) -> str:
        """
        Given a run number return the status of the run as shown in the table
        :param run_number: (str/int) The run number
        :return: (status) The status as a string
        """
        return self.driver.find_element_by_id(f"status-{run_number}").text
