"""
Custom Paginator for the web application and associated Pages that are used to model each
individual page in the pagination.

This works in a similar way to the standard Paginator for Django but gives the added benefit of
easier display names, as well as setting a maximum number of pages to display in the pagination

This is currently used in the instrument_summary.html page
"""


class CustomPaginator(object):
    """
    CustomPaginator to allow for more complex functionality to be used without doing heavy
    lifting in the django template code
    """

    def __init__(self, query_set, items_per_page, page_tolerance, current_page):
        """
        :param query_set: All data to show
        :param items_per_page: Number of items per page
        :param page_tolerance: Number of pages to show
        """
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
        self._construct_pagination()
        self._set_next_and_previous()
        self.current_page = self.page_list[self.current_page_index]
        self._create_display_list()

    def _construct_pagination(self):
        """
        Construct the pages, populate them with records
        and add them to the self.page_list variable.
        """
        if abs(self.current_page_index - 1) <= self.page_tolerance:
            current_page = RunPage(1, self.items_per_page, True)
        else:
            current_page = RunPage(1, self.items_per_page, False)

        for record in self.query_set:
            try:
                current_page.add_record(record)
            except PageLimitException:
                self.page_list.append(current_page)
                next_page_index = current_page.number + 1
                if abs(self.current_page_index - next_page_index) <= self.page_tolerance:
                    current_page = RunPage(next_page_index, self.items_per_page, True)
                else:
                    current_page = RunPage(next_page_index, self.items_per_page, False)

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
                else:
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


class PageLimitException(Exception):
    """ Custom Exception class to catch when page record limit is reached"""
    pass


class CustomPage(object):
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

    def _set_start_and_end(self):
        """ Implemented by child class """
        pass

    def add_record(self, record):
        """
        Adds a record to the page, if the page has reached the limit that it can hold,
        set the start and end run number variables and throw an exception to be caught
        """
        if len(self.records) >= self.max_limit:
            self._set_start_and_end()
            raise PageLimitException("Unable to add record to page. Max number of records reached")
        self.records.append(record)


class RunPage(CustomPage):
    """
    Specific implementation for rendering the pagination if sorting by Run Number
    """

    def _set_start_and_end(self):
        """
        Custom function to set the start and end variables and
        construct the display name for the page
        """
        self.start = self.records[0].run_number
        self.end = self.records[-1].run_number
        self.display_name = "{} - {}".format(self.start, self.end)
