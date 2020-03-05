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
    def __init__(self, plot_type_file_location):
        self.file_location = plot_type_file_location

    def read(self):
        with open(self.file_location) as file:
            file_data = yaml.full_load(file)
            print(file_data)
            return file_data


location = r"plot_types\example.yaml"
inter = Interpreter(location)
data = inter.read()