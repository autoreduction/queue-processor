from django.urls import reverse
from selenium_tests.pages.rerun_jobs_page import RerunJobsPage
from selenium_tests.tests.base_tests import (NavbarTestMixin, BaseTestCase, FooterTestMixin, AccessibilityTestMixin)

from systemtests.utils.data_archive import DataArchive


class TestRerunJobsPage(NavbarTestMixin, BaseTestCase, FooterTestMixin, AccessibilityTestMixin):
    """
    Test cases for the InstrumentSummary page when the Rerun form is NOT visible
    """

    fixtures = BaseTestCase.fixtures + ["run_with_one_variable"]
    excluded_accessibility_rules = [["color-contrast", "*"], ["duplicate-id-aria", "input"]]

    @classmethod
    def setUpClass(cls):
        """Sets up DataArchive for all tests and sets instrument for all tests"""
        super().setUpClass()
        cls.instrument_name = "TestInstrument"
        cls.data_archive = DataArchive([cls.instrument_name], 21, 21)
        cls.data_archive.create()
        cls.data_archive.add_reduction_script(cls.instrument_name, """print('some text')""")
        cls.data_archive.add_reduce_vars_script(cls.instrument_name,
                                                """standard_vars={"variable1":"test_variable_value_123"}""")

    @classmethod
    def tearDownClass(cls) -> None:
        """Destroys created DataArchive"""
        cls.data_archive.delete()
        super().tearDownClass()

    def setUp(self) -> None:
        """Set up RerunJobsPage before each test case"""
        super().setUp()
        self.page = RerunJobsPage(self.driver, self.instrument_name)
        self.page.launch()

    def test_cancel_goes_back_to_runs_list(self):
        """Tests: Clicking canel button returns the runs list page"""
        self.page.cancel_button.click()
        assert reverse("runs:list", kwargs={"instrument": self.instrument_name}) in self.driver.current_url

    def test_reset_values_does_reset_the_values(self):
        """Test that the button to reset the variables to the values from the reduce_vars script works"""
        self.page.variable1_field = "the new value in the field"
        self.page.reset_to_current_values.click()

        # need to re-query the driver because resetting replaces the elements
        var_field = self.page.variable1_field
        assert var_field.get_attribute("value") == "test_variable_value_123"
