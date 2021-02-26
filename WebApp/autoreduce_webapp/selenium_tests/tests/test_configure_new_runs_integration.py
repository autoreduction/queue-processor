# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #

import time
from selenium_tests.pages.variables_summary_page import VariableSummaryPage

from selenium_tests.tests.base_tests import NavbarTestMixin, BaseTestCase, FooterTestMixin
from model.database import access as db
from instrument.models import InstrumentVariable
from systemtests.utils.data_archive import DataArchive
from queue_processors.queue_processor.queue_listener import main
from utils.clients.connection_exception import ConnectionException
from utils.clients.django_database_client import DatabaseClient
from selenium_tests.pages.configure_new_runs_page import ConfigureNewRunsPage
from selenium.common.exceptions import NoSuchElementException

REDUCE_VARS_DEFAULT_VALUE = "default value from reduce_vars"


class TestConfigureNewRunsPageIntegration(BaseTestCase):

    fixtures = BaseTestCase.fixtures + ["run_with_one_variable"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.instrument_name = "TestInstrument"
        cls.data_archive = DataArchive([cls.instrument_name], 21, 21)
        cls.data_archive.create()
        cls.data_archive.add_reduction_script(cls.instrument_name, """print('some text')""")
        cls.data_archive.add_reduce_vars_script(cls.instrument_name,
                                                f"""standard_vars={{"variable1":"{REDUCE_VARS_DEFAULT_VALUE}"}}""")
        cls.database_client = DatabaseClient()
        cls.database_client.connect()
        try:
            cls.queue_client, cls.listener = main()
        except ConnectionException as err:
            raise RuntimeError("Could not connect to ActiveMQ - check you credentials. If running locally check that "
                               "ActiveMQ is running and started by `python setup.py start`") from err

        cls.instrument_name = "TestInstrument"
        cls.rb_number = 1234567
        cls.run_number = 99999

    @classmethod
    def tearDownClass(cls) -> None:
        cls.queue_client.disconnect()
        cls.database_client.disconnect()
        cls.data_archive.delete()
        super().tearDownClass()

    def _find_run_in_database(self):
        """
        Find a ReductionRun record in the database
        This includes a timeout to wait for several seconds to ensure the database has received
        the record in question
        :return: The resulting record
        """
        instrument = db.get_instrument(self.instrument_name)
        return instrument.reduction_runs.filter(run_number=self.run_number)

    def wait_for_result(self):
        """Waits until the queue listener has finished processing the current message"""
        # forces the is_processing to return True so that the listener has time to actually start processing the message
        self.listener._processing = True  #pylint:disable=protected-access
        while self.listener.is_processing_message():
            time.sleep(0.5)

        # Get Result from database
        results = self._find_run_in_database()

        assert results
        return results

    def _submit_var_value(self, value, start=None, end=None, experiment_number=None):
        self.page = ConfigureNewRunsPage(self.driver,
                                         self.instrument_name,
                                         run_start=start,
                                         run_end=end,
                                         experiment_reference=experiment_number)
        self.page.launch()
        self.page.variable1_field = value
        self.page.submit_button.click()

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
        assert new_var.start_run == self.run_number + 1
        assert new_var.value == "new_value"

        summary = VariableSummaryPage(self.driver, self.instrument_name)
        assert summary.current_variables_by_run.is_displayed()
        assert summary.upcoming_variables_by_run.is_displayed()

        with self.assertRaises(NoSuchElementException):
            summary.upcoming_variables_by_experiment.is_displayed()

    def test_submit_experiment_var(self):
        self._submit_var_value("new_value", experiment_number=self.rb_number)

        assert InstrumentVariable.objects.count() == 2
        new_var = InstrumentVariable.objects.last()
        assert new_var.start_run is None
        assert new_var.experiment_reference == self.rb_number
        assert new_var.value == "new_value"

        summary = VariableSummaryPage(self.driver, self.instrument_name)
        assert summary.current_variables_by_run.is_displayed()
        assert summary.upcoming_variables_by_experiment.is_displayed()

        with self.assertRaises(NoSuchElementException):
            summary.upcoming_variables_by_run.is_displayed()

    def test_submit_multiple_run_ranges(self):
        """Test submitting variables for multiple run ranges, and that they show up correctly in 'see instrument variablers'"""
        self._submit_var_value("new_value", self.run_number + 1)
        self._submit_var_value("the newest value", self.run_number + 101)

        assert InstrumentVariable.objects.count() == 3
        first_var, second_var, third_var = InstrumentVariable.objects.all()
        assert first_var.start_run == self.run_number
        assert first_var.experiment_reference is None
        assert first_var.value == "value1"

        assert second_var.start_run == self.run_number + 1
        assert second_var.experiment_reference is None
        assert second_var.value == "new_value"

        assert third_var.start_run == self.run_number + 101
        assert third_var.experiment_reference is None
        assert third_var.value == "the newest value"

        summary = VariableSummaryPage(self.driver, self.instrument_name)
        assert summary.current_variables_by_run.is_displayed()
        assert summary.upcoming_variables_by_run.is_displayed()

        with self.assertRaises(NoSuchElementException):
            assert summary.upcoming_variables_by_experiment.is_displayed()

    def test_submit_multiple_run_ranges_with_ends(self):
        """Test submitting variables for multiple run ranges, and that they show up correctly in 'see instrument variablers'"""
        self._submit_var_value("new_value", self.run_number + 1, self.run_number + 101)
        self._submit_var_value("the newest value", self.run_number + 201, self.run_number + 401)

        assert InstrumentVariable.objects.count() == 5
        first_var, second_var, third_var, fourth_var, fifth_var = InstrumentVariable.objects.all()
        assert first_var.start_run == self.run_number
        assert first_var.experiment_reference is None
        assert first_var.value == "value1"

        assert second_var.start_run == self.run_number + 1
        assert second_var.experiment_reference is None
        assert second_var.value == "new_value"

        assert third_var.start_run == self.run_number + 102
        assert third_var.experiment_reference is None
        assert third_var.value == REDUCE_VARS_DEFAULT_VALUE  # back to the default value from the reduce_vars!

        assert fourth_var.start_run == self.run_number + 201
        assert fourth_var.experiment_reference is None
        assert fourth_var.value == "the newest value"

        assert fifth_var.start_run == self.run_number + 402
        assert fifth_var.experiment_reference is None
        assert fifth_var.value == REDUCE_VARS_DEFAULT_VALUE  # back to the default value from the reduce_vars!

    def test_submit_multiple_experiments(self):
        """Test submitting vars for multiple experiments"""
        self._submit_var_value("new_value", experiment_number=self.rb_number)
        self._submit_var_value("the newest value", experiment_number=self.rb_number + 100)

        assert InstrumentVariable.objects.count() == 3
        first_var, second_var, third_var = InstrumentVariable.objects.all()
        assert first_var.start_run == self.run_number
        assert first_var.experiment_reference is None
        assert first_var.value == "value1"

        assert second_var.start_run is None
        assert second_var.experiment_reference == self.rb_number
        assert second_var.value == "new_value"

        assert third_var.start_run is None
        assert third_var.experiment_reference == self.rb_number + 100
        assert third_var.value == "the newest value"

        summary = VariableSummaryPage(self.driver, self.instrument_name)
        assert summary.current_variables_by_run.is_displayed()
        assert summary.upcoming_variables_by_experiment.is_displayed()

        with self.assertRaises(NoSuchElementException):
            summary.upcoming_variables_by_run.is_displayed()

    def test_submit_multiple_run_ranges_and_then_experiment(self):
        """Test submitting both run range vars and experiment vars"""
        self._submit_var_value("new_value", self.run_number + 1, self.run_number + 101)
        self._submit_var_value("the newest value", self.run_number + 201, self.run_number + 401)
        self._submit_var_value("some value for experiment", experiment_number=self.rb_number)
        self._submit_var_value("some different value for experiment", experiment_number=self.rb_number + 100)

        assert InstrumentVariable.objects.count() == 7
        first_var, second_var, third_var, fourth_var, fifth_var, exp_var1, exp_var2 = InstrumentVariable.objects.all()

        assert first_var.start_run == self.run_number
        assert first_var.experiment_reference is None
        assert first_var.value == "value1"

        assert second_var.start_run == self.run_number + 1
        assert second_var.experiment_reference is None
        assert second_var.value == "new_value"

        assert third_var.start_run == self.run_number + 102
        assert third_var.experiment_reference is None
        assert third_var.value == REDUCE_VARS_DEFAULT_VALUE  # back to the default value from the reduce_vars!

        assert fourth_var.start_run == self.run_number + 201
        assert fourth_var.experiment_reference is None
        assert fourth_var.value == "the newest value"

        assert fifth_var.start_run == self.run_number + 402
        assert fifth_var.experiment_reference is None
        assert fifth_var.value == REDUCE_VARS_DEFAULT_VALUE  # back to the default value from the reduce_vars!

        assert exp_var1.start_run is None
        assert exp_var1.experiment_reference == self.rb_number
        assert exp_var1.value == "some value for experiment"

        assert exp_var2.start_run is None
        assert exp_var2.experiment_reference == self.rb_number + 100
        assert exp_var2.value == "some different value for experiment"

        summary = VariableSummaryPage(self.driver, self.instrument_name)
        assert summary.current_variables_by_run.is_displayed()
        assert summary.upcoming_variables_by_experiment.is_displayed()
        assert summary.upcoming_variables_by_run.is_displayed()

    def test_submit_then_edit_then_delete_run_vars(self):
        self._submit_var_value("new_value", self.run_number + 1, self.run_number + 101)
        self._submit_var_value("the newest value", self.run_number + 201, self.run_number + 401)

        summary = VariableSummaryPage(self.driver, self.instrument_name)

        summary.run_edit_button_for(self.run_number + 1, self.run_number + 101)[0].click()

        self.page.variable1_field = "a new test value 123"
        self.page.submit_button.click()
        self.page.replace_confirm.click()

        upcoming_panel = summary.panels[1]

        assert "new_value" not in upcoming_panel.get_attribute("textContent")
        assert "a new test value 123" in upcoming_panel.get_attribute("textContent")

        summary.run_delete_button_for(self.run_number + 1, self.run_number + 101)[0].click()

        upcoming_panel = summary.panels[1]
        assert "a new test value 123" not in upcoming_panel.get_attribute("textContent")

        incoming_run_numbers = upcoming_panel.find_elements_by_class_name("run-numbers")

        assert "100101" in incoming_run_numbers[0].text
        assert "100199" in incoming_run_numbers[0].text
        assert "100200" in incoming_run_numbers[1].text
        assert "100400" in incoming_run_numbers[1].text
        assert "100401" in incoming_run_numbers[2].text
        assert "Ongoing" in incoming_run_numbers[2].text

        # now for the 2nd variable we made
        summary.run_edit_button_for(self.run_number + 201, self.run_number + 401)[0].click()
        self.page.variable1_field = "another new test value 321"
        self.page.submit_button.click()

        upcoming_panel = summary.panels[1]

        assert "new_value" not in upcoming_panel.get_attribute("textContent")
        assert "another new test value 321" in upcoming_panel.get_attribute("textContent")

        summary.run_delete_button_for(self.run_number + 201, self.run_number + 401)[0].click()

        upcoming_panel = summary.panels[1]
        assert "another new test value 321" not in upcoming_panel.get_attribute("textContent")

        incoming_run_numbers = upcoming_panel.find_elements_by_class_name("run-numbers")

        # there's a few leftover default variables, but that's OK because the user can remove them
        assert "100101" in incoming_run_numbers[0].text
        assert "100400" in incoming_run_numbers[0].text
        assert "100401" in incoming_run_numbers[1].text
        assert "Ongoing" in incoming_run_numbers[1].text

    def test_submit_then_edit_then_delete_experiment_vars(self):
        self._submit_var_value("new_value", experiment_number=1234567)
        self._submit_var_value("the newest value", experiment_number=2345678)
        summary = VariableSummaryPage(self.driver, self.instrument_name)
        summary.experiment_edit_button_for(1234567)[0].click()

        self.page.variable1_field = "a new test value 123"
        self.page.submit_button.click()

        experiment_panel = summary.panels[1]

        assert "new_value" not in experiment_panel.get_attribute("textContent")
        assert "a new test value 123" in experiment_panel.get_attribute("textContent")

        summary.experiment_delete_button_for(1234567)[0].click()

        experiment_panel = summary.panels[1]
        incoming_exp_numbers = experiment_panel.find_elements_by_class_name("run-numbers")

        assert "2345678" in incoming_exp_numbers[0].text

        summary.experiment_edit_button_for(2345678)[0].click()

        self.page.variable1_field = "a new value for experiment 2345678"
        self.page.submit_button.click()

        experiment_panel = summary.panels[1]

        assert "the newest value" not in experiment_panel.get_attribute("textContent")
        assert "a new value for experiment 2345678" in experiment_panel.get_attribute("textContent")

        summary.experiment_delete_button_for(2345678)[0].click()

        # only the current variables panel left
        assert len(summary.panels) == 1
        assert "Runs\n99999\nOngoing\nvariable1: value1" in summary.panels[0].text
