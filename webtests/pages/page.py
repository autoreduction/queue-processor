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

from webtests import configuration


class Page(ABC):
    """
    Abstract base class for page object model classes
    """
    def __init__(self, driver):
        self.driver = driver

    @staticmethod
    @abstractmethod
    def url_path():
        """
        Abstract method to return the path section of the page URL
        """

    @classmethod
    def url(cls):
        """
        Return the URL of the page object
        :return: (str) The url of the page object
        """
        return configuration.get_url() + cls.url_path()

    def launch(self):
        """
        Navigate the webdriver to this page
        :return: The page object
        """
        self.driver.get(self.url())
        return self
