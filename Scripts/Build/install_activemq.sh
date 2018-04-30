wget "http://www.apache.org/dyn/closer.cgi?filename=/activemq/5.15.3/apache-activemq-5.15.3-bin.tar.gz&action=download" -O apache-activemq-5.15.3-bin.tar.gz
sudo tar xvf apache-activemq-5.15.3-bin.tar.gz
sudo chmod 755 apache-activemq-5.15.3/bin/activemq
sudo ./apache-activemq-5.15.3/bin/activemq start
# Sleep required to give the service time to initialise
sleep 5
