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
import os
import traceback
import re
import shutil
from typing import List, Optional, Tuple
from WebApp.autoreduce_webapp.autoreduce_webapp.settings import STATIC_ROOT

LOGGER = logging.getLogger('app')


class PlotHandler:
    """
    Takes parameters for a run and (for now) checks if an associated image exists and retrieves it.
    :param data_filepath: (str) The full path to the input data
    :param server_dir: (str) The path for the directory to search for the data/image files
    :param rb_number: (str)The ISIS RB number.
    """
    def __init__(self, data_filepath: str, server_dir: str, rb_number: str = None):
        self.data_filename: str = self._get_only_data_file_name(data_filepath)
        # Used when searching for full Experiment graph. TODO: not actually used right now
        self.rb_number = rb_number
        # this is a path somewhere on CEPH
        self.server_dir = server_dir
        self.file_extensions = ["png", "jpg", "bmp", "gif", "tiff", "json"]
        # Directory to place fetched data files / images
        self.static_graph_dir = os.path.join(STATIC_ROOT, 'graphs')

    @staticmethod
    def _get_only_data_file_name(data_filepath: str) -> str:
        """
        Parses the file name to return the name of the data file only.

        Currently assumes the path is a Windows path!

        :param data_filepath: (str) The full path to the input data
        """
        if "\\" in data_filepath:
            sep = "\\"
        else:
            sep = "/"
        full_filename = data_filepath.split(sep)[-1]
        filename, _ = os.path.splitext(full_filename)
        return filename

    def _generate_file_name_regex(self) -> str:
        """
        Regular expression used for looking for plot files.
        This assumes that the file names follow the convention:
        <data_file_name>*<.png or other extension>
        """
        _file_extension_regex = self._generate_file_extension_regex()
        return f'{self.data_filename}{_file_extension_regex}'

    def _generate_file_extension_regex(self) -> str:
        """
        Generates the file extension part of the file regex. For example if the file extensions were
        .png, .gif and .jpg: The returned value would be (png|gif|jpg)
        :return: (str) expression pattern matching the file extensions of the plot handler
        """
        return f".*.({','.join(self.file_extensions).replace(',', '|')})"

    def _check_for_plot_files(self):
        """
        Searches the server directory for existing plot files using the directory specified.
        :return: (list) files on the server path that match regex
        """
        if os.path.exists(self.server_dir):
            file_regex = self._generate_file_name_regex()

            filenames = os.listdir(self.server_dir)
            matches = []

            for name in filenames:
                if re.match(file_regex, name) is not None:
                    matches.append(name)

            return matches
        return []

    def _ensure_staticfiles_graphs_exists(self):
        if not os.path.exists(self.static_graph_dir):
            os.makedirs(self.static_graph_dir, exist_ok=True)

    def get_plot_file(self) -> Tuple[Optional[List[str]], Optional[List[str]]]:
        """
        Searches for and retrieves a plot file from CEPH.
        Might find multiple files (e.g. if more than one plot_type is specified),
        but will only copy over one.
        :return: (str) local path to downloaded files OR None if no files found
        """
        _existing_plot_files = self._check_for_plot_files()
        self._ensure_staticfiles_graphs_exists()
        local_plot_paths = []
        server_paths = []
        if _existing_plot_files:
            for plot_file in _existing_plot_files:
                _server_path = f"{self.server_dir}/{plot_file}"
                _local_path = os.path.join(self.static_graph_dir, plot_file)

                try:
                    shutil.copy(_server_path, _local_path)
                    LOGGER.info('File \'%s\' found and saved to %s', _server_path, _local_path)
                    # URL to retrieve the static assert from the static dir - only if succesful
                    local_plot_paths.append(f'/static/graphs/{plot_file}')
                    server_paths.append(_server_path)
                except FileNotFoundError:
                    LOGGER.error("File \'%s\' does not exist. Error: %s", _server_path, traceback.format_exc())
                except PermissionError:
                    LOGGER.error("Insufficient permissions to read \'%s\'. Error: %s", _server_path,
                                 traceback.format_exc())
            return local_plot_paths, server_paths
        # No files found
        return (None, None)
