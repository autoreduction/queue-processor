from suds import Client


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


class SchedulerIngest:

    def __init__(self, user, password, uows_url, scheduler_api):
        self.user = user
        self.password = password
        self.uows_api_url = uows_url
        self.scheduler_api_url = scheduler_api
        self.session_id = self.get_session_id()

    def get_session_id(self):
        uows_client = Client(self.uows_api_url)
        return uows_client.service.login(Account=self.user, Password=self.password)

    def ingest_maintenance_days(self):
        scheduler_client = Client(self.scheduler_api_url)
        return scheduler_client.service.getOfflinePeriods(sessionId=self.session_id,
                                                          reason='Maintenance')

    def ingest_cycle_dates(self):
        scheduler_client = Client(self.scheduler_api_url)
        return scheduler_client.service.getCycles(sessionId=self.session_id)


class SchedulerDataProcessor:

    def __init__(self, user, password, uows_url, scheduler_url):
        self.raw_cycle_data = None
        self.raw_maintenance_data = None
        self.processed_cycle_data = None
        self.ingest = SchedulerIngest(user, password, uows_url, scheduler_url)
        self.get_data()

    def get_data(self):
        self.raw_maintenance_data = self.ingest.ingest_maintenance_days()
        self.raw_cycle_data = self.ingest.ingest_cycle_dates()

    def clean_data(self):
        all_cycle_data = self._combine_lists(self.raw_cycle_data, self.raw_maintenance_data)
        all_cycle_data = self._sort_by_date(all_cycle_data)
        all_cycle_data.pop(0)  # remove date from year 0001 ToDo: Refactor into function that removes all odd data (including: strange cycle names, impossible dates etc.
        self.processed_cycle_data = self._process_raw_cycle_list(all_cycle_data)

    @staticmethod
    def _combine_lists(first, second):
        return first.extend(second)

    @staticmethod
    def _sort_by_date(dates_list):
        return sorted(dates_list, key=lambda date: date.start)

    @staticmethod
    def _process_raw_cycle_list(all_cycle_data):
        #ToDo: Implement such that we create a list of cycles with child maintenance days
        raise NotImplementedError()




# user = None
# password = None
# uows_url = None
# scheduler_url = None
#
# scheduler_data = SchedulerDataProcessor(user, password, uows_url, scheduler_url)
# scheduler_data.get_data()
# print(scheduler_data.raw_cycle_data)
# print(scheduler_data.raw_maintenance_data)


        # def partition_cycle_list(cycle_list):
        #     partitioned_cycle_list = []
        #     for item in cycle_list:
        #         try:
        #             print(f"Cycle {item.name}: {item.start}")
        #
        # def create_cycle_table(cycle_list):
        #     cycle_data_frame = pd.DataFrame()
        #     cycle_entry = {}
        #     for item in cycle_list:
        #         try:
        #             # Is cycle object
        #             print(f"Cycle {item.name}: {item.start}")
        #             if cycle_entry:
        #                 print(f"Transforming {cycle_entry} into data frame")
        #                 print(f"Appending {pd.DataFrame(cycle_entry)} to {cycle_data_frame}")
        #                 cycle_data_frame.append(pd.DataFrame(cycle_entry))
        #                 cycle_data_frame = {}
        #             cycle_entry['Cycle'] = [item.name]
        #             cycle_entry['Start'] = [item.start]
        #             cycle_entry['End'] = [item.end]
        #             cycle_entry['Maintenance day(s)'] = [[]]
        #         except AttributeError:
        #             # is offline period object
        #             print(f"Maintenance day: {item.start}")
        #             cycle_entry['Maintenance day(s)'].append(item.start)
        #     return cycle_data_frame