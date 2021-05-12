from unittest.mock import Mock, patch

from autoreduce_webapp import settings
from autoreduce_webapp.icat_cache import DEFAULT_MESSAGE
from autoreduce_webapp.view_utils import ICATConnectionException
from selenium_tests.pages.error_page import ErrorPage
from selenium_tests.tests.base_tests import (BaseTestCase, FooterTestMixin, NavbarTestMixin)


class TestErrorPage(NavbarTestMixin, BaseTestCase, FooterTestMixin):
    """
    Test cases for the error page
    """
    fixtures = BaseTestCase.fixtures + ["test_overview_page"]

    def setUp(self) -> None:
        """
        Sets up the ErrorPage object
        """
        super().setUp()
        self.page = ErrorPage(self.driver)

    @patch('reduction_viewer.views.authenticate', side_effect=ICATConnectionException)
    def test_error_message(self, authenticate: Mock):
        """
        Test that the page error message matches the expected error
        """
        settings.DEVELOPMENT_MODE = False
        self.page.launch()
        self.assertEqual(DEFAULT_MESSAGE, self.page.get_error_message())
        authenticate.assert_called_once_with(token=self.page.fake_token)
