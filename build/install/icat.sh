#!/usr/bin/env sh
wget https://icatproject.org/misc/python-icat/download/python-icat-0.13.1.tar.gz -O $1/icat.tar.gz
sudo tar xvf $1/icat.tar.gz
cd $1/icat
py_path=$(which python)
sudo $py_path setup.py build
sudo $py_path setup.py install
cd ..
