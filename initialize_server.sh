#!/bin/bash

source ~/virtualenvs/ansible/bin/activate

cd ansible_playbooks

ansible-playbook -i $1 initialize_server.yml

ansible-playbook -i $1 initialize_database.yml
