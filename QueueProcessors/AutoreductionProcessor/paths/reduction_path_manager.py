"""
Contains all of the path related functionality to perform reduction
"""
import os


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
                 reduction_script_variables_path, temporary_output_directory,
                 final_output_directory):

        # Full path to the location of the input data FILE
        self.input_data_file_path = input_data_path
        # Full path to the location of the reduction script FILE
        self.reduction_script_file_path = reduction_script_path
        # Full path to the location of the reduction script variables
        self.reduction_script_variables_file_path = reduction_script_variables_path
        # Full path to a temporary directory for data before it goes to final destination
        # This is to handle re-writing data and ensure we don't overwrite good data by mistake
        self.temporary_output_directory = temporary_output_directory
        # Full path to the final location for the data
        self.final_output_directory = final_output_directory
        # Full path to the directory to store log files (append to final output directory)
        self.final_output_log_directory = self._add_log_dir_to_output_path()

        self.validate_paths()

    def validate_paths(self):
        """
        Validate all locations exist, they are files/directories, and readable
        """
        paths = {
            'input_data_path': ['file', self.input_data_file_path],
            'reduction_script_path': ['file', self.reduction_script_file_path],
            'reduction_script_variables_path': ['file', self.reduction_script_variables_file_path],
            'temporary_output_directory': ['dir', self.temporary_output_directory],
            'output_log_directory': ['dir', self.final_output_log_directory],
            'final_output_directory': ['dir', self.final_output_directory]
        }
        for path_name, value in paths.items():
            if not os.path.exists(value[1]):
                raise ReductionPathError("{} - Doesn't exist: {}".format(path_name, value[1]))
            if not os.path.isabs(value[1]):
                raise ReductionPathError("{} - Not absolute: {}".format(path_name, value[1]))
            if not os.access(value[1], os.R_OK):
                raise ReductionPathError("{} - Not readable: {}".format(path_name, value[1]))
            if value[0] == 'file':
                if not os.path.isfile(value[1]):
                    raise ReductionPathError("{} - Not file: {}".format(path_name, value[1]))
            if value[0] == 'dir':
                if not os.path.isdir(value[1]):
                    raise ReductionPathError("{} - Not directory: {}".format(path_name, value[1]))

    def _add_log_dir_to_output_path(self):
        """
        Identifies the type of path and the path ending then appends the 'reduction_log' directory
        in an appropriate manner
        :return: full path to the reduction_log directory in the output directory
        """
        # If linux
        if '/' in self.final_output_directory:
            if self.final_output_directory.endswith('/'):
                return self.final_output_directory + 'reduction_log/'
            return self.final_output_directory + '/reduction_log/'
        # If windows
        if '\\' in self.final_output_directory:
            if self.final_output_directory.endswith('\\'):
                return self.final_output_directory + 'reduction_log\\'
            return self.final_output_directory + '\\reduction_log\\'
