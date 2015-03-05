# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'configuratorgui.ui'
#
# Created: Thu Mar  5 18:52:34 2015
#      by: PyQt4 UI code generator 4.10.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(960, 540)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog.sizePolicy().hasHeightForWidth())
        Dialog.setSizePolicy(sizePolicy)
        Dialog.setMinimumSize(QtCore.QSize(960, 540))
        Dialog.setMaximumSize(QtCore.QSize(960, 540))
        self.gridLayout_2 = QtGui.QGridLayout(Dialog)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.labelMythtvConfig = QtGui.QLabel(Dialog)
        self.labelMythtvConfig.setObjectName(_fromUtf8("labelMythtvConfig"))
        self.gridLayout.addWidget(self.labelMythtvConfig, 0, 1, 1, 1)
        self.labelYatvgrabberConfig = QtGui.QLabel(Dialog)
        self.labelYatvgrabberConfig.setObjectName(_fromUtf8("labelYatvgrabberConfig"))
        self.gridLayout.addWidget(self.labelYatvgrabberConfig, 0, 2, 1, 1)
        self.clearMythtvXmlTvIdButton = QtGui.QPushButton(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.clearMythtvXmlTvIdButton.sizePolicy().hasHeightForWidth())
        self.clearMythtvXmlTvIdButton.setSizePolicy(sizePolicy)
        self.clearMythtvXmlTvIdButton.setMinimumSize(QtCore.QSize(146, 0))
        self.clearMythtvXmlTvIdButton.setMaximumSize(QtCore.QSize(146, 16777215))
        self.clearMythtvXmlTvIdButton.setObjectName(_fromUtf8("clearMythtvXmlTvIdButton"))
        self.gridLayout.addWidget(self.clearMythtvXmlTvIdButton, 1, 0, 1, 1)
        self.listViewMythtvConfig = QtGui.QListView(Dialog)
        self.listViewMythtvConfig.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listViewMythtvConfig.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.listViewMythtvConfig.setObjectName(_fromUtf8("listViewMythtvConfig"))
        self.gridLayout.addWidget(self.listViewMythtvConfig, 1, 1, 4, 1)
        self.listViewYatvgrabberConfig = QtGui.QListView(Dialog)
        self.listViewYatvgrabberConfig.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listViewYatvgrabberConfig.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.listViewYatvgrabberConfig.setObjectName(_fromUtf8("listViewYatvgrabberConfig"))
        self.gridLayout.addWidget(self.listViewYatvgrabberConfig, 1, 2, 4, 1)
        self.radioButtonWithoutXmlId = QtGui.QRadioButton(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.radioButtonWithoutXmlId.sizePolicy().hasHeightForWidth())
        self.radioButtonWithoutXmlId.setSizePolicy(sizePolicy)
        self.radioButtonWithoutXmlId.setChecked(False)
        self.radioButtonWithoutXmlId.setObjectName(_fromUtf8("radioButtonWithoutXmlId"))
        self.gridLayout.addWidget(self.radioButtonWithoutXmlId, 2, 0, 1, 1)
        self.writeMythtvConfigButton = QtGui.QPushButton(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.writeMythtvConfigButton.sizePolicy().hasHeightForWidth())
        self.writeMythtvConfigButton.setSizePolicy(sizePolicy)
        self.writeMythtvConfigButton.setMinimumSize(QtCore.QSize(146, 0))
        self.writeMythtvConfigButton.setMaximumSize(QtCore.QSize(146, 16777215))
        self.writeMythtvConfigButton.setObjectName(_fromUtf8("writeMythtvConfigButton"))
        self.gridLayout.addWidget(self.writeMythtvConfigButton, 3, 0, 1, 1)
        self.writeYaTvGrabberConfigButton = QtGui.QPushButton(Dialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.writeYaTvGrabberConfigButton.sizePolicy().hasHeightForWidth())
        self.writeYaTvGrabberConfigButton.setSizePolicy(sizePolicy)
        self.writeYaTvGrabberConfigButton.setMinimumSize(QtCore.QSize(146, 0))
        self.writeYaTvGrabberConfigButton.setMaximumSize(QtCore.QSize(146, 16777215))
        self.writeYaTvGrabberConfigButton.setObjectName(_fromUtf8("writeYaTvGrabberConfigButton"))
        self.gridLayout.addWidget(self.writeYaTvGrabberConfigButton, 4, 0, 1, 1)
        self.lineSearchMythtvConfig = QtGui.QLineEdit(Dialog)
        self.lineSearchMythtvConfig.setObjectName(_fromUtf8("lineSearchMythtvConfig"))
        self.gridLayout.addWidget(self.lineSearchMythtvConfig, 5, 1, 1, 1)
        self.lineSearchYatvgrabberConfig = QtGui.QLineEdit(Dialog)
        self.lineSearchYatvgrabberConfig.setObjectName(_fromUtf8("lineSearchYatvgrabberConfig"))
        self.gridLayout.addWidget(self.lineSearchYatvgrabberConfig, 5, 2, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "YaTvGrabber MythTV Configurator", None))
        self.labelMythtvConfig.setText(_translate("Dialog", "MythTV Configuration", None))
        self.labelYatvgrabberConfig.setText(_translate("Dialog", "YaTvGrabber Channel Configuration", None))
        self.clearMythtvXmlTvIdButton.setText(_translate("Dialog", "Clear XMLTV id\n"
"from selected\n"
"MythTV channel", None))
        self.radioButtonWithoutXmlId.setText(_translate("Dialog", "Show only Channels\n"
"without XMLTV id", None))
        self.writeMythtvConfigButton.setText(_translate("Dialog", "Write MythTV channel\n"
"Configuration to\n"
"MySQL database", None))
        self.writeYaTvGrabberConfigButton.setText(_translate("Dialog", "Write used MythTV\n"
"XMLTV ids to\n"
"YaTvGrabber channel\n"
"configuration", None))

