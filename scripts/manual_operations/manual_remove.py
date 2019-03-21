# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Functionality to remove a reduction run from the database
"""
from __future__ import print_function
import argparse

from utils.clients.database_client import DatabaseClient


class ManualRemove(object):
    """
    Handles removing a run from the database
    """

    def __init__(self, instrument, credentials=None):
        if credentials:
            self.database = DatabaseClient(credentials)
        else:
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
            if not value:
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
        for run_number, job_list in self.to_delete.items():
            for version in job_list:
                # Delete the specified version
                print('{}{}:'.format(self.instrument, run_number))
                # Delete reduction location record
                self.delete_record(self.database.reduction_location(),
                                   self.database.reduction_location().
                                   reduction_run_id == version.id)

                # Delete data location record
                self.delete_record(self.database.reduction_data_location(),
                                   self.database.reduction_data_location().
                                   reduction_run_id == version.id)

                # Delete run_variables
                self.delete_variables(version.id)

                # Delete reduction run record
                self.delete_record(self.database.reduction_run(),
                                   self.database.reduction_run().id == version.id)

            # Remove deleted run from dictionary
            del self.to_delete[run_number]

    def delete_variables(self, reduction_run_id):
        """
        Removes all the run parameters associated
        :return:
        """
        # Query runvariable using reduction_run_id to get all associated variable_ptr_id
        connection = self.database.get_connection()
        run_variables = connection.query(self.database.run_variables()) \
            .filter(self.database.run_variables().reduction_run_id == reduction_run_id).all()
        connection.commit()
        # Remove all the runvariables associated with the variable_ptr_id
        for record in run_variables:
            self.delete_record(self.database.run_variables(),
                               self.database.run_variables().variable_ptr_id ==
                               record.variable_ptr_id)

    def delete_record(self, query_value, filter_on):
        """
        Run a delete on the database
        :param query_value: the query to use
        :param filter_on: filtering options
        """
        connection = self.database.get_connection()
        connection.query(query_value).filter(filter_on).delete(synchronize_session='fetch')
        connection.commit()
        print('\t{} ... Deleted'.format(query_value))

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


def run(instrument, run_number):
    """
    Run the remove script
    :param instrument:
    :param run_number:
    """
    manual_remove = ManualRemove(instrument)
    manual_remove.find_runs_in_database(run_number)
    manual_remove.process_results()
    manual_remove.delete_records()


def main():
    """
    Parse user input and run the script
    """
    parser = argparse.ArgumentParser(description='Remove a run from the autoreduction service.',
                                     epilog='./manual_remove.py GEM 83880')
    parser.add_argument('instrument', metavar='instrument', type=str,
                        help='a string of the instrument name e.g "GEM"')
    parser.add_argument('start_run_number', metavar='start_run_number', type=int,
                        help='the start run number e.g. "83880"')
    args = parser.parse_args()
    instrument = args.instrument
    run_number = args.start_run_number
    run(instrument, run_number)


if __name__ == "__main__":  # pragma: no cover
    main()
