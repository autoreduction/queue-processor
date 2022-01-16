# ############################################################################### #
# Autoreduction Repository : https://github.com/autoreduction/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Post-Process Admin Utilities
"""

import sys
from contextlib import contextmanager
from typing import List, Union
from autoreduce_db.reduction_viewer.models import Software
from docker.errors import APIError


@contextmanager
def channels_redirected(out_file, error_file, out_stream):
    """
    This context manager copies the file descriptor(fd) of stdout and stderr to the files given in
    out_file and err_file respectively. The fd is at the C level and so picks up data sent via
    Mantid. Both output streams are additionally also sent to out_stream.
    :param out_file: (str) output path
    :param error_file: (str) error file path
    :param out_stream: (class object) io.StringIO
    """

    old_stdout, old_stderr = sys.stdout, sys.stderr

    class MultipleChannels:
        # pylint: disable=expression-not-assigned
        """ Behaves like a stream object, but outputs to multiple streams."""

        def __init__(self, *streams):
            """
            :param streams: (tuple) (N-path, io.StringIO)
            """
            self.streams = streams

        def write(self, stream_message):
            """ Write to streams.
            :param stream_message: (data) stream message
            """
            [stream.write(stream_message) for stream in self.streams]

        def flush(self):
            """ Flush streams. """
            [stream.flush() for stream in self.streams]

    def _redirect_channels(output_file, err_file):
        """ Redirect channels
        :param output_file: stdout stream
        :param err_file: stderr stream
        """
        sys.stdout.flush(), sys.stderr.flush()  # pylint: disable=expression-not-assigned
        sys.stdout, sys.stderr = output_file, err_file

    with open(out_file, encoding="utf-8", mode='w') as out, open(error_file, encoding="utf-8", mode='w') as err:
        _redirect_channels(MultipleChannels(out, out_stream), MultipleChannels(err, out_stream))
        try:
            # allow code to be run with the redirected channels
            yield
        finally:
            _redirect_channels(old_stdout, old_stderr)  # restore stderr.


def windows_to_linux_path(paths: Union[str, List[str]], temp_root_directory) -> Union[str, List[str]]:
    """ Convert windows path to linux path -> replace \\ with /
    :param path:
    :param temp_root_directory:
    :return: (str) linux formatted file path
    """

    if isinstance(paths, str):
        return paths.replace('\\\\isis\\inst$\\', '/isis/').replace('\\\\autoreduce\\data\\',
                                                                    temp_root_directory + '/data/').replace('\\', '/')
    else:
        for i, path in enumerate(paths):
            paths[i] = path.replace('\\\\isis\\inst$\\',
                                    '/isis/').replace('\\\\autoreduce\\data\\',
                                                      temp_root_directory + '/data/').replace('\\', '/')
        return paths


def get_correct_image(client, software: Software):
    """ Fetch correct image based on the software and version
    :param client: Docker client
    :param software: (class) Software to be used
    :return: (Image) Image that contains the correct version of the software
    """

    try:
        # All 'runner' images are named 'runner-<software_name>-<version>'
        # e.g. 'runner-Mantid:6.2.0'
        image_name = f"ghcr.io/autoreduction/runner-{software.name}:{software.version}"
        return client.images.pull(image_name.lower())
    # If the matching version isn't in the list of versions, then it is unsupported
    except APIError as exc:
        raise exc
