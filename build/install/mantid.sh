#!/usr/bin/env sh
wget https://sourceforge.net/projects/mantid/files/3.12/mantid_3.12.1-0ubuntu1~xenial1_amd64.deb -O /opt/Mantid/mantid_3.12.1-0ubuntu1~xenial1_amd64.deb
sudo apt-get -y install dpkg
sudo dpkg -i /opt/Mantid/mantid_3.12.1-0ubuntu1~xenial1_amd64.deb