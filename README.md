# Autoreduction setup at ISIS

## Red Hat 7

First install Mantid using: http://download.mantidproject.org/redhat.html

### ActiveMQ

1.  Downloaded apache-activemq-5.11.1-bin.tar.gz and unpack (https://activemq.apache.org/activemq-5111-release.html)

        wget http://archive.apache.org/dist/activemq/5.11.1/apache-activemq-5.11.1-bin.tar.gz
        tar -zxvf apache-activemq-5.11.1-bin.tar.gz
        sudo mv apache-activemq-5.11.1 /opt/
        sudo ln -sf /opt/apache-activemq-5.11.1/ /opt/activemq
                

2a. To configure ActiveMQ to communicate with stomp + SSL,

        sudo nano /opt/activemq/conf/activemq.xml
        
    Modify the stomp transportConnector tag to be: 
    
        <transportConnector name="stomp+ssl" uri="stomp+ssl://0.0.0.0:61613?transport.enabledProtocols=TLSv1,TLSv1.1,TLSv1.2&amp;maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
        
    or add it in the <transportConnectors> section if no stomp line exists already.
        
    Add the following directly below the <broker> tag (making sure to change cert names and passwords):
        
        <sslContext>
                <sslContext keyStore="broker.ks" keyStorePassword="changeit"
                trustStore="client.ts" trustStorePassword="changeit"/>
        </sslContext>
        
    Create/renew SSL certificates - keystore and truststore (http://activemq.apache.org/how-do-i-use-ssl.html)
    
        cd /opt/activemq/conf
        sudo rm -f broker.ks broker.ts client.ks client.ts
        keytool -genkey -alias broker -keyalg RSA -keystore broker.ks -validity 2160
        keytool -export -alias broker -keystore broker.ks -file broker_cert
        keytool -genkey -alias client -keyalg RSA -keystore client.ks -validity 2160
        keytool -import -alias broker -keystore client.ts -file broker_cert
        keytool -export -alias client -keystore client.ks -file client_cert -validity 2160
        keytool -import -alias client -keystore broker.ts -file client_cert

    Note that ActiveMQ may sometimes default to using a different configuration file than this; `rm -rf /opt/activemq/examples` to remove a potential conflict.
    
        
2b. ActiveMQ can also be configured to communicate without SSL: 

        sudo nano /opt/activemq/conf/activemq.xml
        
    Modify the stomp transportConnector tag to be: 
    
        <transportConnector name="stomp" uri="stomp://0.0.0.0:61613?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/> 
        
    or add it in the <transportConnectors> section if no stomp line exists already. But autoreduce relies on SSL connections; see below to fix this.
        
        
3. Username and password for submiting jobs by adding to the <broker> section directly below the <sslContext>...</sslContext> entry, or directly below the <broker> tag if there's no such entry (with XXXXXXXXXX substitued by suitable password):

        <plugins>
            <simpleAuthenticationPlugin>
                <users>
                    <authenticationUser username="autoreduce" password="XXXXXXXXXX" groups="users,admins"/>
                </users>
            </simpleAuthenticationPlugin>
        </plugins>


Start ActiveMQ as root: `sudo /opt/activemq/bin/activemq start`

To stop, type: `sudo /opt/activemq/bin/activemq stop`

To check that ActiveMQ is running e.g. type 

* `netstat –tulpn` and check if port **61613** is listed. 
* or `ps ax | grep activemq` and look for java entry running activemq.jar 
* or check if http://localhost:8161/admin/index.jsp is running. Note the factory username/password is admin/admin. 

ActiveMQ logs can by default be found in /activemq-install-dir/data. By default the log level is INFO, this can be
changed in `/activemq-install-dir/log4j.properties`.

### Setting up a worker on linux (redhat) 

1. Clone the autoreduce repository from the home directory

        cd ~
        git clone https://github.com/mantidproject/autoreduce.git

2.  Install the libraries located under SNSPostProcessRPM/rpmbuild/libs. 

        sudo rpm -i SNSPostProcessRPM/rpmbuild/libs/* 

3.  Create and install the RPM

        cd ISISPostProcessRPM/rpmbuild/
        sudo ./make-autoreduce-rpm.sh
        sudo rpm -i ~/rpmbuild/RPMS/x86_64/autoreduce-mq-1.3-16.x86_64.rpm

4.  Modify the address "brokers" in /etc/autoreduce/post_process_consumer.conf to point to ActiveMQ address and username and password for submitting jobs to activemq

5. At present create /autoreducetmp folder can change owner and group to user that will be used to run queueProcessor (to store temporary created reduction files)

6.  At present specify the location where the script and reduced data get stored by modifying `reduction_directory`, `archive_directory` and `ceph_directory` in /etc/autoreduce/post_process_consumer.conf

7.  To start this as a daemon type `python /usr/bin/queueProcessor_daemon.py start` as the user you want to use to run queueProcessor (for some default directories, it may need to be `sudo python /usr/bin/queueProcessor_daemon.py start`)

To modify the software to use plaintext (non-SSL) connections, the Python scripts (/usr/bin/queueProcessor.py, /usr/bin/PostProcessAdmin.py, sendMessage.py) require a slight modification, changing `use_ssl=True, ssl_version=3)` to `use_ssl=False)` in lines of the form `stomp.Connection( ...`

Logging associated with the Logger used in the python worker script gets stored in `/var/log/autoreduction.log`. To modify logging setting edit `/usr/bin/autoreduction_logging_setup.py`.  

To check rpm and uninstall do `rpm -qa | grep autoreduce` and `rpm -evv name-of-rpm-package`.

### Testing the setup

1. In ~/autoreduce/ISISPostProcessRPM/rpmbuild/autoreduce-mq/test/sendMessage.py, point `reduction_script_dir` to the directory containing reduce.py (the same directory is fine)

2. In the same file, point `testdata` to an accessible nxs file, the path of which contains somewhere a folder of the form cycle_xx_x, where x is a digit. The script is set up to take GEM data, and points to a valid network location for one such file.

3. With ActiveMQ and queueProcessor_daemon running, run `sudo python sendMessage.py`. The ActiveMQ control panel should show a message going into the ReductionPending queue, then ReductionStarted, then ReductionComplete.
