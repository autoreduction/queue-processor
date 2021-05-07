# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
This script is expected to be called by a cronjob daily.

It will traverse all instrument folders in the archive (all NDX... folders),
grab reduce.py and reduce_vars.py and upload it to the repository.

The repository of the STORAGE_DIR needs to be manually configured to point to the correct
remote - otherwise this script will fail to commit/push.

There is also a --dry-run option that will just show which files are traversed,
but will not do anything.

The cronjob should be:

0 1 * * * python3 /home/reduce/backup_reduction_scripts.py

The reason it runs at 1AM is that the queue_processor restarting happens at midnight and
there might be some interference. There shouldn't be, but just in case it doesn't hurt
to be scheduled for a bit later.
"""
import os
import sys
import argparse
import datetime
import logging
import shutil
import traceback
from pathlib import Path

from git import Git, exc

from queue_processors.queue_processor.settings import PROJECT_ROOT

ISIS_MOUNT_PATH = Path("/isis")
AUTOREDUCTION_PATH = Path("user/scripts/autoreduction")
REDUCE_FILES_TO_SAVE = ["reduce.py", "reduce_vars.py"]

# STORAGE_DIR is the git repository dir that has been configured to point to the correct remote
STORAGE_DIR = Path("~/autoreduction_scripts").expanduser().absolute()

logging.basicConfig(filename=str(Path(PROJECT_ROOT, 'logs', 'backup_reduction_scripts.log')), level=logging.INFO)
log = logging.getLogger(__file__)
log.addHandler(logging.StreamHandler())


def check_if_git_directory(path: Path):
    """
    Ensures that the directory is a git repo.

    If it is not the function will raise

    :param path: The path to the directory
    """
    repo = Git(path.absolute())
    repo.status()


def ensure_storage_exists(path: Path):
    """
    Tries to make the storage directory, if it doesn't already exist.

    If it didn't succeed raises a RuntimeError.

    :param path: The path to the directory
    """
    path.mkdir(parents=True, exist_ok=True)

    if not path.is_dir():
        raise RuntimeError(f"Could not make the '{path}' directory.")


def get_today() -> str:
    """
    Returns today in "YYYY-MM-DD" format
    """
    return str(datetime.date.today())


def commit_and_push(path: Path):
    """
    Commits all files in the path directory and pushes to origin/master

    :param path: The path to the directory
    """
    repo = Git(path.absolute())
    today = get_today()
    repo.add(".")
    repo.commit("-m", f"Reduction files for {today}")
    repo.push("--set-upstream", "origin", "master")


def main(args):
    """
    Ensures expected directories exist. Then queries the ISIS_MOUNT_PATH for all folders
    starting with NDX, and iterates through each one checking if they contain a
    reduce.py and reduce_vars.py in the expected AUTOREDUCTION_PATH.

    If the expected python files are found they are copied to STORAGE_DIR
    and later committed and pushed to the storage repository.
    """
    ensure_storage_exists(STORAGE_DIR)

    try:
        check_if_git_directory(STORAGE_DIR)
    except exc.GitCommandError as err:  # pylint: disable=no-member
        log.error(
            "Destination folder %s is not a Git repository. "
            "Please configure it manually before running this script.", str(STORAGE_DIR))
        sys.exit(1)

    for inst in [directory for directory in os.listdir(ISIS_MOUNT_PATH) if directory.startswith("NDX")]:
        path = ISIS_MOUNT_PATH / inst / AUTOREDUCTION_PATH
        destination = STORAGE_DIR / inst / AUTOREDUCTION_PATH

        ensure_storage_exists(destination)

        for file in REDUCE_FILES_TO_SAVE:
            fullpath = path / file
            log.info("Copying %s to %s", fullpath, destination)
            if not args.dry_run:
                try:
                    shutil.copy(fullpath, destination, follow_symlinks=True)
                except OSError as err:
                    log.error("Could not copy last entry. Error: %s.\n\n %s", str(err), traceback.format_exc())
    if not args.dry_run:
        commit_and_push(STORAGE_DIR)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Backup reduction scripts")
    parser.add_argument("--dry-run",
                        action="store_true",
                        help="Dry run and display all files that will be copied and to where. But do nothing!")

    _args = parser.parse_args()

    main(_args)
