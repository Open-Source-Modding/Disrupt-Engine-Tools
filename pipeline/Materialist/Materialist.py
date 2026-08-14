"""
Materialist v1.0
Gilbert Arcand
Created on September 20 2019
The purpose of this tool is to help visualise material derivation hierarchy
"""

from os.path import join, dirname, basename, abspath
from os import pardir
from sys import argv, exit, path as sys_path
from PySide import QtGui, QtCore
from PySide.QtCore import Qt
from time import sleep as time_sleep
from scandir import walk
from webbrowser import open as web_open
from time import clock as time_clock

path = dirname(abspath(__file__))
parent_dir = abspath(join(path, pardir))
sys_path.append(parent_dir)
# Simon: This is where all the information comes from... adp asset dependency parser??
from DDV import adp_lib as adp
from Common import pysideUICutils, disrupt_stylesheet, PERFORCE_Stuff, CSV_Stuff, disrupt_modelview as dmv
from p4_utilities import p4_utilities as Perforce

import ctypes
myappid = 'materialist.myproduct.subproduct.version'  # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

class EditSmallBufferDialog(QtGui.QDialog):
    def __init__(self, parent):
        super(EditSmallBufferDialog, self).__init__(parent)
        self.UI = pysideUICutils.get_uitype(join(dirname(__file__), r"UI\MatEdit_Edit_SmallBuffer.ui"))
        self.UI.setupUi(self)

        self.owner = parent
        self.items = None

    def init_ecd(self, value, items):
            
        self.UI.lineEdit_prev.setText(value)
        self.UI.lineEdit_new.setCurrentIndex(int(value))
        self.items = items

    def clicked_copy(self):
        self.UI.lineEdit_new.setCurrentIndex(int(self.UI.lineEdit_prev.text()))
    def clicked_ok(self):
        value = str(self.UI.lineEdit_new.currentIndex())
        self.owner.update_mat_small_buffer(value, self.items)
        self.accept()

    def clicked_cancel(self):
        self.reject()


class ControlMainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(ControlMainWindow, self).__init__()
        self.UI = pysideUICutils.get_uitype(join(path, r"UI\Materialist.ui"))
        self.UI.setupUi(self)
        self.setWindowTitle("Materialist v0.2")
        self.setWindowIcon(QtGui.QIcon(join(path, r"UI\Materialist")))

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(join(path, r"UI\Materialist_Logo.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.UI.pushButton.setIcon(icon)
        self.current_column = None

        self.main_path = path.lower().replace("\\td_tools\\PythonTools\\materialist", "")  # Data path
        self.materials_path = r"W:\main\data\graphics\_materials"

        self.material_list = []
        self.visibility_list = []
        self.search_list_file = []
        self.treeitem_dict = {}
        self.treeitem_dict_rev = {}
        
        
        self.shader_list =[
            "skinnedhologram",
            "blended",
            "wd2emissive",
            "wd2glass",
            "kodoglass",
            "kodoemissive",
            "kodo3glass",
            "wd3glass",
            "wd2confetti",
            "wd2fxwater",
            "wd3fxexplosion",
            "wd2fxsmoke",
            "wd3godraywall",
            "windowlight",
            "wd2fxalpha",
            "wd2fxemissive",
            "wd2fxfire",
            "arcloak",
            "driverwire",
            "wd2fxdistortion",
            "wd2fxnethack",
            "wd3fakefog",
            "detectorvolume",
            "wd2fxwaterwave"
        ]
        
        
        #self.popup_menu = QtGui.QMenu(self)
        #self.connect(self.UI.treeWidget, QtCore.SIGNAL("customContextMenuRequested(const QPoint &)"), self.menuContextTree)
        self.contextmenu = QtGui.QMenu()
        self.p4 = Perforce.P4Helper()
        
        self.edit_smallbuffer_dialog = EditSmallBufferDialog(self)

    def init_mat(self):
        self.toggle_waitcursor()
        initial_time = time_clock()
        self.UI.treeWidget.setColumnWidth(0, 300)
        self.UI.treeWidget.setColumnWidth(1, 100)
        self.UI.treeWidget.setColumnWidth(2, 200)
        self.UI.treeWidget.setColumnWidth(3, 100)
        self.UI.treeWidget.setColumnWidth(4, 50)
        self.UI.treeWidget.setColumnWidth(5, 500)
        self.UI.treeWidget.setColumnWidth(6, 500)
        self.UI.treeWidget.setColumnWidth(7, 500)
        
        self.refresh_ui()
        self.init_context_menu()
        self.get_files()
        self.update_visibility()

        final_time = time_clock()
        self.update_status_bar("Ready (" + str(int(final_time - initial_time)) + " seconds)")
        self.toggle_waitcursor(False)

    def init_context_menu(self):
        self.UI.treeWidget.customContextMenuRequested.connect(self.show_contextmenu)
        action_name2clip = QtGui.QAction(self)
        action_name2clip.setObjectName("action_name2clip")
        action_name2clip.setText("Copy Name")
        action_name2clip.triggered.connect(self.action_name2clip)
        self.contextmenu.addAction(action_name2clip)
        action_path2clip = QtGui.QAction(self)
        action_path2clip.setObjectName("action_path2clip")
        action_path2clip.setText("Copy Path")
        action_path2clip.triggered.connect(self.action_path2clip)
        self.contextmenu.addAction(action_path2clip)
        action_content2clip = QtGui.QAction(self)
        action_content2clip.setObjectName("action_content2clip")
        action_content2clip.setText("Copy Content")
        action_content2clip.triggered.connect(self.action_content2clip)
        self.contextmenu.addAction(action_content2clip)
        
        action_set_small_buffer = QtGui.QAction(self)
        action_set_small_buffer.setObjectName("actionMenu_small_buffer")
        action_set_small_buffer.setText("Set MSAAOptimizationHighQuality")
        action_set_small_buffer.triggered.connect(self.set_small_buffer)
        self.contextmenu.addAction(action_set_small_buffer)

        
    def show_contextmenu(self, point):
        if len(self.UI.treeWidget.selectedIndexes()) > 0:
            print "selectedIndexes" + str(self.UI.treeWidget.selectedIndexes())
            self.current_column = self.UI.treeWidget.columnAt(int(point.x()))
            self.contextmenu.exec_(QtGui.QCursor.pos())

    def action_name2clip(self):
        selection = self.UI.treeWidget.selectedItems()
        values = []
        for i in selection:
            value = self.treeitem_dict.get(i)
            values.append(value)
        names = []
        for v in values:
            names.append(v.name)
        text2print = str(names)
        self._copy2clip(text2print)

    def action_path2clip(self):
        selection = self.UI.treeWidget.selectedItems()
        values = []
        for i in selection:
            value = self.treeitem_dict.get(i)
            values.append(value)
        filenames = []
        for v in values:
            filenames.append(v.filename)
        text2print = str(filenames)
        self._copy2clip(text2print)

    def action_content2clip(self):
        selection = self.UI.treeWidget.selectedItems()
        values = []
        for v in selection:
            values = values + v.data(0, Qt.UserRole).textures
        self._copy2clip(str(values))

    def _copy2clip(self, text):
        clipboard = QtGui.QClipboard()
        clipboard.setText(text)

        
        
    def getPerforceStatus (self, file):
        
      
        status =self.p4.is_available(file, True)
        if status == False:
            revision="Checkout by another user"
        else :
            revision="Available"
        return revision
    
    def get_files(self):

        self.update_status_bar("Get Material files...")

        mat_count = 0
        stride = 1000

        for root, dirs, files in walk(self.materials_path):
            mat_count += len(files)

        self.progressbar_setmax(mat_count / stride)

        count = 0
        
        
        temp={}

        for root, dirs, files in walk(self.materials_path):
            for file in files:
                count += 1
                if count > stride:
                    self.progressbar_update()
                    count = 0

                if file.lower().endswith(".xml"):
                    mat_object = adp.d_material(join(root, file))
                    # Simon to make sure that we can compare path not name as two materials could have the same name...
                    #temp[(mat_object.shader.lower())]=1
                    if mat_object.basematerial:
                        mat_object.basematerial = 'w:\main\data\\'+mat_object.basematerial.lower()
                    
                    
                    if self.is_ins_hader_list(mat_object.shader.lower()):
                        self.material_list.append(mat_object)
                    
                    """
                    if mat_object.shader.lower().startswith('wd2fx'):
                        self.material_list.append(mat_object)
                    if mat_object.shader.lower().startswith('wd3fx'):
                        self.material_list.append(mat_object)
                        
                        
                    if mat_object.shader.lower().startswith('blend'):
                        self.material_list.append(mat_object)
                    if mat_object.shader.lower().startswith('arc'):
                        self.material_list.append(mat_object)
                    if mat_object.shader.lower().startswith('wd3god'):
                        self.material_list.append(mat_object)    
                    if mat_object.shader.lower().startswith('wd3fak'):
                        self.material_list.append(mat_object)    
                    """    
                    if not mat_object.category:
                        mat_object.category = ""  # Fix crash

        self.progressbar_update(True)
        """
        for i in temp:
            print i
        """
        for i in self.material_list:
            self.visibility_list.append(i)

        # Simon Find texture path
        for i in self.material_list:
            i.textures = []
            for k, v in i.parameters.items():
                if type(v) == str:
                    if v.lower().endswith(".png"):
                        i.textures.append(join(self.materials_path, v.lower().replace("graphics\\_materials\\", "")))

        # Simon Move from update_visibility
        self.fill_ui()

        
    def is_ins_hader_list(self,s):  
        res = None
        
        for i in self.shader_list:
            if (s==i): 
                res=i
                break;
        
        if res!=None:   
            return True
        else:
            return False
        
    def fill_ui(self):
        # Simon get the keys from a value
        def getkfromv(dict, theSearch):
            theList = []
            for k, v in dict.items():
                if v is theSearch:
                    theList.append(k)
            return theList

        self.toggle_waitcursor()
        self.update_status_bar("Update UI...")
        parentchilds = {}#Dict item Mat parent, List of Mat child
        rootparents = set()
        # Simon build the parent childs dictionary
        for i in self.material_list:
            if not i.basematerial:
                rootparents.add(i)
            childs = []
            for c in self.material_list:
                if i.filename.lower() == c.basematerial:
                    childs.append(c)
            parentchilds[i] = childs

        # Simon Create material tree item for each materials
        for i in self.material_list:
            tree_item = [ i.name, self.getPerforceStatus(i.filename), i.category, i.shader, self.getMSAAOptimizationHighQuality(i),str(i.textures),str(i.basematerial).lower(),str(i.filename).lower()]
            item = QtGui.QTreeWidgetItem(tree_item)
            # Simon add the mat as user data linked to the widgetitem...
            item.setData(0, Qt.UserRole, i)
            item.setData(1, Qt.UserRole, i.filename)
            item.setData(2, Qt.UserRole, i.textures)
            

            for c in range(item.columnCount()):
                 item.setForeground(c, QtGui.QBrush(QtCore.Qt.white ))

            if self.getPerforceStatus(i.filename) =="Available":
                item.setForeground(1, QtGui.QBrush(QtCore.Qt.green ))
            if self.getPerforceStatus(i.filename) =="Checkout by another user":
                item.setForeground(1, QtGui.QBrush(QtCore.Qt.yellow ))
            
            # create a dict entry with name and mat
            self.treeitem_dict[item] = i
            self.treeitem_dict_rev[i] = item

        # Simon set items children's, I use a list in getkfromv but it should only returns one element
        for k,v in parentchilds.items():
            itemparent = getkfromv(self.treeitem_dict,k)
            rootparent = False
            if ((self.treeitem_dict.get(itemparent[0])) in rootparents):
                rootparent = True
            for i in range(len(v)):
                parentName = k.name
                childName = v[i].name
                parentPath = k.category
                childPath = v[i].category
                itemchild = getkfromv(self.treeitem_dict, v[i])
                # Simon State Color
                itemOk = QtGui.QBrush(QtGui.QColor("#ffffff"))
                itemError = QtGui.QBrush(QtGui.QColor("#ff0000"))
                itemWarning = QtGui.QBrush(QtGui.QColor("#ff8800"))
                # Tool tips
                item_ErrorTip = "Error, derivation contains an underscore at the beginning."
                itemNameWarningTip = "Warning, derivation does not follow naming convention."
                itemPathWarningTip = "Warning, derivation not in the same path as original."
                # Simon Check if parent that are not at the root dont begins with an underscore
                ##itemparent[0].setForeground(0, itemOk)
                if rootparent:
                    if parentName.startswith("_"):
                        parentName = parentName[1::]
                        if parentName.lower().endswith("_master"):
                            parentName = parentName[0:(len(parentName) - 7)]
                if not rootparent:
                    if parentName.startswith("_"):
                        itemparent[0].setForeground(0, itemError)
                # Check if parent and child follows the rules...
                # You must have the parent name in the children
                ##itemchild[0].setForeground(0, itemOk)
                if childName.find(parentName) < 0:
                    itemchild[0].setForeground(0, itemWarning)
                    itemchild[0].setToolTip(0, itemNameWarningTip)
                if childPath.find(parentPath) < 0:
                    itemchild[0].setForeground(2, itemWarning)
                    itemchild[0].setToolTip(2, itemPathWarningTip)
                if childName.startswith("_"):
                    itemchild[0].setForeground(0, itemError)
                    itemchild[0].setToolTip(0,item_ErrorTip)
                itemparent[0].insertChild(i, itemchild[0])

        # Simon Add all the items in the widget
        self.UI.treeWidget.insertTopLevelItems(0, self.treeitem_dict.keys())
        self.clear_status_bar()
        self.UI.label_count.setText(str(len(self.material_list)))
        self.toggle_waitcursor(False)

        
    def getMSAAOptimizationHighQuality(self, item): 
        return item.parameters.get("MSAAOptimizationHighQuality")
        
    def update_visibility(self):
        temp_vis = {}
        #Maxime 
        count=0
        
        # Simon add a check if the dictionary have data empty = false
        if self.treeitem_dict_rev.keys():
            for i in self.material_list:
                temp_vis[i] = True
                # Simon set tree widget visibility
                widget = self.treeitem_dict_rev.get(i)
                widget.setExpanded(False)
                
                for c in range(widget.columnCount()):
                    color = widget.foreground(c).color() 
                    color.setAlpha(255)
                    widget.setForeground(c,color)
                if widget.isHidden():
                    widget.setHidden(False)

            for i in self.material_list:
                for j in self.search_list_file:
                    if j not in i.category.lower() and j not in i.name.lower() and j not in basename(i.filename).lower() and j not in i.shader.lower():
                        temp_vis[i] = False
                        # Simon set tree widget visibility
                        widget = self.treeitem_dict_rev.get(i)
                        
                        for c in range(widget.columnCount()):
                            color = widget.foreground(c).color() 
                            color.setAlpha(64)
                            widget.setForeground(c,color)
                        widget.setHidden(True)
                        
            
            # Maxime make parent visible if child is found 
            for i in self.material_list:
                if temp_vis[i] == True:
                    widget = self.treeitem_dict_rev.get(i)
                    while widget is not None:
                        widget = widget.parent()
                        if widget is not None:
                            widget.setHidden(False)
                            widget.setExpanded(True)
                            for c in range (widget.childCount()):
                               widget.child(c).setHidden(False)
                                
                            
                           
                        
                        
                       
                       
                        
            
            
            self.visibility_list = []

            for key, value in temp_vis.iteritems():
                if value:
                    self.visibility_list.append(key)
                    count+=1
                    
            self.UI.label_count.setText(str(count))    
        # Simon Move to get files
        # self.fill_ui()

        
            
    def set_small_buffer(self):

        items = self.UI.treeWidget.selectedItems()
        smallBufferValue = items[0].text(4)
        
        if smallBufferValue=='':
            smallBufferValue = "0"
        
        for i in items:
            if smallBufferValue.lower() != i.text(4).lower():
                smallBufferValue = "0"
                break
       

        self.edit_smallbuffer_dialog.init_ecd(smallBufferValue, items)
        self.edit_smallbuffer_dialog.exec_()

    def update_mat_small_buffer(self, value, items):
        message=[]
        
        for i in items:
            
            if self.p4.edit(i.text(7), True):
                opened_file = open(i.text(7), "r")
                file_lines = opened_file.readlines()
                opened_file.close()
                
                found =0
                for index, line in enumerate(file_lines):
                    if "MSAAOptimizationHighQuality" in line:
                        file_lines[index] = line.replace(i.text(4), value)
                        i.setText(4,value)
                        found =1
                        break
                
                if found==0:
                    for index, line in enumerate(file_lines):
                        if "</material>" in line:
                            file_lines[index] = line.replace("</material>", "    <parameter name=\"MSAAOptimizationHighQuality\" value=\""+value+"\"/>\n</material>")
                            i.setText(4,value)
                            break 
                    
                
                while 1: #Python is sometimes faster than perforce, keep trying until it works
                    try:
                        opened_file = open(i.text(7), "w")
                        opened_file.writelines(file_lines)
                        break
                    except:
                        pass
            else:
                message.append(self.p4.warning_message)
        nbr_message=len(message)
        if nbr_message>0:  
            if nbr_message>1:
                txt_msg="files"
            else:
                 txt_msg="file"
            self.show_warning( r"Check Out Failed for "+str(nbr_message)+' '+txt_msg, '\n'.join(message))
           
            

    
    def show_warning(self, title, text):
        QtGui.QMessageBox.warning(self, title, text)

    @QtCore.Slot()
    def on_lineEdit_search_returnPressed(self):
        text = self.UI.lineEdit_search.text().lower()
        self.search_list_file = text.split(" ")
        self.update_visibility()

    @QtCore.Slot()
    def on_toolButton_clr_search_clicked(self):
        self.UI.lineEdit_search.clear()
        self.search_list_file = []
        self.update_visibility()

    @QtCore.Slot()
    def on_pushButton_clicked(self):
        web_open('https://www.youtube.com/watch?v=6p-lDYPR2P8')  # Hehe...

    def progressbar_setmax(self, maximum):
        self.UI.progressBar.setMaximum(maximum)

    def progressbar_update(self, maxout=False):
        if maxout:
            self.UI.progressBar.setValue(self.UI.progressBar.maximum())
            self.progressbar_reset()
        else:
            self.UI.progressBar.setValue(self.UI.progressBar.value() + 1)
        self.refresh_ui()

    def progressbar_reset(self):
        time_sleep(0.25)
        self.UI.progressBar.reset()

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
    mySW.init_mat()
    exit(app.exec_())


if __name__ == "__main__":
    main()
