#!/bin/sh

# Test sudo
$(sudo -n echo)
exitCode=$?
if [ $exitCode -ne 0 ] ; then
    echo "This script must be run with sudo" >&2
    exit 1
fi

set -e

sudo mkdir -p $1

echo "Downloading ICAT"
sudo wget -O $1/icat.tar.gz https://icatproject.org/misc/python-icat/download/python-icat-0.16.0.tar.gz -q
sudo tar xvf $1/icat.tar.gz -C $1
cd $1/python-icat-0.16.0/
py_path=$(which python)
sudo $py_path setup.py build
sudo $py_path setup.py install
cd ..
