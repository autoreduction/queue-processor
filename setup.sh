#!/bin/bash
cd ~

isInstalled() {
    yum list installed "$1" >/dev/null 2>&1  || command -v "$1" >/dev/null 2>&1
}

isis_rhel="[isis-rhel]
name=ISIS Software Repository for Redhat Enterprise Linux $releasever - $basearch
baseurl=http://yum.isis.rl.ac.uk/rhel/$releasever/$basearch
failovermethod=priority
enabled=1
gpgcheck=0

[isis-rhel-noarch]
name=ISIS Software Repository for Redhat Enterprise Linux $releasever - noarch
baseurl=http://yum.isis.rl.ac.uk/rhel/$releasever/noarch
failovermethod=priority
enabled=1
gpgcheck=0

[isis-rhel-debuginfo]
name=ISIS Software Repository for Redhat Enterprise Linux $releasever - $basearch - Debug
baseurl=http://yum.isis.rl.ac.uk/rhel/$releasever/$basearch/debug
failovermethod=priority
enabled=1
gpgcheck=0

[isis-rhel-source]
name=ISIS Software Repository for Redhat Enterprise Linux $releasever - $basearch - Source
baseurl=http://yum.isis.rl.ac.uk/rhel/$releasever/SRPMS
failovermethod=priority
enabled=0
gpgcheck=0"


# Install Mantid
if [ ! isInstalled mantid ]
then
    echo "Installing mantid..."
    if [ ! -e /etc/yum.repos.d/isis-rhel.repo ] 
    then
        $isis_rhel > /etc/yum.repos.d/isis-rhel.repo
    fi
    yum install -y mantid
fi


# Install ActiveMQ
if [ ! -d /opt/activemq ]
then
    echo "Installing ActiveMQ..."

    wget http://archive.apache.org/dist/activemq/5.11.1/apache-activemq-5.11.1-bin.tar.gz
    tar -zxvf apache-activemq-5.11.1-bin.tar.gz
    sudo mv apache-activemq-5.11.1 /opt/
    sudo ln -sf /opt/apache-activemq-5.11.1/ /opt/activemq

    # Configure ActiveMQ
    if [ -d /opt/activemq/examples ]
    then
        rm -rf /opt/activemq/examples
    fi
    mv /opt/activemq/conf/activemq.xml /opt/activemq/conf/activemq.xml.old
    activemq_conf=/opt/activemq/conf/activemq.xml # we will install our config here later

    # Configure ActiveMQ certs
    cd /opt/activemq/conf
    read -s -p "Enter a password for the keystore password (at least 6 characters:" storepass
    echo ""
    keytool -genkey -noprompt -alias broker -dname "CN=reduce.isis.cclrc.ac.uk" -keyalg RSA -keystore broker.ks -validity 2160 -keypass $storepass -storepass $storepass
    keytool -genkey -noprompt -alias client -dname "CN=reduce.isis.cclrc.ac.uk" -keyalg RSA -keystore client.ks -validity 2160 -keypass $storepass -storepass $storepass
    keytool -export -noprompt -alias broker -keystore broker.ks -file broker_cert -storepass $storepass
    keytool -export -noprompt -alias client -keystore client.ks -file client_cert -storepass $storepass
    keytool -import -noprompt -alias broker -keystore client.ts -file broker_cert -keypass $storepass -storepass $storepass
    keytool -import -noprompt -alias client -keystore broker.ts -file client_cert -keypass $storepass -storepass $storepass
    cd ~
fi


# Install autoreduce
if [ ! -e /usr/bin/queueProcessor_daemon.py ]
then
    # Get the autoreduce repository
    echo "Installing autoreduction..."
    cd ~/autoreduce

    # Install RPMs
    rpm -i SNSPostProcessRPM/rpmbuild/libs/* 
    cd ISISPostProcessRPM/rpmbuild/
    ./make-autoreduce-rpm.sh
    rpm -i ~/rpmbuild/RPMS/x86_64/autoreduce-mq-*.rpm
    
    cd ~
fi

# Additional setup
if [ -d /autoreducetmp ]
then
    mkdir /autoreducetmp
    chown "ISISautoreduce@fed.cclrc.ac.uk" /autoreducetmp
fi
if [ ! isInstalled "python-pip" ]
then
    yum install -y "python-pip"
fi
pip install stomp.py daemon twisted service_identity


echo "Setup complete. ActiveMQ credentials should be changed in '$activemq_conf' and '/etc/autoreduce/post_process_consumer.conf'. ActiveMQ can be started by running '/opt/activemq/bin/activemq start', the queue processor by 'python /usr/bin/queueProcessor_daemon.py start' and the monitor by 'python /usr/bin/statusMonitor_daemon_daemon.py start'."


