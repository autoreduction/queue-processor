# pylint:skip-file
"""
Wrapper for the functionality for various installation and project setup commands
see:
    `python setup.py help`
for more details
"""
from setuptools import setup, find_packages

setup(
    name="autoreduce_qp",
    version="22.0.0.dev12",  # when updating the version here make sure to also update qp_mantid_python36.D
    description="ISIS Autoreduction queue processor",
    author="ISIS Autoreduction Team",
    url="https://github.com/ISISScientificComputing/autoreduce/",
    install_requires=[
        "autoreduce_db==22.0.0.dev15", "Django==3.2.8", "fire==0.4.0", "plotly==5.3.1", "kaleido==0.2.1",
        "stomp.py==7.0.0"
    ],
    packages=find_packages(),
    entry_points={"console_scripts": ["autoreduce-qp-start = autoreduce_qp.queue_processor.queue_listener:main"]},
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
    ])
