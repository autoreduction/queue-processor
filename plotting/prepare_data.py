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
        self.columns = ["Spectrum", "X", "Y", "E"]

    # TODO: consider pd.read_csv VS individual lines processed in turn
    #   Due to the file size, reading line by line might be more efficient
    def prepare_data(self, input_path, output_path):
        with open(input_path, 'r', ) as input_file:
            reader = csv.reader(input_file)
            first_row = input_file.readline()
            self._check_first_row(first_row)

            second_row = input_file.readline()
            try:
                spectrum = int(second_row)
            except ValueError:
                error_message = (f"Unexpected second row of file.\n"
                                 f"Expected: Integer (first spectrum number)\n"
                                 f"Actual:\t\t{second_row}\n")
                raise RuntimeError(error_message)

            processed_data = []
            for i, row in enumerate(input_file):
                float_list = self.raw_row_to_float_list(row)
                if len(float_list) is 1:
                    spectrum = int(row)
                else:
                    processed_data.append([spectrum]+float_list)
                    # print([spectrum]+float_list)
                # if i > 10000:
                #     break

            return pd.DataFrame(processed_data, columns=self.columns)



            # with open(output_path, 'w') as output_file:
            #     writer = csv.writer(output_file, delimiter=",")
            #     for i, row in enumerate(input_file):
            #         writer.writerow(self.raw_row_to_float_list(row))
            #         if i > 20:
            #             break

    @staticmethod
    def raw_row_to_float_list(row):
        row = row.rstrip()
        split_row = row.split(",")
        return [float(item) for item in split_row]



    def _check_first_row(self, line):
        line = line.rstrip()
        if line != self.expected_file_first_line:
            error_message = (f"Unexpected first row of file.\n"
                             f"Expected:\t{self.expected_file_first_line}\n"
                             f"Actual:\t\t{line}\n")

            raise RuntimeError(error_message)
        return True

prep = PrepareData()
in_path = r"C:\Git\autoreduction\plotting\multi_spectra_data_file.csv"
out_path = r"C:\Git\autoreduction\plotting\\"
out_name = "output.csv"
df = prep.prepare_data(in_path, out_path+out_name)
print(df)