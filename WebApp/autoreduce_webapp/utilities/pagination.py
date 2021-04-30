"""
Custom Paginator for the web application and associated Pages that are used to model each
individual page in the pagination.

This works in a similar way to the standard Paginator for Django but gives the added benefit of
easier display names, as well as setting a maximum number of pages to display in the pagination

This is currently used in the runs_list.html page
"""

import math


class PageLimitException(Exception):
    """ Custom Exception class to catch when page record limit is reached"""


class CustomPaginator:
    """
    CustomPaginator to allow for more complex functionality to be used without doing heavy
    lifting in the django template code
    """
    def __init__(self, page_type, query_set, items_per_page, page_tolerance, current_page):
        """
        :param query_set: All data to show
        :param items_per_page: Number of items per page
        :param page_tolerance: Number of pages to show
        """
        self.page_type = page_type
        self.query_set = query_set
        self.items_per_page = int(items_per_page)
        self.page_tolerance = int(page_tolerance)
        self.current_page_index = int(current_page)
        self.next_page_index = 0
        self.has_next = False
        self.has_previous = False
        self.previous_page_index = 0
        self.page_list = []
        self.display_list = []
        self._validate_current_page()
        self._construct_pagination()
        self._set_next_and_previous()
        if self.page_list:
            self.current_page = self.page_list[self.current_page_index - 1]
        self._create_display_list()

    def _validate_current_page(self):
        """
        Ensure that the current page specified is valid
        Update the page to min/max if outside of expected range
        """
        page_count = int(math.ceil(float(len(self.query_set)) / float(self.items_per_page)))
        self.current_page_index = max(1, min(self.current_page_index, page_count))

    def _construct_pagination(self):
        """
        Construct the pages, populate them with records
        and add them to the self.page_list variable.
        """
        if abs(self.current_page_index - 1) <= self.page_tolerance:
            current_page = self._create_page(self.page_type, 1, self.items_per_page, True)
        else:
            current_page = self._create_page(self.page_type, 1, self.items_per_page, False)

        for record in self.query_set:
            try:
                current_page.add_record(record)
            except PageLimitException:
                self.page_list.append(current_page)
                next_page_index = current_page.number + 1
                if abs(self.current_page_index - next_page_index) <= self.page_tolerance:
                    current_page = self._create_page(self.page_type, next_page_index, self.items_per_page, True)
                else:
                    current_page = self._create_page(self.page_type, next_page_index, self.items_per_page, False)
                # Make sure we add the record to the new page we created
                current_page.add_record(record)
        current_page.set_start_and_end()
        self.page_list.append(current_page)

    @staticmethod
    def _create_page(page_type, page_number, max_number_of_items, visible):
        if page_type.lower() == 'run':
            return RunPage(page_number, max_number_of_items, visible)
        if page_type.lower() == 'date':
            return DatePage(page_number, max_number_of_items, visible)
        # This should never be triggered, but let's default to Run display if there is a problem
        return 'run'

    def _create_display_list(self):
        """
        A compact version of the pagination table that is used for display purposes
        """
        for page in self.page_list:
            if page.is_visible:
                self.display_list.append(page)
            else:
                if len(self.display_list) >= 1 and self.display_list[-1] == "...":
                    continue
                self.display_list.append("...")

    def _set_next_and_previous(self):
        """
        Sets class variables to describe what page is before and after the current page
        """
        if self.current_page_index < len(self.page_list):
            self.next_page_index = self.current_page_index + 1
            self.has_next = True
        if self.current_page_index > 1:
            self.previous_page_index = self.current_page_index - 1
            self.has_previous = True


class CustomPage:
    """
    Generic CustomPage class to model a single page in the pagination
    """
    def __init__(self, number, max_limit, is_visible):
        """
        :param number: The page number
        :param max_limit: The most amount of data items allowed on a page
        :param is_visible: Should this page be shown in the pagination?
        """
        self.records = []
        self.is_visible = is_visible
        self.number = number
        self.max_limit = max_limit
        self.display_name = None
        self.start = 0
        self.end = 0

    def set_start_and_end(self):
        """ Implemented by child class """

    def add_record(self, record):
        """
        Adds a record to the page, if the page has reached the limit that it can hold,
        set the start and end run number variables and throw an exception to be caught
        """
        if len(self.records) >= self.max_limit:
            self.set_start_and_end()
            raise PageLimitException("Unable to add record to page. Max number of records reached")
        self.records.append(record)


class RunPage(CustomPage):
    """
    Specific implementation for rendering the pagination if sorting by Run Number
    """
    def set_start_and_end(self):
        """
        Custom function to set the start and end variables and
        construct the display name for the page
        """
        self.start = self.records[0].run_number
        self.end = self.records[-1].run_number
        if self.start == self.end:
            self.display_name = "{}".format(self.start)
        else:
            self.display_name = "{} - {}".format(self.start, self.end)


class DatePage(CustomPage):
    """
    Specific implementation for rendering the pagination if sorting by Date
    """
    def set_start_and_end(self):
        """
        Custom function to set the start and end variables and
        construct the display name for the page
        """
        self.start = self.records[0].last_updated
        self.end = self.records[-1].last_updated

        if self.start == self.end:
            self.display_name = "{}/{}/{}".format(self.start.day, self.start.month, self.start.year)
        else:
            self.display_name = "{}/{}/{} - {}/{}/{}".format(self.start.day, self.start.month, self.start.year,
                                                             self.end.day, self.end.month, self.end.year)
