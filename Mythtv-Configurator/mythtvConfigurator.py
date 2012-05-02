#! /usr/bin/env python

# standart libraries
import os
import sys
import shutil
import _mysql
from operator import itemgetter

# third party libraries
import argparse
from configobj import ConfigObj
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
        parser = argparse.ArgumentParser(description="MythTV Configurator for YaTvGrabber.",
                                 epilog="Copyright (C) [2012] [lars.schmohl]",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument('--channelconf', type=str,
                            default="/etc/yatvgrabber/channel.grab",
                            help='configured channels for yatvgrabber')
        parser.add_argument('--mythtvdbconf', type=str,
                            default=os.getenv("HOME")+"/.mythtv/mysql.txt",
                            help='mythtv database configuration file')
        arguments = parser.parse_args()
        self.yatvgrabberConfigFile = os.path.realpath(arguments.channelconf)
        self.mythtvDbConfig = ConfigObj(os.path.realpath(arguments.mythtvdbconf), raise_errors=True)
        
        # load the data from the mythtv database
        db = _mysql.connect(host=self.mythtvDbConfig["DBHostName"],
                            user=self.mythtvDbConfig["DBUserName"],
                            passwd=self.mythtvDbConfig["DBPassword"],
                            db=self.mythtvDbConfig["DBName"])
        db.query('SELECT chanid, name, xmltvid FROM channel WHERE visible=1 ORDER BY name ASC')
        results = db.store_result()
        all_rows = results.fetch_row(0, 1) # get all rows at once, use indexed as dic (by name)
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
        
        # read the channel configuration file
        for line in open(arguments.channelconf, 'r'):
            temp = [item.strip() for item in line.split('#')]
            if temp[0] != "":
                qitem = QStandardItem(temp[1] +' ('+ temp[0] +')')
                self.channelConfig.append({'id':temp[0], 'name':temp[1], 'qitem':qitem})
        self.channelConfig.sort(key=itemgetter('name'))
        self.channelModel = QStandardItemModel()
        for item in self.channelConfig:
            self.channelModel.appendRow( item['qitem'])
        self.ui.listViewYatvgrabberConfig.setModel(self.channelModel)
        
        # set the initial selection
        confSelection = self.ui.listViewMythtvConfig.selectionModel().selection()
        confSelection.clear()
        confSelection.select( self.mythtvConfig[0]['qitem'].index(), self.mythtvConfig[0]['qitem'].index())
        self.ui.listViewMythtvConfig.selectionModel().select(confSelection, QItemSelectionModel.ClearAndSelect)
        self.ClickedChannelListView()
        
        # connect the ui controls
        self.ui.writeMythtvConfigButton.clicked.connect(self.ClickedExportToMySQL)
        self.ui.writeYaTvGrabberConfigButton.clicked.connect(self.ClickedExportToChannelConf)
        self.ui.lineSearchMythtvConfig.textChanged.connect(self.UpdatedChannelSearchField)
        self.ui.lineSearchYatvgrabberConfig.textChanged.connect(self.UpdateIdSearchField)
        self.ui.listViewMythtvConfig.clicked.connect(self.ClickedChannelListView)
        self.ui.listViewYatvgrabberConfig.clicked.connect(self.ClickedIdListView)
        self.ui.clearMythtvXmlTvIdButton.clicked.connect(self.ClearSelectedXmlTvId)
        self.ui.radioButtonWithoutXmlId.toggled.connect(self.ToggledWithoutXmlIdRadioButton)
    
    def ClickedExportToMySQL(self):
        db = _mysql.connect(host=self.mythtvDbConfig["DBHostName"],
                            user=self.mythtvDbConfig["DBUserName"],
                            passwd=self.mythtvDbConfig["DBPassword"],
                            db=self.mythtvDbConfig["DBName"])
        db.autocommit(True)
        for row in self.mythtvConfig:
            useairguideFlag = 0 if row['xmltvid'] != "" else 1 # automatic unset / set the useonairguide flag (no xmltvid --> use dvb eit epg)
            db.query('UPDATE channel SET xmltvid=\''+row['xmltvid']+'\', useonairguide='+str(useairguideFlag)+' WHERE chanid='+row['chanid'])
        db.close()
        QMessageBox.information(self, 'Info', 'The channel configuration has been written to the MythTV database.\n' + self.mythtvDbConfig["DBName"] +'@'+ self.mythtvDbConfig["DBHostName"])
    
    def ClickedExportToChannelConf(self):
        shutil.copy(self.yatvgrabberConfigFile, self.yatvgrabberConfigFile + '.bak')
        tempCopy = sorted(self.mythtvConfig, key=itemgetter('xmltvid'))
        chanfile = open(self.yatvgrabberConfigFile, 'w')
        for row in tempCopy:
            if row['xmltvid'] != "":
                chanfile.write(row['xmltvid'] +"#"+ row['name'] +"\n")
        chanfile.close()
        QMessageBox.information(self, 'Info', 'The configuration has been exported to the YaTvGrabber channel file.\n' + self.yatvgrabberConfigFile)
    
    def UpdatedChannelSearchField(self, text_str):
        for (counter, item) in enumerate(self.mythtvConfig):
            self.ui.listViewMythtvConfig.setRowHidden(counter,(item['name'].lower().find(str(text_str).lower()) == -1))
    
    def UpdateIdSearchField(self, text_str):
        for (counter, item) in enumerate(self.channelConfig):
            self.ui.listViewYatvgrabberConfig.setRowHidden(counter,(item['name'].lower().find(str(text_str).lower()) == -1))
    
    def ClickedChannelListView(self):
        selectedMythConfIndex = self.ui.listViewMythtvConfig.currentIndex().row()
        if selectedMythConfIndex == -1:
            selectedMythConfIndex = 0
        confSelection = self.ui.listViewYatvgrabberConfig.selectionModel().selection()
        confSelection.clear()
        for item in self.channelConfig:
            if item['id'] == self.mythtvConfig[selectedMythConfIndex]['xmltvid']:
                confSelection.select( item['qitem'].index(), item['qitem'].index())
                self.ui.listViewYatvgrabberConfig.scrollTo(item['qitem'].index())
        self.ui.listViewYatvgrabberConfig.selectionModel().select(confSelection, QItemSelectionModel.ClearAndSelect)
        # update the id search line to show current selected channel name
        self.ui.lineSearchYatvgrabberConfig.setText(self.mythtvConfig[selectedMythConfIndex]['name'])
        self.UpdateIdSearchField(self.mythtvConfig[selectedMythConfIndex]['name'])
    
    def ClickedIdListView(self):
        selectedChannelConfIndex = self.ui.listViewYatvgrabberConfig.currentIndex().row()
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
        confSelection = self.ui.listViewYatvgrabberConfig.selectionModel().selection()
        confSelection.clear()
        self.ui.listViewYatvgrabberConfig.selectionModel().select(confSelection, QItemSelectionModel.Clear)
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
