# pylint:skip-file
"""
Wrapper for the functionality for various installation and project setup commands
see:
    `python setup.py help`
for more details
"""
from setuptools import setup

import platform

from build.commands.database import InitialiseTestDatabase
from build.commands.help import Help
from build.commands.installs import InstallExternals
from build.commands.migrate_settings import MigrateTestSettings
from build.commands.start import Start

setup_requires = [
    'attrs==20.3.0',
    'dash==1.19.0',
    'dash_html_components==1.1.2',
    # dash 1.16.3 depends on dash-core-components 1.12.1
    'dash_core_components==1.15.0',
    'docker==4.4.3',
    'Django==3.1.2',
    'django_extensions==3.1.1',
    'django_plotly_dash==1.6.1',
    'django-user-agents==0.4.0',
    'filelock==3.0.12',
    'fire==0.4.0',
    'gitpython==3.1.13',
    'nexusformat==0.6.0',
    'numpy==1.19.2',
    'pandas==1.2.2',
    'plotly==4.14.3',
    'pytz==2021.1',
    'PyMySQL==1.0.2',
    'pysftp==0.2.9',
    'python-icat==0.17.0',
    'requests==2.25.1',
    'service_identity==18.1.0',
    'stomp.py==6.1.0',
    'suds-py3==1.4.4.1',
    'PyYAML==5.4.1'
]

if platform.system() == 'Windows':
    setup_requires.append('pypiwin32')
else:
    setup_requires.append('python-daemon==2.2.4')

setup(
    name='AutoReduction',
    version='20.3',
    description='ISIS AutoReduction service',
    author='ISIS Autoreduction Team',
    url='https://github.com/ISISScientificComputing/autoreduce/',
    install_requires=setup_requires,
    cmdclass={
        'test_settings': MigrateTestSettings,
        'database': InitialiseTestDatabase,
        'externals': InstallExternals,
        'start': Start,
        'help': Help,
    },
)
