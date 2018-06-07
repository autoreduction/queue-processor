#!/usr/bin/env sh
wget "http://www.apache.org/dyn/closer.cgi?filename=/activemq/5.15.3/apache-activemq-5.15.3-bin.tar.gz&action=download" -O $1/activemq.tar.gz
sudo tar xvf $1/activemq.tar.gz
sudo chmod 755 $1/activemq/bin/activemq
