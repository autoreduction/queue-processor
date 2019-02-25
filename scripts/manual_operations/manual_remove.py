from utils.clients.database_client import DatabaseClient


class ManualRemove(object):

    def __init__(self):
        self.database = DatabaseClient()
        self.database.connect()
        self.results = {}

    def find_runs_in_database(self, instrument, run_number):
        """
        Find all runs in the database that relate to a given instrument and run number
        :param instrument: the instrument associated with the run
        :param run_number: the run to search for in the database
        :return:
        """
        conn = self.database.get_connection()
        result = conn.query(self.database.reduction_run()) \
            .join(self.database.reduction_run().instrument) \
            .filter(self.database.instrument().name == instrument) \
            .filter(self.database.reduction_run().run_number == run_number) \
            .order_by(self.database.reduction_run().created.desc()) \
            .all()
        conn.commit()
        self.results[run_number] = result
        return result

    def analyse_results(self):
        for key, value in self.results.items():
            if len(value) == 0:
                self.run_not_found()
            if len(value) == 1:
                continue
            if len(value) > 1:
                self.mutilple_versions_found()

    def delete_results(self):
        """
        Delete all the runs in the self.results dict
        """
        for key, value in self.results.items():
            if len(value) >
        conn = self.database.get_connection()
