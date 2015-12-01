#!/bin/bash

source ~/virtualenvs/ansible/bin/activate

cd ansible_playbooks

echo "This requires your local host sudo"

ansible-playbook --ask-become-pass -i $1 backup_database.yml
