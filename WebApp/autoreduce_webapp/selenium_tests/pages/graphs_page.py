# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for the graphs page model
"""
from selenium_tests.pages.page import Page


class GraphsPage(Page):
    """
    Page model class for graphs page
    """

    @staticmethod
    def url_path():
        """
        Return the path section of the graphs url
        :return: (str) Path section of the page url
        """
        return "/graph/"
