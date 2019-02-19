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

echo "Downloading ActiveMQ"
sudo wget -O $1/activemq.tar.gz "http://archive.apache.org/dist/activemq/5.15.5/apache-activemq-5.15.5-bin.tar.gz" -q
sudo tar xvf $1/activemq.tar.gz -C $1
sudo chmod 755 $1/apache-activemq-5.15.5/bin/activemq
