from PySide import QtGui, QtCore
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import xml.etree.cElementTree as ET
import os
from os.path import splitext, basename, join, split, isfile, getsize, getctime, abspath, dirname
import sys 
from sys import argv, exit, path as sys_path
from stat import S_IREAD, S_IRGRP, S_IROTH, S_IWUSR 
import math
import time
import xlsxwriter 
import pandas as pd
from P4 import P4, P4Exception

path = dirname(abspath(__file__))
parent_dir = abspath(join(path, os.pardir))
sys_path.append(parent_dir)
sys_path.append('..')  # Required by .bat file

from Common import pysideUICutils, disrupt_stylesheet
from p4_utilities import p4_utilities as Perforce
from DDV import adp_lib as adp
gx = adp.import_gamex(r"W:\main\python")  # import gamex lib from root EPA
from nfo_utilities import nfo_reader
cur_path = dirname(abspath(__file__))

class ControlMainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(ControlMainWindow, self).__init__()
        self.UI = pysideUICutils.get_uitype(join(dirname(__file__), r"UI\GLMinator.ui"))
        self.UI.setupUi(self)
        #self.UI.pushButton.setToolTip("Drag and Drop the list file onto Building2WLU to batch buildings")
        #Icons||-->> 
        self.red_icon = QtGui.QIcon()
        self.red_icon.addPixmap(QtGui.QPixmap(cur_path + r"\UI\GLMinator_red_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.green_icon = QtGui.QIcon()
        self.green_icon.addPixmap(QtGui.QPixmap(cur_path + r"\UI\GLMinator_green_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
       
        self.lock_icon = QtGui.QIcon()
        self.lock_icon.addPixmap(QtGui.QPixmap(cur_path + r"\UI\GLMinator_lock_icon.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
       
        self.app_icon = QtGui.QIcon()
        self.app_icon.addPixmap(QtGui.QPixmap(cur_path + r"\UI\GLMinator.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.setWindowIcon(self.app_icon)

        self.update_column_width([650, 150, 150,150,150,150])
        #Widget items global
        self.widget_items = []
        
        #P4 side >>
        self.p4 = Perforce.P4Helper()
        self.UI.comboBox_p4_server.addItem(self.p4.guess_studio_server())
        self.p4_ui_update(self.p4.connection_status())
        
         

    #P4 item UI ||-->>
    def set_p4_itemUI(self, item, message, icon, color):
        item.setIcon(1, icon)
        item.setText(1, message)
        item.setForeground(1,color)
    
   
    def get_immediate_subdirectories(self,a_dir):
        return [name for name in os.listdir(a_dir)
                if os.path.isdir(os.path.join(a_dir, name))]


    def get_latest_nfo_files(self,location):
        world = "london.nfo"
        nfo_files = set()
        sub_directories = self.get_immediate_subdirectories(location)
        versions = list()
        for version_directory in sub_directories:
            versions.append(int(version_directory))
        sorted_versions = sorted(versions, reverse=True)
        for i in xrange(len(sorted_versions)):
            found_it = False
            versions_path = join(location, str(sorted_versions[i]), "data_orbis")
            for path, subdirs, files in os.walk(versions_path):
                if world in files:
                    found_it = True
                for name in files:
                    if ".nfo" in name:
                        nfo_files.add(join(path, name))
            if found_it:
                print "Found most recent", world, "in", versions_path
                break
        return nfo_files

    def get_references_from_nfo(self,nfo_files):
        output_dict = dict()
        
        for nfo_file in nfo_files:
            tree = ET.ElementTree(file=nfo_file)
            for file in tree.iter("File"):
                output_dict[file.get("Path")] = [nfo_file, file.get("OriginalFileSize")]
        return output_dict


    def get_nfo(self,location, directpath = False):
        files = set()
        if directpath == False: 
            files = self.get_latest_nfo_files(location)
        else : 
            files = adp.get_files(location, ".nfo", "")
        reference_dict = self.get_references_from_nfo(files)
        return reference_dict
    
    def clicked_refresh(self, state):
        l_bool = False #True False convertion form state 2 == True, 0 == False
        if state == 0: l_bool = True
        for item in range(self.UI.treeWidget_1.topLevelItemCount()):
            self.UI.treeWidget_1.topLevelItem(item).setExpanded(l_bool)
    
    def p4_ui_update(self, p4message):
        self.UI.ResultsLabel.setText(p4message)
        if "connected" in p4message: 
            self.UI.pushButton_p4bool.setIcon(self.green_icon)
            self.UI.label_p4.setText("Connected")
        else : 
            self.UI.pushButton_p4bool.setIcon(self.red_icon)
            self.UI.label_p4.setText("Offline")
        
    def run_p4_command(self, command, file, widget_item, status_check = False): 
        return
#//////////////////////////////MAIN METHODS ///////////////////////////////////////

    def illegal_glm(self, glm_file, depot):
        xlm_file = glm_file.replace(".glm", ".xml")
        if not isfile(xlm_file):
            print(glm_file, "is supposed to be a .glm, but it doesn't have an .xml file.")
            return False
        try:
            tree = ET.ElementTree(file=xlm_file)
        except:
            print(xlm_file, "is invalid.")
            return False
        
        source_file = ""
        for elem in tree.iter("entities"): # from materials
            source_file = str(elem.attrib.get("source_file"))
        
        if source_file == "":
            print ("no source file found in ", xlm_file)
            return False
        source_file = source_file.replace('\\','/')
        source_file = depot + source_file
        
        try:
            self.p4.p4.run("files", source_file)
            return False
        except P4Exception:
            return True
      
        #return False

    def gamex_has_default_logic_material(self, gamex_file):
        with open(gamex_file, "rb") as f:
            gamex_buffer = f.read()
        dag = gx.data.DAG.FromBuffer(gamex_buffer)
        for index, dagNode in enumerate(dag):
            nodeAccessor = dagNode.GetData()
            metadata = nodeAccessor.GetSubData("logic_material_id")
            if metadata:
                for id in metadata.GetData():
                    if id == 4294967295: # check if mesh col is setbyface
                        refID = nodeAccessor.GetSubData(gx.data.Names.Reference)
                        if refID:
                            refID = refID.GetData()
                            meshbuf = dag.GetReferenceBuffer(refID[0])
                            polyMesh = gx.data.PolyMesh.FromBytes(meshbuf)
                            material_ids = "MaterialIDs"
                            for mat_id in set(polyMesh.GetChannel(material_ids).GetElements()):
                                if mat_id+1 ==0: return True #ids_set.add(mat_id+1)
                                    
                    if id == 0: return True #ids_set.add(str(id))
        return False

    def look_for_ccol(self, dag, node):
        nodeData = node.GetData()
        has_ccol = False
        triangle_count = 0
        for i in xrange(node.GetNumChildren()):
            dagNode = node.GetChild(i)
            nodeAccessor = dagNode.GetData()
            metadata = nodeAccessor.GetSubData("type")
            if not metadata:
                continue
            id = metadata.GetData()[0]
            #Get SCOL triangle count >>
            for id in metadata.GetData():
                if 'SCOL_MESH' not in id:
                    continue
                has_ccol = True
                refID = nodeAccessor.GetSubData(gx.data.Names.Reference)
                if not refID:
                    continue
                refID = refID.GetData()
                
                meshbuf = dag.GetReferenceBuffer(refID[0])
                if not meshbuf:
                    continue
                polyMesh = gx.data.PolyMesh.FromBytes(meshbuf)
                triangulation = "Triangulation"
                triangle_count += len(polyMesh.GetChannel(triangulation).GetElements())
               
            #self.look_for_ccol(dag, dagNode)
        return has_ccol, triangle_count

    def get_data_from_gamex(self, root, dag):
        triangle_count = 0
        
        for i in xrange(root.GetNumChildren()):
            dagNode = root.GetChild(i)
            nodeAccessor = dagNode.GetData()
            metadata = nodeAccessor.GetSubData("type")
            if not metadata:
                continue
            #Get Last LOD triangle count >>
            for id in metadata.GetData():
                if 'LOD' not in id:
                    continue
                refID = nodeAccessor.GetSubData(gx.data.Names.Reference)
                if not refID:
                    continue
                refID = refID.GetData()
                meshbuf = dag.GetReferenceBuffer(refID[0])
                if not meshbuf:
                    continue
                polyMesh = gx.data.PolyMesh.FromBytes(meshbuf)
                triangulation = "Triangulation"
                for i in xrange(5,-1,-1):
                    if id == 'LOD'+ str(i) and len(polyMesh.GetChannel(triangulation).GetElements()) > 0:
                        triangle_count = len(polyMesh.GetChannel(triangulation).GetElements())
                        break

        return triangle_count

    def get_files(self,ingame_files) : 
        #files = adp.get_files(r"W:\main\data\graphics", ".gamex", "")
        files = adp.get_files(r"W:\main\data\graphics", ".glm", "")
        filtered_files = {}
        #///////////////////////
        progress = 0
        QtCore.QCoreApplication.processEvents()
        #///////////////////////
        for file in files:
            #///////////////////////
            self.UI.progressBar.setValue((100.00/ len(files)) * progress)
            
            #///////////////////////in game? skip it
            file_name = file.lower()
            file_name = file_name.replace('/','\\')
            file_name = file_name.replace("w:\\main\\data\\","")
            #file_name = file_name.replace('gamex','xbg')
            file_name = file_name.replace('glm','xbg')

            file_name = r"{}".format(file_name)
            
            
            if file_name not in ingame_files:
                continue
            
            
            #/////////////////////// exclusion list
            items_exclusion_list = ["characters", "\\building_kit\\", "vehicles"]
            skip_next = False
            for item in items_exclusion_list:
                if item in file:
                    skip_next = True
                    continue
            if skip_next:
                continue
             #///////////////////////*************************************************************
            bad_practice_modeling = self.illegal_glm(file,"//wd3-data-source/sourcedata_nexus/")
            if bad_practice_modeling:
                filtered_files[file]= ingame_files.get(file_name)[1]
            #///////////////////////**************************************************************
            progress +=1
            #///////////////////////
        progress = 0
        QtCore.QCoreApplication.processEvents()
        #///////////////////////
        dict_len =  len(filtered_files)
        print ("found: ", dict_len)
        f_files = {}
        for f,s in filtered_files.items():
            #///////////////////////
            self.UI.progressBar.setValue((100.00/ dict_len) * progress)
            #///////////////////////
            
            if self.illegal_glm(f,"//wd2-temp-data-source/sourcedata_nexus/") == False:
                f_files[f] = ["WD2",s]
            #elif self.illegal_glm(f,"//wd1-data-source/sourcedata_nexus/") == False:
            #    f_files[f] = "WD1" #No WD1 assets found.
            else:
                f_files[f] = ["Unknown",s]


            #///////////////////////**************************************************************           
            progress +=1
            #///////////////////////
        time.sleep(0.5)
        self.UI.progressBar.reset()
        return f_files
     
#//////////////////////////////BUTTON ACTIONS ////////////////////////////////////

    def clicked_go(self):
        if self.UI.treeWidget_1.topLevelItemCount() == 0:
            return
        filename, extension = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '', ".xlsx(*.xlsx)")
        if filename == "" : return

        info_dict = {}
        headers = ["FileName", "P4 Status", "Repository", "Size"] #Couldn't retrieve columns names from header Stupid approach
        
        for column in range(len(headers)):
            column_data = []
            for i in range(self.UI.treeWidget_1.topLevelItemCount()): #Rows
                #self.UI.treeWidget_1.topLevelItem(item).columnCount()
                column_data.append(self.UI.treeWidget_1.topLevelItem(i).data(column,0))
            #Add them to dict
            info_dict.update({headers[column]:column_data})
        # Create a Pandas dataframe from the data.
        df = pd.DataFrame(info_dict)
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        
        df.to_excel(writer, sheet_name='Sheet1', startrow=1, header=False)
        # Get the xlsxwriter workbook and worksheet objects.
        workbook  = writer.book
        worksheet = writer.sheets['Sheet1']
        # Add a header format.
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1})
        # Write the column headers with the defined format.
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num + 1, value, header_format)       

        # Close the Pandas Excel writer and output the Excel file.
        writer.save()

    def clicked_clear(self):
        self.UI.treeWidget_1.clear()
    
    @QtCore.Slot()
    def on_pushButton_get_files_clicked(self):
        #/////////////////////// glms used in game
        #location = r"D:\Packages\orwell-game"
        location = r"\\ubisoft.org\projects\Orwell\TOR\Versions\Production\orwell-game"
        if self.UI.directpath.text() == "":
            files_used_dict = self.get_nfo(location)
        else :
            location = self.UI.directpath.text().lower()
            files_used_dict = self.get_nfo(location, True)
        #///////////////////////
        files = self.get_files(files_used_dict)
        #///////////////////////
        progress = 0
        QtCore.QCoreApplication.processEvents()
        self.UI.ResultsLabel.setText("GLM Files : " + str(len(files)))
        #///////////////////////
        self.UI.treeWidget_1.clear()
        for file,depot in files.items():
            #///////////////////////
            self.UI.progressBar.setValue((100.00/ len(files)) * progress)
            #///////////////////////
            #scol_triangle_count = '{:>10}'.format(str(priority[1]))
            #last_lod_triangle_count = '{:>10}'.format(str(priority[2]))
            #difference = '{:>10}'.format(str(int(priority[1]) -int(priority[2])))
            item_columns = [file, "" , depot[0],depot[1]]
            item_obj = QtGui.QTreeWidgetItem(item_columns)
            perfor_status = self.p4.is_available(file)
            red_col = QtGui.QBrush(QtGui.QColor(QtCore.Qt.red))
            white_col = QtGui.QBrush(QtGui.QColor(QtCore.Qt.white))
            self.set_p4_itemUI(item_obj,"Available" if perfor_status else self.p4.cur_item_message, self.green_icon if perfor_status else self.lock_icon, white_col if perfor_status else red_col)
            self.widget_items.append(item_obj)
            #///////////////////////
            progress +=1
            #///////////////////////
        self.UI.treeWidget_1.insertTopLevelItems(0, self.widget_items)
        #///////////////////////
        time.sleep(0.5)
        self.UI.progressBar.reset()
        #///////////////////////
        return
    
    def update_column_width(self, ColumnsWidth=[]):
        for i in range(len(ColumnsWidth)):
            self.UI.treeWidget_1.setColumnWidth(i,ColumnsWidth[i])

def main():
    app = QtGui.QApplication(argv)
    disrupt_stylesheet.set_stylesheet(app)
    mySW = ControlMainWindow()
    mySW.show()    
    exit(app.exec_())


if __name__ == "__main__":
    main()
