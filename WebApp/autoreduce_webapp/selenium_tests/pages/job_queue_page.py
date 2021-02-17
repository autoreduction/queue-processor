# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module for the job queue page model
"""
from selenium_tests.pages.component_mixins.footer_mixin import FooterMixin
from selenium_tests.pages.component_mixins.navbar_mixin import NavbarMixin
from selenium_tests.pages.page import Page


class JobQueuePage(Page, NavbarMixin, FooterMixin):
    """
    Page model class for job queue page
    """
    @staticmethod
    def url_path():
        """
        Return the path section of the job queue url
        :return: (str) Path section of the page url
        """
        return "/runs/queue/"
