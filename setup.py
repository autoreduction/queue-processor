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
    'dash==1.16.3',
    'dash_html_components==1.1.1',
    # dash 1.16.3 depends on dash-core-components 1.12.1
    'dash_core_components==1.12.1',
    'docker==4.4.1',
    'Django==3.1.2',
    'django_extensions==3.1.0',
    'django_plotly_dash==1.5.0',
    'django-user-agents==0.4.0',
    'filelock==3.0.12',
    'fire==0.4.0',
    'gitpython==3.1.12',
    # this is the highest available version that pip can find on CentOS - be careful when updating
    # because GitHub Actions runs Ubuntu so even if the build pass, the installation could fail
    'IPython==7.20.0',
    'mysqlclient==2.0.3',
    'mysql-connector==2.2.9',
    'nexusformat==0.6.0',
    'numpy==1.20.1',
    'pandas==1.2.1',
    'plotly==4.14.3',
    'pytz==2021.1',
    'PyMySQL==1.0.2',
    'pysftp==0.2.9',
    'python-icat==0.17.0',
    'requests==2.25.1',
    'service_identity==18.1.0',
    'SQLAlchemy==1.3.23',
    'stomp.py==6.1.0',
    'suds-py3==1.4.4.1',
    'Twisted==20.3.0',
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
