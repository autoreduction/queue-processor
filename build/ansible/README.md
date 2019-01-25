## Autoreduction Ansible Script

This Ansible script deploys a complete autoreduction instance on a cloud VM running Ubuntu Trusty.
A separate RedHat Linux machine is required in order to deploy the playbook.

# Install

All these instructions should take place on the RHEL machine. The setup on the Ubuntu machine will
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
