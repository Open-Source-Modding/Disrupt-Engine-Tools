from maya import OpenMayaUI as omui
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtUiTools import *
from shiboken2 import wrapInstance
import shiboken2
import maya.cmds as cmds
from PySide2 import QtCore, QtGui, QtUiTools
import os
import abc
import time

# This is a base class for Maya PySide windows.
class PySideWindow(object):
    # Add the ability to have abstract methods in Python
    __metaclass__ = abc.ABCMeta

    # Constructor
    def __init__(self, uiFilePath):
        self.uiFilePath = uiFilePath
        self.MainWindow = None
        # QtCore.QTimer.singleShot(0, self.buttonSelScaleClick) # for automating clicks on timers

    # Obtain the maya window wrapper to ensure correct window focusing
    def getMayaWindow():
        ptr = omui.MQtUtil.mainWindow()
        if ptr is not None:
            return shiboken.wrapInstance(long(ptr), QtGui.QWidget)

    # Use PySide to load the ui file, converting it into a PySide QDialog object
    def loadUiWidget(self, uifilename, parent=getMayaWindow()):
        loader = QtUiTools.QUiLoader()
        uifile = QFile('g:/Code/maya/qt/shaderParser.ui')
        uifile.open(QtCore.QFile.ReadOnly)
        ui = loader.load(uifile, parent)
        uifile.close()
        ui.setWindowFlags(Qt.Window)

        return ui

    # Show the dialog
    def show(self):
        self.close()
        app = QtGui.QApplication.instance()

        self.MainWindow = self.loadUiWidget(self.uiFilePath)
        self.connectSignals()
        # setColumnWidth(int, int)
        self.MainWindow.show()
        app.exec_()

    # Dispose the dialog
    def close(self):
        if self.MainWindow != None:
            self.MainWindow.close()
            self.MainWindow = None

    ############################################################
    # custom methods begin
    def customMethod(self):
        print 'custom method ran'


############################################################################
# Abstract method to be overridden in classes that inherit this base class.
#@abc.abstractmethod

def connectSignals(self):
    raise NotImplementedError("Please implement this method")

class AssetTaggerWindow(PySideWindow):
    # Constructor
    def __init__(self):
        uiFilePath = QFile('d:/Code/maya/qt/shaderParser.ui') # TODO: Replace this to code repo
        super(AssetTaggerWindow, self).__init__(uiFilePath)

    # Override connect signals method
    def connectSignals(self):
        self.MainWindow.buttonShaderFile.clicked.connect(self.buttonShaderFileClick)
        self.MainWindow.buttonBuildShader.clicked.connect(self.buttonBuildShaderClick)

    # Signal Methods
    def buttonShaderFileClick(self):
		print "button shader file clocked"

	def buttonBuildShaderClick(self):
		print "button build shader clicked"