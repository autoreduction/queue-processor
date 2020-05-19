# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
import logging
LOGGER = logging.getLogger('app')


class PlotHandler(object):
    """
    Utility that takes parameters for a run and (for now) checks if an associated image exists, retrieves it and
    displays the image on the webpage.
    :param instrument_name: The name of the beamline/spectrometer/instrument.
    :param rb_number: The ISIS RB number.
    :param run_number: The run number on the given instrument for the given RB number.
    :param plot_type:
        The type of plot file / file extension to be searched for (e.g. "png").
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
        self.plot_file_path = None

    def _get_single_plot_file(self, CEPH_path):
        """Calls the SFTP client to get a single plot file from CEPH. Returns a PATH object to the local file
        downloaded from CEPH."""
        client = SFTPClient()
        try:
            client.retrieve(server_path=CEPH_path, local_path=None)
        except RuntimeError:
            logging.Error("file does not exist")

    def get_plot_file(self):
        """Searches for and retrieves a plot file from CEPH. Can search for multiple plot types. If no existing plot
        file is found a default picture is retrieved instead. Returns a PATH object to the local file downloaded from CEPH."""
        for plot_type_i in self.plot_type:
            # combine directory and regular expression for file name into the file path to be looked up
            CEPH_path = self._RBfolder + self._regexp_for_file_name(run_number=self.run_number, plot_type=plot_type_i)
            local_path = "/local/directory/for/storing/the/file"
            try:
                # try to retrieve the file, if it is found, set the flag_file_exists and break out of the loop
                self.plot_file_path = self._get_single_plot_file(CEPH_path=CEPH_path, local_path=None)
                break
            except RuntimeError:
                # if the file does not exist, continue looping/looking
                pass
        if self.plot_file_path is None:
            # if no existing plot file has been found do nothing
            pass
        return self.plot_file_path

    def _regexp_for_file_name(self, run_number, plot_type):
        """
        Regular expression used for looking for plot files. It assumes that the file names follow the convention
        <instrument_abbreviation><run_number>*<.png or other extension>
        """
        try:
            _regexp = self._instrument_dict[self.instrument_name] + run_number + "*." + plot_type
            return _regexp
        except KeyError:  # if the instrument name does not appear in the dictionary of known instruments
            LOGGER.info("The instrument name is not recognised")

    def construct_plot(self):
        """Calls the plot factory to construct an iframe from a NumpyArray and plot_type"""
        pass


import os


def _futurefunctionality_find_all_run_numbers(self):
    """Searches for all subdirectories in the RB folder (self._RBfolder). This functionality will be needed to automate
    the plot_handler to work for all run numbers with a particular RB folder."""
    # see possible solutions at
    # https://stackoverflow.com/questions/800197/how-to-get-all-of-the-immediate-subdirectories-in-python
    # Could use f.name instead of f.path to extract all run numbers from the subdirectory names instead.
    _subdirectories = [f.path for f in os.scandir(self._RBfolder) if f.is_dir()]
    return _subdirectories
