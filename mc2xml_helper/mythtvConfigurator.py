#! /usr/bin/env python

# standart libraries
import os
import sys
import _mysql
from operator import itemgetter

# third party libraries
import argparse
from lxml import etree
from PyQt4.QtGui import QDialog, QApplication, QStandardItem, QStandardItemModel, QItemSelectionModel, QMessageBox

# own libraries
from configuratorgui import Ui_Dialog

class MainDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.mythtvConfig = list()
        self.channelConfig = list()

        # parse the arguments
        parser = argparse.ArgumentParser(description="MythTV Configurator for XMLTV.",
                                 epilog="Copyright (C) [2015] [lars.schmohl]",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--xmltvfile', type=str,
                            default="xmltv.xml",
                            help='input xmltv file for mythfilldatabase')
        parser.add_argument('--mythtvdbconf', type=str,
                            default=os.getenv("HOME")+"/.mythtv/config.xml",
                            help='mythtv database configuration file')
        arguments = parser.parse_args()
        for _,element in etree.iterparse(os.path.realpath(arguments.mythtvdbconf)):
            if element.tag == "Host":
                self.dbHostName = element.text
            elif element.tag == "UserName":
                self.dbUserName = element.text
            elif element.tag == "Password":
                self.dbPassword = element.text
            elif element.tag == "DatabaseName":
                self.dbName = element.text
            elif element.tag == "Port":
                self.dbPort = int(element.text)

        # load the data from the mythtv database
        db = _mysql.connect(host=self.dbHostName,
                            port=self.dbPort,
                            user=self.dbUserName,
                            passwd=self.dbPassword,
                            db=self.dbName)
        db.query('SELECT chanid, name, xmltvid FROM channel WHERE visible=1 ORDER BY name ASC')
        results = db.store_result()
        all_rows = results.fetch_row(0, 1) # get all rows at once, use indexed as dict (by name)
        db.close()
        self.mythtvModel = QStandardItemModel()
        for row in all_rows:
            dataChanId = row["chanid"].strip()
            dataName = row["name"].strip()
            dataXmlTvId = row["xmltvid"].strip()
            qitem = QStandardItem(dataName +' ('+ dataXmlTvId +')')
            self.mythtvConfig.append({'chanid':dataChanId, 'name':dataName, 'xmltvid':dataXmlTvId, 'qitem':qitem})
            self.mythtvModel.appendRow( qitem)
        self.ui.listViewMythtvConfig.setModel(self.mythtvModel)

        # read the channel from the xmltv file
        lastChannelId = None
        for event,element in etree.iterparse(os.path.realpath(arguments.xmltvfile), events=("start","end")):
            if element.tag == "channel" and event == "start":
                lastChannelId = element.get('id')
            elif element.tag == "display-name" and event == "start" and element.text:
                qitem = QStandardItem(element.text +' ('+ lastChannelId +')')
                self.channelConfig.append({'id':lastChannelId, 'name':element.text, 'qitem':qitem})
            elif event == "end":
                element.clear()
        self.channelConfig.sort(key=itemgetter('name'))
        self.channelModel = QStandardItemModel()
        for item in self.channelConfig:
            self.channelModel.appendRow( item['qitem'])
        self.ui.listViewXmltvConfig.setModel(self.channelModel)

        # set the initial selection
        confSelection = self.ui.listViewMythtvConfig.selectionModel().selection()
        confSelection.clear()
        confSelection.select( self.mythtvConfig[0]['qitem'].index(), self.mythtvConfig[0]['qitem'].index())
        self.ui.listViewMythtvConfig.selectionModel().select(confSelection, QItemSelectionModel.ClearAndSelect)
        self.ClickedChannelListView()

        # connect the ui controls
        self.ui.writeMythtvConfigButton.clicked.connect(self.ClickedExportToMySQL)
        self.ui.writeChannelConfigButton.clicked.connect(self.ClickedExportToChannelConf)
        self.ui.lineSearchMythtvConfig.textChanged.connect(self.UpdatedChannelSearchField)
        self.ui.lineSearchXmltvConfig.textChanged.connect(self.UpdateIdSearchField)
        self.ui.listViewMythtvConfig.clicked.connect(self.ClickedChannelListView)
        self.ui.listViewXmltvConfig.clicked.connect(self.ClickedIdListView)
        self.ui.clearMythtvXmlTvIdButton.clicked.connect(self.ClearSelectedXmlTvId)
        self.ui.radioButtonWithoutXmlId.toggled.connect(self.ToggledWithoutXmlIdRadioButton)

    def ClickedExportToMySQL(self):
        db = _mysql.connect(host=self.dbHostName,
                            port=self.dbPort,
                            user=self.dbUserName,
                            passwd=self.dbPassword,
                            db=self.dbName)
        db.autocommit(True)
        for row in self.mythtvConfig:
            useairguideFlag = 0 if row['xmltvid'] != "" else 1 # automatic unset / set the useonairguide flag (no xmltvid --> use dvb eit epg)
            db.query('UPDATE channel SET xmltvid=\''+row['xmltvid']+'\', useonairguide='+str(useairguideFlag)+' WHERE chanid='+row['chanid'])
        db.close()
        QMessageBox.information(self, 'Info', 'The channel configuration has been written to the MythTV database.\n' + self.mythtvDbConfig["DBName"] +'@'+ self.mythtvDbConfig["DBHostName"])

    def ClickedExportToChannelConf(self):
        tempCopy = sorted(self.mythtvConfig, key=itemgetter('xmltvid'))
        chanfile = open('mc2xml.chl', 'w')
        for row in tempCopy:
            if row['xmltvid'] != "":
                chanfile.write(row['xmltvid'] +"\n")
        chanfile.close()
        QMessageBox.information(self, 'Info', 'The configuration has been exported to the mc2xml channel file.\n' + os.path.realpath('mc2xml.chl'))

    def UpdatedChannelSearchField(self, text_str):
        for (counter, item) in enumerate(self.mythtvConfig):
            self.ui.listViewMythtvConfig.setRowHidden(counter,(item['name'].lower().find(str(text_str).lower()) == -1))

    def UpdateIdSearchField(self, text_str):
        for (counter, item) in enumerate(self.channelConfig):
            self.ui.listViewXmltvConfig.setRowHidden(counter,(item['name'].lower().find(str(text_str).lower()) == -1))

    def ClickedChannelListView(self):
        selectedMythConfIndex = self.ui.listViewMythtvConfig.currentIndex().row()
        if selectedMythConfIndex == -1:
            selectedMythConfIndex = 0
        confSelection = self.ui.listViewXmltvConfig.selectionModel().selection()
        confSelection.clear()
        for item in self.channelConfig:
            if item['id'] == self.mythtvConfig[selectedMythConfIndex]['xmltvid']:
                confSelection.select( item['qitem'].index(), item['qitem'].index())
                self.ui.listViewXmltvConfig.scrollTo(item['qitem'].index())
        self.ui.listViewXmltvConfig.selectionModel().select(confSelection, QItemSelectionModel.ClearAndSelect)
        # update the id search line to show current selected channel name
        self.ui.lineSearchXmltvConfig.setText(self.mythtvConfig[selectedMythConfIndex]['name'])
        self.UpdateIdSearchField(self.mythtvConfig[selectedMythConfIndex]['name'])

    def ClickedIdListView(self):
        selectedChannelConfIndex = self.ui.listViewXmltvConfig.currentIndex().row()
        selectedMythConfIndex = self.ui.listViewMythtvConfig.currentIndex().row()
        temp = self.mythtvConfig[selectedMythConfIndex]
        temp['xmltvid'] = self.channelConfig[selectedChannelConfIndex]['id']
        temp['qitem'].setText(temp['name'] +' ('+ temp['xmltvid'] +')')
        # update the without xml id selection
        self.ToggledWithoutXmlIdRadioButton(self.ui.radioButtonWithoutXmlId.isChecked())

    def ClearSelectedXmlTvId(self):
        temp = self.mythtvConfig[self.ui.listViewMythtvConfig.currentIndex().row()]
        temp['xmltvid'] = ""
        temp['qitem'].setText(temp['name'] +' ('+ temp['xmltvid'] +')')
        confSelection = self.ui.listViewXmltvConfig.selectionModel().selection()
        confSelection.clear()
        self.ui.listViewXmltvConfig.selectionModel().select(confSelection, QItemSelectionModel.Clear)
        # update the without xml id selection
        self.ToggledWithoutXmlIdRadioButton(self.ui.radioButtonWithoutXmlId.isChecked())

    def ToggledWithoutXmlIdRadioButton(self, state):
        for (counter, item) in enumerate(self.mythtvConfig):
            self.ui.listViewMythtvConfig.setRowHidden(counter,(state and item['xmltvid'] != ""))

# open the gui
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainDialog()
    window.show()
    sys.exit(app.exec_())
