#!/usr/bin/env sh
wget https://icatproject.org/misc/python-icat/download/python-icat-0.13.1.tar.gz
sudo tar xvf python-icat-0.13.1.tar.gz
cd python-icat-0.13.1
py_path=$(which python)
sudo $py_path setup.py build
sudo $py_path setup.py install
cd ..
