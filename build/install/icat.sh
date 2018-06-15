#!/bin/env sh
mkdir $1
wget -O $1/icat.tar.gz https://icatproject.org/misc/python-icat/download/python-icat-0.13.1.tar.gz
sudo tar xvf $1/icat.tar.gz -C $1
cd $1/python-icat-0.13.1/
py_path=$(which python)
sudo $py_path setup.py build
sudo $py_path setup.py install
cd ..
