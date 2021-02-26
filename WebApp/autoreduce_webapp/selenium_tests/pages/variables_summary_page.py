# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

from typing import List, Tuple

from django.urls import reverse
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

from selenium_tests import configuration
from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.component_mixins.tour_mixin import TourMixin
from selenium_tests.pages.page import Page
from selenium_tests.pages.run_summary_page import RunSummaryPage
from selenium_tests.pages.component_mixins.rerun_form_mixin import RerunFormMixin

from selenium_tests.pages.page import Page


class VariableSummaryPage(Page, NavbarMixin, FooterMixin, TourMixin):
    """
    Page model class for run summary page
    """
    def __init__(self, driver, instrument):
        super().__init__(driver)
        self.instrument = instrument

    def url_path(self) -> str:
        """
        Return the current URL of the page.
        :return: (str) the url path
        """
        return reverse("instrument:variables_summary", kwargs={
            "instrument": self.instrument,
        })

    @property
    def current_variables_by_run(self) -> WebElement:
        return self.driver.find_element_by_id("current_variables_by_run")

    @property
    def upcoming_variables_by_run(self) -> WebElement:
        return self.driver.find_element_by_id("upcoming_variables_by_run")

    @property
    def upcoming_variables_by_experiment(self) -> WebElement:
        return self.driver.find_element_by_id("upcoming_variables_by_experiment")

    def run_edit_button_for(self, start: int, end: int) -> Tuple[WebElement, str]:
        url = reverse("instrument:variables", kwargs={"instrument": self.instrument, "start": start, "end": end})
        return self.driver.find_element_by_css_selector(f'[href*="{url}"]'), url

    def run_delete_button_for(self, start: int, end: int) -> Tuple[WebElement, str]:
        url = reverse("instrument:delete_variables", kwargs={"instrument": self.instrument, "start": start, "end": end})
        return self.driver.find_element_by_css_selector(f'[href*="{url}"]'), url

    def experiment_edit_button_for(self, experiment_reference: int) -> Tuple[WebElement, str]:
        url = reverse("instrument:variables_by_experiment",
                      kwargs={
                          "instrument": self.instrument,
                          "experiment_reference": experiment_reference
                      })
        return self.driver.find_element_by_css_selector(f'[href*="{url}"]'), url

    def experiment_delete_button_for(self, experiment_reference: int) -> Tuple[WebElement, str]:
        url = reverse("instrument:delete_variables_by_experiment",
                      kwargs={
                          "instrument": self.instrument,
                          "experiment_reference": experiment_reference
                      })
        return self.driver.find_element_by_css_selector(f'[href*="{url}"]'), url

    @property
    def message(self) -> WebElement:
        return self.driver.find_element_by_id("message")

    @property
    def panels(self) -> List[WebElement]:
        return self.driver.find_elements_by_class_name("panel-body")