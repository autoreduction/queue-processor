"""
Utility function to get project root directory
"""
import os
import git


def get_git_root():
    """
    Get project root
    :return: file path to the root of the project
    """
    git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")

    assert os.path.exists(git_root)
    return git_root
