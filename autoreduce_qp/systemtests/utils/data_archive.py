# ############################################################################### #
# Autoreduction Repository : https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
import logging
import os
from pathlib import Path
from shutil import rmtree
from contextlib import ContextDecorator
from typing import List, Optional

from autoreduce_utils.settings import SCRIPTS_DIRECTORY, CYCLE_DIRECTORY, ARCHIVE_ROOT

logger = logging.getLogger(__name__)


class DataArchive:
    """
    Class for the local data-archive used in the end to end tests.
    """

    def __init__(self, instruments: List[str], start_year: int, end_year: int):
        self.instruments = instruments
        self.start_year = start_year
        self.end_year = end_year

    def create(self) -> None:
        """
        Create the data-archive structure as required by the end to end tests
        """
        for instrument in self.instruments:
            self._create_cycle_path(instrument)
            self._create_script_directory(instrument)

    def add_reduction_script(self, instrument: str, script_text: str) -> None:
        """
        Given an instrument and a script text, create a reduce.py file in that instruments folder matching the given
        script text
        :param instrument: (str) the instrument for the reduce.py
        :param script_text: (str) the content for the reduce.py
        """
        location = Path(SCRIPTS_DIRECTORY % instrument, "reduce.py")
        self._create_file_at_location(location, script_text)

    def add_reduce_vars_script(self, instrument: str, script_text: str):
        """
        Given an instrument and script_text, create the reduce_vars.py file for that instrument with the given script
        text
        :param instrument: (str) the instrument for the reduce_vars.py
        :param script_text: (str) the content of the reduce_vars.py
        """
        location = Path(SCRIPTS_DIRECTORY % instrument, "reduce_vars.py")
        self._create_file_at_location(location, script_text)

    @staticmethod
    def add_data_file(instrument: str, datafile_name: str, year: int, cycle_num: int) -> str:
        """
        Given an instrument, datafile name, year and cycle number. Create a datafile in the appropriate place within
        the data-archive
        :param instrument: (str) The instrument of the datafile
        :param datafile_name: (str) The name of the datafile
        :param year: (int) The year of the run in the format yy where xxyy is the full year
        :param cycle_num: (int) The cycle number for that year
        :return: (str) The string path of the datafile created.
        """
        location = Path(CYCLE_DIRECTORY % (instrument, f"{year}_{cycle_num}"))
        os.makedirs(location, mode=0o777, exist_ok=True)
        datafile = Path(location, datafile_name)
        datafile.touch()
        os.chmod(datafile, 0o777)
        return str(datafile)

    def _create_cycle_path(self, instrument: str) -> None:
        for year in range(self.start_year, self.end_year):
            for cycle_number in range(1, 6):
                path = Path(CYCLE_DIRECTORY % (instrument, f"{year}_{cycle_number}"))
                os.makedirs(path, mode=0o777, exist_ok=True)

    @staticmethod
    def _create_script_directory(instrument: str) -> None:
        Path(SCRIPTS_DIRECTORY % instrument).mkdir(parents=True, exist_ok=True)
        os.chmod(Path(SCRIPTS_DIRECTORY % instrument), 0o777)

    @staticmethod
    def _create_file_at_location(location: Path, file_text: str) -> None:
        logger.info("Creating file at location %s", location)
        with open(location, encoding="utf-8", mode="w+") as fle:
            fle.write(file_text)
        os.chmod(location, 0o777)

    @staticmethod
    def delete() -> None:
        """
        Remove the created data-archive from disk.
        """
        rmtree(ARCHIVE_ROOT)


class DefaultDataArchive(ContextDecorator):
    """
    Provides a context managed data archive that creates and deletes itself with some sample values.
    """

    def __init__(self, instrument_name) -> None:
        self.instrument_name = instrument_name
        self.data_archive = DataArchive([self.instrument_name], 21, 21)

    def __enter__(self):
        self.data_archive.create()
        self.data_archive.add_reduction_script(self.instrument_name, """def main(in_f, out_d): print('some text')""")
        self.data_archive.add_reduce_vars_script(self.instrument_name, """standard_vars={"variable1":"value1"}""")

    def __exit__(self, *exc) -> Optional[bool]:
        self.data_archive.delete()
