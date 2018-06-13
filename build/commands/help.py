"""
Command to print the help information for setup.py
"""
from distutils.core import Command


class Help(Command):

    description = "Provide help on using this setup"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        help_text = (('Usage       :', 'python setup.py [commands]'),
                     ('Description :', 'Script to setup project and testing environment'),
                     ('', ''),
                     ('Commands: ', '')
                     )
        commands = (('     test_settings', 'Copy test_settings.py to settings.py'),
                    ('     database', 'Initialise database on localhost'),
                    ('     externals', 'Install all external programs'),
                    ('     develop', 'Run test_settings, database and externals'),
                    ('     help', 'Show the help documentation')
                    )
        for args in help_text:
            print '{0:<15} {1:<10}'.format(*args)
        for command in commands:
            print '{0:<20} {1:<10}'.format(*command)