# ############################################################################### #
#  Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
#  Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
#  SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for the PlotCache class
"""
from unittest import TestCase

from unittest.mock import patch, MagicMock, call

from plotting.plot_cache import PlotCache


# pylint:disable=protected-access
class TestPlotCache(TestCase):
    """Tests the functionality of the PlotCache"""
    PLOT_PATH = "path"

    def setUp(self):
        """
        Setup the plot cache and the opened cache file mock
        """
        dir_ = MagicMock()
        params = MagicMock()
        self.cache = PlotCache(dir_, params)
        self.openened_cache_file = MagicMock()

    @patch('os.remove')
    def test__delete_plot_removes_plot(self, mock_os_remove):
        """
        Test: os.remove is called
        When: _delete_plot is called
        """
        self.cache._delete_plot(TestPlotCache.PLOT_PATH)
        mock_os_remove.assert_called_once_with(TestPlotCache.PLOT_PATH)

    # pylint:disable=unused-argument
    @patch('os.remove', side_effect=OSError)
    def test__delete_plot_no_plot_passes(self, mock_os_remove):
        """
        Test: Exception caught and method passes
        When: Plot file does not exist
        """
        self.cache._delete_plot(TestPlotCache.PLOT_PATH)

    @patch('pickle.load', side_effect=EOFError)
    @patch('time.time', return_value=100.1)
    @patch('plotting.plot_cache.PlotCache._delete')
    def test__is_expired_eof_error_and_expired_returns_true(self, mock_delete, mock_time_time, mock_pickle_load):
        """
        Test: _is_expired returns true
        When: The cache file is empty
        """
        result = self.cache._is_expired(self.openened_cache_file)

        mock_pickle_load.assert_called_with(self.openened_cache_file)
        mock_time_time.assert_called_once()
        self.openened_cache_file.close.assert_called_once()
        mock_delete.assert_called_with(self.openened_cache_file.name)

        self.assertTrue(result)

    # pylint:disable=too-many-arguments
    @patch('pickle.load', return_value=100.123)
    @patch('time.time', return_value=101.123)
    @patch('pickle.loads', return_value=["path1", "path2"])
    @patch('zlib.decompress')
    @patch('plotting.plot_cache.PlotCache._delete_plot')
    @patch('plotting.plot_cache.PlotCache._delete')
    def test__is_expired_is_expired_returns_true(self, mock_delete, mock_plot_delete, mock_zlib_decompress,
                                                 mock_pickle_loads, mock_time_time, mock_pickle_load):
        """
        Test: _is_expired returns true and cache entry and plot are deleted
        When: When the cache entry has expired

        """
        result = self.cache._is_expired(self.openened_cache_file)

        mock_pickle_load.assert_called_with(self.openened_cache_file)
        mock_time_time.assert_called_once()
        self.openened_cache_file.read.assert_called_once()
        mock_zlib_decompress.assert_called_with(self.openened_cache_file.read())
        mock_pickle_loads.assert_called_with(mock_zlib_decompress())
        calls = [call("path1"), call("path2")]
        mock_plot_delete.assert_has_calls(calls)
        self.openened_cache_file.close.assert_called_once()
        mock_delete.assert_called_with(self.openened_cache_file.name)

        self.assertTrue(result)

    @patch('pickle.load', return_value=100.123)
    @patch('time.time', return_value=10.1)
    def test__is_expired_not_expired_returns_false(self, mock_time, mock_pickle_load):
        """
        Test: _is_expired returns false
        When: cache entry has not expired
        """
        result = self.cache._is_expired(self.openened_cache_file)

        mock_pickle_load.assert_called_with(self.openened_cache_file)
        mock_time.assert_called()

        self.assertFalse(result)
