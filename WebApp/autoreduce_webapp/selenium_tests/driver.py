# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Module containing functions for obtaining webdrivers
"""
import os

from selenium import webdriver
from selenium_tests import configuration

WINDOW_SIZE = "1920,1080"


def get_chrome_driver() -> webdriver.Chrome:
    """
    Get an instance of a chrome driver
    :return: (Chrome) instance of a chromedriver
    """
    options = webdriver.ChromeOptions()
    if configuration.is_headless():
        options.add_argument("--headless")
    else:
        if "DISPLAY" not in os.environ:
            raise RuntimeError("Trying to run Chrome driver with a GUI but no DISPLAY environment variable! " +
                               "This results in Chrome crashing. Please set the DISPLAY environment " +
                               "variable and run the tests again.")

    options.add_argument("--window-size=" + WINDOW_SIZE)
    options.add_argument("log-level=3")
    if "SELENIUM_REMOTE" in os.environ:
        driver = webdriver.Remote(options=options)
    else:
        driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    driver.set_page_load_timeout(30)
    return driver
