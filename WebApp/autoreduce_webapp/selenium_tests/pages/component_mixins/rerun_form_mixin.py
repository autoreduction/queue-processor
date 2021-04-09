# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

from selenium.webdriver.remote.webelement import WebElement


class RerunFormMixin:
    @staticmethod
    def _set_field(field, value):
        field.clear()
        new_value = value
        field.send_keys(new_value)

    @property
    def cancel_button(self) -> WebElement:
        """
        Finds and returns the back button for toggling the form on the page.
        """
        return self.driver.find_element_by_id("cancel")

    @property
    def submit_button(self) -> WebElement:
        """
        Finds and returns the back button for toggling the form on the page.
        """
        return self.driver.find_element_by_id("variableSubmit")

    @property
    def variable1_field(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable1")

    @property
    def variable1_field_val(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable1").get_attribute("value")

    @variable1_field.setter
    def variable1_field(self, value) -> None:
        """
        Clears the field and sends the keys to the input field.

        Selenium requires that we clear the field first!
        """
        self._set_field(self.variable1_field, value)
