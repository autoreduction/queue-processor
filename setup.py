# pylint:skip-file
"""
Wrapper for the functionality for various installation and project setup commands
see:
    `python setup.py help`
for more details
"""
from setuptools import setup

import platform

from build.commands import (InitialiseTestDatabase, Help,
                            InstallExternals, MigrateTestSettings,
                            Start)

setup_requires = ['Django',
                  'django_extensions',
                  'django-user-agents',
                  'gitpython',
                  'MySQL-python',
                  'pytz',
                  'pymysql',
                  'requests',
                  'SQLAlchemy',
                  'mysql-connector',
                  'stomp.py',
                  'suds',
                  'Twisted',
                  'watchdog']

if platform.system() == 'Windows':
    setup_requires.append('pypiwin32')
else:
    setup_requires.append('python-daemon')


setup(name='AutoReduction',
      version='1.0',
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
