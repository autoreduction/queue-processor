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
        self.expected_file_first_line = "# X , Y , E"

    # TODO: update draw.io
    def prepare_data(self, in_path, out_path):
        # TODO: consider pd.read_csv VS individual lines processed in turn
        #   Due to the file size, reading line by line might be more efficient
        with open(in_path, 'r') as in_file:
            reader = csv.reader(in_file)
            self._check_file_first_line(in_file.readline())

            with open(out_path, 'w') as out_file:
                for i, row in enumerate(reader):
                    writer = csv.writer(out_path)
                    if i > 20: break

    def _check_file_first_line(self, line):
        line = line.rstrip()
        if line != self.expected_file_first_line:
            error_message = (f"Unexpected first line of file.\n"
                             f"Expected:\t{self.expected_file_first_line}\n"
                             f"Actual:\t\t{line}\n")

            raise RuntimeError(error_message)
        return True

prep = PrepareData()
path = r"C:\Git\autoreduction\plotting\multi_spectra_data_file.csv"
prep.prepare_data(path)