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

import pandas as pd
import csv


class PrepareData:

    def __init__(self):
        self.expected_first_row = "# X , Y , E"
        self.columns = ["Spectrum", "X", "Y", "E"]

    def prepare_data(self, path):
        processed_data = []
        with open(path, 'r') as input_file:
            self._check_first_row(input_file.readline())    # Using input_file to treat row as 1 string item
            spectrum = self._check_second_row(input_file.readline())

            reader = csv.reader(input_file)
            for row in reader:
                float_list = [float(item) for item in row]  # Ensures
                if len(float_list) is 1:
                    spectrum = int(row[0])
                else:
                    processed_data.append([spectrum]+float_list)

        return pd.DataFrame(processed_data, columns=self.columns)

    def _check_first_row(self, row_as_string):
        row = row_as_string.rstrip()
        if row != self.expected_first_row:
            error_message = (f"Unexpected first row of file.\n"
                             f"Expected:\t{self.expected_first_row}\n"
                             f"Actual:\t\t{row}\n"
                             f"\nDifference breakdown:\n")

            diff = ndiff(self.expected_first_row.splitlines(keepends=True),
                         row.splitlines(keepends=True))
            error_message += "\n".join(diff)

            raise RuntimeError(error_message)
        return True

    @staticmethod
    def _check_second_row(row_as_string):
        try:
            first_spectrum = int(row_as_string)
        except ValueError:
            error_message = (f"Unexpected second row of file.\n"
                             f"Expected: Integer (first spectrum number)\n"
                             f"Actual:\t\t{row_as_string}\n")
            raise RuntimeError(error_message)
        return first_spectrum
