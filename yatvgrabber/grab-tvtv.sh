#!/bin/sh

XMLTV_FILE="/tmp/tvtv.xml"
LOG_FILE="/tmp/grab_tvtv.log"
SOURCE_IDS="1"

set -e

touch $LOG_FILE
chmod 666 $LOG_FILE
date >> $LOG_FILE

#remove the old file
[ -e $XMLTV_FILE ] && mv -f $XMLTV_FILE ${XMLTV_FILE}.old >> $LOG_FILE

#get the data
nice /usr/bin/python /usr/local/sbin/grabtv.py --outputfile $XMLTV_FILE >> $LOG_FILE

# add the data to the db
if [ -e $XMLTV_FILE ]; then
    for id in $SOURCE_IDS
    do
        nice mythfilldatabase --only-update-guide --file --sourceid $id --xmlfile $XMLTV_FILE >> $LOG_FILE
    done
else
    echo "no xmltv file found - $XMLTV_FILE" >> $LOG_FILE
fi
