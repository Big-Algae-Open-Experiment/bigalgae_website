#!/bin/bash

source ~/virtualenvs/ansible/bin/activate

cd ansible_playbooks

ansible-playbook -i hosts manual_mongodump.yml

echo "This requires your local host sudo"

ansible-playbook --ask-become-pass -i hosts backup_database.yml

ansible-playbook -i hosts initialize_server.yml

echo "This requires your local host sudo"

ansible-playbook --ask-become-pass -i hosts restore_database.yml
