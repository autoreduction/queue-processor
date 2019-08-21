"""
Classes for different collections of paths that relate to each other for example a class that holds
all of the input paths (e.g. data_file, reduction_script, reduction_variables)
"""

from paths.path import Path


class AbstractPathCollection(object):
    """
    Abstract class to ensure that the self.all_paths variable exists and the paths are validated
    """

    def __init__(self):
        if not self.all_paths:
            raise RuntimeError('Collections must specify self.all_paths to allow for validation')

    def validate_files(self):
        for path in self.all_paths:
            path.validate_path()


class InputPaths(AbstractPathCollection):
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
        AbstractPathCollection.__init__(self)


class TemporaryPaths(AbstractPathCollection):
    """
    Data object to hold paths for temporary storage locations
    Temporary storage locations are required as an intermediate step to handle re-writing data
    and ensure we don't overwrite good data by mistake
    """

    def __init__(self, root_directory, data_output_directory, script_output_directory):
        # Full path to a temporary root directory (for data before it goes to final destination)
        self.root_directory = Path(root_directory, 'directory')
        # Full file path to the reduction data temporary directory (this is /temp/ + /output_dir/)
        self.data_output_directory = Path(data_output_directory, 'directory')
        # Full file path to the script output temporary directory (this is /temp/ + /reduction_log/)
        self.script_output_directory = Path(script_output_directory, 'directory')
        self.all_paths = [self.root_directory, self.data_output_directory,
                          self.script_output_directory]
        AbstractPathCollection.__init__(self)


class OutputPaths(AbstractPathCollection):
    """
    Data object to hold paths for output locations
    """

    def __init__(self, output_directory, output_script_directory):
        # Full path to the final location for the data
        self.output_directory = Path(output_directory, 'directory')
        # Full path to the directory to store log files (append to final output directory)
        self.output_script_directory = Path(output_script_directory, 'directory')
        self.all_paths = [self.output_directory, self.output_script_directory]
        AbstractPathCollection.__init__(self)
