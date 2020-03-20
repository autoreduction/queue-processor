import re
from datetime import datetime

from suds import Client

# TODO: can make these classes serialisable (see online tutorial)
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

# TODO: To delete (functionality migrated to busapps_ingestion_client)
# class SchedulerIngest:
#
#     def __init__(self, user, password, uows_url, scheduler_api):
#         self.user = user
#         self.password = password
#         self.uows_api_url = uows_url
#         self.scheduler_api_url = scheduler_api
#         self.session_id = self.get_session_id()
#
#     def get_session_id(self):
#         uows_client = Client(self.uows_api_url)
#         return uows_client.service.login(Account=self.user, Password=self.password)
#
#     def ingest_maintenance_days(self):
#         scheduler_client = Client(self.scheduler_api_url)
#         return scheduler_client.service.getOfflinePeriods(sessionId=self.session_id,
#                                                           reason='Maintenance')
#
#     def ingest_cycle_dates(self):
#         scheduler_client = Client(self.scheduler_api_url)
#         return scheduler_client.service.getCycles(sessionId=self.session_id)


# TODO: Might want to remove class, just make as a static library of methods
class SchedulerDataProcessor:

    def __init__(self):

        self._earliest_possible_date = datetime(2000, 1, 1)
        # TODO: confirm what is to be accepted (vs what is invalid)
        #   Current regex =  4 digits | '/' | 1 or more digit/letter(s) | end
        self._cycle_name_regex = "\d{4}/\w*$"
        self._maintenance_specific_key = 'facility'
        self._datetime_fields = ["start", "end"]
        self._sort_by_field = "start"

    def convert_raw_to_structured(self, raw_cycle_data, raw_maintenance_data):
        pre_processed = self._pre_process(raw_cycle_data, raw_maintenance_data)
        processed = self._process(pre_processed)
        return processed

    def _pre_process(self, raw_cycle_data, raw_maintenance_data):
        combined_list = self._combine_lists(raw_cycle_data, raw_maintenance_data)
        sorted_list = self._sort_by_date(combined_list)
        stripped_list = self._strip_timezone(sorted_list)
        cleaned_list = self._clean_data(stripped_list)
        return cleaned_list

    def print_start_dates(self, list):  #TODO: Note - this is just used for testing
        for idx, item in enumerate(list):
            print(f"{idx}: {item['start']}")

    def _clean_data(self, list):
        print("cleaning..")
        print(f"Original length: {len(list)}")
        clean_list = []
        for item in list:
            if 'name' in item and not re.search(self._cycle_name_regex, item['name']):
                print(f"Item removed due to strange cycle name ({item['name']}).\nFull item: {item}")
            elif item['start'] < self._earliest_possible_date:
                print(f"Item removed due to impossible date ({item['start']}).\nFull item: {item}")
            else:
                clean_list.append(item)
        print(f"New length: {len(clean_list)}")
        return clean_list

    @staticmethod
    def _combine_lists(first, second):
        print("combining..")
        combined = first + second
        return combined

    def _sort_by_date(self, items):
        print("sorting..")
        return sorted(items, key=lambda date: date[self._sort_by_field])

    def _strip_timezone(self, items):
        stripped_items = items.copy()
        for item in stripped_items:
            for key in self._datetime_fields:
                if key in item:
                    item[key] = datetime.strptime(str(item[key]).split("+")[0], "%Y-%m-%d %H:%M:%S")    # TODO: Refactor!!
        return stripped_items


    def _process(self, items):
        cycle_list = []
        idx = 0
        while idx < len(items):
            # TODO: I've avoided using try/except for expected behaviour, unlike the draft implementation
            #   (i.e. an exception is only raised in exceptional circumstances) - in line with good code practice.
            try:
                # print(f"{idx} adding cycle: {list[idx]}")
                cycle = Cycle(items[idx]['name'],
                              items[idx]['start'],
                              items[idx]['end'])
                idx += 1
                while idx < len(items) and self._maintenance_specific_key in items[idx]:
                    # print(f"{idx} adding maintn: {list[idx]}")
                    cycle.add_maintenance_day(items[idx]['start'],
                                              items[idx]['end'])
                    idx += 1
                cycle_list.append(cycle)
            except AttributeError:
                raise RuntimeError("Unexpected list entry encountered. Ensure to sort the list before processing")

        return cycle_list
