# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Helper functions for navigating the project
"""

import os
import git


def get_project_root() -> str:
    """
    Use git to find the project root
    :return: file path to root of the project folder
    """
    # pylint:disable=import-outside-toplevel
    git_repo = git.Repo(os.path.dirname(os.path.realpath(__file__)), search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")

    assert os.path.exists(git_root)
    return str(git_root)


def get_log_file(filename):
    """
    Get the full file path to a log file. This function will make the
    file if it does not exist
    :param filename: The name of the log file to find
    :return: a path to the log file
    """
    file_path = os.path.join(get_project_root(), 'logs', str(filename))
    if not os.path.exists(file_path):
        with open(file_path, 'w') as _:
            pass
    return file_path


PROJECT_ROOT = get_project_root()
