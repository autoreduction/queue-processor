# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Reduction service contains the classes, and functions that performs a reduction
"""
import logging
import time
from pathlib import Path

from queue_processors.autoreduction_processor.settings import MISC

LOGGER = logging.getLogger(__file__)

class ReductionDirectory:
    """
    ReductionDirectory encapsulated directory creation, deletion and handling output type
    (flat or not)
    """

    def __init__(self, instrument, rb_number, run_number, overwrite=False):
        self.overwrite = overwrite
        self._is_flat_directory = instrument in MISC["flat_output_instruments"]
        self.path = Path(
            MISC["ceph_directory"] % (instrument, rb_number, run_number))
        self._build_path()
        self.log_path = self.path / "reduction_log"
        self.mantid_log = self.log_path / f"RB_{rb_number}_Run_{run_number}_Mantid.log"
        self.script_log = self.log_path / f"RB_{rb_number}_Run_{run_number}_Script.out"

    def create(self):
        """
        Creates the reduction directory including the log path, Script.out and Mantid.log files
        """
        LOGGER.info("Creating reduction directory: %s", self.path)
        self.path.mkdir(parents=True)
        self.log_path.mkdir()
        self.script_log.touch()
        self.mantid_log.touch()

    def delete(self):
        """
        Delete the Reduction directory and all of its contents recursively
        """
        LOGGER.info("Deleting directory: %s", self.path)
        for sleep in [0, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20]:
            self._rm_tree(self.path)
            if not self.path.exists():
                break
            time.sleep(sleep)
        else:
            LOGGER.warning("Failed to delete %s", self.path)

    def _rm_tree(self, path):
        for child in path.glob("*"):
            if child.is_file():
                try:
                    child.unlink()
                except FileNotFoundError:
                    pass
            else:
                self._rm_tree(child)
        path.rmdir()

    def _build_path(self):
        if self._is_flat_directory:
            self.path = self.path.parent
        else:
            self._append_run_version()

    def _append_run_version(self):
        if self.overwrite:
            self.path = self.path / "run-version-0"
        else:
            versions = [int(str(i).split("-")[-1])
                        for i in self.path.glob("run-version-[0-9]*") if i.is_dir()]
            try:
                self.path = self.path / f"run-version-{max(versions) + 1}"
            except ValueError:
                self.path = self.path / "run-version-0"

