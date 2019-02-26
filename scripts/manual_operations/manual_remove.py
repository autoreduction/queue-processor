"""
Functionality to remove a reduction run from the database
"""
import argparse

from utils.clients.database_client import DatabaseClient


class ManualRemove(object):

    def __init__(self, instrument):
        self.database = DatabaseClient()
        self.database.connect()
        self.to_delete = {}
        self.instrument = instrument

    def find_runs_in_database(self, run_number):
        """
        Find all runs in the database that relate to a given instrument and run number
        :param run_number: the run to search for in the database
        :return:
        """
        conn = self.database.get_connection()
        result = conn.query(self.database.reduction_run()) \
            .join(self.database.reduction_run().instrument) \
            .filter(self.database.instrument().name == self.instrument) \
            .filter(self.database.reduction_run().run_number == run_number) \
            .order_by(self.database.reduction_run().created.desc()) \
            .all()
        conn.commit()
        self.to_delete[run_number] = result
        return result

    def process_results(self):
        """
        Process all the results what to do with the run based on the result of database query
        """
        for key, value in self.to_delete.items():
            if len(value) == 0:
                self.run_not_found(run_number=key)
            if len(value) == 1:
                continue
            if len(value) > 1:
                self.multiple_versions_found(run_number=key)

    def run_not_found(self, run_number):
        """
        Inform user and remove key from dictionary
        :param run_number: The run to remove from the dictionary
        """
        print('No runs found associated with {} for instrument {}'.format(run_number,
                                                                          self.instrument))
        del self.to_delete[run_number]

    def multiple_versions_found(self, run_number):
        """
        Ask the user which versions they want to remove
        Update the self.to_delete dictionary by removing unwanted versions
        :param run_number: The run number with multiple versions
        """
        # Display run_number - title - version for all matching runs
        print("Discovered multiple reduction versions for {}{}:".format(self. instrument,
                                                                        run_number))
        for run in self.to_delete[run_number]:
            print("\tv{} - {}".format(run.run_version, run.run_name))

        # Get user input for which versions they wish to delete
        user_input = raw_input("Which runs would you like to delete (e.g. 1,2,3): ")
        input_valid, user_input = self.validate_csv_input(user_input)
        while input_valid is False:
            user_input = raw_input('Input of \'{}\' was invalid. '
                                   'Please provide a comma separated list of values:')
            input_valid, user_input = self.validate_csv_input(user_input)

        # Remove runs that the user does NOT want to delete from the delete list
        for reduction_job in self.to_delete[run_number]:
            if not int(reduction_job.run_version) in user_input:
                self.to_delete[run_number].remove(reduction_job)

    def delete_records(self):
        """
        Delete all records from the database that match those found in self.to_delete
        """
        conn = self.database.get_connection()
        for run_number, job_list in self.to_delete.items():
            for version in job_list:
                # Delete the specified version
                print('{}{}:'.format(self.instrument, run_number))
                # Delete reduction location record
                conn.query(self.database.reduction_location()) \
                    .filter(self.database.reduction_location().id == version.id) \
                    .delete(synchronize_session='fetch')
                conn.commit()
                print('\treduction_viewer_reductionlocation ... Deleted')

                # Delete data location record
                conn.query(self.database.reduction_data_location()) \
                    .filter(self.database.reduction_data_location().id == version.id) \
                    .delete(synchronize_session='fetch')
                conn.commit()
                print('\treduction_viewer_datalocation ... Deleted')

                # Delete reduction run record
                conn.query(self.database.reduction_run()) \
                    .filter(self.database.reduction_run().id == version.id) \
                    .delete(synchronize_session='fetch')
                conn.commit()
                print('\treduction_viewer_reductionrun ... Deleted')
            # Remove deleted run from dictionary
            del self.to_delete[run_number]

    @staticmethod
    def validate_csv_input(user_input):
        """
        checks if a comma separated list was provided
        :return: (tuple) = (bool - is valid? , list - csv as list (empty list if invalid))
        """
        processed_input = []
        if ',' in user_input:
            versions_to_delete = user_input.split(',')
            for number in versions_to_delete:
                try:
                    number = int(number)
                    processed_input.append(number)
                except ValueError:
                    return False, []
        else:
            try:
                user_input = int(user_input)
                processed_input.append(user_input)
            except ValueError:
                return False, []
        return True, processed_input


def main():
    parser = argparse.ArgumentParser(description='Remove a run from the autoreduction service.',
                                     epilog='./manual_remove.py GEM 83880')
    parser.add_argument('instrument', metavar='instrument', type=str,
                        help='a string of the instrument name e.g "GEM"')
    parser.add_argument('start_run_number', metavar='start_run_number', type=int,
                        help='the start run number e.g. "83880"')
    args = parser.parse_args()

    instrument = args.instrument
    run_number = args.start_run_number
    manual_remove = ManualRemove(instrument)
    manual_remove.find_runs_in_database(run_number)
    manual_remove.process_results()
    manual_remove.delete_records()


if __name__ == "__main__":
    main()
