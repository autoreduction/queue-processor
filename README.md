# Autoreduction setup at ISIS

## Red Hat 7

Please see: http://www.mantidproject.org/Installing_Mantid_Via_Yum#ISIS_RHEL7_.28beta.29

### ActiveMQ

1.  Ensure http proxy is set.

        export http_proxy=http://wwwcache.rl.ac.uk
        export https_proxy=http://wwwcache.rl.ac.uk

2.  Downloaded apache-activemq-5.8.0-bin.tar.gz and unpack (https://activemq.apache.org/activemq-580-release.html)

        wget http://archive.apache.org/dist/activemq/apache-activemq/5.8.0/apache-activemq-5.8.0-bin.tar.gz -o autoreduce-mq.tgz
        tar -zxvf autoreduce-mq.tgz
        mv apache-activemq-5.8.0 /opt/
        ln -sf /opt/apache-activemq-5.6.0/ /opt/activemq
    
For option for starting up ActiveMQ type: `/opt/activemq/bin/activemq`

To check that ActiveMQ is listening type e.g. 'lsof –i' or 'netstat –tulpn'. Note in table outputted, 'command' or 'program name' for activemq is 'java'. To check which java is used you may type "ls –l /proc/'PID number'/exe" and to get the working directory of a process "ls –l /proc/'PID number'/cwd"
ActiveMQ should be listening on ports **61616** and **61613**

Use a URL like http://autoreduce.isis.cclrc.ac.uk:8161/admin/index.jsp to check ActiveMQ. This should be tested from localhost first (due to firewall restrictions). Note the factory username/password is admin/admin. 

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

6.  Type: `sudo python /usr/bin/queueProcessor.py`


Logging associated with the Logger used in the python worker script gets stored in `/var/log/mantid_autoreduce_worker.log` (optionally change this in `/usr/bin/Configuration.py`).  

In step 4 if the key python line reads: `instrument_dir = "/home/autoreducetmp/" + self.instrument.lower() + "/"` then it is assumed that the reduce.py for a given instrument is located at `reduce_script_path = instrument_dir + "scripts/reduce.py"` and the output will be stored at `reduce_result_dir = instrument_dir + "results/" + self.proposal + "/"`

To test that it works copy content of folder https://github.com/mantidproject/autoreduce/tree/master/ISISPostProcessRPM/rpmbuild/autoreduce-mq/test into "~/tmp/". 
Edit the sendMessage.py file and change the message1 data_file property to point at the testData.txt within the tmp folder you have chosen.
Then in this directory type: `python sendMessage.py`. A file ./hrpd/results/RB-1310123/result_hrpd.txt should appear containing just the text string "something".
