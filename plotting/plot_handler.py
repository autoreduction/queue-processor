# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Implements the PlotHandler class which acts as the controller for the plot functionality.
This class is (will be) responsible for:
Searching for and retrieving an existing plotting file via the SFTP client
Getting the associated plotting meta data file
Instructing the Plotting factory to build an IFrame based on the above
"""
import logging
from utils.clients.sftp_client import SFTPClient

LOGGER = logging.getLogger('app')


# pylint:disable=line-too-long, no-else-return
class PlotHandler:
    """
    Utility that takes parameters for a run and (for now) checks if an associated image exists and retrieves it.
    :param instrument_name: The name of the beamline/spectrometer/instrument.
    :param rb_number: The ISIS RB number.
    :param run_number: The run number on the given instrument for the given RB number.
    :param plot_type:
        The type of plot file / file extension to be searched for (e.g. "png"). Can be a list of extensions.
        If None, a list of common graphics file extensions is searched for.
    """

    def __init__(self, instrument_name, rb_number, run_number, plot_type=None):
        self.instrument_name = instrument_name
        self.rb_number = rb_number
        self.run_number = run_number
        if plot_type is None:
            # list of plot types the handler looks for if none is provided; it searches for the types in the order of
            # the list and selects the first one that exists. In future: could add vector graphics (.pdf, .eps)
            self.plot_type = ["png", "jpg", "bmp", "gif", "tiff"]
        elif isinstance(plot_type, str):
            # if only a single str is passed for a plot type then pass it into a list (so that a single for-loop can be
            # used to loop over plot types).
            self.plot_type = [plot_type]
        else:
            self.plot_type = plot_type
        # dictionary of regular expressions for each instrument to describe the possible prefixes in the file name(s)
        self._instrument_dict = {"MARI": "MAR[I]", "WISH": "WISH"}
        # path to directory with files for given instrument and RB number
        self._rbfolder = "/instrument/" + self.instrument_name + "/RBNumber/RB" + str(
            self.rb_number) + "/" + str(self.run_number) + "/autoreduced/"
        # parameter to store the file names of any existing plot files found
        self._existing_plot_files = []

    def _regexp_for_file_name(self, plot_type):
        """
        Regular expression used for looking for plot files. It assumes that the file names follow the convention
        <instrument_abbreviation><run_number>*<.png or other extension>
        """
        try:
            _regexp = self._instrument_dict[self.instrument_name] + str(
                self.run_number) + "*." + plot_type
            return _regexp
        except KeyError:  # if the instrument name does not appear in the dictionary of known instruments
            LOGGER.info("The instrument name is not recognised")

    def _check_for_plot_files(self):
        """
        Searches the CEPH directory for existing plot files using the directory specified by instrument_name, rb_number,
        run_number, and a regular expression for the file name based on the instrument_name, run_number and plot_type.
        """
        # start sftpclient
        client = SFTPClient()
        # initialise list to store names of existing files matching the search
        _found_files = []
        for plot_type_i in self.plot_type:
            # directory where existing plot file(s) would be located
            ceph_dir = self._rbfolder
            # regular expression for plot file name(s)
            file_regex = self._regexp_for_file_name(plot_type=plot_type_i)
            # use sftpclient to check if files matching the regular expression exist and add any matches to the list
            _found_files.extend(client.get_filenames(server_dir_path=ceph_dir, regex=file_regex))
        return _found_files

    def get_plot_file(self):
        """
        Searches for and retrieves a plot file from CEPH. Might find multiple files (e.g. if more than one plot_type is
        specified), but will only copy over one. If no existing plot file is found it does nothing at the moment.
        """
        self._existing_plot_files = self._check_for_plot_files()
        if len(self._existing_plot_files) == 0:  # no existing file was found
            return []  # return an empty list for now
        else:  # if one or more existing files were found, use the first one (order of items in plot_type affects this)
            _ceph_path = self._rbfolder + self._existing_plot_files[0]
            # in case the local path to which the file gets copied to needs to be specified
            _local_path = None
            # create sftpclient object and try to retrieve the file
            client = SFTPClient()
            try:
                client.retrieve(server_file_path=_ceph_path, local_file_path=_local_path, override=True)
            except RuntimeError:
                logging.error("file does not exist")
            return self._existing_plot_files  # this is currently not set

    # pylint:disable=unnecessary-pass
    def construct_plot(self):
        """Calls the plot factory to construct an iframe from a NumpyArray and plot_type"""
        pass
