import glob
import logging

LOGGER = logging.getLogger('app')


class PlotHandler(object):
    """Utility that takes parameters for a run and (for now) checks if an associated image exists and retrieves it."""

    def __init__(self, instrument_name, rb_number, run_number=None, plot_type=None):
        self.instrument_name = instrument_name
        self.rb_number = rb_number
        self.run_number = run_number
        if plot_type is None:
            # list of plot types the handler looks for if none is provided; could add vector graphics (.pdf, .eps)
            self.plot_type = ["jpg", "png", "bmp", "gif", "tiff"]
        # dictionary of regular expressions for each instruments that describe the possible prefixes in the plotfile name(s)
        self._instrument_dict = {"MARI": "MAR[I]", "WISH": "WISH"}
        # possible default picture to display when not plotfile exists:
        self._default_ifnoplot = "some_path_to_a_default_picture"
        # path to files for given RB number and instrument
        self._RBfolder = "/instrument/" + self.instrument_name + "/RBNumber/RB" + str(self.rb_number) + "/"

    # the method below is probably no longer needed as either a plot_type is passed to the PlotHandler or it automatically searches through the list in self.plot_type
    # def get_plot_type(self):
    #     """Returns the plot type for a particular run via database lookup from the reduction run variables"""
    #     pass

    def find_all_run_numbers(self):
        """Searches for all subdirectories in the RB folder (self._RBfolder) and extracts all run numbers from the subdirectory names."""
        # see possible solutions at https://stackoverflow.com/questions/800197/how-to-get-all-of-the-immediate-subdirectories-in-python
        _subdirectories = glob.glob(self._RBfolder + "*/")
        _run_numbers = _subdirectories.split("/")

    def find_plot_file(self, run_number, plot_type):
        """Searches for existing plot file(s) for a particular run on a specified instrument"""
        _directory = self._RBfolder + str(run_number) + "/"
        return glob.glob(_directory + self._regexp_for_file_lookup(plot_type=plot_type))

    def get_plot_file(self):
        """Calls the SFTP client to get the plot file from CEPH. Returns a PATH object to the local file downloaded from CEPH"""
        pass

    def _regexp_for_file_lookup(self, plot_type):
        """Regular expression used for looking for plot files. It assumes """
        try:
            _regexp = self._instrument_dict[self.instrument_name] + str(self.run_number) + "*." + plot_type
            return _regexp
        except KeyError:  # if the instrument name does not appear in the dictionary of known instruments
            LOGGER.info("The instrument name is not recognised")

    def construct_plot(self):
        """Calls the plot factory to construct an iframe from a NumpyArray and plot_type"""
        pass
