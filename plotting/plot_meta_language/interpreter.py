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
    """
    This class reads in plot type files from given locations
    and interprets them as a dictionary to be used as a 'plotly' graph layout
    """
    @staticmethod
    def read(plot_type_file_location):
        """
        Reads a plot type file from a given location
        :param plot_type_file_location: The file path
        :return: A dictionary containing the data from the plot type file
        :raises RuntimeError: If location does not point to a file
        """
        try:
            with open(plot_type_file_location) as file:
                return yaml.full_load(file)
        except FileNotFoundError as exp:
            raise RuntimeError("The plot type file could not be " "found at the location provided.") from exp

    def interpret(self, plot_type_file_location):
        """
        Returns a layout dictionary based on the plot type file at the given location
        :param plot_type_file_location: The file path
        :return: Layout dictionary, to be used as a 'plotly' graph
        :raises RuntimeError: If either of the following occur:
            1) The plot type file is empty
            2) The plot type file data cannot be interpreted as a dict
        Note: an error message will describe which of these cases above has occurred.
        """
        file_data = self.read(plot_type_file_location)
        if len(file_data) < 1:
            raise RuntimeError("The plot type file is empty. " "Please see the example.yaml file for guidance.")
        if not isinstance(file_data, dict):
            raise RuntimeError("The format of the plot type file is not as expected. "
                               "Please see the example.yaml file for guidance.")
        lowercase_keys = [k.lower() for k in file_data.keys()]
        if len(file_data) == 1 and "figure" in lowercase_keys:
            file_data = file_data["figure"]

        return file_data
