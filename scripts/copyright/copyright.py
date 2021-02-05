# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
# pylint:skip-file
"""
Class to add copyright statements to all files
"""
import sys
import os
import datetime
import argparse

# Directories to ignore - any pathss including these strings will be ignored, so it will cascade
directories_to_ignore = ["Documentation", "venv", ".pytesy_cache", "logs", ".git"]
# Accepted file extensions
accepted_file_extensions = [".py", ".yml"]


def get_copyright(year):
    """
    Creates a copyright statement as a string
    """
    return """# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; {0} ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #""".format(year)


def process_file_tree(path):
    """
    Walks the file tree processing each file
    :param path: The file path to start from
    """
    for dir_name, subdir_list, file_list in os.walk(path):
        if dir_name in directories_to_ignore:
            continue
        for filename in file_list:
            print('\t%s' % filename)
            basename, file_extension = os.path.splitext(filename)
            if file_extension.lower() in accepted_file_extensions:
                process_file(os.path.join(dir_name, filename))


def process_file(file_path):
    """
    Adds the copyright statement to the file
    :param file_path: The file path of a file to edit
    """
    with open(file_path, 'r') as file_handle:
        content = file_handle.readlines()
    with open(file_path, 'w') as file_handle:
        file_handle.write(get_copyright(datetime.datetime.now().year))
        file_handle.write('\n')
        for line in content:
            file_handle.write(line)


def main():
    parser = argparse.ArgumentParser(description='Add a copyright statement to all files in the project',
                                     epilog='./copyright.py /path/tp/project/root')
    parser.add_argument('file_path', metavar='file_path', type=str, help='project root directory')
    args = parser.parse_args()
    file_path = args.file_path
    if not os.path.isdir(file_path):
        print("supplied file path: \'{}\' was not recognised as a directory.".format(file_path))
        print("Please ensure directory exists and try again.")
        sys.exit(1)
    process_file_tree(file_path)


if __name__ == "__main__":
    main()
