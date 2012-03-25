# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'configuratorgui.ui'
#
# Created: Sun Mar 25 18:02:02 2012
#      by: PyQt4 UI code generator 4.8.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

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
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "YaTvGrabber MythTV Configurator", None, QtGui.QApplication.UnicodeUTF8))
        self.listViewMythtvConfig = QtGui.QListView(Dialog)
        self.listViewMythtvConfig.setGeometry(QtCore.QRect(210, 40, 361, 451))
        self.listViewMythtvConfig.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listViewMythtvConfig.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.listViewMythtvConfig.setObjectName(_fromUtf8("listViewMythtvConfig"))
        self.listViewYatvgrabberConfig = QtGui.QListView(Dialog)
        self.listViewYatvgrabberConfig.setGeometry(QtCore.QRect(590, 40, 361, 451))
        self.listViewYatvgrabberConfig.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.listViewYatvgrabberConfig.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.listViewYatvgrabberConfig.setObjectName(_fromUtf8("listViewYatvgrabberConfig"))
        self.writeMythtvConfigButton = QtGui.QPushButton(Dialog)
        self.writeMythtvConfigButton.setGeometry(QtCore.QRect(10, 320, 191, 101))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.writeMythtvConfigButton.sizePolicy().hasHeightForWidth())
        self.writeMythtvConfigButton.setSizePolicy(sizePolicy)
        self.writeMythtvConfigButton.setText(QtGui.QApplication.translate("Dialog", "Write MythTV channel\n"
"Configuration to\n"
"MySQL database", None, QtGui.QApplication.UnicodeUTF8))
        self.writeMythtvConfigButton.setObjectName(_fromUtf8("writeMythtvConfigButton"))
        self.writeYaTvGrabberConfigButton = QtGui.QPushButton(Dialog)
        self.writeYaTvGrabberConfigButton.setGeometry(QtCore.QRect(10, 430, 191, 101))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.writeYaTvGrabberConfigButton.sizePolicy().hasHeightForWidth())
        self.writeYaTvGrabberConfigButton.setSizePolicy(sizePolicy)
        self.writeYaTvGrabberConfigButton.setText(QtGui.QApplication.translate("Dialog", "Write used MythTV\n"
"XMLTV ids to\n"
"YaTvGrabber channel\n"
"configuration", None, QtGui.QApplication.UnicodeUTF8))
        self.writeYaTvGrabberConfigButton.setObjectName(_fromUtf8("writeYaTvGrabberConfigButton"))
        self.lineSearchYatvgrabberConfig = QtGui.QLineEdit(Dialog)
        self.lineSearchYatvgrabberConfig.setGeometry(QtCore.QRect(590, 500, 361, 27))
        self.lineSearchYatvgrabberConfig.setObjectName(_fromUtf8("lineSearchYatvgrabberConfig"))
        self.lineSearchMythtvConfig = QtGui.QLineEdit(Dialog)
        self.lineSearchMythtvConfig.setGeometry(QtCore.QRect(210, 500, 361, 27))
        self.lineSearchMythtvConfig.setObjectName(_fromUtf8("lineSearchMythtvConfig"))
        self.labelMythtvConfig = QtGui.QLabel(Dialog)
        self.labelMythtvConfig.setGeometry(QtCore.QRect(210, 10, 361, 21))
        self.labelMythtvConfig.setText(QtGui.QApplication.translate("Dialog", "MythTV Configuration", None, QtGui.QApplication.UnicodeUTF8))
        self.labelMythtvConfig.setObjectName(_fromUtf8("labelMythtvConfig"))
        self.labelYatvgrabberConfig = QtGui.QLabel(Dialog)
        self.labelYatvgrabberConfig.setGeometry(QtCore.QRect(590, 10, 361, 21))
        self.labelYatvgrabberConfig.setText(QtGui.QApplication.translate("Dialog", "YaTvGrabber Channel Configuration", None, QtGui.QApplication.UnicodeUTF8))
        self.labelYatvgrabberConfig.setObjectName(_fromUtf8("labelYatvgrabberConfig"))
        self.clearMythtvXmlTvIdButton = QtGui.QPushButton(Dialog)
        self.clearMythtvXmlTvIdButton.setGeometry(QtCore.QRect(10, 10, 191, 111))
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.clearMythtvXmlTvIdButton.sizePolicy().hasHeightForWidth())
        self.clearMythtvXmlTvIdButton.setSizePolicy(sizePolicy)
        self.clearMythtvXmlTvIdButton.setText(QtGui.QApplication.translate("Dialog", "Clear XMLTV id\n"
"from selected\n"
"MythTV channel", None, QtGui.QApplication.UnicodeUTF8))
        self.clearMythtvXmlTvIdButton.setObjectName(_fromUtf8("clearMythtvXmlTvIdButton"))
        self.radioButtonWithoutXmlId = QtGui.QRadioButton(Dialog)
        self.radioButtonWithoutXmlId.setGeometry(QtCore.QRect(10, 140, 181, 31))
        self.radioButtonWithoutXmlId.setText(QtGui.QApplication.translate("Dialog", "Show only Channels\n"
"without XMLTV id", None, QtGui.QApplication.UnicodeUTF8))
        self.radioButtonWithoutXmlId.setChecked(False)
        self.radioButtonWithoutXmlId.setObjectName(_fromUtf8("radioButtonWithoutXmlId"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        pass

