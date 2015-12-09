#!/bin/bash

GLOBAL_CV2=$(/usr/bin/python -c 'import cv2; print(cv2)' | awk '{print $4}' | sed s:"['>]":"":g)

DESTINATION_CV2='/var/www/html/baoe-app/env/lib64/python2.7/cv2.so'

cp $GLOBAL_CV2 $DESTINATION_CV2