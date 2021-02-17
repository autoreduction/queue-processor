# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module containing the tour mixin
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


# pylint: disable=no-member;  We disable as pylint cannot deal with multiple Mixins, that is it will
# complain that step is missing but not driver.
class TourMixin:
    """
    TourMixin can be added to page classes to add the tour functionalities
    """
    TOUR_STEP_ID = "step-%s"
    TOUR_BUTTON_ID = "tour-btn"
    NEXT_BUTTON_XPATH = "//*[@data-role='next']"
    PREV_BUTTON_XPATH = "//*[@data-role='prev']"
    END_BUTTON_XPATH = "//*[@data-role='end']"

    def start_tour(self):
        """
        Start the tour on the page
        """
        self.driver.find_element_by_id(self.TOUR_BUTTON_ID).click()

    def is_tour_visible(self):
        """
        Checks if the tour is currently visible
        :return: (bool) True if tour is visible, False otherwise
        """
        return WebDriverWait(self.driver,
                             10).until(EC.presence_of_element_located((By.ID, self.TOUR_STEP_ID % self.step)))

    def is_tour_hidden(self):
        """
        Checks if the tour is currently hidden
        :return: (bool) True if tour is visible, False otherwise
        """
        return WebDriverWait(self.driver,
                             30).until_not(EC.presence_of_element_located((By.ID, self.TOUR_STEP_ID % self.step)))

    def next_tour_step(self):
        """
        Click the next step of the tour
        """
        self.driver.find_element_by_xpath(self.NEXT_BUTTON_XPATH).click()
        self.step += 1

    def previous_tour_step(self):
        """
        Click the previous step of the tour
        """
        self.driver.find_element_by_xpath(self.PREV_BUTTON_XPATH).click()
        self.step -= 1

    def end_tour(self):
        """
        Ends the current tour
        """
        self.driver.find_element_by_xpath(self.END_BUTTON_XPATH).click()

    def is_tour_previous_button_enabled(self):
        """
        Checks if the previous step button is currently enabled
        :return: (bool) True if button is enabled, False otherwise
        """
        return self.driver.find_element_by_xpath(self.PREV_BUTTON_XPATH).is_enabled()

    def is_tour_next_button_enabled(self):
        """
        Checks if the next step button is currently enabled
        :return: (bool) True if button is enabled, False otherwise
        """
        return self.driver.find_element_by_xpath(self.NEXT_BUTTON_XPATH).is_enabled()
