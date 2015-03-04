#!/bin/sh

XMLTV_FILE="/tmp/mc2xml.xml"
LOG_FILE="/tmp/grab_mc2xml.log"
SOURCE_IDS="1"

rm -f $LOG_FILE
touch $LOG_FILE
chmod 666 $LOG_FILE
date >> $LOG_FILE

cd /var/cache/mc2xml

#get the data
echo "-----------" >> $LOG_FILE
echo "uk - London" >> $LOG_FILE
echo "-----------" >> $LOG_FILE
[ -e $XMLTV_FILE ] && rm -f $XMLTV_FILE  >> $LOG_FILE
mc2xml -U -c gb -g "SW1X 7LA" -D mc2xml_gb.dat -o $XMLTV_FILE >> $LOG_FILE
[ $? -eq 0 ] && nice mythfilldatabase --only-update-guide --file --sourceid $id --xmlfile $XMLTV_FILE >> $LOG_FILE


echo "---------" >> $LOG_FILE
echo "au - Wien" >> $LOG_FILE
echo "---------" >> $LOG_FILE
[ -e $XMLTV_FILE ] && rm -f $XMLTV_FILE  >> $LOG_FILE
mc2xml -U -c at -g 1010 -D mc2xml_au.dat -o $XMLTV_FILE >> $LOG_FILE
[ $? -eq 0 ] && nice mythfilldatabase --only-update-guide --file --sourceid $id --xmlfile $XMLTV_FILE >> $LOG_FILE

echo "---------" >> $LOG_FILE
echo "de - Berlin Mitte" >> $LOG_FILE
echo "---------" >> $LOG_FILE
[ -e $XMLTV_FILE ] && rm -f $XMLTV_FILE  >> $LOG_FILE
mc2xml -U -c de -g 10115 -D mc2xml_de.dat -o $XMLTV_FILE >> $LOG_FILE
[ $? -eq 0 ] && nice mythfilldatabase --only-update-guide --file --sourceid $id --xmlfile $XMLTV_FILE >> $LOG_FILE

echo "---------" >> $LOG_FILE
echo "ch - Ballwil" >> $LOG_FILE
echo "---------" >> $LOG_FILE
[ -e $XMLTV_FILE ] && rm -f $XMLTV_FILE  >> $LOG_FILE
mc2xml -U -c ch -g 6275 -D mc2xml_ch.dat -o $XMLTV_FILE >> $LOG_FILE
[ $? -eq 0 ] && nice mythfilldatabase --only-update-guide --file --sourceid $id --xmlfile $XMLTV_FILE >> $LOG_FILE

