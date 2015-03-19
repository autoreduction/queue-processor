# Autoreduction setup at ISIS

## Red Hat 7

Please see: http://www.mantidproject.org/Installing_Mantid_Via_Yum#ISIS_RHEL7_.28beta.29

### ActiveMQ

1.  Ensure http proxy is set.

        export http_proxy=http://wwwcache.rl.ac.uk
        export https_proxy=http://wwwcache.rl.ac.uk

2.  Downloaded apache-activemq-5.8.0-bin.tar.gz and unpack (https://activemq.apache.org/activemq-5111-release.html)

        wget http://www.apache.org/dyn/closer.cgi?path=/activemq/5.11.1/apache-activemq-5.11.1-bin.tar.gz
        tar -zxvf apache-activemq-5.11.1-bin.tar.gz
        mv apache-activemq-5.11.1 /opt/
        ln -sf /opt/apache-activemq-5.11.1/ /opt/activemq

3. Create/renew SSL certificates - keystore and truststore (http://activemq.apache.org/how-do-i-use-ssl.html)

        keytool -genkey -alias broker -keyalg RSA -keystore broker.ks -validity 2160
        keytool -export -alias broker -keystore broker.ks -file broker_cert
        keytool -genkey -alias client -keyalg RSA -keystore client.ks -validity 2160
        keytool -import -alias broker -keystore client.ts -file broker_cert
        keytool -export -alias client -keystore client.ks -file client_cert -validity 2160
        keytool -import -alias client -keystore broker.ts -file client_cert
        cp all of above created files into activemq/conf
                
4. Configure ActiveMQ to require SSL

        nano /opt/activemq/conf/activemq.xml
        Modify the transportConnector tag to be: <transportConnector name="stomp+ssl" uri="stomp+ssl://0.0.0.0:61613?maximumConnections=1000&amp;wireFormat.maxFrameSize=104857600"/>
        Add the following (making sure to change cert names and passwords):
        <sslContext>
                <sslContext keyStore="broker.ks" keyStorePassword="changeit"
                trustStore="client.ts" trustStorePassword="changeit"/>
        </sslContext>

To start up ActiveMQ, ensure you are in root and type: `/opt/activemq/bin/activemq start`

To stop, type: `/opt/activemq/bin/activemq stop`

To check that ActiveMQ is running e.g. type 

* `netstat –tulpn` and check if port **61613** is listed. 
* or `ps ax | grep activemq` and look for java entry running activemq.jar 
* or check if http://localhost:8161/admin/index.jsp is running. Note the factory username/password is admin/admin. 

ActiveMQ logs can by default be found in /activemq-install-dir/data.

### Setting up a worker on linux (redhat) 

1. Clone the autoreduce repository

        git clone https://github.com/mantidproject/autoreduce.git

2.  Install the libraries located under SNSPostProcessRPM/rpmbuild/libs. 

        sudo rpm -i SNSPostProcessRPM/rpmbuild/libs/* 

3.  Create and install the RPM

        sudo ISISPostProcessRPM/rpmbuild/make-autoreduce-rpm.sh
        sudo rpm -i ~/rpmbuild/RPMS/x86_64/autoreduce-mq-1.3-16.x86_64.rpm

4.  Modify the address "brokers" in /etc/autoreduce/post_process_consumer.conf to point to ActiveMQ address 

5.  At present specify the location where the script and reduced data get stored by modifying the instrument_dir variable in the method reduce() of python file /usr/bin/PostProcessAdmin.py

6.  Type: `sudo python /usr/bin/queueProcessor.py` or to start this as a daemon type `python /usr/bin/queueProcessor_daemon.py start`

Logging associated with the Logger used in the python worker script gets stored in `/var/log/mantid_autoreduce_worker.log` (optionally change this in `/usr/bin/Configuration.py`).  

To check rpm and uninstall do `rpm -qa | grep autoreduce` and `rpm -evv name-of-rpm-package`.

In step 4 if the key python line reads: `instrument_dir = "/home/autoreducetmp/" + self.instrument.lower() + "/"` then it is assumed that the reduce.py for a given instrument is located at `reduce_script_path = instrument_dir + "scripts/reduce.py"` and the output will be stored at `reduce_result_dir = instrument_dir + "results/" + self.proposal + "/"`

To test that it works copy content of folder https://github.com/mantidproject/autoreduce/tree/master/ISISPostProcessRPM/rpmbuild/autoreduce-mq/test into "~/tmp/". 
Edit the sendMessage.py file and change the message1 data_file property to point at the testData.txt within the tmp folder you have chosen.
Then in this directory type: `python sendMessage.py`. A file ./hrpd/results/RB-1310123/result_hrpd.txt should appear containing just the text string "something".
