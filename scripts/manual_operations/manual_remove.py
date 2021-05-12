# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Functionality to remove a reduction run from the database
"""
from __future__ import print_function

import sys

import fire
from django.db import IntegrityError
from model.database import access as db
from model.database.django_database_client import DatabaseClient
from scripts.manual_operations.util import get_run_range


class ManualRemove:
    """
    Handles removing a run from the database
    """
    def __init__(self, instrument):
        """
        :param instrument: (str) The name of the instrument associated with runs
        """
        self.database = DatabaseClient()
        self.database.connect()
        self.to_delete = {}
        self.instrument = instrument

    def find_run_versions_in_database(self, run_number):
        """
        Find all run versions in the database that relate to a given instrument and run number
        :param run_number: (int) The run to search for in the database
        :return: (QuerySet) The result of the query
        """
        instrument_record = db.get_instrument(self.instrument)
        result = self.database.data_model.ReductionRun.objects \
            .filter(instrument=instrument_record.id) \
            .filter(run_number=run_number) \
            .order_by('-created')
        self.to_delete[run_number] = list(result)
        return result

    def process_results(self, delete_all_versions: bool):
        """
        Process all the results what to do with the run based on the result of database query
        """
        copy_to_delete = self.to_delete.copy()
        for key, value in copy_to_delete.items():
            if not value:
                self.run_not_found(run_number=key)
            if len(value) == 1:
                continue
            if len(value) > 1 and not delete_all_versions:
                self.multiple_versions_found(run_number=key)

    def run_not_found(self, run_number):
        """
        Inform user and remove key from dictionary
        :param run_number: (int) The run to remove from the dictionary
        """
        print('No runs found associated with {} for instrument {}'.format(run_number, self.instrument))
        del self.to_delete[run_number]

    def multiple_versions_found(self, run_number):
        """
        Ask the user which versions they want to remove
        Update the self.to_delete dictionary by removing unwanted versions
        :param run_number: (int) The run number with multiple versions
        """
        # Display run_number - title - version for all matching runs
        print("Discovered multiple reduction versions for {}{}:".format(self.instrument, run_number))
        for run in self.to_delete[run_number]:
            print("\tv{} - {}".format(run.run_version, run.run_description))

        # Get user input for which versions they wish to delete
        user_input = input("Which runs would you like to delete (e.g. 0,1,2,3 or 0-3): ")
        input_valid, user_input = self.validate_csv_input(user_input)
        while input_valid is False:
            user_input = input('Input was invalid. ' 'Please provide a comma separated list or a range of values: ')
            input_valid, user_input = self.validate_csv_input(user_input)

        # Remove runs that the user does NOT want to delete from the delete list
        self.to_delete[run_number] = [
            reduction_job for reduction_job in self.to_delete[run_number] if reduction_job.run_version in user_input
        ]

    def delete_records(self):
        """
        Delete all records from the database that match those found in self.to_delete
        """
        # Make a copy to ensure dict being iterated stays same size through processing
        to_delete_copy = self.to_delete.copy()
        for run_number, job_list in to_delete_copy.items():
            for version in job_list:
                print(f'Deleting {self.instrument}{run_number} - v{version.run_version}')
                try:
                    version.delete()
                except IntegrityError as err:
                    print(f"Encountered integrity error: {err}\n\n"
                          "Reverting to old behaviour - manual deletion. This can take much longer.")
                    # For some reason some entries can throw an integrity error.
                    # In that case we revert to the previous (much slower) way of manually
                    # deleting everything. Perhaps there is a badly configured relation
                    # but I am not sure why it works on _most_
                    self.delete_reduction_location(version.id)
                    self.delete_data_location(version.id)
                    self.delete_variables(version.id)
                    self.delete_reduction_run(version.id)

    def delete_reduction_location(self, reduction_run_id):
        """
        Delete a ReductionLocation record from the database
        :param reduction_run_id: (int) The id of the associated reduction job
        """
        self.database.data_model.ReductionLocation.objects \
            .filter(reduction_run_id=reduction_run_id) \
            .delete()

    def delete_data_location(self, reduction_run_id):
        """
        Delete a DataLocation record from the database
        :param reduction_run_id: (int) The id of the associated reduction job
        """
        self.database.data_model.DataLocation.objects \
            .filter(reduction_run_id=reduction_run_id) \
            .delete()

    def delete_variables(self, reduction_run_id):
        """
        Removes all the RunVariable records associated with a given ReductionRun from the database
        :param reduction_run_id: (int) The id of the associated reduction job
        """
        run_variables = self.find_variables_of_reduction(reduction_run_id)
        for record in run_variables:
            self.database.variable_model.RunVariable.objects \
                .filter(variable_ptr_id=record.variable_ptr_id) \
                .delete()

    def find_variables_of_reduction(self, reduction_run_id):
        """
        Find all the RunVariable records in the database associated with a reduction job
        :param reduction_run_id: (int) The id of the reduction job to filter by
        :return: (QuerySet) of the associated RunVariables
        """
        return self.database.variable_model.RunVariable.objects \
            .filter(reduction_run_id=reduction_run_id)

    def delete_reduction_run(self, reduction_run_id):
        """
        Delete a ReductionRun record from the database
        :param reduction_run_id: (int) The id of the associated reduction job
        """
        self.database.data_model.ReductionRun.objects \
            .filter(id=reduction_run_id) \
            .delete()

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
        elif "-" in user_input:
            range_of_versions_to_delete = user_input.split('-')
            if len(range_of_versions_to_delete) != 2:
                return False, []

            sorted_range_of_versions = sorted(map(int, range_of_versions_to_delete))
            smaller_version = int(sorted_range_of_versions[0])
            larger_version = int(sorted_range_of_versions[1])

            return True, list(range(smaller_version, larger_version + 1))
        else:
            try:
                user_input = int(user_input)
                processed_input.append(user_input)
            except ValueError:
                return False, []
        return True, processed_input


def remove(instrument, run_number, delete_all_versions: bool):
    """
    Run the remove script for an instrument and run_number
    :param instrument: (str) Instrument to run on
    :param run_number: (int) The run number to remove
    """
    manual_remove = ManualRemove(instrument)
    manual_remove.find_run_versions_in_database(run_number)
    manual_remove.process_results(delete_all_versions)
    manual_remove.delete_records()


def user_input_check(instrument, run_numbers):
    """
    User prompt for boolean value to to assert if user really wants to remove N runs
    :param instrument (str) Instrument name related to runs user intends to remove
    :param run_numbers (range object) range of instruments submitted by user
    :return (bool) True or False to confirm removal of N runs or exit script
    """
    valid = {"Y": True, "N": False}

    print(f"You are about to remove more than 10 runs from {instrument} \n"
          f"Are you sure you want to remove run numbers: {run_numbers[0]}-{run_numbers[-1]}?")
    user_input = input("Please enter Y or N: ").upper()

    try:
        return valid[user_input]
    except KeyError:
        print("Invalid input, please enter either 'Y' or 'N' to continue to exit script")
    return user_input


def main(instrument: str, first_run: int, last_run: int = None, delete_all_versions=False):
    """
    Parse user input and run the script to remove runs for a given instrument
    :param instrument: (str) Instrument to run on
    :param first_run: (int) First run to be removed
    :param last_run: (int) Optional last run to be removed
    :param delete_all_versions: (bool) Deletes all versions for a run without asking
    """
    run_numbers = get_run_range(first_run, last_run=last_run)

    instrument = instrument.upper()

    if len(run_numbers) >= 10:
        user_input = user_input_check(instrument, run_numbers)
        if not user_input:
            sys.exit()

    for run in run_numbers:
        remove(instrument, run, delete_all_versions)


if __name__ == "__main__":  # pragma: no cover
    fire.Fire(main)
