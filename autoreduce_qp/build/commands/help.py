# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Command to print the help information for setup.py
"""
from __future__ import print_function

# pylint:disable=no-name-in-module
from distutils.core import Command


class Help(Command):
    """
    Command class to display help message
    """

    description = "Provide help on using this setup"
    user_options = []

    def initialize_options(self):
        """ No args hence pass """

    def finalize_options(self):
        """ No args hence pass """

    # pylint:disable=no-self-use
    def run(self):
        """
        Print out the help documentation to console
        """
        help_text = (('Usage       :', 'python setup.py [commands]'),
                     ('Description :', 'Script to setup project and testing environment'), ('', ''), ('Commands: ', ''))
        commands = (('     test_settings', 'Copy test_credentials.py to credentials.py'),
                    ('     database', 'Initialise database on localhost'), ('     externals',
                                                                            'Install all external programs'),
                    ('              ', 'Use the -s argument to specify a comma'
                     'separated list of services:'), ('              ',
                                                      '    python setup.py externals -s activemq,mantid'),
                    ('     start', 'starts required services: activemq'), ('     help', 'Show the help documentation'))
        for args in help_text:
            print('{0:<15} {1:<10}'.format(*args))
        for command in commands:
            print('{0:<20} {1:<10}'.format(*command))
