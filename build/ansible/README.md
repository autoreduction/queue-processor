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

This should automatically deploy Autoreduce to the target machine.

# Licensing

By using this playbook you agree to abide by the Oracle JDK license at: https://www.oracle.com/technetwork/java/javase/terms/license/index.html
