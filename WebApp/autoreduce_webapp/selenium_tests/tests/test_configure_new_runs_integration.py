# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

from selenium.common.exceptions import NoSuchElementException
from selenium_tests.pages.configure_new_runs_page import ConfigureNewRunsPage
from selenium_tests.pages.variables_summary_page import VariableSummaryPage
from selenium_tests.tests.base_tests import (BaseTestCase, FooterTestMixin, NavbarTestMixin, AccessibilityTestMixin)

from instrument.models import InstrumentVariable
from model.database import access as db
from WebApp.autoreduce_webapp.selenium_tests.utils import \
    setup_external_services

REDUCE_VARS_DEFAULT_VALUE = "default value from reduce_vars"


class TestConfigureNewRunsPageIntegration(NavbarTestMixin, BaseTestCase, FooterTestMixin, AccessibilityTestMixin):
    fixtures = BaseTestCase.fixtures + ["run_with_one_variable"]

    accessibility_test_ignore_rules = {
        # https://github.com/ISISScientificComputing/autoreduce/issues/790
        "color-contrast": "*",

        # https://github.com/ISISScientificComputing/autoreduce/issues/1267
        "duplicate-id-aria": "input",
    }

    @classmethod
    def setUpClass(cls):
        """
        Sets up the Datarchive complete with scripts, the database client and checks the queue client and listerner
        are running for all testcases
        """
        super().setUpClass()
        cls.instrument_name = "TestInstrument"
        cls.data_archive, cls.database_client, cls.queue_client, cls.listener = setup_external_services(
            cls.instrument_name, 21, 21)
        cls.data_archive.add_reduction_script(cls.instrument_name, """print('some text')""")
        cls.data_archive.add_reduce_vars_script(cls.instrument_name,
                                                f"""standard_vars={{"variable1":"{REDUCE_VARS_DEFAULT_VALUE}"}}""")
        cls.rb_number = 1234567
        cls.run_number = 99999

    @classmethod
    def tearDownClass(cls) -> None:
        """
        Destroys the created data-archive and disconnects the database and queue clients
        """
        cls.queue_client.disconnect()
        cls.database_client.disconnect()
        cls.data_archive.delete()
        super().tearDownClass()

    def setUp(self) -> None:
        """Sets up the ConfigureNewRunsPage before each test case"""
        super().setUp()
        self.page = ConfigureNewRunsPage(self.driver, self.instrument_name, run_start=self.run_number + 1)

    def _find_run_in_database(self):
        """
        Find a ReductionRun record in the database
        This includes a timeout to wait for several seconds to ensure the database has received
        the record in question
        :return: The resulting record
        """
        instrument = db.get_instrument(self.instrument_name)
        return instrument.reduction_runs.filter(run_number=self.run_number)

    def _submit_var_value(self, value, start=None, experiment_number=None):
        self.page = ConfigureNewRunsPage(self.driver,
                                         self.instrument_name,
                                         run_start=start,
                                         experiment_reference=experiment_number)
        self.page.launch()
        self.page.variable1_field = value
        self.page.submit_button.click()

    @staticmethod
    def assert_expected_var(var: InstrumentVariable, expected_run_number, expected_reference, expected_value):
        """
        Assert that a var has the expected values
        :param var: The var to check
        :param expected_run_number: The expected run_number
        :param expected_reference: The expected reference
        :param expected_value: The expected var value
        """
        if expected_run_number is not None:
            assert var.start_run == expected_run_number
        else:
            assert var.start_run is None
        if expected_reference is not None:
            assert var.experiment_reference == expected_reference
        else:
            assert var.experiment_reference is None
        assert var.value == expected_value

    def test_submit_submit_same_variables_does_not_add_new_variables(self):
        """
        Test: Just opening the submit page and clicking rerun
        """
        self.page = ConfigureNewRunsPage(self.driver, self.instrument_name, run_start=self.run_number + 1)
        self.page.launch()
        self.page.submit_button.click()
        assert InstrumentVariable.objects.count() == 1

        summary = VariableSummaryPage(self.driver, self.instrument_name)
        assert summary.current_variables_by_run.is_displayed()

        with self.assertRaises(NoSuchElementException):
            summary.upcoming_variables_by_run.is_displayed()
        with self.assertRaises(NoSuchElementException):
            summary.upcoming_variables_by_experiment.is_displayed()

    def test_submit_new_value(self):
        """
        Test: Just opening the submit page and clicking rerun
        """
        self._submit_var_value("new_value", self.run_number + 1)
        assert InstrumentVariable.objects.count() == 2
        new_var = InstrumentVariable.objects.last()
        self.assert_expected_var(new_var, self.run_number + 1, None, "new_value")

        summary = VariableSummaryPage(self.driver, self.instrument_name)
        assert summary.current_variables_by_run.is_displayed()
        assert summary.upcoming_variables_by_run.is_displayed()

        with self.assertRaises(NoSuchElementException):
            summary.upcoming_variables_by_experiment.is_displayed()

    def test_submit_experiment_var(self):
        """Tests the functionality foe submitting a new variable for an experiment"""
        self._submit_var_value("new_value", experiment_number=self.rb_number)

        assert InstrumentVariable.objects.count() == 2
        new_var = InstrumentVariable.objects.last()
        self.assert_expected_var(new_var, None, self.rb_number, "new_value")

        summary = VariableSummaryPage(self.driver, self.instrument_name)
        assert summary.current_variables_by_run.is_displayed()
        assert summary.upcoming_variables_by_experiment.is_displayed()

        with self.assertRaises(NoSuchElementException):
            summary.upcoming_variables_by_run.is_displayed()

    def test_submit_multiple_run_ranges(self):
        """
        Test submitting variables for multiple run ranges, and that they show up correctly
        in 'see instrument variables'
        """
        self._submit_var_value("new_value", self.run_number + 1)
        self._submit_var_value("the newest value", self.run_number + 101)

        assert InstrumentVariable.objects.count() == 3
        first_var, second_var, third_var = InstrumentVariable.objects.all()
        self.assert_expected_var(first_var, self.run_number, None, "value1")
        self.assert_expected_var(second_var, self.run_number + 1, None, "new_value")
        self.assert_expected_var(third_var, self.run_number + 101, None, "the newest value")

        summary = VariableSummaryPage(self.driver, self.instrument_name)
        assert summary.current_variables_by_run.is_displayed()
        assert summary.upcoming_variables_by_run.is_displayed()

        with self.assertRaises(NoSuchElementException):
            assert summary.upcoming_variables_by_experiment.is_displayed()

    def test_submit_multiple_run_ranges_with_ends(self):
        """
        Test submitting variables for multiple run ranges, and that they show up correctly
        in 'see instrument variablers'
        """
        self._submit_var_value("new_value", self.run_number + 1)
        self._submit_var_value("the newest value", self.run_number + 201)

        assert InstrumentVariable.objects.count() == 3
        first_var, second_var, fourth_var = InstrumentVariable.objects.all()
        self.assert_expected_var(first_var, self.run_number, None, "value1")
        self.assert_expected_var(second_var, self.run_number + 1, None, "new_value")
        self.assert_expected_var(fourth_var, self.run_number + 201, None, "the newest value")

    def test_submit_multiple_experiments(self):
        """Test submitting vars for multiple experiments"""
        self._submit_var_value("new_value", experiment_number=self.rb_number)
        self._submit_var_value("the newest value", experiment_number=self.rb_number + 100)

        assert InstrumentVariable.objects.count() == 3
        first_var, second_var, third_var = InstrumentVariable.objects.all()
        self.assert_expected_var(first_var, self.run_number, None, "value1")
        self.assert_expected_var(second_var, None, self.rb_number, "new_value")
        self.assert_expected_var(third_var, None, self.rb_number + 100, "the newest value")

        summary = VariableSummaryPage(self.driver, self.instrument_name)
        assert summary.current_variables_by_run.is_displayed()
        assert summary.upcoming_variables_by_experiment.is_displayed()

        with self.assertRaises(NoSuchElementException):
            summary.upcoming_variables_by_run.is_displayed()

    def test_submit_multiple_run_ranges_and_then_experiment(self):
        """Test submitting both run range vars and experiment vars"""
        self._submit_var_value("new_value", self.run_number + 1)
        self._submit_var_value("the newest value", self.run_number + 201)
        self._submit_var_value("some value for experiment", experiment_number=self.rb_number)
        self._submit_var_value("some different value for experiment", experiment_number=self.rb_number + 100)

        assert InstrumentVariable.objects.count() == 5
        first_var, second_var, fourth_var, exp_var1, exp_var2 = InstrumentVariable.objects.all()

        self.assert_expected_var(first_var, self.run_number, None, "value1")
        self.assert_expected_var(second_var, self.run_number + 1, None, "new_value")
        self.assert_expected_var(fourth_var, self.run_number + 201, None, "the newest value")
        self.assert_expected_var(exp_var1, None, self.rb_number, "some value for experiment")
        self.assert_expected_var(exp_var2, None, self.rb_number + 100, "some different value for experiment")

        summary = VariableSummaryPage(self.driver, self.instrument_name)
        assert summary.current_variables_by_run.is_displayed()
        assert summary.upcoming_variables_by_experiment.is_displayed()
        assert summary.upcoming_variables_by_run.is_displayed()

    def test_submit_then_edit_then_delete_run_vars(self):
        """Test submitting new variables for run ranges, then editing them, then deleting them"""
        self._submit_var_value("new_value", self.run_number + 1)
        self._submit_var_value("the newest value", self.run_number + 101)
        self._submit_var_value("value for 201", self.run_number + 201)
        self._submit_var_value("value for 301", self.run_number + 301)

        summary = VariableSummaryPage(self.driver, self.instrument_name)

        summary.click_run_edit_button_for(self.run_number + 1, self.run_number + 100)

        self.page.variable1_field = "a new test value 123"
        self.page.submit_button.click()
        self.page.replace_confirm.click()

        upcoming_panel = summary.panels[1]

        assert "new_value" not in upcoming_panel.get_attribute("textContent")
        assert "a new test value 123" in upcoming_panel.get_attribute("textContent")

        summary.click_run_delete_button_for(self.run_number + 1, self.run_number + 100)

        upcoming_panel = summary.panels[1]
        assert "a new test value 123" not in upcoming_panel.get_attribute("textContent")

        incoming_run_numbers = upcoming_panel.find_elements_by_class_name("run-numbers")

        assert "100100" in incoming_run_numbers[0].text
        assert "100199" in incoming_run_numbers[0].text
        assert "100200" in incoming_run_numbers[1].text
        assert "100299" in incoming_run_numbers[1].text
        assert "100300" in incoming_run_numbers[2].text
        assert "Ongoing" in incoming_run_numbers[2].text

        # now for the 2nd variable we made
        summary.click_run_edit_button_for(self.run_number + 201, self.run_number + 300)
        self.page.variable1_field = "another new test value 321"
        self.page.submit_button.click()
        self.page.replace_confirm.click()

        upcoming_panel = summary.panels[1]

        assert "new_value" not in upcoming_panel.get_attribute("textContent")
        assert "another new test value 321" in upcoming_panel.get_attribute("textContent")

        summary.click_run_delete_button_for(self.run_number + 201, self.run_number + 300)

        upcoming_panel = summary.panels[1]
        assert "another new test value 321" not in upcoming_panel.get_attribute("textContent")

        incoming_run_numbers = upcoming_panel.find_elements_by_class_name("run-numbers")

        # there's a few leftover default variables, but that's OK because the user can remove them
        assert "100100" in incoming_run_numbers[0].text
        assert "100299" in incoming_run_numbers[0].text
        assert "100300" in incoming_run_numbers[1].text
        assert "Ongoing" in incoming_run_numbers[1].text

    def test_submit_then_edit_then_delete_experiment_vars(self):
        """Test submitting new variables for experiment reference, then editing them, then deleting them"""
        self._submit_var_value("new_value", experiment_number=1234567)
        self._submit_var_value("the newest value", experiment_number=2345678)
        summary = VariableSummaryPage(self.driver, self.instrument_name)
        summary.click_experiment_edit_button_for(1234567)

        self.page.variable1_field = "a new test value 123"
        self.page.submit_button.click()

        experiment_panel = summary.panels[1]

        assert "new_value" not in experiment_panel.get_attribute("textContent")
        assert "a new test value 123" in experiment_panel.get_attribute("textContent")

        summary.click_experiment_delete_button_for(1234567)

        experiment_panel = summary.panels[1]
        incoming_exp_numbers = experiment_panel.find_elements_by_class_name("run-numbers")

        assert "2345678" in incoming_exp_numbers[0].text

        summary.click_experiment_edit_button_for(2345678)

        self.page.variable1_field = "a new value for experiment 2345678"
        self.page.submit_button.click()

        experiment_panel = summary.panels[1]

        assert "the newest value" not in experiment_panel.get_attribute("textContent")
        assert "a new value for experiment 2345678" in experiment_panel.get_attribute("textContent")

        summary.click_experiment_delete_button_for(2345678)

        # only the current variables panel left
        assert len(summary.panels) == 1
        assert "Runs\n99999\nOngoing\nvariable1: value1" in summary.panels[0].text
