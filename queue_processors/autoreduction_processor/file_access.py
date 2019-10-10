"""
Helper functions to check for file access permisions, existance, etc.
"""
import os


class PermissionException(Exception):
    pass


def create_dir_if_does_not_exist(path):
    """
    Check if a path exists and if it is a directory
    If not create that directory
    """
    if not os.path.isdir(path):
        os.makedirs(path)


def check_exists(path):
    """
    Check if a file has read access, else raise exception
    """
    if not os.access(path, os.F_OK):
        raise PermissionException("Path: {} - does not exist")


def check_read(path):
    """
    Check if a file has read access, else raise exception
    """
    if not os.access(path, os.R_OK):
        raise PermissionException("Path: {} - Does not have read access")


def check_write(path):
    """
    Check if a file has read access, else raise exception
    """
    if not os.access(path, os.W_OK):
        raise PermissionException("Path: {} - Does not have write access")
