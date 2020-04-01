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
        self._maintenance_specific_key = "facility"
        self._datetime_fields = ["start", "end"]
        self._sort_by_field = "start"

    def convert_raw_to_structured(self, raw_cycle_data, raw_maintenance_data):
        """ Converts raw data received from the Scheduler API into a list of Cycle objects,
        containing a list of MaintenanceDay objects - all which fall within the given cycle period.
        :param raw_cycle_data: Cycle data received from the Scheduler API (as a list)
        :param raw_maintenance_data: Maintenance day data received from the Scheduler API
                                     (as a list)
        :return: A list of Cycle objects containing a list of 0 or more MaintenanceDay objects. """
        pre_processed_cycles, pre_processed_maintenance\
            = self._pre_process(raw_cycle_data, raw_maintenance_data)
        return self._process(pre_processed_cycles, pre_processed_maintenance)

    @staticmethod
    def print_start_dates(data):
        """ Print each 'start' attribute within a list, prefixed by an index.
        :param data: The list of items to print the start dates of """
        for idx, item in enumerate(data):
            print(f"{idx}: {item['start']}")

    def _pre_process(self, raw_cycle_data, raw_maintenance_data):
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
                print(f"\nItem removed as cycle name did not match the expected regex "
                      f"({item['name']}).\nFull item: {item}")
            elif item['start'].replace(tzinfo=None) < self._earliest_possible_date:
                print(f"\nItem removed as date lies outside range of interest "
                      f"({item['start']}).\nFull item: {item}")
            else:
                clean_list.append(item)
        print(f"New length: {len(clean_list)}")
        print("END Data clean\n")
        return clean_list

    def _sort_by_date(self, data):
        """ Sorts a list by a date field (specified by the _sort_by_field variable)
        :param data: The list to be sorted
        :return: The list sorted by the specified field """
        return sorted(data, key=lambda date: date[self._sort_by_field])

    def _process(self, cycle_data, maintenance_data):
        """ Converts pre-processed cycle data items and maintenance day data items
        into a single list of Cycle objects. Each cycle object contains a list
        of MaintenanceDay objects - all of which fall within the given cycle period.
        Maintenance Days which fall outside of cycle periods are highlighted and discarded.
        :param cycle_data: A pre-processed list containing all valid cycle data items.
        :param maintenance_data: A pre-processed list of all valid maintenance day data items.
        :return: A list of Cycle objects containing a list of 0 or more MaintenanceDay objects. """
        cycle_list = []
        maintenance_data_copy = maintenance_data.copy()
        for index, current_cycle_data in enumerate(cycle_data):
            cycle_obj = Cycle(current_cycle_data['name'],
                              current_cycle_data['start'],
                              current_cycle_data['end'])
            while len(maintenance_data_copy) > 0:
                m_day = maintenance_data_copy[0]
                if m_day['start'] < cycle_obj.start:
                    # if this m_day is EARLIER than the current cycle START
                    if index == len(cycle_list)-1:  # TODO: Edward - Make test for this     pylint:disable=fixme
                        next_cycle = None
                    else:
                        next_cycle = cycle_list[index+1]
                    self._unexpected_maintenance_day_warning(m_day, cycle_obj, next_cycle)
                    maintenance_data_copy.pop(0)
                elif m_day['end'] < cycle_obj.end:
                    # if this m_day is EARLIER than the current cycle END
                    cycle_obj.add_maintenance_day(m_day['start'], m_day['end'])
                    maintenance_data_copy.pop(0)
                elif index == len(cycle_list)-1:
                    # if this m_day is LATER than the LAST cycle END
                    self._unexpected_maintenance_day_warning(m_day, cycle_obj, None)
                else:
                    # if this m_day is LATER than the current (not last) cycle END
                    break
            cycle_list.append(cycle_obj)
        return cycle_list

    @staticmethod
    def _unexpected_maintenance_day_warning(m_day, this_cycle, next_cycle=None):
        if next_cycle:
            cycle_after_string = f"start: {next_cycle.start}, end: {next_cycle.end}"
        else:
            cycle_after_string = f"NONE (No later cycle dates)"
        print(f"WARNING - Encountered maintenance day outside of cycle dates "
              f"(assuming cycle_data and maintenance_data "
              f"were ordered as earliest-to-latest).\n"
              f"Maintenance Day= start: {m_day['start']}, end: {m_day['end']}\n"
              f"Closest Cycle before= start: {this_cycle.start}, end: {this_cycle.end}\n"
              f"Closest Cycle after= {cycle_after_string}\n"
              f"This Maintenance Day has therefore been discarded.\n")
