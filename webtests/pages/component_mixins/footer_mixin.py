# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module containing the footer mixin
"""


class FooterMixin:
    """
    Footer mixin contains functionality for the page footer when inherited
    """
    FOOTER_ID = "footer"
    HELP_LINK_ID = "footer-help"
    GITHUB_LINK_ID = "footer-github"
    SUPPORT_EMAIL_LINK_ID = "footer-email"

    def is_footer_visible(self):
        """
        Checks whether the footer is visible
        :returns: (bool) True if footer is visible, otherwise False
        """
        return self.driver.find_element_by_id(self.FOOTER_ID).is_displayed()

    def click_footer_help_link(self):
        """
        Clicks the help link in the footer
        """
        help_link = self.driver.find_element_by_id(self.HELP_LINK_ID)
        help_link.click()
        return self

    def click_footer_github_link(self):
        """
        Clicks the github link in the footer
        """
        github_link = self.driver.find_element_by_id(self.GITHUB_LINK_ID)
        github_link.click()
        return self

    def is_footer_email_visible(self):
        """
        Check if the support email is visible within the header
        :return: (bool) True if visible, otherwise False
        """
        return self.driver.find_element_by_id(self.SUPPORT_EMAIL_LINK_ID).is_displayed()
