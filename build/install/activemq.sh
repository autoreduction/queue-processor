#!/usr/bin/env sh
wget "http://www.apache.org/dyn/closer.cgi?filename=/activemq/5.15.3/apache-activemq-5.15.3-bin.tar.gz&action=download" -O /opt/apache-activemq-5.15.3-bin.tar.gz
sudo tar xvf /opt/apache-activemq-5.15.3-bin.tar.gz
sudo chmod 755 /opt/apache-activemq-5.15.3/bin/activemq
