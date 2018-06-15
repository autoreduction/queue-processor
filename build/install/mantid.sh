#!/bin/env sh

mkdir $1
wget https://sourceforge.net/projects/mantid/files/3.12/mantid_3.12.1-0ubuntu1~xenial1_amd64.deb -O $1/mantid.deb
sudo apt-get -y install dpkg
sudo dpkg -i $1/mantid.deb