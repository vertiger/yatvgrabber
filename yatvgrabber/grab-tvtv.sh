#!/bin/sh

XMLTV_FILE="/tmp/tvtv.xml"
LOG_FILE="/tmp/grab_tvtv.log"
SOURCE_IDS="1"

chmod 666 $LOG_FILE
date >> $LOG_FILE

#remove the old file
if [ -e $XMLTV_FILE ]; then
    mv -f $XMLTV_FILE ${XMLTV_FILE}.old >> $LOG_FILE
fi

#get the data
nice /usr/bin/python /usr/local/sbin/grabtv.py --outputfile $XMLTV_FILE >> $LOG_FILE
retValue=$?
if [ "$retValue" -ne "0" ]; then
    echo "aborting, grabtv.py returned $retValue" >> $LOG_FILE
    exit $retValue
fi

# add the data to the db
if [ -e $XMLTV_FILE ]; then
    for id in $SOURCE_IDS
    do
        nice mythfilldatabase --only-update-guide --file --sourceid $id --xmlfile $XMLTV_FILE >> $LOG_FILE
    done
else
    echo "no xmltv file found - $XMLTV_FILE" >> $LOG_FILE
fi
