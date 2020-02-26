# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
A better model for a file or directory path than just strings
"""

import os


class PathError(RuntimeError):
    """ Custom version of run time error to add more detail"""
    pass


class Path(object):
    """
    A class to hold a path, specify what type of path it is (directory or file) and validate that it
    exists in the specified state (e.g. isfile() / isdir())
    """

    # pylint:disable=too-many-arguments
    def __init__(self, value, path_type,
                 validate_absolute=True,
                 validate_exists=True,
                 validate_readable=True,
                 validate_type=True,
                 validate_writable=False):
        """
        :param value: The string value of the path
        :param path_type: If the path is a directory or file (dir is also accepted)
        :param validate_absolute: Check if the path is absolute? Default: True
        :param validate_exists: Check if the path exists? Default: True
        :param validate_readable: Check if the path has read permissions? Default: True
        :param validate_writable: Check if the path has write permissions? Default: False
        """
        self.value = value
        path_type = path_type.lower()
        accepted_path_types = ['file', 'dir', 'directory']
        if path_type not in accepted_path_types:
            raise RuntimeError('Path type must be either \'directory\', \'dir\' or \'file\'.')
        if path_type == 'dir':
            path_type = 'directory'
        self.type = path_type
        # The different attributes the path should be validated against
        self.validate_absolute = validate_absolute
        self.validate_exists = validate_exists
        self.validate_readable = validate_readable
        self.validate_type = validate_type
        self.validate_writable = validate_writable

    def validate(self):
        """
        Ensure that paths are: absolute, exist, have read access and are file/directory
        If these conditions are not met, an exception is thrown
        """
        if not os.path.isabs(self.value) and self.validate_absolute:
            raise PathError("Path is not absolute: {}".format(self.value))
        if not os.path.exists(self.value) and self.validate_exists:
            raise PathError("Path doesn't exist: {}".format(self.value))
        if not os.access(self.value, os.R_OK) and self.validate_readable:
            raise PathError("Path is not readable: {}".format(self.value))
        if not os.access(self.value, os.W_OK) and self.validate_writable:
            raise PathError("Path is not writable: {}".format(self.value))
        if self.validate_type:
            if self.type == 'file':
                if not os.path.isfile(self.value):
                    raise PathError("Path is not a file: {}".format(self.value))
            if self.type == 'directory':
                if not os.path.isdir(self.value):
                    raise PathError("Path is not a directory: {}".format(self.value))
        return True

    def __eq__(self, other):
        if other.value == self.value and other.type == self.type:
            return True
        return False
