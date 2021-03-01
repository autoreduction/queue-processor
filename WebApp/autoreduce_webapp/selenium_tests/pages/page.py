# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module containing the base Page object class
"""
from abc import ABC, abstractmethod

from selenium_tests import configuration


class Page(ABC):
    """
    Abstract base class for page object model classes
    """
    def __init__(self, driver):
        self.driver = driver

    @abstractmethod
    def url_path(self):
        """
        Abstract method to return the path section of the page URL
        """

    def url(self):
        """
        Return the URL of the page object
        :return: (str) The url of the page object
        """
        return configuration.get_url() + self.url_path()

    def launch(self):
        """
        Navigate the webdriver to this page
        :return: The page object
        """
        self.driver.get(configuration.get_url())
        self.driver.get(self.url())
        return self

    def get_id(self, id_str: str):
        return self.driver.find_element_by_id(id_str)
