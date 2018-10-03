"""
Helper functions for navigating the project
"""

import os


def get_project_root():
    """
    Use git to find the project root
    :return: file path to root of the project folder
    """
    import git
    git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")

    assert os.path.exists(git_root)
    return git_root
