# pylint:skip-file
"""
Wrapper for the functionality for various installation and project setup commands
see:
    `python setup.py help`
for more details
"""
from setuptools import setup

setup_requires = [
    'autoreduce_db==0.1.2', 'autoreduce_utils==0.1.2', 'Django==3.2.2', 'plotly==4.14.3', 'stomp.py==6.1.0'
]

setup(name='autoreduce_qp',
      version='21.1',
      description='ISIS Autoreduction queue processor',
      author='ISIS Autoreduction Team',
      url='https://github.com/ISISScientificComputing/autoreduce/',
      install_requires=setup_requires,
      packages=["autoreduce_qp"])
