"""
Unit tests for the Custom pagination module
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from utilities.pagination import CustomPage, RunPage, CustomPaginator, PageLimitException


class TestCustomPage(unittest.TestCase):
    """ Test the generic CustomPage functionality """
    def setUp(self):
        self.page = CustomPage(1, 1, False)

    def test_init(self):
        """
        Ensure that all variables are set up as expected in the __init__
        """
        self.assertEqual(self.page.records, [])
        self.assertEqual(self.page.is_visible, False)
        self.assertEqual(self.page.number, 1)
        self.assertEqual(self.page.max_limit, 1)
        self.assertEqual(self.page.display_name, None)
        self.assertEqual(self.page.start, 0)
        self.assertEqual(self.page.end, 0)

    def test_set_start_and_end(self):
        """
        Ensure this does not do anything in the case of a generic class
        """
        self.page.set_start_and_end()
        self.assertEqual(self.page.start, 0)
        self.assertEqual(self.page.end, 0)
        self.assertEqual(self.page.display_name, None)

    def test_add_record_valid(self):
        """
        Test that a record can be added to the page when the page is not full
        """
        self.assertEqual(len(self.page.records), 0)
        self.page.add_record('test_record')
        self.assertEqual(len(self.page.records), 1)

    def test_add_record_full(self):
        """
        Test that adding a record to a full page will raise an exception
        """
        self.page.add_record('test_record')
        self.assertEqual(len(self.page.records), 1)
        self.assertEqual(self.page.start, 0)
        self.assertEqual(self.page.end, 0)
        self.assertEqual(self.page.display_name, None)
        self.assertRaises(PageLimitException, self.page.add_record, 'test_record_2')


# pylint:disable=too-few-public-methods
class MockRunData(object):
    """ Test class to simulate a Run record from the database """
    def __init__(self, run_number, date):
        self.run_number = run_number
        self.last_updated = date


# pylint:disable=too-few-public-methods
class TestRunPage(unittest.TestCase):
    """ Test the specific RunPage functionality """
    def test_set_start_and_end(self):
        """
        Ensure the start and end values for the page are calculated correctly
        """
        page = RunPage(1, 2, False)
        today = datetime.now()
        page.add_record(MockRunData(1, today))
        page.add_record(MockRunData(2, today))
        page.set_start_and_end()
        self.assertEqual(page.start, 1)
        self.assertEqual(page.end, 2)
        self.assertEqual(page.display_name, '1 - 2')


# pylint:disable=invalid-name
class TestCustomPaginator(unittest.TestCase):
    """ Test the functionality of the Custom Pagination """
    def setUp(self):
        """
        Generate mock data to use for page population
        """
        now = datetime.now()
        self.data = [
            MockRunData(1, now),
            MockRunData(2, now - timedelta(1)),
            MockRunData(3, now - timedelta(2)),
            MockRunData(4, now - timedelta(3)),
            MockRunData(5, now - timedelta(4))
        ]

    @patch('utilities.pagination.CustomPaginator._validate_current_page')
    @patch('utilities.pagination.CustomPaginator._construct_pagination')
    @patch('utilities.pagination.CustomPaginator._set_next_and_previous')
    @patch('utilities.pagination.CustomPaginator._create_display_list')
    def test_init(self, mock_create_display_list, mock_set_next_and_previous, mock_construct_pagination,
                  mock_validate_current_page):
        """
        Ensure that all variables are set as expected in the __init__
        and the functions to populate / validate / render the paginator are run
        """
        paginator = CustomPaginator('run', self.data, 3, 2, 1)
        self.assertEqual(paginator.query_set, self.data)
        self.assertEqual(paginator.items_per_page, 3)
        self.assertEqual(paginator.page_tolerance, 2)
        self.assertEqual(paginator.current_page_index, 1)
        self.assertEqual(paginator.next_page_index, 0)
        self.assertEqual(paginator.has_next, False)
        self.assertEqual(paginator.has_previous, False)
        self.assertEqual(paginator.previous_page_index, 0)
        self.assertEqual(paginator.page_list, [])
        self.assertEqual(paginator.display_list, [])
        mock_validate_current_page.assert_called_once()
        mock_construct_pagination.assert_called_once()
        mock_set_next_and_previous.assert_called_once()
        mock_create_display_list.assert_called_once()

    def test_validate_current_page_valid(self):
        """
        Ensure that current page index does not change if it is valid
        """
        paginator = CustomPaginator('run', self.data, 3, 2, 1)
        self.assertEqual(paginator.current_page_index, 1)

    def test_validate_current_page_low(self):
        """
        Ensure that the current page is at least 1 when a number less than 1 is provided
        """
        paginator = CustomPaginator('run', self.data, 3, 2, -1)
        self.assertEqual(paginator.current_page_index, 1)

    def test_validate_current_page_high(self):
        """
        Ensure that the current page is set to maximum page number if larger than maximum pages
        """
        paginator = CustomPaginator('run', self.data, 3, 2, 10)
        self.assertEqual(paginator.current_page_index, 2)

    def test_construct_pagination_single_page(self):
        """
        Test that the pages are created correct if only a single page is required
        """
        paginator = CustomPaginator('run', self.data, 5, 2, 1)
        self.assertEqual(len(paginator.page_list), 1)
        self.assertIsInstance(paginator.page_list[0], RunPage)
        self.assertTrue(paginator.page_list[0].is_visible)

    def test_construct_pagination_multi_page(self):
        """
        Test that the pages are created correctly if multiple pages are required
        """
        paginator = CustomPaginator('run', self.data, 2, 2, 1)
        self.assertEqual(len(paginator.page_list), 3)

    def test_construct_pagination_visibility(self):
        """
        Test that the pages visibility are set correctly
        """
        paginator = CustomPaginator('run', self.data, 1, 1, 1)
        self.assertEqual(len(paginator.page_list), 5)
        self.assertFalse(paginator.page_list[4].is_visible)
        self.assertFalse(paginator.page_list[3].is_visible)
        self.assertFalse(paginator.page_list[2].is_visible)
        self.assertTrue(paginator.page_list[1].is_visible)
        self.assertTrue(paginator.page_list[0].is_visible)

    def test_create_display(self):
        """
        Ensure that the page display is made correctly
        """
        paginator = CustomPaginator('run', self.data, 1, 1, 1)
        self.assertEqual(len(paginator.display_list), 3)
        self.assertEqual(paginator.display_list[0].records[0].run_number, 1)
        self.assertEqual(paginator.display_list[1].records[0].run_number, 2)
        self.assertEqual(paginator.display_list[2], '...')

    def test_create_display_date(self):
        """
        Ensure that the page display is made correctly for date filter
        """
        paginator = CustomPaginator('date', self.data, 1, 1, 1)
        self.assertEqual(len(paginator.display_list), 3)
        self.assertEqual(paginator.display_list[0].records[0].last_updated, self.data[0].last_updated)
        self.assertEqual(paginator.display_list[1].records[0].last_updated, self.data[1].last_updated)
        self.assertEqual(paginator.display_list[2], '...')

    def test_set_next_and_previous_with_both(self):
        """
        Ensure that each the next and previous page are correctly set for the current page
        """
        paginator = CustomPaginator('run', self.data, 1, 1, 2)
        self.assertTrue(paginator.has_next)
        self.assertTrue(paginator.has_previous)
        self.assertEqual(paginator.next_page_index, 3)
        self.assertEqual(paginator.previous_page_index, 1)

    def test_set_next_and_previous_only_previous(self):
        """
        Ensure that only a previous page is set when on the max page
        """
        paginator = CustomPaginator('run', self.data, 1, 1, 5)
        self.assertFalse(paginator.has_next)
        self.assertTrue(paginator.has_previous)
        self.assertEqual(paginator.next_page_index, 0)
        self.assertEqual(paginator.previous_page_index, 4)

    def test_set_next_and_previous_only_next(self):
        """
        Ensure that only a next page is set when on the max page
        """
        paginator = CustomPaginator('run', self.data, 1, 1, 1)
        self.assertTrue(paginator.has_next)
        self.assertFalse(paginator.has_previous)
        self.assertEqual(paginator.next_page_index, 2)
        self.assertEqual(paginator.previous_page_index, 0)
