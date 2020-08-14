# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Post Process Admin Utlities
"""

import sys
from contextlib import contextmanager


class SkippedRunException(Exception):
    """
    Exception for runs that have been skipped
    Note: this is currently only the case for EnginX Event mode runs at ISIS
    """


@contextmanager
def channels_redirected(out_file, err_file, out_stream):
    """
    This context manager copies the file descriptor(fd) of stdout and stderr to the files given in
    out_file and err_file respectively. The fd is at the C level and so picks up data sent via
    Mantid. Both output streams are additionally also sent to out_stream.
    """
    old_stdout, old_stderr = sys.stdout, sys.stderr

    class MultipleChannels:
        # pylint: disable=expression-not-assigned
        """ Behaves like a stream object, but outputs to multiple streams."""

        def __init__(self, *streams):
            self.streams = streams

        def write(self, stream_message):
            """ Write to steams. """
            [stream.write(stream_message) for stream in self.streams]

        def flush(self):
            """ Flush streams. """
            [stream.flush() for stream in self.streams]

    def _redirect_channels(output_file, error_file):
        """ Redirect channels? """
        sys.stdout.flush(), sys.stderr.flush()  # pylint: disable=expression-not-assigned
        sys.stdout, sys.stderr = output_file, error_file

    with open(out_file, 'w') as out, open(err_file, 'w') as err:
        _redirect_channels(MultipleChannels(out, out_stream), MultipleChannels(err, out_stream))
        try:
            # allow code to be run with the redirected channels
            yield
        finally:
            _redirect_channels(old_stdout, old_stderr)  # restore stderr.


def windows_to_linux_path(path, temp_root_directory):
    """ Convert windows path to linux path. """
    # '\\isis\inst$\' maps to '/isis/'
    path = path.replace('\\\\isis\\inst$\\', '/isis/')
    path = path.replace('\\\\autoreduce\\data\\', temp_root_directory + '/data/')
    path = path.replace('\\', '/')
    return path
