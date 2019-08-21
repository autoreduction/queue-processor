"""
Contains all of the path related functionality to perform reduction
"""
import os

from paths.collections import InputPaths, TemporaryPaths, OutputPaths
from paths.path_manipulation import add_to_path


class ReductionPathError(RuntimeError):
    """
    Implementation of RuntimeError to show that the error is relating to the reduction paths
    """
    pass


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
        self.output_paths = OutputPaths(output_directory=final_output_directory,
                                        output_script_directory=add_to_path(final_output_directory,
                                                                            ['reduction_log']))
        # Holds all of the paths for temporary output locations before data is migrated
        # to final destination
        temp_dir = add_to_path(temporary_root_directory, os.path.split(final_output_directory))
        self.temporary_paths = TemporaryPaths(root_directory=temporary_root_directory,
                                              data_output_directory=temp_dir,
                                              script_output_directory=add_to_path(temp_dir,
                                                                                  ['reduction_log'])
                                              )
