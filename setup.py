"""
Functionality for project setup and various installations. Enter the following
for more details:
    `python setup.py --help`
"""
from setuptools import setup, find_packages

setup(
    name="autoreduce_qp",
    version="22.0.0.dev35",  # when updating the version here make sure to also update qp_mantid_python36.D
    description="ISIS Autoreduction queue processor",
    author="ISIS Autoreduction Team",
    url="https://github.com/autoreduction/autoreduce/",
    install_requires=[
        "autoreduce_db==22.0.0.dev34", "Django>=3.2.10", "fire==0.4.0", "plotly==5.3.1", "kaleido==0.2.1", "stomp.py",
        "docker==5.0.3", "confluent-kafka==1.8.2"
    ],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "autoreduce-qp-start = autoreduce_qp.queue_processor.confluent_consumer:main",
            "autoreduce-runner-start = autoreduce_qp.queue_processor.reduction.runner:main"
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
    ])
