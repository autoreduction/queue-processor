# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Classes for different collections of paths that relate to each other for example a class that holds
all of the input paths (e.g. data_file, reduction_script, reduction_variables)
"""

from paths.path import Path


# pylint:disable=too-few-public-methods
class PathCollection(object):
    """
    Abstract class to ensure that the self.all_paths variable exists and the paths are validated
    """

    all_paths = []

    def __init__(self):
        if not self.all_paths:
            raise RuntimeError('Collections must specify self.all_paths to allow for validation')
        self.validate_paths()

    def validate_paths(self):
        """
        Runs the validate path function for all the paths in the self.all_paths variable
        """
        for path in self.all_paths:
            path.validate_path()


# pylint:disable=too-few-public-methods
class InputPaths(PathCollection):
    """
    Data object to hold paths for input locations
    """

    def __init__(self, data_path, reduction_script_path, reduction_variables_path):
        # Full path to the location of the input data FILE
        self.data_path = Path(data_path, 'file')
        # Full path to the location of the reduction script FILE
        self.reduction_script_path = Path(reduction_script_path, 'file')
        # Full path to the location of the reduction script variables
        self.reduction_variables_path = Path(reduction_variables_path, 'file')
        self.all_paths = [self.data_path, self.reduction_script_path, self.reduction_variables_path]
        PathCollection.__init__(self)


# pylint:disable=too-few-public-methods
class TemporaryPaths(PathCollection):
    """
    Data object to hold paths for temporary storage locations
    Temporary storage locations are required as an intermediate step to handle re-writing data
    and ensure we don't overwrite good data by mistake
    """

    def __init__(self, root_directory, data_directory, log_directory):
        # Full path to a temporary root directory (for data before it goes to final destination)
        self.root_directory = Path(root_directory, 'directory')
        # Full file path to the reduction data temporary directory (this is /temp/ + /output_dir/)
        self.data_directory = Path(data_directory, 'directory')
        # Full file path to the script output temporary directory (this is /temp/ + /reduction_log/)
        self.log_directory = Path(log_directory, 'directory')
        self.all_paths = [self.root_directory, self.data_directory, self.log_directory]
        PathCollection.__init__(self)


# pylint:disable=too-few-public-methods
class OutputPaths(PathCollection):
    """
    Data object to hold paths for output locations
    """

    def __init__(self, data_directory, log_directory):
        # Full path to the final location for the data
        self.data_directory = Path(data_directory, 'directory')
        # Full path to the directory to store log files (append to final output directory)
        self.log_directory = Path(log_directory, 'directory')
        self.all_paths = [self.data_directory, self.log_directory]
        PathCollection.__init__(self)
