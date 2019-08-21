"""
Helper functions for paths
"""
import os

from paths.path import PathError


def is_path_windows(path):
    """
    Given a path, detect if the path is a windows path
    :param path: The path to examine
    :return: True (Windows) or False (Unix)
    """
    if '\\' in path and '/' in path:
        raise PathError('Path contains a mix of windows and linux separators: {}'.format(path))
    if '\\' in path:
        return True
    return False


def path_separator(path):
    """
    Given a path, return the type of separator to use either / or \\
    :param path: The path to examine
    :return
    """
    if is_path_windows(path):
        return '\\'
    return '/'


def add_separator_to_end_of_directory(path):
    """
    Add the correct separator to the end of a path if required
    :param path: The path to add to
    :return: The path with a separator added to the end e.g. /test/path becomes /test/path/
    """
    # If the path ends in a file then return immediately
    if '.' in os.path.split(path)[-1]:
        return path

    separator = path_separator(path)
    if path.endswith('\\') or path.endswith('/'):
        return path
    return path + separator


def add_to_path(path, list_to_append):
    """
    Given a path, append further directories / files with the correct separators
    :param path: The path to append to
    :param list_to_append: items to append to the file path
    :return: A file path items in the list_to_append appended to the original path
    """
    for item in list_to_append:
        path = add_separator_to_end_of_directory(path)
        path += item
    return path

