# pylint:skip-file
"""
Wrapper for the functionality for various installation and project setup commands
see:
    `python setup.py help`
for more details
"""
from setuptools import setup

from build.commands.database import InitialiseTestDatabase, LoadDBFixtures
from build.commands.help import Help
from build.commands.installs import InstallExternals
from build.commands.migrate_settings import MigrateTestSettings
from build.commands.start import Start

setup(
    name='AutoReduction',
    version='20.3',
    description='ISIS AutoReduction service',
    author='ISIS Autoreduction Team',
    url='https://github.com/ISISScientificComputing/autoreduce/',
    cmdclass={
        'test_settings': MigrateTestSettings,
        'database': InitialiseTestDatabase,
        'fixtures': LoadDBFixtures,
        'externals': InstallExternals,
        'start': Start,
        'help': Help,
    },
)
