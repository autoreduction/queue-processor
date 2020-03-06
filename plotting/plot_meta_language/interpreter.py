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


# TODO:
#   - Do I need try-excepts? (can just test those raised already)
#   - Make docstrings
#   - Make tests
class Interpreter:

    def read(self, plot_type_file_location):
        with open(plot_type_file_location) as file:
            return yaml.full_load(file)

    def interpret(self, plot_type_file_location):
        file_data = self.read(plot_type_file_location)
        if not isinstance(file_data, dict) or len(file_data) < 1:
            raise RuntimeError("Format of yaml file not as expected."
                               "Please see the example.yaml file for guidance.")
        if len(file_data) == 1 and "figure" in file_data.keys():
            file_data = file_data["figure"]

        return file_data


location = r"plot_types\edward_example.yaml"
# location = "test"
inter = Interpreter()
layout = inter.interpret(location)
print(f"layout: {layout}")