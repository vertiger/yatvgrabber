#!/bin/sh

set -e

XMLTV_FILE="/tmp/mc2xml.xml"
LOG_FILE="/tmp/grab_mc2xml.log"
SOURCE_IDS="1"

touch $LOG_FILE
chmod 666 $LOG_FILE
date >> $LOG_FILE

#remove the old file
if [ -e $XMLTV_FILE ]; then
    mv -f $XMLTV_FILE ${XMLTV_FILE}.old >> $LOG_FILE
fi

cd /var/cache/mc2xml

#get the data
echo "-----------" >> $LOG_FILE
echo "uk - London" >> $LOG_FILE
echo "-----------" >> $LOG_FILE
mc2xml -c gb -g "SW1X 7LA" -D mc2xml_gb.dat -o /tmp/xmltv_gb.xml >> $LOG_FILE

echo "---------" >> $LOG_FILE
echo "au - Wien" >> $LOG_FILE
echo "---------" >> $LOG_FILE
mc2xml -c at -g 1010 -D mc2xml_au.dat -I /tmp/xmltv_gb.xml -o /tmp/xmltv_au.xml >> $LOG_FILE

echo "---------" >> $LOG_FILE
echo "de - Berlin Mitte" >> $LOG_FILE
echo "---------" >> $LOG_FILE
mc2xml -c de -g 10115 -D mc2xml_de.dat -I /tmp/xmltv_au.xml -o /tmp/xmltv_de.xml >> $LOG_FILE

echo "---------" >> $LOG_FILE
echo "ch - Ballwil" >> $LOG_FILE
echo "---------" >> $LOG_FILE
mc2xml -c ch -g 6275 -D mc2xml_ch.dat -I /tmp/xmltv_de.xml -o $XMLTV_FILE >> $LOG_FILE

# add the data to the db
if [ -e $XMLTV_FILE ]; then
    for id in $SOURCE_IDS
    do
        nice mythfilldatabase --only-update-guide --file --sourceid $id --xmlfile $XMLTV_FILE >> $LOG_FILE
    done
else
    echo "no xmltv file found - $XMLTV_FILE" >> $LOG_FILE
fi

