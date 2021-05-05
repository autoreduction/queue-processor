# pylint:skip-file
"""
Wrapper for the functionality for various installation and project setup commands
see:
    `python setup.py help`
for more details
"""
from setuptools import setup

import platform

from build.commands.database import InitialiseTestDatabase, LoadDBFixtures
from build.commands.help import Help
from build.commands.installs import InstallExternals
from build.commands.migrate_settings import MigrateTestSettings
from build.commands.start import Start

setup_requires = [
    'attrs==20.3.0',
    'dash==1.20.0',
    'dash_html_components==1.1.3',
    'dash_core_components==1.16.0',
    'docker==5.0.0',
    'Django==3.2.1',
    'django_extensions==3.1.3',
    'django_plotly_dash==1.6.3',
    'django-user-agents==0.4.0',
    'filelock==3.0.12',
    'fire==0.4.0',
    'gitpython==3.1.14',
    'nexusformat==0.6.1',
    'numpy==1.19.2',
    'pandas==1.1.5',
    'plotly==4.14.3',
    'pytz==2021.1',
    'PyMySQL==1.0.2',
    'pysftp==0.2.9',
    'python-icat==0.18.1',
    'requests==2.25.1',
    'service_identity==18.1.0',
    'stomp.py==6.1.0',
    'suds-py3==1.4.4.1',
    'PyYAML==5.4.1',
]

if platform.system() == 'Windows':
    setup_requires.append('pypiwin32')
else:
    setup_requires.append('python-daemon==2.2.4')

setup(
    name='AutoReduction',
    version='21.1',
    description='ISIS AutoReduction service',
    author='ISIS Autoreduction Team',
    url='https://github.com/ISISScientificComputing/autoreduce/',
    install_requires=setup_requires,
    cmdclass={
        'test_settings': MigrateTestSettings,
        'database': InitialiseTestDatabase,
        'fixtures': LoadDBFixtures,
        'externals': InstallExternals,
        'start': Start,
        'help': Help,
    },
)
