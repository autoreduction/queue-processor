"""
Collection of functions for file filtering
"""
import datetime
import os


def check_file_extension(file_to_check, accepted_extensions):
    """
    Ensures that the extension of a particular file is either .nxs or .raw
    :param file_to_check: the file being queried
    :param accepted_extensions: tuple of valid file extensions
    :return: True if the is .nxs/.raw
    """
    extensions = tuple(item.lower() for item in accepted_extensions)
    return file_to_check.lower().endswith(extensions)


def filter_files_by_extension(files_to_check, accepted_extensions):
    """
    Filter all files in a list by file extension
    :param files_to_check: List off all file to be checked for valid extensions
    :param accepted_extensions: List of valid extensions
    :return: List of files that have valid extensions
    """
    return [current_file for current_file in files_to_check
            if check_file_extension(current_file, accepted_extensions)]


def filter_files_by_time(directory, cut_off_time):
    """
    Filter all files in a given directory by modification time
    :param directory: directory containing files to check
    :param cut_off_time: The cut off time for files we are interested in
    :return: list of files that does not contain any file which has a
             most recent modification that was before the cut_off_time
    """
    all_files = os.listdir(directory)
    new_files = []
    for current_file in all_files:
        current_file = os.path.join(directory, current_file)
        modification_time = datetime.datetime.fromtimestamp(os.path.getmtime(current_file))
        if modification_time > cut_off_time:
            new_files.append(current_file)
    return new_files

