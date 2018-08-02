import git
import os


def get_git_root():
    git_repo = git.Repo(os.getcwd(), search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")

    assert(os.path.exists(git_root))
    return git_root