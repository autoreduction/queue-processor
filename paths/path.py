# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
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

    def __init__(self, value, path_type):
        self.value = value
        path_type = path_type.lower()
        accepted_path_types = ['file', 'dir', 'directory']
        if path_type not in accepted_path_types:
            raise RuntimeError('Path type must be either \'directory\', \'dir\' or \'file\'.')
        if path_type == 'dir':
            path_type = 'directory'
        self.type = path_type

    def validate_path(self):
        """
        Ensure that paths are: absolute, exist, have read access and are file/directory
        If these conditions are not met, an exception is thrown
        """
        if not os.path.isabs(self.value):
            raise PathError("Path is not absolute: {}".format(self.value))
        if not os.path.exists(self.value):
            raise PathError("Path doesn't exist: {}".format(self.value))
        if not os.access(self.value, os.R_OK):
            raise PathError("Path is not readable: {}".format(self.value))
        if self.type == 'file':
            if not os.path.isfile(self.value):
                raise PathError("Path is not a file: {}".format(self.value))
        if self.type == 'directory':
            if not os.path.isdir(self.value):
                raise PathError("Path is not a directory: {}".format(self.value))

    def __eq__(self, other):
        if other.value == self.value and other.type == self.type:
            return True
        return False
