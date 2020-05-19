# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
import logging
from utils.clients.sftp_client import SFTPClient
LOGGER = logging.getLogger('app')


class PlotHandler(object):
    """
    Utility that takes parameters for a run and (for now) checks if an associated image exists, retrieves it and
    displays the image on the webpage.
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
        self._RBfolder = "/instrument/" + self.instrument_name + "/RBNumber/RB" + str(self.rb_number) + "/autoreduced/"
        # parameter to store the file path for the copied plot file
        self.plot_file_names = []

    def _regexp_for_file_name(self, plot_type):
        """
        Regular expression used for looking for plot files. It assumes that the file names follow the convention
        <instrument_abbreviation><run_number>*<.png or other extension>
        """
        try:
            _regexp = self._instrument_dict[self.instrument_name] + str(self.run_number) + "*." + plot_type
            return _regexp
        except KeyError:  # if the instrument name does not appear in the dictionary of known instruments
            LOGGER.info("The instrument name is not recognised")

    def _check_for_plot_files(self):
        """
        Searches the CEPH directory for existing plot files using the directory specified by instrument_name, rb_number
        and run_number, and a regular expression for the file name based on the instrument_name, run_number and plot_type.
        """
        for plot_type_i in self.plot_type:
            # directory where existing plot file(s) would be located
            CEPH_dir = self._RBfolder
            # regular expression for plot file name(s)
            file_regex = self._regexp_for_file_name(plot_type=plot_type_i)
            # use sftpclient to check if suitable file name(s) exist and add them to the plot_file_names
            client = SFTPClient()
        return client.get_filenames(server_dir_path=CEPH_dir, regex=file_regex)

    def _get_single_plot_file(self, CEPH_path, local_path=None):
        """
        Calls the SFTP client to copy a single plot file from CEPH.
        :param CEPH_path: the complete path to the file to be retrieved
        :param local_path: (from sftp client documentation:)
            The location to download the file to, including filename with extension.
            If None, local_path is the local directory.
        """
        client = SFTPClient()
        try:
            client.retrieve(server_path=CEPH_path, local_path=local_path, override=True)
        except RuntimeError:
            logging.Error("file does not exist")

    def get_plot_file(self):
        """
        Searches for and retrieves a plot file from CEPH. Might find multiple files (e.g. if more than one plot_type is
        specified), but will only copy over one. If no existing plot file is found it does nothing at the moment.
        """
        self.plot_file_names = self._check_for_plot_files()
        if len(self.plot_file_names)=0:  # no existing file was found
            return False
        else:  # if one or more existing files were found, use the first one (order of items in plot_type affects this)
            _ceph_path = self._RBfolder + self.plot_file_names[0]
            # in case the local path to which the file gets copied to needs to be specified
            _local_path=None
            # create sftpclient object and try to retrieve the file
            client = SFTPClient()
            try:
                client.retrieve(server_path=_ceph_path, local_path=_local_path, override=True)
            except RuntimeError:
                logging.Error("file does not exist")
            return True

    def construct_plot(self):
        """Calls the plot factory to construct an iframe from a NumpyArray and plot_type"""
        pass
