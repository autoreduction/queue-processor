# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
This script is expected to be called by a cronjob daily.

It will traverse all instruments in VALID_INSTRUMENTS, grab reduce.py and reduce_vars.py
and upload it to the repository.

The repository of the STORAGE_DIR needs to be manually configured to point to the correct
remote - otherwise this script will fail to commit/push.

There is also a --dry-run option that will just show which files are traversed,
but will not do anything.

"""

import sys
import argparse
import datetime
import logging
import shutil
import traceback
from datetime import date
from pathlib import Path

import git
from git import Git

from utils.project.static_content import LOG_FORMAT
from utils.project.structure import get_log_file
from utils.settings import VALID_INSTRUMENTS

ISIS_MOUNT_PATH = Path("/isis")
AUTOREDUCTION_PATH = Path("user/scripts/autoreduction")
REDUCE_FILES_TO_SAVE = ["reduce.py", "reduce_vars.py"]

STORAGE_DIR = Path("~/autoreduction_scripts").expanduser().absolute()

logging.basicConfig(filename=get_log_file('backup_reduction_scripts.log'),
                    level=logging.INFO,
                    format=LOG_FORMAT)
log = logging.getLogger(__file__)
log.addHandler(logging.StreamHandler())


def ensure_git_directory(path: Path):
    g = Git(path.absolute())
    g.status()


def ensure_storage_exists(path: Path):
    path.mkdir(exist_ok=True)

    if not path.is_dir():
        raise RuntimeError(f"Could not make the '{path}' directory.")


def get_today() -> str:
    return str(datetime.date.today())


def commit_and_push(path: Path):
    g = Git(path.absolute())
    today = get_today()
    g.add(".")
    g.commit("-m", f"Reduction files for {today}")
    g.push("--set-upstream", "origin", "master")


def main(args):
    ensure_storage_exists(STORAGE_DIR)

    try:
        ensure_git_directory(STORAGE_DIR)
    except git.exc.GitCommandError as err:  # pylint: disable=no-member
        log.error(
            "Destination folder %s is not a Git repository. "
            "Please configure it manually before running this script.", str(STORAGE_DIR))
        sys.exit(1)

    for inst in VALID_INSTRUMENTS:
        path = ISIS_MOUNT_PATH / f"NDX{inst}" / AUTOREDUCTION_PATH
        destination = STORAGE_DIR / inst

        ensure_storage_exists(destination)

        for file in REDUCE_FILES_TO_SAVE:
            fullpath = path / file
            log.info("Copying %s to %s", fullpath, destination)
            if not args.dry_run:
                try:
                    shutil.copy(fullpath, destination, follow_symlinks=True)
                except OSError as err:
                    log.error("Could not copy last entry. Error: %s.\n\n %s", str(err),
                              traceback.format_exc())
    if not args.dry_run:
        commit_and_push(STORAGE_DIR)


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Backup reduction scripts")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run and display all files that will be copied and to where. But do nothing!")

    args = parser.parse_args()

    main(args)
