# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
The interpreter for our plotting meta-language

Takes a file location of a plot-type file, written in our meta-language.
Read this meta-language data and interprets the data as a 'plotly' graph layout dictionary.
"""
import yaml


class Interpreter:

    def read(self, plot_type_file_location):
        try:
            with open(plot_type_file_location) as file:
                return yaml.full_load(file)
        except FileNotFoundError:
            raise RuntimeError("The plot type file could not be found at the location provided.")

    def interpret(self, plot_type_file_location):
        file_data = self.read(plot_type_file_location)
        if len(file_data) < 1:
            raise RuntimeError("The plot type file is empty. "
                               "Please see the example.yaml file for guidance.")
        elif not isinstance(file_data, dict):
            raise RuntimeError("The format of the plot type file is not as expected. "
                               "Please see the example.yaml file for guidance.")
        if len(file_data) == 1 and "figure" in file_data.keys():
            file_data = file_data["figure"]

        return file_data
