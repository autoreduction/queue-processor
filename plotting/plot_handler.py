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
import os
import logging
from utils.clients.sftp_client import SFTPClient
from utils.project.structure import get_project_root

LOGGER = logging.getLogger('app')

INSTRUMENT_REGEX_MAP = {"MARI": "MAR(I)?", "WISH": "WISH"}


class PlotHandler:
    """
    Takes parameters for a run and (for now) checks if an associated image exists and retrieves it.
    :param instrument_name: (str) The name of the beamline/spectrometer/instrument.
    :param rb_number: (str)The ISIS RB number.
    :param run_number: (str/int) The run number on the given instrument for the given RB number.
    :param server_dir: (str) The path for the directory to search for the data/image files
    """

    def __init__(self, instrument_name, run_number, server_dir, rb_number=None):
        self.instrument_name = instrument_name
        self.rb_number = rb_number  # Used when searching for full Experiment graph
        self.run_number = run_number
        self.server_dir = server_dir
        self.file_extensions = ["png", "jpg", "bmp", "gif", "tiff"]
        # Directory to place fetched data files / images
        self.static_graph_dir = os.path.join(get_project_root(), 'WebApp',
                                             'autoreduce_webapp', 'static',
                                             'graphs')

    def _generate_file_name_regex(self, plot_type):
        """
        Regular expression used for looking for plot files.
        This assumes that the file names follow the convention:
        <instrument_abbreviation><run_number>*<.png or other extension>
        :param plot_type: (str) the type of file to be searched for, e.g. "png"
        """
        try:
            _inst_regex = INSTRUMENT_REGEX_MAP[self.instrument_name]
            return f'{_inst_regex}{self.run_number}.*.{plot_type}'
        except KeyError:  # Instrument name does not appear in dictionary of known instruments
            LOGGER.info("The instrument name is not recognised")
            return None

    def _check_for_plot_files(self):
        """
        Searches the server directory for existing plot files using the directory specified.
        :return: (list) files on the server path that match regex
        """
        # start sftpclient
        client = SFTPClient()
        # initialise list to store names of existing files matching the search
        _found_files = []
        for plot_type in self.file_extensions:
            # regular expression for plot file name(s)
            file_regex = self._generate_file_name_regex(plot_type=plot_type)
            # Add files that match regex to the list of files found
            _found_files.extend(client.get_filenames(server_dir_path=self.server_dir,
                                                     regex=file_regex))
        return _found_files

    def get_plot_file(self):
        """
        Searches for and retrieves a plot file from CEPH.
        Might find multiple files (e.g. if more than one plot_type is specified),
        but will only copy over one.
        :return: (str) local path to downloaded files OR None if no files found
        """
        _existing_plot_files = self._check_for_plot_files()
        if _existing_plot_files:
            # Generate paths to data on server and destination on local machine
            _server_path = self.server_dir + _existing_plot_files[0]
            _local_path = os.path.join(self.static_graph_dir, _existing_plot_files[0])

            client = SFTPClient()
            try:
                client.retrieve(server_file_path=_server_path,
                                local_file_path=_local_path,
                                override=True)
                LOGGER.info('File %s found and saved to %s', _server_path, _local_path)
            except RuntimeError:
                LOGGER.error("file does not exist")
                return None
            return f'/static/graphs/{_existing_plot_files[0]}'  # shortcut to static dir
        # No files found
        return None

    # pylint:disable=unnecessary-pass
    def construct_plot(self):
        """Calls the plot factory to construct an iframe from a NumpyArray and plot_type"""
        pass
