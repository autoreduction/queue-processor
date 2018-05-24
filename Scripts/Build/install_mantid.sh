#!/usr/bin/env sh
#default to install script location if no arguements given

if [ $# -eq 0 ]
  then
    echo "No file path supplied, using default location"
    DIRECTORY="$( cd "$(dirname "$0")" ; pwd -P )"
else
    DIRECTORY=$1
fi

wget -P $DIRECTORY https://sourceforge.net/projects/mantid/files/3.12/mantid_3.12.1-0ubuntu1~xenial1_amd64.deb
sudo apt-get -y install gdebi
sudo gdebi -y $DIRECTORY/mantid_3.12.1-0ubuntu1~xenial1_amd64.deb