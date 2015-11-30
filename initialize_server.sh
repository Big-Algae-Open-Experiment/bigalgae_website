#!/bin/bash

source ~/virtualenvs/ansible/bin/activate

cd ansible_playbooks

ansible-playbook -i hosts initialize_server.yml

ansible-playbook -i hosts initialize_database.yml
