"""
SlimShader v1.0
Gilbert Arcand
Created on February 26 2019
The purpose of this tool is to help compiling shader
"""

from os.path import join, dirname, abspath, isfile
from os import pardir
from subprocess import Popen, PIPE
from sys import argv, exit, path as sys_path
from PySide import QtGui, QtCore
from scandir import walk
from webbrowser import open as web_open
from time import clock as time_clock
from datetime import datetime
import ConfigParser

path = dirname(abspath(__file__))
parent_dir = abspath(join(path, pardir))
sys_path.append(parent_dir)

from Common import pysideUICutils, disrupt_stylesheet

import ctypes
myappid = 'slimshader.myproduct.subproduct.version'  # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


class SlimLayer(QtGui.QWidget):
    def __init__(self, parent, name, key):
        super(SlimLayer, self).__init__()
        self.UI = pysideUICutils.get_uitype(join(path, r"UI\SlimShader_Layer.ui"))
        self.UI.setupUi(self)

        self._controler = parent

        self.name = name
        self.key = key

        self.UI.checkBox.setText(self.name)
        self.UI.checkBox.setStyleSheet("QCheckBox::indicator { width:16px; height: 16px; }");

    def is_checked(self):
        return self.UI.checkBox.isChecked()

    def check(self, value=True):
        return self.UI.checkBox.setChecked(value)

    @QtCore.Slot()
    def on_checkBox_toggled(self):
        self._controler.update_count()
        self._controler.toggle_compile_button()


class ControlMainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(ControlMainWindow, self).__init__()
        self.UI = pysideUICutils.get_uitype(join(path, r"UI\SlimShader.ui"))
        self.UI.setupUi(self)
        self.setWindowTitle("SlimShader v1.01")
        self.setWindowIcon(QtGui.QIcon(join(path, r"UI\SlimShader")))

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(join(path, r"UI\SlimShader_Logo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.UI.pushButton.setIcon(icon)

        self.main_path = path.lower().replace("\\tools\\python\\slimshader", "")  # Data path

        self.ini_file = join(path, r"SlimShader.ini")
        self.master_section = "Path"
        self.key_bin = "Bin"
        self.key_fx = "Fx"
        self.key_fil = "Filter"
        self.key_win = "win"
        self.key_orb = "orb"
        self.key_dur = "dur"
        self.key_yet = "yet"
        self.key_edi = "edi"

        self.files_list = []
        self.search_list = []
        self.layers_ui = []

    def init_slim(self):
        self.toggle_waitcursor()
        initial_time = time_clock()

        self.UI.pushButton_compile.setEnabled(False)

        self.refresh_ui()
        self.import_ini()

        if self.UI.lineEdit_bin.text() == "":
            self.on_toolButton_browse_bin_clicked()

        if self.UI.lineEdit_fx.text() == "":
            self.on_toolButton_browse_fx_clicked()

        self.get_files()
        self.fill_ui()
        self.refresh_scrollarea()
        self.refresh_ui()

        self.update_visibility()

        final_time = int(time_clock() - initial_time)

        text = "Ready (" + str(final_time) + " second"
        if final_time > 1:
            text += "s"
        text += ")"

        self.update_status_bar(text)
        self.toggle_waitcursor(False)

    def get_files(self):
        self.update_status_bar("Get FX files...")

        fx_path = self.UI.lineEdit_fx.text()

        for root, dirs, files in walk(fx_path):
            for file in files:
                if file.lower().endswith(".fx"):
                    if isfile(join(fx_path, file)):
                        self.files_list.append(("", file.lower()))

            for dir in dirs:
                for root2, dirs2, files2 in walk(join(root, dir)):
                    for file2 in files2:
                        if file2.lower().endswith(".fx"):
                            if isfile(join(fx_path, dir, file2)):
                                self.files_list.append((dir, file2.lower()))

            break

    def fill_ui(self):
        self.update_status_bar("Update UI...")

        for i in self.files_list:
            if i[0] != "":
                fx_name = i[0] + r" / " + i[1]
            else:
                fx_name = i[1]

            self.layers_ui.append(SlimLayer(self, fx_name, i))

        self.clear_status_bar()

    def refresh_scrollarea(self):
        scrollarea_layout = QtGui.QVBoxLayout()
        for i in reversed(self.layers_ui):
            scrollarea_layout.insertWidget(0, i)
        spacer = QtGui.QSpacerItem(40, 2000, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        scrollarea_layout.addSpacerItem(spacer)
        scrollarea_layout.setContentsMargins(0, 0, 0, 0)
        scrollarea_layout.setSpacing(0)

        widget = QtGui.QWidget()
        widget.setLayout(scrollarea_layout)

        self.UI.scrollArea.setWidget(widget)

    def changed_search(self):
        search_string = self.UI.lineEdit_search.text().lower()
        self.search_list = []
        self.search_list = search_string.split(" ")
        self.update_visibility()

    def update_visibility(self):
        temp_vis = {}

        for i in self.files_list:
            temp_vis[i] = False

        for i in self.files_list:
            for j in self.search_list:
                if j not in i[0].lower() and j not in i[1].lower():
                    temp_vis[i] = True

        for key, value in temp_vis.iteritems():
            for i in self.layers_ui:
                if key == i.key:
                    i.setHidden(value)
                    break

        self.update_count()

    def update_count(self):
        count_sel = 0
        count_total = 0

        for i in self.layers_ui:
            if not i.isHidden():
                count_total += 1

                if i.is_checked():
                    count_sel += 1

        self.UI.label_sel.setText(str(count_sel))
        count = str(count_total) + " shader"
        if count_total > 1:
            count += "s"
        self.UI.label_count.setText(count)

    def compile_shaders(self):
        self.toggle_waitcursor()
        self.update_status_bar("Please wait...")
        self.UI.verticalWidget.setEnabled(False)
        self.UI.verticalWidget_2.setEnabled(False)
        self.refresh_ui()

        path_bin = self.UI.lineEdit_bin.text()
        #path_fx = self.UI.lineEdit_fx.text()

        # ToolLauncher_r64.exe ShaderGenerator2 platform = win64 operation = generate families = Mesh_VFXIntersection, Mesh_VFXLaser, Particle_WD2FxAlpha
        path_toollauncher = path_bin + r"\ToolLauncher_r64.exe ShaderGenerator2 platform="

        platform_list = []

        if self.UI.checkBox_win.isChecked():
            platform_list.append(r"win64")
        if self.UI.checkBox_orb.isChecked():
            platform_list.append(r"orbis")
        if self.UI.checkBox_dur.isChecked():
            platform_list.append(r"durango")
        if self.UI.checkBox_yet.isChecked():
            platform_list.append(r"yeti api=vulkan")
        if self.UI.checkBox_edi.isChecked():
            platform_list.append(r"win64 editor")

        text_operation = r" operation=generate families="

        text_families = ""
        

        for i in self.layers_ui:
            if not i.isHidden():
                if i.is_checked():

                    family = i.name.replace(r".fx", "")
                    family = family.replace(" ", "")
                    try:
                        family = family.split("/")[1]
                    except:
                        pass

                    text_families += family + ","

        #Kill last comma
        if text_families[-1] == ",":
            text_families = text_families[0:-1]

        for i in platform_list:
            text_command = path_toollauncher + i + text_operation + text_families

            self.UI.textEdit.append("--- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---")
            self.UI.textEdit.append(str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.UI.textEdit.append(text_command)
            self.UI.textEdit.append("\n")

            self.refresh_ui()

            pipe = Popen(text_command, stdout=PIPE)
            potato = pipe.communicate()[0]

            self.UI.textEdit.append(potato)

            self.refresh_ui()

        self.UI.verticalWidget.setEnabled(True)
        self.UI.verticalWidget_2.setEnabled(True)
        self.update_status_bar("All done.")
        self.refresh_ui()
        self.toggle_waitcursor(False)

    def closeEvent(self, event):
        try:
            with open(self.ini_file, 'w') as saved_file:
                self.export_ini().write(saved_file)
        except:
            pass

    def import_ini(self):
        try:
            import_ini = ConfigParser.RawConfigParser()
            import_ini.read(self.ini_file)

            path_bin = str(import_ini.get(self.master_section, self.key_bin))
            path_fx = str(import_ini.get(self.master_section, self.key_fx))
            search_fil = str(import_ini.get(self.master_section, self.key_fil))
            platform_win = str(import_ini.get(self.master_section, self.key_win))
            platform_orb = str(import_ini.get(self.master_section, self.key_orb))
            platform_dur = str(import_ini.get(self.master_section, self.key_dur))
            platform_edi = str(import_ini.get(self.master_section, self.key_edi))
            platform_yet = str(import_ini.get(self.master_section, self.key_yet))

            self.UI.lineEdit_bin.setText(path_bin)
            self.UI.lineEdit_fx.setText(path_fx)
            self.UI.lineEdit_search.setText(search_fil)

            self.UI.checkBox_win.setChecked(True if platform_win == "True" else False)
            self.UI.checkBox_orb.setChecked(True if platform_orb == "True" else False)
            self.UI.checkBox_dur.setChecked(True if platform_dur == "True" else False)
            self.UI.checkBox_edi.setChecked(True if platform_edi == "True" else False)
            self.UI.checkBox_yet.setChecked(True if platform_yet == "True" else False)
            
            self.changed_search()
        except:
            pass

    def export_ini(self):
        export_ini = ConfigParser.RawConfigParser()

        export_ini.add_section(self.master_section)
        export_ini.set(self.master_section, self.key_bin, self.UI.lineEdit_bin.text())
        export_ini.set(self.master_section, self.key_fx, self.UI.lineEdit_fx.text())
        export_ini.set(self.master_section, self.key_fil, self.UI.lineEdit_search.text())
        export_ini.set(self.master_section, self.key_win, self.UI.checkBox_win.isChecked())
        export_ini.set(self.master_section, self.key_orb, self.UI.checkBox_orb.isChecked())
        export_ini.set(self.master_section, self.key_dur, self.UI.checkBox_dur.isChecked())
        export_ini.set(self.master_section, self.key_edi, self.UI.checkBox_edi.isChecked())
        export_ini.set(self.master_section, self.key_yet, self.UI.checkBox_yet.isChecked())

        return export_ini

    def toggle_compile_button(self):
        self.clear_status_bar()

        self.UI.pushButton_compile.setEnabled(False)

        toggle = False

        for i in self.layers_ui:
            if not i.isHidden():
                if i.is_checked():
                    toggle = True
                    break

        if toggle:
            if self.UI.checkBox_win.isChecked():
                self.UI.pushButton_compile.setEnabled(True)
            elif self.UI.checkBox_orb.isChecked():
                self.UI.pushButton_compile.setEnabled(True)
            elif self.UI.checkBox_dur.isChecked():
                self.UI.pushButton_compile.setEnabled(True)
            elif self.UI.checkBox_edi.isChecked():
                self.UI.pushButton_compile.setEnabled(True)
            elif self.UI.checkBox_yet.isChecked():
                self.UI.pushButton_compile.setEnabled(True)

    def show_warning(self, title, text):
        QtGui.QMessageBox.warning(self, title, text)

    @QtCore.Slot()
    def on_toolButton_browse_bin_clicked(self):
        binPath = QtGui.QFileDialog.getExistingDirectory(self, r'Browse for bin folder', self.UI.lineEdit_bin.text())
        if binPath:
            self.UI.lineEdit_bin.setText(binPath)

    @QtCore.Slot()
    def on_toolButton_browse_fx_clicked(self):
        fxPath = QtGui.QFileDialog.getExistingDirectory(self, r'Browse for data\engine\shaders\Meta folder', self.UI.lineEdit_fx.text())
        if fxPath:
            self.UI.lineEdit_fx.setText(fxPath)

    @QtCore.Slot()
    def on_toolButton_clr_clicked(self):
        self.UI.lineEdit_search.clear()
        self.search_list = []
        self.update_visibility()

    @QtCore.Slot()
    def on_pushButton_compile_clicked(self):
        self.compile_shaders()

    @QtCore.Slot()
    def on_toolButton_all_clicked(self):
        for i in self.layers_ui:
            if not i.isHidden():
                i.check()

        self.update_count()

    @QtCore.Slot()
    def on_toolButton_none_clicked(self):
        for i in self.layers_ui:
            i.check(False)

        self.update_count()

    @QtCore.Slot()
    def on_lineEdit_search_returnPressed(self):
        self.changed_search()

    @QtCore.Slot()
    def on_pushButton_clicked(self):
        web_open('https://www.youtube.com/watch?v=eJO5HU_7_1w')  # Hehe...

    @QtCore.Slot()
    def on_checkBox_win_toggled(self):
        self.toggle_compile_button()

    @QtCore.Slot()
    def on_checkBox_orb_toggled(self):
        self.toggle_compile_button()

    @QtCore.Slot()
    def on_checkBox_dur_toggled(self):
        self.toggle_compile_button()

    @QtCore.Slot()
    def on_checkBox_yet_toggled(self):
        self.toggle_compile_button()
    @QtCore.Slot()
    def on_checkBox_edi_toggled(self):
        self.toggle_compile_button()

    @QtCore.Slot()
    def on_toolButton_clr_text_clicked(self):
        self.UI.textEdit.clear()

    @QtCore.Slot()
    def on_toolButton_cpy_text_clicked(self):
        text = self.UI.textEdit.toPlainText()
        QtGui.QApplication.clipboard().setText(text)

    def update_status_bar(self, text):
        self.UI.statusbar.showMessage(text)

    def clear_status_bar(self):
        self.UI.statusbar.clearMessage()

    @staticmethod
    def refresh_ui():
        QtCore.QCoreApplication.processEvents()

    @staticmethod
    def toggle_waitcursor(bwait=True):
        if bwait:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        else:
            QtGui.QApplication.restoreOverrideCursor()


def main():
    app = QtGui.QApplication(argv)
    disrupt_stylesheet.set_stylesheet(app)
    mySW = ControlMainWindow()
    mySW.show()
    mySW.init_slim()
    exit(app.exec_())


if __name__ == "__main__":
    main()
