# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

import tempfile

from selenium_tests.pages.rerun_jobs_page import RerunJobsPage
from selenium_tests.tests.base_tests import (BaseTestCase, FooterTestMixin, NavbarTestMixin, AccessibilityTestMixin)
from selenium_tests.utils import submit_and_wait_for_result

from WebApp.autoreduce_webapp.selenium_tests.utils import setup_external_services

TEMP_OUT_FILE = tempfile.NamedTemporaryFile()
SCRIPT = f"""
import sys
import os

sys.path.append(os.path.dirname(__file__))

import reduce_vars as web_var

def main(input_file, output_dir):
    with open("{TEMP_OUT_FILE.name}", 'w+') as file:
        file.write("\\n".join([str(var) for var in web_var.standard_vars.items()]))
"""


class TestRerunJobsPageIntegrationMultiVar(BaseTestCase, NavbarTestMixin, FooterTestMixin, AccessibilityTestMixin):
    fixtures = BaseTestCase.fixtures + ["run_with_multiple_variables"]

    accessibility_test_ignore_rules = {
        # https://github.com/ISISScientificComputing/autoreduce/issues/1267
        "duplicate-id-aria": "input",
    }

    @classmethod
    def setUpClass(cls):
        """Starts external services and sets instrument for all test cases"""
        super().setUpClass()
        cls.instrument_name = "TestInstrument"
        cls.data_archive, cls.database_client, cls.queue_client, cls.listener = setup_external_services(
            cls.instrument_name, 21, 21)
        cls.data_archive.add_reduction_script(cls.instrument_name, SCRIPT)
        cls.data_archive.add_reduce_vars_script(
            cls.instrument_name, """standard_vars={"variable_str":"test_variable_value_123",
                                                "variable_int":123, "variable_float":123.321,
                                                "variable_listint":[1,2,3], "variable_liststr":["a","b","c"],
                                                "variable_none":None, "variable_empty":""}""")
        cls.instrument_name = "TestInstrument"
        cls.rb_number = 1234567
        cls.run_number = 99999

    @classmethod
    def tearDownClass(cls) -> None:
        """Stops external services."""
        cls.queue_client.disconnect()
        cls.database_client.disconnect()
        cls.data_archive.delete()
        super().tearDownClass()

    def setUp(self) -> None:
        """Sets up RerunJobsPage before each test case"""
        super().setUp()
        self.page = RerunJobsPage(self.driver, self.instrument_name)
        self.page.launch()

    def test_variables_appear_as_expected(self):
        """
        Test: Just opening the submit page and clicking rerun
        """
        assert self.page.variable_str_field_val == "value1"
        assert self.page.variable_int_field_val == "123"
        assert self.page.variable_float_field_val == "123.321"
        assert self.page.variable_listint_field_val == "[1, 2, 3]"
        assert self.page.variable_liststr_field_val == "['a', 'b', 'c']"
        assert self.page.variable_none_field_val == "None"

    def test_submit_rerun_same_variables(self):
        """
        Test: Just opening the submit page and clicking rerun
        """
        result = submit_and_wait_for_result(self)
        assert len(result) == 2

        assert result[0].run_version == 0
        assert result[1].run_version == 1

        for run0_var, run1_var in zip(result[0].run_variables.all(), result[1].run_variables.all()):
            assert run0_var.variable == run1_var.variable

    def test_submit_rerun_changed_variable_arbitrary_value(self):
        """
        Test: Open submit page, change a variable, submit the run
        """
        new_str_value = "the new value in the field"
        self.page.variable_str_field = new_str_value
        new_int = "42"
        self.page.variable_int_field = new_int
        new_float = "144.33"
        self.page.variable_float_field = new_float
        new_listint = "[111, 222]"
        self.page.variable_listint_field = new_listint
        new_liststr = "['string1', 'string2']"
        self.page.variable_liststr_field = new_liststr

        result = submit_and_wait_for_result(self)
        assert len(result) == 2

        assert result[0].run_version == 0
        assert result[1].run_version == 1

        for run0_var, run1_var in zip(result[0].run_variables.all(), result[1].run_variables.all()):
            # the value of the variable has been overwritten because it's the same run number
            assert run0_var.variable == run1_var.variable

        run_vars = result[1].run_variables.all()
        assert run_vars[0].variable.value == new_str_value
        assert run_vars[1].variable.value == new_int
        assert run_vars[2].variable.value == new_float
        assert run_vars[3].variable.value == new_listint
        assert run_vars[4].variable.value == new_liststr
        assert run_vars[5].variable.value == "None"
        assert run_vars[6].variable.value == ""

        with open(TEMP_OUT_FILE.name, 'r') as fil:
            contents = fil.read()

        for runvar in run_vars:
            assert runvar.variable.name in contents
            assert runvar.variable.value in contents
