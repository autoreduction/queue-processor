# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for the help page model
"""
from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.page import Page


class HelpPage(Page, NavbarMixin, FooterMixin):
    """
    Page model class for help page
    """
    @staticmethod
    def url_path():
        """
        Return the path section of the help page
        :return: (str) Path section of the page url
        """
        return "/help/"
