# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Classes to represent and process cycle data received from the scheduler API
"""
import re
from datetime import datetime

from suds import Client


class MaintenanceDay:
    """
    Class to represent a cycle maintenance day
    """
    def __init__(self, start, end):
        self.start = start
        self.end = end


class Cycle:
    """
    Class to represent a cycle period
    """
    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end
        self.maintenance_days = []

    def add_maintenance_day(self, start, end):
        self.maintenance_days.append(MaintenanceDay(start, end))


class SchedulerDataProcessor:
    """
    Class to process data received from the Scheduler API
    """
    def __init__(self):
        self._earliest_possible_date = datetime(2000, 1, 1, tzinfo=None)
        # TODO: confirm what is to be accepted (vs what is invalid)
        #   Current regex =  4 digits | '/' | 1 or more digit/letter(s) | end
        self._cycle_name_regex = "\d{4}/\w*$"
        self._maintenance_specific_key = 'facility'
        self._datetime_fields = ["start", "end"]
        self._sort_by_field = "start"

    def convert_raw_to_structured(self, raw_cycle_data, raw_maintenance_data):
        """
        Converts raw data received from the Scheduler API into a list of Cycle objects,
        containing a list of MaintenanceDay objects - all which fall within the given cycle period.
        :param raw_cycle_data: Cycle data received from the Scheduler API (as a list)
        :param raw_maintenance_data: Maintenance day data received from the Scheduler API (as a list)
        :return: A list of Cycle objects containing a list of 0 or more MaintenanceDay objects.
        """
        pre_processed = self._pre_process(raw_cycle_data, raw_maintenance_data)
        return self._process(pre_processed)

    @staticmethod
    def print_start_dates(data):
        """
        Print each 'start' attribute within a list, prefixed by an index.
        :param data: The list of items to print the start dates of
        """
        for idx, item in enumerate(data):
            print(f"{idx}: {item['start']}")

    def _pre_process(self, raw_cycle_data, raw_maintenance_data):
        """
        Makes adjustments to the data without converting it to a different data type.
        These adjustments are necessary for the data to be properly processed
        into Cycle and Maintenance Day objects.
        :param raw_cycle_data: Cycle data received from the Scheduler API (as a list)
        :param raw_maintenance_data: Maintenance day data received from the Scheduler API (as a list)
        :return: A single list containing all valid items from both lists
        """
        data = self._combine_lists(raw_cycle_data, raw_maintenance_data)
        data = self._sort_by_date(data)
        data = self._clean_data(data)
        return data

    def _clean_data(self, data):
        """
        Removes invalid items from the data.
        :param data: The list of items to be validated
        :return: The list of items that were passed in, but with all invalid items removed
        """
        print("cleaning..")
        print(f"Original length: {len(data)}")
        clean_list = []
        for item in data:
            if 'name' in item and not re.search(self._cycle_name_regex, item['name']):
                print(f"\nItem removed due to strange cycle name ({item['name']}).\nFull item: {item}")
            elif item['start'].replace(tzinfo=None) < self._earliest_possible_date:
                print(f"\nItem removed due to impossible date ({item['start']}).\nFull item: {item}")
            else:
                clean_list.append(item)
        print(f"New length: {len(clean_list)}")
        return clean_list

    # TODO: question - I've used the method of combining the lists as this was suggested,
    #  but I'm not exactly sure why we do this instead of keeping them separate?
    #  Is it a speed optimisation perhaps? I wonder if it makes us more prone to bugs/confusing code..
    @staticmethod
    def _combine_lists(first, second):
        """
        Combines two lists together.
        :param first: The first list to be combined
        :param second: The second list to be combined
        :return: The single combined list
        """
        print("combining..")
        combined = first + second
        return combined

    def _sort_by_date(self, data):
        """
        Sorts a list by a date field (specified by the _sort_by_field variable)
        :param data: The list to be sorted
        :return: The list sorted by the specified field
        """
        print("sorting..")
        return sorted(data, key=lambda date: date[self._sort_by_field])

    # TODO: question - can a maintenance day ever occur outside of a cycle period?
    #   Currently, _process assumes maintenance days will always be within the latest cycle
    def _process(self, data):
        """
        Converts a pre-processed list of cycle and maintenance day data items into a list of Cycle objects,
        each containing a list of MaintenanceDay objects - all which fall within the given cycle period.
        :param data: A pre-processed list containing all valid cycle and maintenance day data items.
        :return: A list of Cycle objects containing a list of 0 or more MaintenanceDay objects.
        """
        cycle_list = []
        idx = 0
        while idx < len(data):
            # TODO: I've avoided using try/except for expected behaviour, unlike the draft implementation
            #   (i.e. an exception is only raised in exceptional circumstances) - in line with good code practice.
            try:
                cycle = Cycle(data[idx]['name'],
                              data[idx]['start'],
                              data[idx]['end'])
                idx += 1
                while idx < len(data) and self._maintenance_specific_key in data[idx]:
                    cycle.add_maintenance_day(data[idx]['start'],
                                              data[idx]['end'])
                    idx += 1
                cycle_list.append(cycle)
            except AttributeError:
                raise RuntimeError("Unexpected list entry encountered. Ensure to sort the list before processing")

        return cycle_list
