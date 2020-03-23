import re
from datetime import datetime

from suds import Client

# TODO: make these classes serialisable (see online tutorial)
class MaintenanceDay:

    def __init__(self, start, end):
        self.start = start
        self.end = end


class Cycle:

    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end
        self.maintenance_days = []

    def add_maintenance_day(self, start, end):
        self.maintenance_days.append(MaintenanceDay(start, end))


# TODO: Might want to remove class, just make as a static library of methods
class SchedulerDataProcessor:

    def __init__(self):
        self._earliest_possible_date = datetime(2000, 1, 1, tzinfo=None)
        # TODO: confirm what is to be accepted (vs what is invalid)
        #   Current regex =  4 digits | '/' | 1 or more digit/letter(s) | end
        self._cycle_name_regex = "\d{4}/\w*$"
        self._maintenance_specific_key = 'facility'
        self._datetime_fields = ["start", "end"]
        self._sort_by_field = "start"

    def convert_raw_to_structured(self, raw_cycle_data, raw_maintenance_data):
        pre_processed = self._pre_process(raw_cycle_data, raw_maintenance_data)
        return self._process(pre_processed)

    @staticmethod
    def print_start_dates(items):
        for idx, item in enumerate(items):
            print(f"{idx}: {item['start']}")

    def _pre_process(self, raw_cycle_data, raw_maintenance_data):
        data = self._combine_lists(raw_cycle_data, raw_maintenance_data)
        data = self._sort_by_date(data)
        data = self._clean_data(data)
        return data

    def _clean_data(self, data):
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

    @staticmethod
    def _combine_lists(first, second):
        print("combining..")
        combined = first + second
        return combined

    def _sort_by_date(self, data):
        print("sorting..")
        return sorted(data, key=lambda date: date[self._sort_by_field])

    def _process(self, data):
        cycle_list = []
        idx = 0
        while idx < len(data):
            # TODO: I've avoided using try/except for expected behaviour, unlike the draft implementation
            #   (i.e. an exception is only raised in exceptional circumstances) - in line with good code practice.
            try:
                # print(f"{idx} adding cycle: {list[idx]}")
                cycle = Cycle(data[idx]['name'],
                              data[idx]['start'],
                              data[idx]['end'])
                idx += 1
                while idx < len(data) and self._maintenance_specific_key in data[idx]:
                    # print(f"{idx} adding maintn: {list[idx]}")
                    cycle.add_maintenance_day(data[idx]['start'],
                                              data[idx]['end'])
                    idx += 1
                cycle_list.append(cycle)
            except AttributeError:
                raise RuntimeError("Unexpected list entry encountered. Ensure to sort the list before processing")

        return cycle_list
