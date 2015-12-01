#!/bin/bash

source ~/virtualenvs/ansible/bin/activate

cd ansible_playbooks

ansible-playbook -i $1 manual_mongodump.yml

echo "This requires your local host sudo"

ansible-playbook --ask-become-pass -i $1 backup_database.yml

ansible-playbook -i $1 initialize_server.yml

echo "This requires your local host sudo"

ansible-playbook --ask-become-pass -i $1 restore_database.yml
