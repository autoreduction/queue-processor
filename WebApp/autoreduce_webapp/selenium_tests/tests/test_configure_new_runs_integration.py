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
                                                """standard_vars={"variable1":"test_variable_value_123"}""")
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

    def submit_after_reset(self):
        """
        Submit after a reset button has been clicked.

        Sticks the submission in a loop in case the first time doesn't work. The reason
        it may not work is that resetting actually swaps out the whole form using JS, which
        replaces ALL the elements and triggers a bunch of DOM re-renders/updates, and that isn't fast.
        """
        page_url = self.page.url()
        while page_url in self.driver.current_url:
            # NOTE that we MUST wait first and then try to submit, otherwise the processing
            # may be finished before wait_for_result is called, causing it to be stuck forever
            time.sleep(1)
            self.page.submit_button.click()

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
        assert third_var.value == "test_variable_value_123"  # back to the default value from the reduce_vars!

        assert fourth_var.start_run == self.run_number + 201
        assert fourth_var.experiment_reference is None
        assert fourth_var.value == "the newest value"

        assert fifth_var.start_run == self.run_number + 402
        assert fifth_var.experiment_reference is None
        assert fifth_var.value == "test_variable_value_123"  # back to the default value from the reduce_vars!

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
        assert third_var.value == "test_variable_value_123"  # back to the default value from the reduce_vars!

        assert fourth_var.start_run == self.run_number + 201
        assert fourth_var.experiment_reference is None
        assert fourth_var.value == "the newest value"

        assert fifth_var.start_run == self.run_number + 402
        assert fifth_var.experiment_reference is None
        assert fifth_var.value == "test_variable_value_123"  # back to the default value from the reduce_vars!

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
