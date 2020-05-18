import glob
import os
import logging
LOGGER = logging.getLogger('app')

from utils.clients.sftp_client import SFTPClient

class PlotHandler(object):
    """Utility that takes parameters for a run and (for now) checks if an associated image exists, retrieves it and displays the image on the webpage."""

    def __init__(self, instrument_name, rb_number, run_number=None, plot_type=None):
        self.instrument_name = instrument_name
        self.rb_number = rb_number
        # path to files for given RB number and instrument
        self._RBfolder = "/instrument/" + self._instrument_dict[self.instrument_name] + "/RBNumber/RB" + str(self.rb_number) + "/autoreduced/"
        self.run_number = run_number
        if plot_type is None:
            # list of plot types the handler looks for if none is provided; could add vector graphics (.pdf, .eps)
            self.plot_type = ["jpg", "png", "bmp", "gif", "tiff"]
        # dictionary of regular expressions for each instruments that describe the possible prefixes in the plotfile name(s)
        self._instrument_dict = {"MARI": "MAR[I]", "WISH": "WISH"}
        # possible default picture to display when no plotfile exists:
        self._default_ifnoplot = "some_path_to_a_default_picture"


    # the method below is probably no longer needed as either a plot_type is passed to the PlotHandler or it automatically searches through the list in self.plot_type
    # def get_plot_type(self):
    #     """Returns the plot type for a particular run via database lookup from the reduction run variables"""
    #     pass

    def _find_single_plot_file(self, run_number, plot_type):
        """Searches for a single, existing plot file for a particular run on a specified instrument."""
        _directory = self._RBfolder + str(run_number) + "/"
        return glob.glob(_directory + self._regexp_for_file_lookup(plot_type=plot_type))

    def find_plot_file(self):
        """Searches for any existing plot files, allowing for a list of run numbers and plot types on a specified instrument. Returns a list of PATH objects to the existing CEPH files"""
        file_paths=[]
        #if no run_number is passed, use the SFTP client to find all run numbers from the subdirectories in the RBfolder
        if self.run_number is None:
            run_numbers=self._find_all_run_numbers()
        else:
            run_numbers=run_numbers
        # loop over all combinations of run numbers and
        for run_i in run_numbers:
            for plot_i in self.plot_type:
                filepaths.append(self._find_single_plot_file(run_number=run_i, plot_type=plot_i))
        return file_paths

    def _get_single_plot_file(self,CEPH_path,local_path):
        """Calls the SFTP client to get a single plot file from CEPH. Returns a PATH object to the local file downloaded from CEPH."""
        client = SFTPClient()
        try:
            file = client.retrieve(CEPH_path,local_path=local_path)
        except RuntimeError:
            logging.Error("file does not exist")
        return local_path

    def get_plot_file(self):
        """Calls the SFTP client to get all relevant plot files from CEPH. Returns a list of PATH objects to the local file downloaded from CEPH."""
        CEPH_paths=self.find_plot_file()
        self._get_single_plot_file(file_i)
        return file_aths

    def construct_plot(self):
        """Calls the plot factory to construct an iframe from a NumpyArray and plot_type"""
        pass

    def _regexp_for_file_lookup(self, run_number, plot_type):
        """Regular expression used for looking for plot files. It assumes """
        try:
            _regexp = self._instrument_dict[self.instrument_name] + run_number + "*." + plot_type
            return _regexp
        except KeyError:  # if the instrument name does not appear in the dictionary of known instruments
            LOGGER.info("The instrument name is not recognised")

    def _find_all_run_numbers(self):
        """Searches for all subdirectories in the RB folder (self._RBfolder). This functionality will be needed to automate the plot_handler to work for all run numbers with a particular RB folder."""
        # see possible solutions at https://stackoverflow.com/questions/800197/how-to-get-all-of-the-immediate-subdirectories-in-python
        # Could use f.name instead of f.path to extract all run numbers from the subdirectory names instead.
        _subdirectories = [f.path for f in os.scandir(self._RBfolder) if f.is_dir()]
        return _subdirectories

