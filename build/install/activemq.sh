#!/bin/sh

set -e

sudo mkdir -p $1

echo "Downloading ActiveMQ"
sudo wget -O $1/activemq.tar.gz "http://www.apache.org/dyn/closer.cgi?filename=/activemq/5.15.3/apache-activemq-5.15.3-bin.tar.gz&action=download" -q
sudo tar xvf $1/activemq.tar.gz -C $1
sudo chmod 755 $1/apache-activemq-5.15.3/bin/activemq
