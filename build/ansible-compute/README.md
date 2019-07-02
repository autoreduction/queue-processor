# Autoreduction Ansible Script

This Ansible script deploys a complete Autoreduction instance on a cloud VM running Scientific Linux 7.
A separate SL7 Ansible server is required in order to deploy the playbook. The following components are installed

 * Autoreduction queue processors
 * Archive mounts
 * Mantid

# Cloud VMs needed

* An ansible server VM
* A host VM onto which Autoreduction is installed 

# Setup

All install instructions should take place on the server VM. The setup on the host VM will
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

Get the Autoreduction source code

```
git clone https://github.com/ISISScientificComputing/autoreduce.git
```

and cd to ```build/ansible-compute``` within this git repository.

# Create a vault

Credentials are stored in an encrypted Ansible Vault for security. You will need to create this vault in
```group_vars/all/vault.yml``` and define all variables prefixed with vault_ in group_vars/all/vars.yml.

To create the vault use:

```
ansible-vault create vault.yml
```

You will be prompted to enter a password. The vault can be edited using:

```
ansible-vault edit vault.yml
```

The contents of the vault should look like a standard variables file, see vars.yml for an example.

# Running

Now run the playbook:

```
ansible-playbook site.yml --ask-vault-pass
```

If your public key isn't present on the remote host then you will need to pass Ansible a username and password.

```
ansible-playbook site.yml --user user --ask-pass --ask-vault-pass
```

This should automatically deploy the autoreduction compute node to the target machine.

