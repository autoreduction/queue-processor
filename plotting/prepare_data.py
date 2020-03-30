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
        self.expected_file_first_row = "# X , Y , E"
        self.columns = ["Spectrum", "X", "Y", "E"]

    # TODO: consider pd.read_csv VS individual lines processed in turn
    #   Due to the file size, reading line by line might be more efficient
    def prepare_data(self, path):
        with open(path, 'r', ) as input_file:
            first_row = input_file.readline()
            self._check_first_row(first_row)    # Using input_file to treat row as 1 string item

            second_row = input_file.readline()
            spectrum = self._check_first_row(second_row)

            reader = csv.reader(input_file)
            processed_data = []
            for i, row in enumerate(reader):
                float_list = [float(item) for item in row]  # Ensures
                if len(float_list) is 1:
                    spectrum = int(row[0])
                else:
                    processed_data.append([spectrum]+float_list)

            return pd.DataFrame(processed_data, columns=self.columns)

    def _check_first_row(self, row):
        row = row.rstrip()
        if row != self.expected_file_first_row:
            error_message = (f"Unexpected first row of file.\n"
                             f"Expected:\t{self.expected_file_first_row}\n"
                             f"Actual:\t\t{row}\n")

            raise RuntimeError(error_message)
        return True

    @staticmethod
    def _check_second_row(row):
        try:
            first_spectrum = int(row)
        except ValueError:
            error_message = (f"Unexpected second row of file.\n"
                             f"Expected: Integer (first spectrum number)\n"
                             f"Actual:\t\t{row}\n")
            raise RuntimeError(error_message)
        return first_spectrum


# TODO: Note - below for testing only
prep = PrepareData()
in_path = r"C:\Git\autoreduction\plotting\multi_spectra_data_file.csv"
df = prep.prepare_data(in_path)
print(df)
