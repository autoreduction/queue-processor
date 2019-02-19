# Autoreduction Ansible Script

This Ansible script deploys a complete autoreduction instance on a cloud VM running Scientific Linux 7.
A separate SL7 Ansible server is required in order to deploy the playbook. The following components are installed

 * Autoreduction WebApp
 * Autoreduction queue processors
 * Autoreduction utilities
 * All packages necessary for the above
 * ActiveMQ
 * Python ICAT
 * Packages for mounting the network drive (Full instructions: https://github.com/ISISScientificComputing/autoreduce/wiki/Cloud-Instances)

# Install

All these instructions should take place on the server machine. The setup on the host will
be handled automatically by the playbook.

Get ansible:

```
yum install ansible
```

Add the hostname of your VM to /etc/ansible/hosts

```
[autoreduce-hosts]
myhost.name.com
```

Now run the playbook:

```
ansible-playbook site.yml
```

If your public key isn't present on the remote host then you will need to pass Ansible a username and password.

```
ansible-playbook site.yml --user user --ask-pass
```

This should automatically deploy Autoreduce to the target machine.

# Notes

This playbook does not currently install Mantid because of the difficulty in setting up the environment for
a successful install. Instructions have instead been provided on the wiki: https://github.com/ISISScientificComputing/autoreduce/wiki/Cloud-Instances
