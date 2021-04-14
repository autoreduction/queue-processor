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

    @property
    def variable_str_field(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable_str")

    @property
    def variable_str_field_val(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable_str").get_attribute("value")

    @variable_str_field.setter
    def variable_str_field(self, value) -> None:
        """
        Clears the field and sends the keys to the input field.

        Selenium requires that we clear the field first!
        """
        self._set_field(self.variable_str_field, value)

    @property
    def variable_int_field(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable_int")

    @property
    def variable_int_field_val(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable_int").get_attribute("value")

    @variable_int_field.setter
    def variable_int_field(self, value) -> None:
        """
        Clears the field and sends the keys to the input field.

        Selenium requires that we clear the field first!
        """
        self._set_field(self.variable_int_field, value)

    @property
    def variable_float_field(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable_float")

    @property
    def variable_float_field_val(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable_float").get_attribute("value")

    @variable_float_field.setter
    def variable_float_field(self, value) -> None:
        """
        Clears the field and sends the keys to the input field.

        Selenium requires that we clear the field first!
        """
        self._set_field(self.variable_float_field, value)

    @property
    def variable_listint_field(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable_listint")

    @property
    def variable_listint_field_val(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable_listint").get_attribute("value")

    @variable_listint_field.setter
    def variable_listint_field(self, value) -> None:
        """
        Clears the field and sends the keys to the input field.

        Selenium requires that we clear the field first!
        """
        self._set_field(self.variable_listint_field, value)

    @property
    def variable_liststr_field(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable_liststr")

    @property
    def variable_liststr_field_val(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable_liststr").get_attribute("value")

    @variable_liststr_field.setter
    def variable_liststr_field(self, value) -> None:
        """
        Clears the field and sends the keys to the input field.

        Selenium requires that we clear the field first!
        """
        self._set_field(self.variable_liststr_field, value)

    @property
    def variable_none_field(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable_none")

    @property
    def variable_none_field_val(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable_none").get_attribute("value")

    @variable_none_field.setter
    def variable_none_field(self, value) -> None:
        """
        Clears the field and sends the keys to the input field.

        Selenium requires that we clear the field first!
        """
        self._set_field(self.variable_none_field, value)

    @property
    def variable_empty_field(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable_empty")

    @property
    def variable_empty_field_val(self) -> WebElement:
        """
        Finds and returns the variabl1 input field
        """
        return self.driver.find_element_by_id("var-standard-variable_empty").get_attribute("value")

    @variable_empty_field.setter
    def variable_empty_field(self, value) -> None:
        """
        Clears the field and sends the keys to the input field.

        Selenium requires that we clear the field first!
        """
        self._set_field(self.variable_empty_field, value)
