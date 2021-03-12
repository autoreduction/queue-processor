# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Prepares raw 'XYE' data to be plotted by converting it into a data frame.
"""
from difflib import ndiff

import csv
import pandas as pd


class PrepareData:
    """
    This class prepares data to be plotted by first reading it from a given path,
    validating initial rows are as expected, and ultimately converting the data
    into a pandas data frame.
    """
    def __init__(self):
        self.expected_first_row = "# X , Y , E"
        self.columns = ["Spectrum", "X", "Y", "E"]

    def prepare_data(self, path):
        """
        Reads raw XYE data from a given path.
        Validates initial 2 rows are as expected.
        Converts the data into a pandas.DataFrame
        :param path: The location of the XYE data to be prepared
        :return: The pandas.DataFrame comprising the data
        """
        processed_data = []
        with open(path, 'r') as input_file:
            self._check_first_row(input_file.readline())
            spectrum = self._check_second_row(input_file.readline())

            reader = csv.reader(input_file)
            for row in reader:
                float_list = [float(item) for item in row]
                if len(float_list) == 1:
                    spectrum = int(row[0])
                else:
                    processed_data.append([spectrum] + float_list)

        return pd.DataFrame(processed_data, columns=self.columns)

    def _check_first_row(self, row_as_string):
        """
        Validates the first row of the data by comparing it with the
        predefined expected_first_row
        :param row_as_string: The first row of the data in it's natural string format
        :return: True if the row matches the expected_first_row
        :raises RuntimeError: If the row does not match the expected_first_row.
            A breakdown of the differences between the expected and actual
            first row is provided.
        """
        row = row_as_string.rstrip()
        if row != self.expected_first_row:
            error_message = (f"Unexpected first row of file.\n"
                             f"Expected:\t{self.expected_first_row}\n"
                             f"Actual:\t\t{row}\n"
                             f"\nDifference breakdown:\n")

            diff = ndiff(self.expected_first_row.splitlines(keepends=True), row.splitlines(keepends=True))
            error_message += "\n".join(diff)

            raise RuntimeError(error_message)
        return True

    @staticmethod
    def _check_second_row(row_as_string):
        """
        Validates the second row of the data can be converted into an integer
        (i.e. that it is the first spectrum number)
        :param row_as_string: The second row of the data in it's natural string format
        :return: The row converted to an integer
        :raises RuntimeError: If the row cannot be cast to an integer.
        """
        try:
            first_spectrum = int(row_as_string)
        except ValueError as exp:
            error_message = (f"Unexpected second row of file.\n"
                             f"Expected: Integer (first spectrum number)\n"
                             f"Actual:\t\t{row_as_string}\n")
            raise RuntimeError(error_message) from exp
        return first_spectrum
