#!/bin/bash

BACKUP_FOLDER="/var/www/html/baoe-app/backups/$(date +baoe_backup_%Y_%m_%d_%H_%M)"

mkdir -p $BACKUP_FOLDER/images
mkdir -p $BACKUP_FOLDER/mongodb

cp /var/www/html/baoe-app/images/* $BACKUP_FOLDER/images/
mongodump -o $BACKUP_FOLDER/mongodb
