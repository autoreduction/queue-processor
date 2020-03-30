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


class MaintenanceDay:   # pylint:disable=too-few-public-methods
    """
    Class to represent a cycle maintenance day
    """
    def __init__(self, start, end):
        self.start = start
        self.end = end


class Cycle:    # pylint:disable=too-few-public-methods
    """
    Class to represent a cycle period
    """
    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end
        self.maintenance_days = []

    def add_maintenance_day(self, start, end):
        """ Adds a maintenance day object to this cycle
         :param start: The start date of the maintenance day being added
         :param end: The end date of the maintenance day being added """
        self.maintenance_days.append(MaintenanceDay(start, end))


class SchedulerDataProcessor:
    """
    Class to process data received from the Scheduler API
    """
    def __init__(self):
        self._earliest_possible_date = datetime(2000, 1, 1, tzinfo=None)
        # Current regex =  4 digits | '/' | 1 or more digit/letter(s) | end
        self._cycle_name_regex = r"\d{4}/\w*$"
        self._maintenance_specific_key = 'facility'
        self._datetime_fields = ["start", "end"]
        self._sort_by_field = "start"

    def convert_raw_to_structured_as_single_list(self, raw_cycle_data, raw_maintenance_data):
        """ Converts raw data received from the Scheduler API into a list of Cycle objects,
        containing a list of MaintenanceDay objects - all which fall within the given cycle period.
        :param raw_cycle_data: Cycle data received from the Scheduler API (as a list)
        :param raw_maintenance_data: Maintenance day data received from the Scheduler API
                                     (as a list)
        :return: A list of Cycle objects containing a list of 0 or more MaintenanceDay objects. """
        pre_processed = self._pre_process_as_single_list(raw_cycle_data, raw_maintenance_data)
        return self._process_as_single_list(pre_processed)

    def convert_raw_to_structured_as_separate(self, raw_cycle_data, raw_maintenance_data):
        """ Converts raw data received from the Scheduler API into a list of Cycle objects,
        containing a list of MaintenanceDay objects - all which fall within the given cycle period.
        :param raw_cycle_data: Cycle data received from the Scheduler API (as a list)
        :param raw_maintenance_data: Maintenance day data received from the Scheduler API
                                     (as a list)
        :return: A list of Cycle objects containing a list of 0 or more MaintenanceDay objects. """
        pre_processed_cycles, pre_processed_maintenance\
            = self._pre_process_as_separate(raw_cycle_data, raw_maintenance_data)
        return self._process_from_separate(pre_processed_cycles, pre_processed_maintenance)

    @staticmethod
    def print_start_dates(data):
        """ Print each 'start' attribute within a list, prefixed by an index.
        :param data: The list of items to print the start dates of """
        for idx, item in enumerate(data):
            print(f"{idx}: {item['start']}")

    def _pre_process_as_single_list(self, raw_cycle_data, raw_maintenance_data):
        """ Makes adjustments to the data without converting it to a different data type.
        These adjustments are necessary for the data to be properly processed
        into Cycle and Maintenance Day objects.
        :param raw_cycle_data: Cycle data received from the Scheduler API (as a list)
        :param raw_maintenance_data: Maintenance day data received from the Scheduler API
                                     (as a list)
        :return: A single list containing all valid items from both lists """
        data = self._combine_lists(raw_cycle_data, raw_maintenance_data)
        data = self._sort_by_date(data)
        data = self._clean_data(data)
        return data

    def _pre_process_as_separate(self, raw_cycle_data, raw_maintenance_data):
        """ Makes adjustments to the data without converting the data type.
        These adjustments are necessary for the data to be properly processed
        into Cycle and Maintenance Day objects.
        :param raw_cycle_data: Cycle data received from the Scheduler API (as a list)
        :param raw_maintenance_data: Maintenance day data received from the Scheduler API
                                     (as a list)
        :return: A pre-processed cycle data list, and pre-processed maintenance data list """
        cycle_data = self._sort_by_date(raw_cycle_data)
        cycle_data = self._clean_data(cycle_data)

        maintenance_data = self._sort_by_date(raw_maintenance_data)
        maintenance_data = self._clean_data(maintenance_data)

        return cycle_data, maintenance_data

    def _clean_data(self, data):
        """ Removes invalid items from the data.
        :param data: The list of items to be validated
        :return: The list of items that were passed in, but with all invalid items removed """
        print("\nBEGIN Data clean")
        print(f"Original length: {len(data)}")
        clean_list = []
        for item in data:
            if 'name' in item and not re.search(self._cycle_name_regex, item['name']):
                print(f"\nItem removed due to strange cycle name "
                      f"({item['name']}).\nFull item: {item}")
            elif item['start'].replace(tzinfo=None) < self._earliest_possible_date:
                print(f"\nItem removed due to impossible date "
                      f"({item['start']}).\nFull item: {item}")
            else:
                clean_list.append(item)
        print(f"New length: {len(clean_list)}")
        print("END Data clean\n")
        return clean_list

    @staticmethod
    def _combine_lists(first, second):
        """ Combines two lists together.
        :param first: The first list to be combined
        :param second: The second list to be combined
        :return: The single combined list """
        combined = first + second
        return combined

    def _sort_by_date(self, data):
        """ Sorts a list by a date field (specified by the _sort_by_field variable)
        :param data: The list to be sorted
        :return: The list sorted by the specified field """
        return sorted(data, key=lambda date: date[self._sort_by_field])

    @staticmethod
    def _process_from_separate(cycle_data, maintenance_data):
        """ Converts pre-processed cycle data items and maintenance day data items
        into a single list of Cycle objects. Each cycle object contains a list
        of MaintenanceDay objects - all of which fall within the given cycle period.
        Maintenance Days which fall outside of cycle periods are highlighted and discarded.
        :param cycle_data: A pre-processed list containing all valid cycle data items.
        :param maintenance_data: A pre-processed list of all valid maintenance day data items.
        :return: A list of Cycle objects containing a list of 0 or more MaintenanceDay objects. """
        cycle_list = []
        unused_maintenance_data = maintenance_data.copy()
        for current_cycle_data in cycle_data:

            cycle_obj = Cycle(current_cycle_data['name'],
                              current_cycle_data['start'],
                              current_cycle_data['end'])
            while len(unused_maintenance_data) > 0:
                m_day = unused_maintenance_data[0]
                if m_day['start'] < cycle_obj.start:
                    # if the next m_day is EARLIER than the current cycle START
                    if len(unused_maintenance_data) > 1:
                        cycle_after_string = f"start: {unused_maintenance_data[1].start}, " \
                                             f"end: {unused_maintenance_data[1].end}"
                    else:
                        cycle_after_string = f"NONE (No later cycle dates)"
                    print(f"WARNING - Encountered maintenance day outside of cycle dates "
                          f"(assuming cycle_data and maintenance_data "
                          f"were ordered as earliest-to-latest).\n"
                          f"Maintenance Day= start: {m_day['start']}, end: {m_day['end']}\n"
                          f"Closest Cycle before= start: {cycle_obj.start}, end: {cycle_obj.end}\n"
                          f"Closest Cycle after= {cycle_after_string}\n"
                          f"This Maintenance Day has therefore been discarded.\n")
                    unused_maintenance_data.pop(0)
                elif m_day['end'] < cycle_obj.end:
                    # if the next m_day is EARLIER than the current cycle END
                    cycle_obj.add_maintenance_day(m_day['start'], m_day['end'])
                    unused_maintenance_data.pop(0)
                else:
                    # if the next m_day is LATER than the current cycle END
                    break
            cycle_list.append(cycle_obj)
        return cycle_list

    def _process_as_single_list(self, data):
        """ Converts a pre-processed list of cycle and maintenance day data items
        into a list of Cycle objects, each containing a list of MaintenanceDay
        objects - all which fall within the given cycle period.
        :param data: A pre-processed list containing all valid cycle and maintenance day data items.
        :return: A list of Cycle objects containing a list of 0 or more MaintenanceDay objects.
        :raises RuntimeError:
            If a maintenance day is encountered in the data before a cycle.
            This will only occur if the data has not been properly pre-processed. """
        cycle_list = []
        index = 0
        while index < len(data):
            try:
                cycle = Cycle(data[index]['name'],
                              data[index]['start'],
                              data[index]['end'])
                index += 1
                while index < len(data) and self._maintenance_specific_key in data[index]:
                    cycle.add_maintenance_day(data[index]['start'],
                                              data[index]['end'])
                    index += 1
                cycle_list.append(cycle)
            except AttributeError:
                raise RuntimeError("Unexpected list entry encountered."
                                   "Ensure to sort the list before processing")

        return cycle_list
