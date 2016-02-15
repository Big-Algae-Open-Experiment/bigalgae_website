#!/bin/bash

BACKUP_FOLDER="/var/www/html/baoe-app/backups/"

BACKUPS=($(ls $BACKUP_FOLDER ))

MOST_RECENT_BACKUP=${BACKUPS[${#BACKUPS[@]} - 1]}

cp $BACKUP_FOLDER/$MOST_RECENT_BACKUP/images/* /var/www/html/baoe-app/images/
mongo bigalgae --eval "db.dropDatabase()"
mongorestore $BACKUP_FOLDER/$MOST_RECENT_BACKUP/mongodb
