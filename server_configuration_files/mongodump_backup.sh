#!/bin/bash

BACKUP_FOLDER="/var/www/html/baoe-app/backups/"

# Create a new backup
CURRENT_FOLDER=$BACKUP_FOLDER$(date -u +baoe_backup_%Y_%m_%d_%H_%M)

mkdir -p $CURRENT_FOLDER/images
mkdir -p $CURRENT_FOLDER/mongodb

cp /var/www/html/baoe-app/images/* $CURRENT_FOLDER/images/
mongodump -o $CURRENT_FOLDER/mongodb

# Delete old backups
BACKUP_FOLDERS=($(ls $BACKUP_FOLDER))

NUMBER_OF_BACKUPS_TO_KEEP=5

for ((i=0; i<${#BACKUP_FOLDERS[@]}-$NUMBER_OF_BACKUPS_TO_KEEP; i++));
do
    rm -rf $BACKUP_FOLDER${BACKUP_FOLDERS[$i]}
done
