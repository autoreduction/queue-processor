# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Contains all of the paths to perform reduction
"""

from paths.collections import InputPaths, TemporaryPaths, OutputPaths
from paths.path_manipulation import append_path, split


# pylint:disable=too-many-arguments,too-few-public-methods
class ReductionPathManager(object):
    """
    Hold the required paths for reduction and some basic validation functionality
    """

    def __init__(self, input_data_path, reduction_script_path,
                 reduction_variables_path, temporary_root_directory,
                 final_output_directory):

        # Holds all of the paths to the input locations for data
        self.input_paths = InputPaths(data_path=input_data_path,
                                      reduction_script_path=reduction_script_path,
                                      reduction_variables_path=reduction_variables_path)

        # Holds all of the paths for the final output location of the data
        self.output_paths = OutputPaths(data_directory=final_output_directory,
                                        log_directory=append_path(final_output_directory,
                                                                  ['reduction_log']))
        # Holds all of the paths for temporary output locations before data is migrated
        # to final destination
        temp_dir = append_path(temporary_root_directory, split(final_output_directory))
        self.temporary_paths = TemporaryPaths(root_directory=temporary_root_directory,
                                              data_directory=temp_dir,
                                              log_directory=append_path(temp_dir, ['reduction_log'])
                                             )
