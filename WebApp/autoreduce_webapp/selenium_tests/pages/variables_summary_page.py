# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

from typing import List, Tuple

from django.urls import reverse
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.component_mixins.tour_mixin import TourMixin
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
        """Return the current_variables_by_run panel"""
        return self.driver.find_element_by_id("current_variables_by_run")

    @property
    def upcoming_variables_by_run(self) -> WebElement:
        """Return the upcoming_variables_by_run panel"""
        return self.driver.find_element_by_id("upcoming_variables_by_run")

    @property
    def upcoming_variables_by_experiment(self) -> WebElement:
        """Return the upcoming_variables_by_experiment panel"""
        return self.driver.find_element_by_id("upcoming_variables_by_experiment")

    def click_run_edit_button_for(self, start: int, end: int):
        """
        Clicks the edit button for the given run start and end
        :param start: The start run
        :param end: The end run
        :return: The edit button
        """
        url = reverse("instrument:variables", kwargs={"instrument": self.instrument, "start": start, "end": end})
        button = self.driver.find_element_by_css_selector(f'[href*="{url}"]')

        def button_clicked_successfully(driver):
            button.click()
            return url in driver.current_url

        WebDriverWait(self.driver, 10).until(button_clicked_successfully)

    def click_run_delete_button_for(self, start: int, end: int):
        """
        Clicks the delete button for the given run start and run end
        :param start: The start run
        :param end: The end run
        :return: The delete button
        """
        url = reverse("instrument:delete_variables", kwargs={"instrument": self.instrument, "start": start, "end": end})
        button = self.driver.find_element_by_css_selector(f'[href*="{url}"]')

        def button_clicked_successfully(_):
            try:
                button.click()
                return False
            except StaleElementReferenceException:
                return True

        WebDriverWait(self.driver, 10).until(button_clicked_successfully)

    def experiment_edit_button_for(self, experiment_reference: int) -> Tuple[WebElement, str]:
        """
        Get the edit button for the given experiment reference
        :param experiment_reference: The experiment reference
        :return: The edit button
        """
        url = reverse("instrument:variables_by_experiment",
                      kwargs={
                          "instrument": self.instrument,
                          "experiment_reference": experiment_reference
                      })
        return self.driver.find_element_by_css_selector(f'[href*="{url}"]'), url

    def experiment_delete_button_for(self, experiment_reference: int) -> Tuple[WebElement, str]:
        """
        Get the delete button for the given experiment reference
        :param experiment_reference: The experiment refence
        :return: The delete button
        """
        url = reverse("instrument:delete_variables_by_experiment",
                      kwargs={
                          "instrument": self.instrument,
                          "experiment_reference": experiment_reference
                      })
        return self.driver.find_element_by_css_selector(f'[href*="{url}"]'), url

    @property
    def message(self) -> WebElement:
        """Return the message"""
        return self.driver.find_element_by_id("message")

    @property
    def panels(self) -> List[WebElement]:
        """Return the variable summary panels"""
        return self.driver.find_elements_by_class_name("panel-body")
