#  Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
#  Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
#  SPDX - License - Identifier: GPL-3.0-or-later
#

"""
Implementation of PlotCache class which extends the django native FileBasedCache

"""
import os
import pickle
import time
import zlib

from django.core.cache.backends.filebased import FileBasedCache


class PlotCache(FileBasedCache):
    """
    Custom Django cache backend extended from the existing django FileBasedCache
    The cache holds reference to plot files that exist locally, and will expire them after the
    timeout. The key for a plot is the regular expression pattern that was used to find it remotely.
    Usage of the cache is handled by django
    """

    #pylint:disable=no-self-use
    def _delete_plot(self, plot_path):
        """
        Given the path of a plot, delete it
        :param plot_path: The path of the plot to be deleted
        """
        try:
            os.remove(plot_path)
        except OSError:
            pass

    def _is_expired(self, f):
        """
        Based on the django implementation of the FileBasedCache, Checks if cache entry is expired
        and if it is, deletes it and its corresponding plots
        will delete the plot if it is
        :param f: the opened cache file
        :return: True if the plot is expired else False
        """
        try:
            exp = pickle.load(f)
        except EOFError:
            exp = 0
        if exp is not None and exp < time.time():
            for path in pickle.loads(zlib.decompress(f.read())):
                self._delete_plot(path)
            f.close()
            self._delete(f.name)
            return True
        return False
