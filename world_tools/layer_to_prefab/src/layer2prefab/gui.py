import os
import sys
import logging
from layer2prefab import __version__
from layer2prefab.core import my_script
from layer2prefab.core import updateGroups
from PySide import QtCore, QtGui


class CentralMainWidgetSignals(QtCore.QObject):
    status = QtCore.Signal(str)
    call_script = QtCore.Signal(str, str, str or None)
    call_script_groups = QtCore.Signal(str)


class QDialogNoClose(QtGui.QFileDialog):
    def __init__(self):
        QtGui.QFileDialog.__init__(self)

    def accept(self, evt):
        # .. todo:: add validation that the selected path is under the associated root?
        evt.accept()


class LineEditWithLabel(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.label = QtGui.QLabel()
        self.label.setText("Prefab Group:")
        self.switch_new = QtGui.QCheckBox()
        self.switch_new.setText("New Group")
        self.edit = QtGui.QLineEdit()
        self.edit.hide()
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.switch_new)
        layout.addWidget(self.edit)
        self.groups = QtGui.QComboBox()
        layout.addWidget(self.groups)
        self.setLayout(layout)
        self.switch_new.stateChanged.connect(self.change_visibility)

        # on toggle, or on click drop down
        # call updateGroups and get group list
        # update dropdown
        #   self.groups.addItems(groupNames)
        #      self.go_button.clicked.connect(self.do_work)

    def change_visibility(self, state):
        self.groups.setVisible(not state)
        self.edit.setVisible(state)

    def updateGroups(self):
        groupNames = ["1","2"]
        self.groups.addItems(groupNames)

    @property
    def group(self):
        state = self.switch_new.checkState()
        if state:
            return self.edit.text()
        return self.groups.currentText()


class CentralMainWidget(QtGui.QWidget):
    root = r"W:\main\data"
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.signals = CentralMainWidgetSignals()
        self.layer_path = QDialogNoClose()
        self.layer_path.setDirectory(self.root + r"\worlds")
        self.layer_path.setFilter("*.xml")
        self.prefab_path = QDialogNoClose()
        self.prefab_path.setDirectory(self.root + r"\databases\Prefabs")
        self.prefab_path.setFilter("*.xml")
        self.go_button = QtGui.QPushButton("Convert Layer to Prefab")
        self.prefab_groupname = LineEditWithLabel()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.layer_path)
        layout.addWidget(self.prefab_path)
        layout.addWidget(self.prefab_groupname)
        layout.addWidget(self.go_button)
        self.setLayout(layout)
        self.go_button.clicked.connect(self.debug_print)
        self.go_button.clicked.connect(self.do_work)
        self.go_button.clicked.connect(self.get_groups)
        #self.prefab_path.mouseDoubleClickEvent()#connect(self.get_groups)




    def do_work(self):
        prefab = self.prefab_path.selectedFiles()[0]
        world = self.layer_path.selectedFiles()[0]
        group = self.prefab_groupname.group
        if not os.path.isfile(prefab):
            return
        if not os.path.isfile(world):
            return
        self.signals.call_script.emit(prefab, world, group)

    def debug_print(self):
        prefab = self.prefab_path.selectedFiles()[0]
        world = self.layer_path.selectedFiles()[0]
        msg = "Prefab %s, Layer %s" % (prefab, world)
        if not os.path.isfile(prefab):
            msg = "Please select a Prefab from the second list"
        if not os.path.isfile(world):
            msg = "Please select a World from the first list"
        logging.info(msg)
        self.signals.status.emit(msg)

    def get_groups(self):
        prefab = self.prefab_path.selectedFiles()[0]
        if not os.path.isfile(prefab):
            return
        self.signals.call_script_groups.emit(prefab)

class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        cw = CentralMainWidget()
        self.setCentralWidget(cw)
        self.setWindowTitle("Pina's L2P Converter v%s" % __version__)
        cw.signals.status.connect(self.statusBar().showMessage)
        cw.signals.call_script.connect(my_script)
        cw.signals.call_script_groups.connect(updateGroups)
        self.statusBar().showMessage("Ready")


def main():
    app = QtGui.QApplication(sys.argv)
    logging.basicConfig(level=logging.INFO)
    mw = MainWindow()
    mw.show()
    app.exec_()


if __name__ == '__main__':
    main()
