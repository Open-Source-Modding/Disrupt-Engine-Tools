from os.path import exists, isfile, basename, splitext, dirname, abspath, join, expanduser, realpath, getmtime, isdir
from os import pardir, environ, system, listdir
import adp_lib as adp
from PySide import QtGui, QtCore
from sys import argv, exit, path as sys_path
from time import clock as time_clock, time, sleep
from csv import DictWriter as csv_writer
import xml.etree.cElementTree as ET
import math
from random import randrange
from ddv_loading import LoadingDialog
from ddv_search import SearchDialog
import base64
import getpass
import random
import sqlite3
import cPickle
import gc
import json
import zipfile


path = dirname(abspath(__file__))
parent_dir = abspath(join(path, pardir))
sys_path.append(parent_dir)
sys_path.append('..')  # Required by .bat file
from Common import pysideUICutils, disrupt_stylesheet, disrupt_modelview as dmv

import ctypes
myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

from jira.client import JIRA
from jira.exceptions import JIRAError
try:
    del environ['http_proxy']
    del environ['https_proxy']
except:
    pass
    
import requests # disables the warnings from JIRA
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from collections import OrderedDict
from _winreg import ConnectRegistry, OpenKey, QueryValueEx, HKEY_CURRENT_USER

###
# sys_path.append(r"W:\main\td_tools\gcassel")
# import deeper
###
    
# Global Variables
cur_path = dirname(abspath(__file__))
data_path = r"w:\main\data"             # wd3
# data_path = r"w:\wd2-temp\main\data"  # wd2
# data_path = r"w:\wd1\main\data"       # wd1
graphics_path = r"\graphics"
materials_path = r"" #r"\_materials"
list_path = r"\objects\list.xml"
spline_layer_path = r"\worlds\london\road\roads"
#spline_layer_path = r"\worlds\san_francisco\road\roads"
layer_brushes_path = r"\terrain\collections\london"
#layer_brushes_path = r"\terrain\collections\sanfrancisco"
brush_libraries_path = r"\editor\brushes"
collection_resource_library_file = r"\editor\collectionsystem\collectionresourceslibrary.xml"
proxies_path = r"\editor\proxy"
archetypes_path = r"\editor\entitylibrary"
prefabs_path = r"\databases\prefabs"
building_facade_prefabs_path = r"\databases\building"
generic_path = r"\databases\generic"
particle_emi_path = r"\databases\particlesemitters"
particle_sys_path = r"\databases\particlessystems"
character_par_path = r"\databases\generic\graphickit_parts"
character_mod_path = r"\databases\generic\graphickit_models"
character_col_path = r"\databases\generic\graphickit_collections"
markup_path = r"\animations"
sequence_path = r"\sequences"

class display_data(object):
    def __init__(self, label_parent, label_child, label_grandchild):
        super(display_data, self).__init__()

        # Model/View Stuff
        model_header = [("Name", "kwName"),  # kwName means keyword name, see disrup_modelview.py get_lambda_function()
                        ("Type", "kwType"),
                        ("Filename", "kwFile")]

        keys = ["parent", "current_item", "child", "grandchild"]

        self.model_dict = {x: dmv.d_tree_model(model_header) for x in keys}
        self.label_dict = {keys[0]: label_parent, keys[2]: label_child, keys[3]: label_grandchild}

    def feed_me(self, family_member, food):
        treeitem_dict = {}

        # Remove double entries
        for i in food:
            if treeitem_dict.get(i.identifier) is None:
                treeitem_dict[i.identifier] = i

        self.model_dict[family_member].setupModelData(treeitem_dict.values())

        #Update count label
        if family_member is not "current_item":
            self.label_dict[family_member].setText(str(self.model_dict[family_member].rowCount()))

    def clear(self):
        for model in self.model_dict.itervalues():
            model.clearChildren()

        for label in self.label_dict.values():
            label.setText("0")

    def get_object(self, index):
        for m in self.model_dict.itervalues():
            ret = m.GetObjectsList([index])
            if ret and len(ret) == 1:
                return ret[0] #Return only first item

    def get_model(self, family_member):
        return self.model_dict[family_member]


class stream_optimizer(object):
    def __init__(self, wlu_file):
        super(stream_optimizer, self).__init__()        
        self.cells = {}
        self.get_wlus(wlu_file)
        
    def get_wlus(self, wlu_file):
        root = None
        # if isinstance(wlu_file, basestring):
        #     root = ET.fromstring(wlu_file)
        # else:
        #     tree = ET.ElementTree(file=wlu_file)
        #     root = tree.getroot()
        if isfile(wlu_file):
            tree = ET.ElementTree(file=wlu_file)
            root = tree.getroot()
        else:
            root = ET.fromstring(wlu_file)

        for elem in root.findall("wlu"):
            new_cell = stream_optimizer_cell()
            new_cell.id = elem.get("ID","")
            new_cell.bbox_min = elem.get("BBox_Min","")
            new_cell.bbox_max = elem.get("BBox_Max","")
            new_cell.total_cost = 0.0
            for sub_elem in elem.iter():
                if sub_elem.tag == "Resource":
                    remove_gain = sub_elem.get("RemoveGain","").replace("MB","")
                    remove_gain = float(remove_gain)
                    id = sub_elem.get("ID", "")
                    id = id.lower()
                    if "_high.hkx" in id:
                        continue
                    new_cell.resource_files[id] = remove_gain
                    cost = float(sub_elem.get("EstimatedStreamingCost").replace("MB",""))
                    new_cell.total_cost += cost
            new_cell.total_cost = int(math.ceil(new_cell.total_cost))

            new_cell.get_coord()
            self.cells[new_cell.x, new_cell.y] = new_cell
                
    def get_cell(self, x, y):
        try:
            return self.cells[(x, y)]
        except:
            return None
            
                
class stream_optimizer_cell(object):
    def __init__(self):
        super(stream_optimizer_cell, self).__init__()
        self.id = ""
        self.bbox_min = ""
        self.bbox_max = ""
        self.total_cost = ""
        self.resource_files = {}
        self.resource_objects = {}
        self.x = 0
        self.y = 0
        
    def get_coord(self):
        values = self.bbox_min.split(",")
        x = float(values[0])
        y = float(values[1])
        x += 64.0 # get the center of the cell
        y += 64.0
        
        x += 4097 # offset because the grid in DDV starts at 0 and not -4096
        y += 4097
        
        self.x = int((math.ceil((x) / 128) * 128) / 128)
        self.y = int((math.ceil((y) / 128) * 128) / 128)     


class ControlMainWindow(QtGui.QMainWindow):
    def __init__(self):
        super(ControlMainWindow, self).__init__()

        q_pixmap = QtGui.QPixmap(join(cur_path, r"UI\ddv_icon256.png"))
        q_icon = QtGui.QIcon(q_pixmap)
        self.setWindowIcon(q_icon)        
        self.settings_file = join(expanduser("~\.DDV"), "DDV.ini")
        self.model_topview = None
        self.model_proparazzi = None
        self.pixmap_item = None        
        self.history = []
        self.current_total_cost = "0"        
        self.recursive_search_items = []
        
        self.old_data_hack()
        
        self.current_object = None
        self.parse_count = 22
        self.parse_world = True
        self.parse_spline_layers = True
        self.parse_libraries = True
        self.parse_graphics = True
        self.parse_particles = True
        self.parse_characters = True
        self.parse_animations = True
        self.parse_vegetation = True
        self.parse_worldlayer = True
        self.parse_entity = True
        self.parse_proxy = True
        self.parse_archetype = True
        self.parse_prefab = True
        self.parse_generic = True
        self.parse_emitter = True
        self.parse_system = True
        self.parse_part = True
        self.parse_model = True
        self.parse_collection = True
        self.parse_markup = True
        self.parse_geometry = True
        self.parse_material = True
        self.parse_texture = True
        self.parse_building = True
        self.parse_layerbrush = True
        self.parse_brushlib = True
        self.parse_vegecol = True
        self.parse_sequence = True

        self.world_object = None
        self.texture_profiles = None
        self.stream_optimizer_object = None
        self.world_layer_objects = {}
        self.world_cell_objects = {}
        self.entity_objects = {}
        self.spline_layer_objects = {}
        self.spline_objects = {}
        self.range_objects = {}
        self.proxy_objects = {}
        self.archetype_libraries_objects = {}
        self.archetype_item_objects = {}
        self.prefab_libraries_objects = {}
        self.prefab_item_objects = {}
        self.prefab_entity_objects = {}
        self.building_facade_prefab_libraries_objects = {}
        self.building_facade_prefab_item_objects = {}
        self.layer_brushes_objects = {}
        self.brush_libraries_objects = {}
        self.brush_item_objects = {}
        self.collection_resource_library_objects = {}
        self.collection_resource_item_objects = {}
        self.generic_libraries_objects = {}
        self.generic_item_objects = {}
        self.collection_item_objects = {}
        self.particle_emi_libraries_objects = {}
        self.particle_emi_item_objects = {}
        self.particle_sys_libraries_objects = {}
        self.particle_sys_item_objects = {}
        self.character_par_libraries_objects = {}
        self.character_par_item_objects = {}
        self.character_mod_libraries_objects = {}
        self.character_mod_item_objects = {}
        self.character_col_libraries_objects = {}
        self.character_col_item_objects = {}
        self.markup_objects = {}
        self.geometry_objects = {}
        self.material_objects = {}
        self.texture_objects = {}
        self.bink_objects = {}
        self.city_block_cell_objects = {}
        self.sequence_objects = {}
        
        self.object_dictionaries = (self.world_layer_objects, 
                                    self.world_cell_objects, 
                                    self.city_block_cell_objects, 
                                    self.entity_objects, 
                                    self.spline_layer_objects, 
                                    self.spline_objects, 
                                    self.range_objects, 
                                    self.proxy_objects, 
                                    self.archetype_libraries_objects, 
                                    self.archetype_item_objects, 
                                    self.prefab_libraries_objects, 
                                    self.prefab_item_objects, 
                                    self.prefab_entity_objects, 
                                    self.building_facade_prefab_libraries_objects, 
                                    self.building_facade_prefab_item_objects,
                                    self.layer_brushes_objects, 
                                    self.brush_libraries_objects, 
                                    self.brush_item_objects, 
                                    self.collection_resource_library_objects, 
                                    self.collection_resource_item_objects,
                                    self.generic_libraries_objects, 
                                    self.generic_item_objects,
                                    self.particle_emi_libraries_objects, 
                                    self.particle_emi_item_objects, 
                                    self.particle_sys_libraries_objects, 
                                    self.particle_sys_item_objects, 
                                    self.character_par_libraries_objects,
                                    self.character_par_item_objects, 
                                    self.character_mod_libraries_objects, 
                                    self.character_mod_item_objects, 
                                    self.character_col_libraries_objects, 
                                    self.character_col_item_objects,
                                    self.markup_objects,
                                    self.geometry_objects,
                                    self.material_objects,
                                    self.texture_objects,
                                    self.bink_objects, 
                                    self.collection_item_objects,
                                    self.sequence_objects,
                                    )
        
        self.proparazzi_stats_dict = None # dict used by the export csv button from proparazzi
        self.jira_ob_issues = []        
        self.jira_city_blocks_issues_la = []
        self.jira_city_blocks_issues_ld = []        
        self.city_locations = []
        self.atlas_data_dict_in = {}        
        self.atlas_data_dict_out_1 = {}
        self.atlas_data_dict_out_2 = {}        
        self.zones_dict = {}        
        self.selected_city_block_cell = None
        self.topview_mode = 0 #0 = WLU, 1 = City Blocks
        #self.game_map_path = cur_path + r"\UI\game_map_none.bmp"
        self.game_map_path = cur_path + r"\UI\game_map_none.bmp"

        self.game_map_path_cb = cur_path + r"\UI\game_map_studios.bmp"
        self.image_path = self.game_map_path
        self.image_path_cb = self.game_map_path_cb
        self.highlight_path = cur_path + r"\UI\highlight.png"
        self.highlight_lr_path = cur_path + r"\UI\highlight_lr.png"
        self.game_map_zones_image = QtGui.QImage(cur_path + r"\\UI\\" + "game_map_london_zones.bmp")
        self.game_map_cb_image = QtGui.QImage(cur_path + r"\\UI\\" + "game_map_cityblocks.bmp")
        self.city_blocks_image = None
        self.city_blocks_heatmap_image = None
        self.image_size = 1024
        self.zoom_index = 9
        self.zoom_factor = []
        self.top_view_scale = 1
        self._brush_gray = QtGui.QBrush(QtGui.QColor(0x808080))
        self.graphicsview_callback = True
        self.topview_selection = (-1, -1)
        self.topview_mute = False  # Shield top view from crashing when draging mouse around

        self.copy_buffer = [] #A list of stuff to send to clibpard via context menu, inelegant
        self.mute_selection = False #Used to avoid recursive "clear selection"
        self.db_file = cur_path + r"\resources\DDV_Data.db"
        self.use_old_parsing_method = False
        
        self.init_ui()

    def init_ui(self):
        self.version = "v1.932.1"
        self.title = "Disrupt Dependency Viewer "
        self.quote = " - Entia non sunt multiplicanda praeter necessitatem. - Qui totum vult totum perdit. -"
        self.world_name = ""
        self.world_path = r"\worlds\%s" % self.world_name
    
        self.UI = pysideUICutils.get_uitype(join(dirname(__file__), r"UI\Disrupt_Dependency_Viewer_UI.ui"))
        print(self.UI)
        self.UI.setupUi(self)
        self.UI.dockWidget_advanced_mode.setVisible(False)
        self.UI.statusbar.setVisible(False)
        self.UI.label_DDV.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.UI.lineEdit_pre.setVisible(False)
        self.ui_data = display_data(self.UI.label_count_parents,
                            self.UI.label_count_children,
                            self.UI.label_count_grandchld)
                            
        self.init_treeviews()
        self.loading_dialog = LoadingDialog(self)
        self.search_dialog = SearchDialog(self)
        
        self.contextmenu_copy = QtGui.QMenu() #Copy Context
        self.contextmenu_search = QtGui.QMenu()
        self.contextmenu_rs = QtGui.QMenu() #Context menu for red square tree view
        self.contextmenu_prop = QtGui.QMenu()
        self.contextmenu_search_panel = QtGui.QMenu()
        self.init_actions()
        self.init_context_menu()
        
        self.init_overrides()
        self.init_topview()

        if self.world_name == "san_francisco":
            self.game_map_path = cur_path + r"\UI\game_map_sanfran.bmp"
        
        self.check_user()
        
    def init_DDV(self):
        self.UI.tabWidget.setEnabled(False)
        
        self.settings = QtCore.QSettings(self.settings_file, QtCore.QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)
        
        self.UI.lineEdit_jira_login.setText(self.settings.value("login"))
        self.UI.lineEdit_jira_pwd.setText(base64.b64decode(self.settings.value("password", "Tm9uZQ==")))
        
        if self.UI.lineEdit_jira_login.text() == "":
            self.UI.lineEdit_jira_login.setText("@ubisoft.com")
            
        self.fill_comboboxes()
        self.get_zones()

        self.loading_dialog.init_ld()
        if not self.loading_dialog.exec_():
            self.loading_dialog.stop_timer()
            self.UI.tabWidget.setEnabled(True)
            return

        self.refresh_ui()

        initial_time = time_clock()

        self.toggle_waitcursor(True)
        self.progressbar_setmax(self.parse_count, True)

        if self.parse_world and self.world_object is None:
            self.update_status_bar("Retrieving World: "+ self.world_name)
            self.world_object = adp.d_world(data_path + self.world_path, self.callback, self.game_map_zones_image, self.zones_dict)

        self.refresh_ui()
        self.parse_graphic_data()       
        self.clear_genealogy()
        self.parse_genealogy()

        final_time = time_clock()
        self.update_status_bar("Ready (" + str(int(final_time - initial_time)) + " seconds)")
        self.toggle_waitcursor(False)

        self.UI.tabWidget.setEnabled(True)
        self.update_view()
        self.refresh_ui()

    def init_treeviews(self):
        keys = ["current_item", "parent", "child", "grandchild"]
        trees = [self.UI.treeView_0, self.UI.treeView_1, self.UI.treeView_2, self.UI.treeView_3]

        for index, tree in enumerate(trees):
            tree.sortByColumn(0, QtCore.Qt.AscendingOrder)
            tree.setModel(self.ui_data.get_model(keys[index]))
            tree.setColumnWidth(0, 250)
            tree.setColumnWidth(1, 100)

        # Proparazzi
        model_header = [("Item", "kwName"),  # kwName means keyword name, see disrup_modelview.py get_lambda_function()
                        ("Count", "kwCount"),
                        ("Type", "kwType"),
                        ("Filename", "kwFile"),
                        ("World Layer", "kwWorL"),
                        ("WLU", "kwWLU"),
                        ("Size", "kwSize"),
                        ("Special Info", "kwSpec")]

        self.model_proparazzi = dmv.d_tree_model(model_header)

        self.UI.treeView_prop.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.UI.treeView_prop.setModel(self.model_proparazzi)
        self.UI.treeView_prop.setColumnWidth(0, 250)
        self.UI.treeView_prop.setColumnWidth(1, 50)
        self.UI.treeView_prop.setColumnWidth(2, 100)
        self.UI.treeView_prop.setColumnWidth(3, 300)
        self.UI.treeView_prop.setColumnWidth(4, 300)
        self.UI.treeView_prop.setColumnWidth(5, 50)
        self.UI.treeView_prop.setColumnWidth(6, 75)

        # Topview
        model_header = [("Item", "kwName"),  # kwName means keyword name, see disrup_modelview.py get_lambda_function()
                        ("Count", "kwCount"),
                        ("Type", "kwType"),
                        ("World Layer", "kwWorL"),
                        ("WLU", "kwWLU"),
                        ("Special Info", "kwSpec")]

        self.model_topview = dmv.d_tree_model(model_header)

        self.UI.treeView_top.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.UI.treeView_top.setModel(self.model_topview)
        self.UI.treeView_top.setColumnWidth(0, 150)
        self.UI.treeView_top.setColumnWidth(1, 50)
        self.UI.treeView_top.setColumnWidth(2, 100)
        self.UI.treeView_top.setColumnWidth(3, 200)
        self.UI.treeView_top.setColumnWidth(4, 50)

    def init_parsing(self, bool_array):
        self.parse_world = bool_array[0]
        self.parse_libraries = bool_array[1]
        self.parse_graphics = bool_array[2]
        self.parse_particles = bool_array[3]
        self.parse_characters = bool_array[4]
        self.parse_animations = bool_array[5]
        self.parse_vegetation = bool_array[6]
        self.parse_worldlayer = bool_array[7]
        self.parse_entity = bool_array[8]
        self.parse_proxy = bool_array[9]
        self.parse_archetype = bool_array[10]
        self.parse_prefab = bool_array[11]
        self.parse_generic = bool_array[12]
        self.parse_emitter = bool_array[13]
        self.parse_system = bool_array[14]
        self.parse_part = bool_array[15]
        self.parse_model = bool_array[16]
        self.parse_collection = bool_array[17]
        self.parse_markup = bool_array[18]
        self.parse_geometry = bool_array[19]
        self.parse_material = bool_array[20]
        self.parse_texture = bool_array[21]
        self.parse_building = bool_array[22]
        self.parse_layerbrush = bool_array[23]
        self.parse_brushlib = bool_array[24]
        self.parse_vegecol = bool_array[25]
        self.parse_sequence = bool_array[26]

        #Group boxes disable the entire section
        if not self.parse_world:
            self.parse_worldlayer = self.parse_entity = False

        if not self.parse_libraries:
            self.parse_archetype = self.parse_prefab = self.parse_generic = self.parse_building = False

        if not self.parse_graphics:
            self.parse_proxy = self.parse_geometry = self.parse_material = self.parse_texture = False

        if not self.parse_particles:
            self.parse_emitter = self.parse_system = False

        if not self.parse_characters:
            self.parse_part = self.parse_model = self.parse_collection = False

        if not self.parse_animations:
            self.parse_markup = False

        if not self.parse_vegetation:
            self.parse_layerbrush = self.parse_brushlib = self.parse_vegecol = False


        temp_list = [self.parse_worldlayer,
                    self.parse_entity,
                    self.parse_proxy,
                    self.parse_archetype,
                    self.parse_prefab,
                    self.parse_generic,
                    self.parse_emitter,
                    self.parse_system,
                    self.parse_part,
                    self.parse_model,
                    self.parse_collection,
                    self.parse_markup,
                    self.parse_geometry,
                    self.parse_material,
                    self.parse_texture,
                    self.parse_building,
                    self.parse_layerbrush,
                    self.parse_brushlib,
                    self.parse_vegecol,
                    self.parse_sequence,
                    ]

        self.parse_count = 7
        for i in temp_list:
            if i:
                self.parse_count += 1

    #Init copy context menu actions
    def init_actions(self):

        self.action_set_current_item = QtGui.QAction(self)
        self.action_copy_iden = QtGui.QAction(self)
        self.action_copy_id = QtGui.QAction(self)
        self.action_copy_name = QtGui.QAction(self)
        self.action_copy_file = QtGui.QAction(self)
        self.action_open_file = QtGui.QAction(self)
        self.action_copy_coord = QtGui.QAction(self)

        self.action_separator = QtGui.QAction(self)
        self.action_separator.setSeparator(True)

        self.action_set_current_item.setObjectName("action_set_as_currentitem")
        self.action_copy_iden.setObjectName("actionMenu_copy_iden")
        self.action_copy_id.setObjectName("actionMenu_copy_id")
        self.action_copy_name.setObjectName("actionMenu_copy_name")
        self.action_copy_file.setObjectName("actionMenu_copy_file")
        self.action_open_file.setObjectName("actionMenu_open_file")
        self.action_copy_coord.setObjectName("actionMenu_copy_coord")

        self.action_set_current_item.setText("Set Current Item")
        self.action_copy_iden.setText("Copy Identifier")
        self.action_copy_id.setText("Copy ID")
        self.action_copy_name.setText("Copy Name")
        self.action_copy_file.setText("Copy File Name")
        self.action_open_file.setText("Open File With Default Program")
        self.action_copy_coord.setText("Copy Entity Coords")

        self.action_set_current_item.triggered.connect(self.contextmenu_setascurrentitem)
        self.action_copy_iden.triggered.connect(self.contextmenu_copy_iden)
        self.action_copy_id.triggered.connect(self.contextmenu_copy_id)
        self.action_copy_name.triggered.connect(self.contextmenu_copy_name)
        self.action_copy_file.triggered.connect(self.contextmenu_copy_file)
        self.action_open_file.triggered.connect(self.contextmenu_open_file)
        self.action_copy_coord.triggered.connect(self.contextmenu_copy_coord)
        

    #context Menu
    def init_context_menu(self):
        self.UI.listWidget_advanced_search.customContextMenuRequested.connect(self.show_contextmenu_search_panel)

        self.UI.treeView_0.customContextMenuRequested.connect(self.show_contextmenu_copy_0)
        self.UI.treeView_1.customContextMenuRequested.connect(self.show_contextmenu_copy_1)
        self.UI.treeView_2.customContextMenuRequested.connect(self.show_contextmenu_copy_2)
        self.UI.treeView_3.customContextMenuRequested.connect(self.show_contextmenu_copy_3)
        self.contextmenu_copy.addAction(self.action_copy_iden)
        #self.contextmenu_copy.addAction(self.action_copy_id)
        self.contextmenu_copy.addAction(self.action_copy_name)
        self.contextmenu_copy.addAction(self.action_copy_file)
        self.contextmenu_copy.addAction(self.action_open_file)
        self.contextmenu_copy.addAction(self.action_copy_coord)

        self.search_dialog.UI.treeView.customContextMenuRequested.connect(self.show_contextmenu_search)
        self.contextmenu_search.addAction(self.action_copy_iden)
        #self.contextmenu_search.addAction(self.action_copy_id)
        self.contextmenu_search.addAction(self.action_copy_name)
        self.contextmenu_search.addAction(self.action_copy_file)
        self.contextmenu_search.addAction(self.action_open_file)
        self.contextmenu_search.addAction(self.action_copy_coord)

        self.UI.treeView_top.customContextMenuRequested.connect(self.show_contextmenu_rs)
        # self.UI.action_setascurrentitem.triggered.connect(self.contextmenu_setascurrentitem) #Action is defined in .ui
        # self.contextmenu_rs.addAction(self.UI.action_setascurrentitem)
        self.contextmenu_rs.addAction(self.action_set_current_item)
        self.contextmenu_rs.addAction(self.action_separator)
        self.contextmenu_rs.addAction(self.action_copy_iden)
        #self.contextmenu_rs.addAction(self.action_copy_id)
        self.contextmenu_rs.addAction(self.action_copy_name)
        self.contextmenu_rs.addAction(self.action_copy_file)
        self.contextmenu_rs.addAction(self.action_open_file)
        self.contextmenu_rs.addAction(self.action_copy_coord)

        self.UI.treeView_prop.customContextMenuRequested.connect(self.show_contextmenu_prop)
        # self.contextmenu_prop.addAction(self.UI.action_setascurrentitem)
        self.contextmenu_prop.addAction(self.action_set_current_item)
        self.contextmenu_prop.addAction(self.action_separator)
        self.contextmenu_prop.addAction(self.action_copy_iden)
        #self.contextmenu_prop.addAction(self.action_copy_id)
        self.contextmenu_prop.addAction(self.action_copy_name)
        self.contextmenu_prop.addAction(self.action_copy_file)
        self.contextmenu_prop.addAction(self.action_open_file)
        self.contextmenu_prop.addAction(self.action_copy_coord)

    def old_data_hack(self):
        if "wd2" in data_path:
            self.loading_dialog.UI.comboBox_world_name.addItem("san_francisco")
            
        if "wd1" in data_path:
            self.loading_dialog.UI.comboBox_world_name.addItem("windy_city")
    
    def show_contextmenu_copy_0(self, point):
        self._show_contextmenu_copy(point, self.UI.treeView_0)

    def show_contextmenu_copy_1(self, point):
        self._show_contextmenu_copy(point, self.UI.treeView_1)

    def show_contextmenu_copy_2(self, point):
        self._show_contextmenu_copy(point, self.UI.treeView_2)

    def show_contextmenu_copy_3(self, point):
        self._show_contextmenu_copy(point, self.UI.treeView_3)

    def _show_contextmenu_copy(self, point, cur_tree):
        selection = self.get_tree_selection(cur_tree)
        
        if selection is None:
            return
        
        if len(selection) > 1:
            return

        current_obj = selection[0]

        if current_obj is not None:
            self.action_copy_iden.setText("Copy Identifier: " + str(current_obj.identifier))
            self.action_copy_id.setText(  "Copy ID:           " + str(current_obj.file_id))
            self.action_copy_name.setText("Copy Name:      " + str(current_obj.name))
            self.action_copy_file.setText("Copy File Name: " + str(current_obj.filename))
            coord_string = ""
            if current_obj.type == "Entity" or current_obj.type == "Range":
                coord_string = self.format_coordinate_string(current_obj)
                self.action_copy_coord.setText("Copy Entity/Range Coords: " + str(current_obj.position))
            else:
                coord_string = "Not an Entity, no coords available!"
                self.action_copy_coord.setText("Copy Entity/Range Coords: " + coord_string)

            self.copy_buffer = [current_obj.identifier, str(current_obj.file_id), current_obj.name, current_obj.filename, coord_string]

            self.contextmenu_copy.exec_(QtGui.QCursor.pos())

    def show_contextmenu_search(self, point):
        self._show_contextmenu_copy(point, self.search_dialog.UI.treeView)
        
    def show_contextmenu_search_panel(self, point):
        self._show_contextmenu_copy(point, self.search_dialog.UI.treeView)

    def show_contextmenu_rs(self, point):
        selection = self.get_tree_selection(self.UI.treeView_top)

        if len(selection) > 1:
            return

        current_obj = selection[0]

        if current_obj is not None:
            self.action_copy_iden.setText("Copy Identifier: " + str(current_obj.identifier))
            self.action_copy_id.setText(  "Copy ID:           " + str(current_obj.file_id))
            self.action_copy_name.setText("Copy Name:      " + str(current_obj.name))
            self.action_copy_file.setText("Copy File Name: " + str(current_obj.filename))
            coord_string = ""
            if current_obj.type == "Entity" or current_obj.type == "Range":
                coord_string = self.format_coordinate_string(current_obj)
                self.action_copy_coord.setText("Copy Entity/Range Coords: " + str(current_obj.position))
            else:
                coord_string = "Not an Entity, no coords available!"
                self.action_copy_coord.setText("Copy Entity/Range Coords: " + coord_string)

            self.copy_buffer = [current_obj.identifier, str(current_obj.file_id), current_obj.name, current_obj.filename, coord_string]

            self.contextmenu_rs.exec_(QtGui.QCursor.pos())

    def show_contextmenu_prop(self, point):
        self._show_contextmenu_copy(point, self.UI.treeView_prop)

    def contextmenu_copy_iden(self):
        clipboard = QtGui.QClipboard()
        clipboard.setText(self.copy_buffer[0])

    def contextmenu_copy_id(self):
        clipboard = QtGui.QClipboard()
        clipboard.setText(self.copy_buffer[1])

    def contextmenu_copy_name(self):
        clipboard = QtGui.QClipboard()
        clipboard.setText(self.copy_buffer[2])

    def contextmenu_copy_file(self):
        clipboard = QtGui.QClipboard()
        clipboard.setText(self.copy_buffer[3])
        
    def contextmenu_open_file(self):
        if not isfile(str(self.copy_buffer[3])):
            return
        system("start " + self.copy_buffer[3])
        
    def contextmenu_copy_coord(self):
        clipboard = QtGui.QClipboard()
        clipboard.setText(self.copy_buffer[4])

    def contextmenu_setascurrentitem(self):
        self.current_object = self.get_tree_selection(self.UI.treeView_top)[0]
        self.set_current_object()
    
    def parse_graphic_data(self):
        self.update_status_bar("Getting Local Files")
        self.progressbar_setmax(17)

        progressbar_stride = 250

        spline_layer_files = set()
        proxy_files = set()
        archetype_libraries_files = set()
        prefab_libraries_files = set()
        building_facade_prefab_libraries_files = set()
        layer_brushes_files = set()
        brush_libraries_files = set()
        geometry_files = set()
        material_files = set()
        texture_files = set()
        particle_emi_libraries_files = set()
        particle_sys_libraries_files = set()
        character_par_libraries_files = set()
        character_mod_libraries_files = set()
        character_col_libraries_files = set()
        generic_libraries_files = set()
        markup_files = set()
        bink_files = set()
        sequence_files = set()

        # Get all the necessary files
        if self.parse_spline_layers:
            spline_layer_files = adp.get_files(data_path+spline_layer_path, [".xml"], "")
        self.progressbar_update()
        
        if self.parse_proxy:
            proxy_files = adp.get_files(data_path+proxies_path, [".xml"], "")
        self.progressbar_update()

        if self.parse_archetype:
            archetype_libraries_files = adp.get_files(data_path+archetypes_path, [".xml"], "")
        self.progressbar_update()

        if self.parse_prefab:
            prefab_libraries_files = adp.get_files(data_path+prefabs_path, [".xml"], "")
        self.progressbar_update()

        if self.parse_building:
            building_facade_prefab_libraries_files = adp.get_files(data_path+building_facade_prefabs_path, [".xml"], "")
        self.progressbar_update()

        if self.parse_layerbrush:
            layer_brushes_files = adp.get_files(data_path+ self.world_path+layer_brushes_path, [".xml"], "")
        self.progressbar_update()

        if self.parse_brushlib:
            brush_libraries_files = adp.get_files(data_path+brush_libraries_path, [".xml"], "")
        self.progressbar_update()

        if self.parse_geometry:
            temp_geometry_files = adp.get_files(data_path+graphics_path, [".glm", ".gamex", ".lft"], "")
            for file in temp_geometry_files:
                file = file.replace(".glm", ".xml")
                file = file.replace(".gamex", ".xml")
                file = file.replace(".lft", ".xml")
                if not isfile(file):
                    continue
                geometry_files.add(file)
        self.progressbar_update()

        if self.parse_material:
            material_files = adp.get_files(data_path+graphics_path+materials_path, [".material.xml"], "")
        self.progressbar_update()

        if self.parse_texture:
            texture_files = adp.get_files(data_path+graphics_path, [".png"], "")
        self.progressbar_update()

        if self.parse_emitter:
            particle_emi_libraries_files = adp.get_files(data_path+particle_emi_path, [".xml"], "")
        self.progressbar_update()

        if self.parse_system:
            particle_sys_libraries_files = adp.get_files(data_path+particle_sys_path, [".xml"], "")
        self.progressbar_update()

        if self.parse_part:
            character_par_libraries_files = adp.get_files(data_path+character_par_path, [".xml"], "")
        self.progressbar_update()

        if self.parse_model:
            character_mod_libraries_files = adp.get_files(data_path+character_mod_path, [".xml"], "")
        self.progressbar_update()

        if self.parse_collection:
            character_col_libraries_files = adp.get_files(data_path+character_col_path, [".xml"], "")
        self.progressbar_update()

        if self.parse_generic:
            generic_libraries_files = adp.get_files(data_path+generic_path, [".xml"], "")#, False) #Don't explore sub-folders
        self.progressbar_update()

        if self.parse_markup:
            markup_files = adp.get_files(data_path+markup_path, [".markup"], "")
        self.progressbar_update(True)
        
        if self.parse_texture: # hooked on textures because binks are referenced like textures
            bink_files = adp.get_files(data_path, [".bik"], "")
        self.progressbar_update(True)
        
        if self.parse_sequence:
            sequence_files = adp.get_files(data_path+sequence_path, [".seq"], "")
        
        if self.use_old_parsing_method:
            # Parse the world layers of the selected world
            if self.world_object is not None:
                self.update_status_bar("Parsing World Layer File")
                self.progressbar_setmax(len(self.world_object.layer_objects))
                
                city_block_layers = set()
                for layer_obj in self.world_object.layer_objects:
                    self.progressbar_update()
                    self.world_layer_objects[layer_obj.identifier] = layer_obj
                    self.world_layer_objects[layer_obj.get_content("|")] = layer_obj

                    if "city_block_shapes" in layer_obj.filename:
                        city_block_layers.add(layer_obj.filename)
                
                self.draw_city_blocks(city_block_layers)
                self.progressbar_update(True)
            
        # Parse the world cells of the selected world
        if self.world_object is not None:
            self.update_status_bar("Parsing World Cells")
            self.progressbar_setmax(len(self.world_object.world_grid.cells))

            for cell in self.world_object.world_grid.cells.values():
                self.progressbar_update()
                self.world_cell_objects[cell.identifier] = cell
                self.world_cell_objects[cell.get_content("|")] = cell
            self.progressbar_update(True)

        # Parse all entities
        if self.use_old_parsing_method:
            if self.parse_worldlayer:
                self.update_status_bar("Parsing World Layer Entities")
                self.progressbar_setmax(len(self.world_layer_objects))

                for layer_obj in self.world_layer_objects.values():
                    self.progressbar_update()
                    for entity in layer_obj.entities:
                        self.entity_objects[entity.identifier] = entity
                        self.entity_objects[entity.get_content("|")] = entity
                        cb = self.city_block_cell_objects.get(entity.get_city_block_color(self.city_blocks_image))
                        if cb is None:
                            continue
                        cb.entities.add(entity)
                        cb.add_dependency(entity.identifier)
                self.progressbar_update(True)
            
        # Parse the spline layers
        if self.use_old_parsing_method:
            if self.parse_worldlayer: # using same flag as world layers, are spline layers are somewhat the same thing
                self.update_status_bar("Reticulating Splines")
                self.progressbar_setmax(len(spline_layer_files))

                for file in spline_layer_files:
                    self.progressbar_update()
                    spline_layer = adp.d_spline_layer(file)
                    self.spline_layer_objects[spline_layer.identifier] = spline_layer
                    self.spline_layer_objects[spline_layer.get_content("|")] = spline_layer
                    #self.spline_layer_objects[spline_layer.name] = spline_layer
                    
                    for spline in spline_layer.spline_objects:
                        self.spline_objects[spline.identifier] = spline
                        self.spline_objects[spline.get_content("|")] = spline
                        #self.spline_objects[spline.name + " " + spline.identifier] = spline
                        
                        for range in spline.range_objects:
                            self.range_objects[range.identifier] = range
                            self.range_objects[range.get_content("|")] = range
                            #self.range_objects[range.name + " " + range.identifier] = range
                            
                            cb = self.city_block_cell_objects.get(range.get_city_block_color(self.city_blocks_image, self.world_object.world_size))
                            if cb is None:
                                continue
                            cb.entities.add(range)
                            cb.add_dependency(range.identifier)
                    
                self.world_object.fill_cells_with_ranges(self.range_objects)
                    
                self.progressbar_update(True)

        # Parse all proxies
        if self.use_old_parsing_method:
            if self.parse_proxy:
                counter = progressbar_stride
                self.update_status_bar("Parsing Proxy Files")
                self.progressbar_setmax(len(proxy_files) / progressbar_stride)

                for proxy_obj in proxy_files:
                    counter += 1
                    if counter > progressbar_stride:
                        self.progressbar_update()
                        counter = 0
                    prox = adp.d_proxy(proxy_obj)
                    self.proxy_objects[prox.identifier] = prox
                    self.proxy_objects[prox.get_content("|")] = prox
                    self.proxy_objects[prox.file_id] = prox # file_id acts as a second identifier!!!
                    # self.proxy_objects[prox.name + " " + prox.identifier] = prox
                self.progressbar_update(True)

        # Parse all archetype libraries
        if self.use_old_parsing_method:
            if self.parse_archetype:
                self.update_status_bar("Parsing Archetype Libraries")
                self.progressbar_setmax(len(archetype_libraries_files))

                for arc_lib in archetype_libraries_files:
                    self.progressbar_update()
                    arch = adp.d_archetype_lib(arc_lib)
                    self.archetype_libraries_objects[arch.identifier] = arch
                    self.archetype_libraries_objects[arch.get_content("|")] = arch

                self.update_status_bar("Parsing Archetype Objects")

                for arc_obj in self.archetype_libraries_objects.values():
                    for item in arc_obj.lib_items_objects:
                        self.archetype_item_objects[item.identifier] = item
                        self.archetype_item_objects[item.get_content("|")] = item
                        #self.archetype_item_objects[item.name + " " + item.identifier] = item
                self.progressbar_update(True)

        # Parse all prefab libraries
        if self.use_old_parsing_method:
            if self.parse_prefab:
                self.update_status_bar("Parsing Prefab Libraries")
                self.progressbar_setmax(len(prefab_libraries_files))

                for prefab_lib in prefab_libraries_files:
                    self.progressbar_update()
                    pref = adp.d_prefab_lib(prefab_lib)
                    self.prefab_libraries_objects[pref.identifier] = pref
                    self.prefab_libraries_objects[pref.get_content("|")] = pref

                self.update_status_bar("Parsing Prefab Items")

                for pre_obj in self.prefab_libraries_objects.values():
                    for item in pre_obj.lib_items_objects:
                        self.prefab_item_objects[item.identifier] = item
                        self.prefab_item_objects[item.get_content("|")] = item
                        #self.prefab_item_objects[item.name + " " + item.identifier] = item
                        
                self.update_status_bar("Parsing Prefab Entities")

                for pre_item_obj in self.prefab_item_objects.values():
                    for pref_ent in pre_item_obj.entities:
                        if pref_ent.identifier in self.prefab_entity_objects.keys():
                            print 'Duplicated GUID in Prefab:', pref_ent.identifier, pref_ent.file_name
                        self.prefab_entity_objects[pref_ent.identifier] = pref_ent
                        self.prefab_entity_objects[pref_ent.get_content("|")] = pref_ent
                        #self.prefab_entity_objects[pref_ent.name + " " + pref_ent.identifier] = pref_ent
                        
                self.progressbar_update(True)
        
        # Parse all building facade prefab libraries
        if self.parse_building:
            self.update_status_bar("Parsing Building Facade Prefab Libraries")
            self.progressbar_setmax(len(building_facade_prefab_libraries_files))

            for bf_lib in building_facade_prefab_libraries_files:
                self.progressbar_update()
                bfp = adp.d_building_facade_prefab_lib(bf_lib)
                self.building_facade_prefab_libraries_objects[bfp.identifier] = bfp
                self.building_facade_prefab_libraries_objects[bfp.get_content("|")] = bfp
            self.progressbar_update(True)

            self.update_status_bar("Parsing Building Facade Prefab Libraries Objects")

            for bf_obj in self.building_facade_prefab_libraries_objects.values():
                for item in bf_obj.lib_items_objects:
                    self.building_facade_prefab_item_objects[item.identifier] = item
                    self.building_facade_prefab_item_objects[item.get_content("|")] = item
                    #self.building_facade_prefab_item_objects[item.name + " " + item.identifier] = item
                    
            self.progressbar_update(True)
        
        # Parse all Layer Brushes (collection systems)
        if self.parse_layerbrush:
            self.update_status_bar("Parsing Layer Brushes")
            self.progressbar_setmax(len(layer_brushes_files))

            for file in layer_brushes_files:
                self.progressbar_update()
                layer_brushes = adp.d_layer_brushes(file)
                self.layer_brushes_objects[layer_brushes.identifier] = layer_brushes
                self.layer_brushes_objects[layer_brushes.get_content("|")] = layer_brushes
            self.progressbar_update(True)

        # Parse all Brush Libraries (collection systems)
        if self.parse_brushlib:
            self.update_status_bar("Parsing Brush Libraries")
            self.progressbar_setmax(len(brush_libraries_files))

            for file in brush_libraries_files:
                self.progressbar_update()
                brush_lib = adp.d_brush_lib(file)
                self.brush_libraries_objects[brush_lib.identifier] = brush_lib
                self.brush_libraries_objects[brush_lib.get_content("|")] = brush_lib

            self.update_status_bar("Parsing Brush Objects")

            for brush_obj in self.brush_libraries_objects.values():
                for item in brush_obj.items:
                    self.brush_item_objects[item.identifier] = item
                    self.brush_item_objects[item.get_content("|")] = item
                    #self.brush_item_objects[item.name + " " + item.identifier] = item
            self.progressbar_update(True)
        
        # Parse all Collection Resources (collection systems)
        if self.parse_vegecol:
            self.update_status_bar("Collection Resources")

            collection_resource_lib_obj = adp.d_collection_resources_lib(data_path+collection_resource_library_file) # there's only one Collection Resource file
            self.collection_resource_library_objects[collection_resource_lib_obj.identifier] = collection_resource_lib_obj

            for col_res_obj in self.collection_resource_library_objects.values():
                for item in col_res_obj.items:
                    self.collection_resource_item_objects[item.identifier] = item
                    self.collection_resource_item_objects[item.get_content("|")] = item
                    #self.collection_resource_item_objects[item.name + " " + item.identifier] = item
            self.progressbar_update(True)

        # Parse all generic libraries
        # We don't parse generic libs items for now # oh yes we do now
        if self.use_old_parsing_method:
            if self.parse_generic:
                self.update_status_bar("Parsing Generic Libraries")
                self.progressbar_setmax(len(generic_libraries_files))

                for gen_lib in generic_libraries_files:
                    self.progressbar_update()
                    gen = adp.d_generic_lib(gen_lib)
                    self.generic_libraries_objects[gen.identifier] = gen
                    self.generic_libraries_objects[gen.get_content("|")] = gen
                self.progressbar_update(True)
                
                for lib_obj in self.generic_libraries_objects.values():
                    for item in lib_obj.lib_items_objects:
                        self.generic_item_objects[item.identifier] = item
                        self.generic_item_objects[item.get_content("|")] = item
                        #self.generic_item_objects[item.name + " " + item.identifier] = item
                        for collection_item in item.collection_items:
                            self.collection_item_objects[collection_item.identifier] = collection_item
                            self.collection_item_objects[collection_item.get_content("|")] = collection_item
                self.progressbar_update(True)

        # Parse all Particle Emitters
        if self.use_old_parsing_method:
            if self.parse_emitter:
                self.update_status_bar("Parsing Particle Emitterz")
                self.progressbar_setmax(len(particle_emi_libraries_files))

                for emi_lib in particle_emi_libraries_files:
                    self.progressbar_update()
                    emi = adp.d_particle_emi_lib(emi_lib)
                    self.particle_emi_libraries_objects[emi.identifier] = emi

                self.update_status_bar("Parsing Particle Emitterz Objects")

                for emi_obj in self.particle_emi_libraries_objects.values():
                    for item in emi_obj.lib_items_objects:
                        self.particle_emi_item_objects[item.identifier] = item
                self.progressbar_update(True)

        # Parse all Particle Systems
        if self.use_old_parsing_method:
            if self.parse_system:
                self.update_status_bar("Parsing Particle Systemz")
                self.progressbar_setmax(len(particle_sys_libraries_files))

                for sys_lib in particle_sys_libraries_files:
                    self.progressbar_update()
                    sys = adp.d_particle_sys_lib(sys_lib)
                    self.particle_sys_libraries_objects[sys.identifier] = sys

                self.update_status_bar("Parsing Particle Systemz Objects")

                for sys_obj in self.particle_sys_libraries_objects.values():
                    for item in sys_obj.lib_items_objects:
                        self.particle_sys_item_objects[item.identifier] = item
                self.progressbar_update(True)

        # Parse all Character Parts
        if self.parse_part:
            self.update_status_bar("Parsing Character Parts")
            self.progressbar_setmax(len(character_par_libraries_files))

            for par_lib in character_par_libraries_files:
                self.progressbar_update()
                par = adp.d_character_par_lib(par_lib)
                self.character_par_libraries_objects[par.identifier] = par

            self.update_status_bar("Parsing Character Parts Objects")

            for par_obj in self.character_par_libraries_objects.values():
                for item in par_obj.lib_items_objects:
                    self.character_par_item_objects[item.identifier] = item
            self.progressbar_update(True)

        # Parse all Character Models
        if self.parse_model:
            self.update_status_bar("Parsing Character Models")
            self.progressbar_setmax(len(character_mod_libraries_files))

            for mod_lib in character_mod_libraries_files:
                self.progressbar_update()
                mod = adp.d_character_mod_lib(mod_lib)
                self.character_mod_libraries_objects[mod.identifier] = mod

            self.update_status_bar("Parsing Character Models Objects")

            for mod_obj in self.character_mod_libraries_objects.values():
                for item in mod_obj.lib_items_objects:
                    self.character_mod_item_objects[item.identifier] = item
            self.progressbar_update(True)

        # Parse all Character Collections
        if self.parse_collection:
            self.update_status_bar("Parsing Character Collections")
            self.progressbar_setmax(len(character_col_libraries_files))

            for col_lib in character_col_libraries_files:
                self.progressbar_update()
                col = adp.d_character_col_lib(col_lib)
                self.character_col_libraries_objects[col.identifier] = col

            self.update_status_bar("Parsing Character Collections Objects")

            for col_obj in self.character_col_libraries_objects.values():
                for item in col_obj.lib_items_objects:
                    self.character_col_item_objects[item.identifier] = item
            self.progressbar_update(True)

        # Parse all Markup
        if self.use_old_parsing_method:
            if self.parse_markup:
                counter = progressbar_stride
                self.update_status_bar("Parsing Markup Files")
                self.progressbar_setmax(len(markup_files) / progressbar_stride)

                for markup_obj in markup_files:
                    counter += 1
                    if counter > progressbar_stride:
                        self.progressbar_update()
                        counter = 0
                    mark = adp.d_markup(markup_obj)
                    self.markup_objects[mark.identifier] = mark
                self.progressbar_update(True)

        # Parse all geometries
        if self.use_old_parsing_method:
            if self.parse_geometry:
                counter = progressbar_stride
                self.update_status_bar("Parsing Geometry Files")
                self.progressbar_setmax(len(geometry_files) / progressbar_stride)

                for geo in geometry_files:
                    counter += 1
                    if counter > progressbar_stride:
                        self.progressbar_update()
                        counter = 0
                    geom = adp.d_geometry(geo)
                    if geom.identifier is not None:
                        self.geometry_objects[geom.identifier] = geom
                        self.geometry_objects[geom.get_content("|")] = geom
                        #self.geometry_objects[geom.default_id_int] = geom # the more, the merrier
                        #self.geometry_objects[adp.convert_to_path_type(geom.filename,2)] = geom # this is to be able to find the geometries that have no unique ID, like the lofts (.lft/.xlf), especially in generic libraries
                        for i in geom.models:
                            if i is not None:
                                self.geometry_objects[i] = geom
                self.progressbar_update(True)
        
        # Parse all materials
        if self.use_old_parsing_method:
            if self.parse_material:
                counter = progressbar_stride
                self.update_status_bar("Parsing Material Files")
                self.progressbar_setmax(len(material_files) / progressbar_stride)

                for material_obj in material_files:
                    counter += 1
                    if counter > progressbar_stride:
                        self.progressbar_update()
                        counter = 0
                    mate = adp.d_material(material_obj)
                    category = ""
                    if mate.category is not None:
                        category = " " + mate.category
                    self.material_objects[mate.identifier] = mate
                    #self.material_objects[mate.name + " " + mate.identifier + str(category)] = mate
                    self.material_objects[mate.get_content("|")] = mate
                self.progressbar_update(True)
            

        # Parse all textures
        if self.use_old_parsing_method:
            profiles_obj = adp.d_texture_profiles()
            if self.parse_texture:
                self.update_status_bar("Parsing Textures")
                self.progressbar_setmax(len(texture_files))

                for texture_obj in texture_files:
                    self.progressbar_update()
                    text = adp.d_texture(texture_obj, profiles_obj)
                    self.texture_objects[text.identifier] = text
                    #self.texture_objects[text.name + " " + text.identifier] = text
                    self.texture_objects[text.get_content("|")] = text

            self.progressbar_update(True)
        
        # Parse all binks, well not really parsing, but whatever
        if self.parse_texture:
            self.update_status_bar("Looking for Binks")
            self.progressbar_setmax(len(bink_files))
            
            for bink in bink_files:
                self.progressbar_update()
                bink_obj = adp.d_bink(bink)
                self.bink_objects[bink_obj.identifier] = bink_obj

        self.progressbar_update(True)
        
        # new code to support sqlite db
        if not self.use_old_parsing_method:
            ddv = self
            
            db = adp.d_sqlite_db()
        
            conn = db.connect_to_db()
            cursor = conn.cursor()
            db.create_tables(cursor)
            
            self.update_status_bar("Getting Timestamps From Database")
            timestamps = db.get_timestamps(cursor)
            
            counter = progressbar_stride
            all_files = set()
            
            if self.parse_worldlayer: # world layers need custom code because how they are constructed
                self.update_status_bar("Updating World Layers Database")
                all_files = all_files.union(self.world_object.layer_files)
                self.progressbar_setmax(len(self.world_object.layer_files) / progressbar_stride)
                
                # need to get the city blocks world layers first to get self.city_blocks_image
                city_block_layers = set()
                for world_layer_file in self.world_object.layer_files:
                    if "city_block_shapes" in world_layer_file:
                        city_block_layers.add(world_layer_file)
                self.draw_city_blocks(city_block_layers)

                status = None
                files_to_delete = set() #db.get_orphaned_files(self.world_object.layer_files, timestamps) #set()
                files_to_insert = set()

                for file in self.world_object.layer_files:

                    counter += 1
                    if counter > progressbar_stride:
                        self.progressbar_update()
                        counter = 0

                    status = db.check_timestamp(file, timestamps)
                    if status == True:
                        continue
                    if status == False:
                        files_to_delete.add((file,))
                    
                    #custom code for world layers
                    object = adp.d_world_layer(file, self.world_object.world_size, self.game_map_zones_image, self.zones_dict)                    
                    object.world_layer_type = self.world_object.special_layers.get(object.name.lower())
                    for entity in object.subitems:
                        entity.world_layer_type = object.world_layer_type
                    #end custom code for world layers
                    
                    for subitem in object.subitems:
                        subitem._content = subitem.get_content("|")

                    object._content = object.get_content("|")
                    p = cPickle.dumps(object, cPickle.HIGHEST_PROTOCOL)
                    files_to_insert.add((file,getmtime(file),sqlite3.Binary(p),object.type))
                    
                if files_to_delete:
                    db.delete_files(cursor, files_to_delete)
                if files_to_insert:
                    db.insert_files(cursor, files_to_insert)
                
                # get objects from db here
                self.update_status_bar("Getting World Layers From Database")
                db.get_objects_from_db(cursor, "World Layer", self.world_layer_objects, self.entity_objects, None, ddv)
                
                # other chunk of custom code to fill cells
                self.update_status_bar("Updating Cells")
                for id, entity in self.entity_objects.iteritems():
                    cb = self.city_block_cell_objects.get(entity.get_city_block_color(self.city_blocks_image))
                    if cb is None:
                        continue
                    cb.entities.add(entity)
                    cb.add_dependency(entity.identifier)
                self.update_status_bar("Updating City Blocks")
                for id, object in self.world_layer_objects.iteritems():
                    self.world_object.layer_objects.add(object)
                self.world_object.fill_cells()
                # end custom code
                
                self.progressbar_update(True)
                
                # parse spline layers
                self.update_status_bar("Updating Spline Database")
                all_files = all_files.union(spline_layer_files)
                self.progressbar_setmax(len(spline_layer_files) / progressbar_stride)
                
                db.update_files_in_db(cursor, spline_layer_files, timestamps, adp.d_spline_layer, progressbar_stride, counter, ddv)
                self.update_status_bar("Getting Splines From Database")
                db.get_objects_from_db(cursor, "Spline Layer", self.spline_layer_objects, self.spline_objects, self.range_objects, ddv)
                self.progressbar_update(True)                
                self.update_status_bar("Reticulating Splines")
                for id, range in self.range_objects.iteritems():                    
                    cb = self.city_block_cell_objects.get(range.get_city_block_color(self.city_blocks_image, self.world_object.world_size))
                    if cb is None:
                        continue
                    cb.entities.add(range)
                    cb.add_dependency(range.identifier)
            
            if self.parse_generic:
                self.update_status_bar("Updating Generic Database")
                all_files = all_files.union(generic_libraries_files)
                self.progressbar_setmax(len(generic_libraries_files) / progressbar_stride)
                db.update_files_in_db(cursor, generic_libraries_files, timestamps, adp.d_generic_lib, progressbar_stride, counter, ddv)
                self.update_status_bar("Getting Generics From Database")
                db.get_objects_from_db(cursor, "Generic Library", self.generic_libraries_objects, self.generic_item_objects, self.collection_item_objects, ddv)
                self.progressbar_update(True)
            
            if self.parse_prefab:
                self.update_status_bar("Updating Prefab Database")
                all_files = all_files.union(prefab_libraries_files)
                self.progressbar_setmax(len(prefab_libraries_files) / progressbar_stride)
                db.update_files_in_db(cursor, prefab_libraries_files, timestamps, adp.d_prefab_lib, progressbar_stride, counter, ddv)
                self.update_status_bar("Getting Prefabs From Database")
                db.get_objects_from_db(cursor, "Prefab Library", self.prefab_libraries_objects, self.prefab_item_objects, self.prefab_entity_objects, ddv)
                self.progressbar_update(True)
                
            if self.parse_emitter:
                self.update_status_bar("Updating Particle Emitters Database")
                all_files = all_files.union(particle_emi_libraries_files)
                self.progressbar_setmax(len(particle_emi_libraries_files) / progressbar_stride)
                db.update_files_in_db(cursor, particle_emi_libraries_files, timestamps, adp.d_particle_emi_lib, progressbar_stride, counter, ddv)
                self.update_status_bar("Getting Particle Emitters From Database")
                db.get_objects_from_db(cursor, "Particle Emitter Library", self.particle_emi_libraries_objects, self.particle_emi_item_objects, None, ddv)
                self.progressbar_update(True)
                
            if self.parse_system:
                self.update_status_bar("Updating Particle Systems Database")
                all_files = all_files.union(particle_sys_libraries_files)
                self.progressbar_setmax(len(particle_sys_libraries_files) / progressbar_stride)
                db.update_files_in_db(cursor, particle_sys_libraries_files, timestamps, adp.d_particle_sys_lib, progressbar_stride, counter, ddv)
                self.update_status_bar("Getting Particle Systems From Database")
                db.get_objects_from_db(cursor, "Particle System Library", self.particle_sys_libraries_objects, self.particle_sys_item_objects, None, ddv)
                self.progressbar_update(True)
            
            if self.parse_archetype:
                self.update_status_bar("Updating Archetype Database")
                all_files = all_files.union(archetype_libraries_files)
                self.progressbar_setmax(len(archetype_libraries_files) / progressbar_stride)
                db.update_files_in_db(cursor, archetype_libraries_files, timestamps, adp.d_archetype_lib, progressbar_stride, counter, ddv) 
                self.update_status_bar("Getting Archetypes From Database")
                db.get_objects_from_db(cursor, "Archetype Library", self.archetype_libraries_objects, self.archetype_item_objects, None, ddv)
                self.progressbar_update(True)
            
            if self.parse_proxy:
                self.update_status_bar("Updating Proxy Database")
                all_files = all_files.union(proxy_files)
                self.progressbar_setmax(len(proxy_files) / progressbar_stride)
                db.update_files_in_db(cursor, proxy_files, timestamps, adp.d_proxy, progressbar_stride, counter, ddv) 
                self.update_status_bar("Getting Proxies From Database")
                db.get_objects_from_db(cursor, "Proxy", self.proxy_objects, None, None, ddv)
                self.progressbar_update(True)
                
            if self.parse_markup:
                self.update_status_bar("Updating Markup Database")
                all_files = all_files.union(markup_files)
                self.progressbar_setmax(len(markup_files) / progressbar_stride)
                db.update_files_in_db(cursor, markup_files, timestamps, adp.d_markup, progressbar_stride, counter, ddv)
                self.update_status_bar("Getting Markups From Database")
                db.get_objects_from_db(cursor, "Markup", self.markup_objects, None, None, ddv)
                self.progressbar_update(True)
                
            if self.parse_sequence:
                self.update_status_bar("Updating Sequence Database")
                all_files = all_files.union(sequence_files)
                self.progressbar_setmax(len(sequence_files) / progressbar_stride)
                db.update_files_in_db(cursor, sequence_files, timestamps, adp.d_sequence, progressbar_stride, counter, ddv)
                self.update_status_bar("Getting Sequences From Database")
                db.get_objects_from_db(cursor, "Sequence", self.sequence_objects, None, None, ddv)
                self.progressbar_update(True)
            
            if self.parse_geometry:
                self.update_status_bar("Updating Geometry Database")
                all_files = all_files.union(geometry_files)
                self.progressbar_setmax(len(geometry_files) / progressbar_stride)
                db.update_files_in_db(cursor, geometry_files, timestamps, adp.d_geometry, progressbar_stride, counter, ddv)
                self.update_status_bar("Getting Geometries From Database")
                db.get_objects_from_db(cursor, "Geometry", self.geometry_objects, None, None, ddv)
                self.progressbar_update(True)
            
            if self.parse_material:
                self.update_status_bar("Updating Material Database")
                all_files = all_files.union(material_files)
                self.progressbar_setmax(len(material_files) / progressbar_stride)
                db.update_files_in_db(cursor, material_files, timestamps, adp.d_material, progressbar_stride, counter, ddv)
                self.update_status_bar("Getting Materials From Database")
                db.get_objects_from_db(cursor, "Material", self.material_objects, None, None, ddv)
                self.progressbar_update(True)
                
            if self.parse_texture:
                self.texture_profiles = adp.d_texture_profiles()
                self.update_status_bar("Updating Texture Database")
                all_files = all_files.union(texture_files)
                self.progressbar_setmax(len(texture_files) / progressbar_stride)
                db.update_files_in_db(cursor, texture_files, timestamps, adp.d_texture, progressbar_stride, counter, ddv)
                self.update_status_bar("Getting Textures From Database")
                db.get_objects_from_db(cursor, "Texture", self.texture_objects, None, None, ddv)            
                self.progressbar_update(True)
            
            self.update_status_bar("Deleting orphans")

            orphans = db.get_orphaned_files(all_files, timestamps)
            if orphans:
                db.delete_files(cursor, orphans)
            
            db.disconnect_from_db(conn)
            
            del db
          
    def clear_genealogy(self):
        self.update_status_bar("Clear Genealogy")

        #World Object
        if self.world_object is not None:
            self.world_object._parents = {} #Now a dict
            self.world_object._children = {}

        stuff_to_parse = [
            self.world_layer_objects,
            self.world_cell_objects,
            self.entity_objects,
            self.spline_layer_objects,
            self.spline_objects,
            self.range_objects,
            self.proxy_objects,
            self.archetype_libraries_objects,
            self.archetype_item_objects,
            self.prefab_libraries_objects,
            self.prefab_item_objects,
            self.prefab_entity_objects,
            self.building_facade_prefab_libraries_objects,
            self.building_facade_prefab_item_objects,
            self.layer_brushes_objects,
            self.brush_libraries_objects,
            self.brush_item_objects,
            self.collection_resource_library_objects,
            self.collection_resource_item_objects,
            self.generic_libraries_objects,
            self.generic_item_objects,
            self.collection_item_objects,
            self.particle_emi_libraries_objects,
            self.particle_emi_item_objects,
            self.particle_sys_libraries_objects,
            self.particle_sys_item_objects,
            self.character_par_libraries_objects,
            self.character_par_item_objects,
            self.character_mod_libraries_objects,
            self.character_mod_item_objects,
            self.character_col_libraries_objects,
            self.character_col_item_objects,
            self.markup_objects,
            self.geometry_objects,
            self.material_objects,
            self.sequence_objects,
            ]

        for i in stuff_to_parse:
            for j in i.values():
                j._parents = {} #Now a dict
                j._children = {}

    def parse_genealogy(self):
        self.update_status_bar("Building Genealogy -- World Object")
        self.progressbar_setmax(33)

        #World Object
        if self.world_object is not None:
            for i in self.world_object.layer_objects:
                i._parents[self.world_object] = 0
                self.world_object._children[i] = 0
        self.progressbar_update()

        #World Layers
        self.update_status_bar("Building Genealogy -- World Layers")
        for i in self.world_layer_objects.values():
            for j in i.entities: #entities are already d_entities
                j._parents[i] = 0
                i._children[j] = 0
        self.progressbar_update()
        
        #World Cells
        self.update_status_bar("Building Genealogy -- World Cells")
        for i in self.world_cell_objects.values():
            for j in i.entities: #entities are already d_entities
                j._parents[i] = 0
                i._children[j] = 0
        self.progressbar_update()
        
        #City Block Cells
        self.update_status_bar("Building Genealogy -- World Cells")
        for i in self.city_block_cell_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None and meat is not i: #Avoid adding yourself into your own genealoty :O
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()

        #Entities
        self.update_status_bar("Building Genealogy -- Entities")
        for i in self.entity_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()
        
        #Spline Layers
        self.update_status_bar("Building Genealogy -- Spline Layers")
        for i in self.spline_layer_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None and meat is not i: #Avoid adding yourself into your own genealoty :O
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()
        
        #Splines
        self.update_status_bar("Building Genealogy -- Splines")
        for i in self.spline_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None and meat is not i: #Avoid adding yourself into your own genealoty :O
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()
        
        #Ranges
        self.update_status_bar("Building Genealogy -- Ranges")
        for i in self.range_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None and meat is not i: #Avoid adding yourself into your own genealoty :O
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()

        #Proxy
        self.update_status_bar("Building Genealogy -- Proxies")
        for i in self.proxy_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()

        #Arch Lib
        self.update_status_bar("Building Genealogy -- Archetypes")
        for i in self.archetype_libraries_objects.values():
            for j in i.lib_items_objects:
                j._parents[i] = 0
                i._children[j] = 0
        self.progressbar_update()

        #Arch Obj
        for i in self.archetype_item_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()

        #Prefab Lib
        self.update_status_bar("Building Genealogy -- Prefabs")
        for i in self.prefab_libraries_objects.values():
            for j in i.lib_items_objects:
                j._parents[i] = 0
                i._children[j] = 0
        self.progressbar_update()

        #Prefab Item
        for i in self.prefab_item_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()
        
        #Prefab Entity
        for i in self.prefab_entity_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()

        #Building Facade Prefab Lib
        self.update_status_bar("Building Genealogy -- Facades")
        for i in self.building_facade_prefab_libraries_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None and meat is not i: #Avoid adding yourself into your own genealoty :O
                    if meat.type != "Building Facade Prefab Library":
                        meat._parents[i] = 0
                        i._children[meat] = 0
        self.progressbar_update()
        
        #Building Facade Prefab Item
        for i in self.building_facade_prefab_item_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()
        
        #Layer brushes
        self.update_status_bar("Building Genealogy -- Brushes")
        for i in self.layer_brushes_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None and meat is not i: #Avoid adding yourself into your own genealoty :O
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()
        
        #Brush Libraries
        for i in self.brush_libraries_objects.values():
            for j in i.items:
                j._parents[i] = 0
                i._children[j] = 0
        self.progressbar_update()
        
        #Brush Items
        for i in self.brush_item_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None and meat is not i: #Avoid adding yourself into your own genealoty :O
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()
        
        #Collection Resources Libraries
        self.update_status_bar("Building Genealogy -- Collections")
        for i in self.collection_resource_library_objects.values():
            for j in i.items:
                j._parents[i] = 0
                i._children[j] = 0
        self.progressbar_update()
        
        #Collection Resources Items
        for i in self.collection_resource_item_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None and meat is not i: #Avoid adding yourself into your own genealoty :O
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()
        
        #Generic Lib
        self.update_status_bar("Building Genealogy -- Generic Libs")
        for i in self.generic_libraries_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()
        
        #Generic Obj
        for i in self.generic_item_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()
        
        #Collection Item
        for i in self.collection_item_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()

        #Particle Emitter Lib
        self.update_status_bar("Building Genealogy -- Particles")
        for i in self.particle_emi_libraries_objects.values():
            for j in i.lib_items_objects:
                j._parents[i] = 0
                i._children[j] = 0
        self.progressbar_update()

        #Particle Emitter Obj
        for i in self.particle_emi_item_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()

        #Particle System Lib
        for i in self.particle_sys_libraries_objects.values():
            for j in i.lib_items_objects:
                j._parents[i] = 0
                i._children[j] = 0
        self.progressbar_update()

        #Particle System Obj
        for i in self.particle_sys_item_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()

        #Character Parts Lib
        self.update_status_bar("Building Genealogy -- Characters")
        for i in self.character_par_libraries_objects.values():
            for j in i.lib_items_objects:
                j._parents[i] = 0
                i._children[j] = 0
        self.progressbar_update()

        #Character Parts Obj
        for i in self.character_par_item_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()

        #Character Model Lib
        for i in self.character_mod_libraries_objects.values():
            for j in i.lib_items_objects:
                j._parents[i] = 0
                i._children[j] = 0
        self.progressbar_update()

        #Character Model Obj
        for i in self.character_mod_item_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()

        #Character Collection Lib
        for i in self.character_col_libraries_objects.values():
            for j in i.lib_items_objects:
                j._parents[i] = 0
                i._children[j] = 0
        self.progressbar_update()

        #Character Collection Obj
        for i in self.character_col_item_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()

        #Markup Obj
        self.update_status_bar("Building Genealogy -- Markups")
        for i in self.markup_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()
        
        #Sequence Obj
        self.update_status_bar("Building Genealogy -- Sequences")
        for i in self.sequence_objects.values():
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update()

        #Geometry Obj      
        self.update_status_bar("Building Genealogy -- Geometries")
        unique_geometries = set()
        
        for i in self.geometry_objects.values():
            unique_geometries.add(i)
        
        for i in unique_geometries:
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
            self.refresh_ui() #To avoid not responding
        self.progressbar_update()
        unique_geometries = set()


        #Material Obj
        self.update_status_bar("Building Genealogy -- Materials")
        unique_materials = set()
        
        for i in self.material_objects.values():
            unique_materials.add(i)
        
        for i in unique_materials:
            for j in i.dependencies:
                meat = self.find_something(j)
                if meat is not None:
                    meat._parents[i] = 0
                    i._children[meat] = 0
        self.progressbar_update(True) #Maxout
        self.progressbar_reset(True)

    def get_immediate_subdirectories(self, a_dir):
        return [name for name in listdir(a_dir)
                if isdir(join(a_dir, name))]

    def get_latest_zip_file(self, location):
        sub_directories = self.get_immediate_subdirectories(location)
        versions = list()
        for version_directory in sub_directories:
            versions.append(int(float(version_directory)))
        sorted_versions = sorted(versions, reverse=True)
        for current_version in sorted_versions:
            current_location = join(location, str(current_version), "data-orbis")
            if not exists(current_location):
                continue
            random_directory = self.get_immediate_subdirectories(current_location)[0]
            current_location = join(current_location, random_directory, "build-world")
            log_file = join(current_location, "logs.zip")
            if exists(log_file):
                return log_file

    def get_xml_from_log_file(self, log_file):
        xml_streams = list()
        current_zip = zipfile.ZipFile(log_file)
        files_in_zip = current_zip.namelist()
        for current_file in files_in_zip:
            if r'streamoptimizer/orbis/london/00_current_cache_by_byte_impact' in current_file.lower() and ".xml" in current_file.lower():
                f = current_zip.open(current_file)
                contents = f.read()
                xml_streams.append(contents)
                f.close()
        return xml_streams

    @QtCore.Slot()
    def on_pushButton_streamoptimizer_clicked(self):
        location = r"\\ubisoft.org\projects\Orwell\TOR\BuildSystem\Operarius\Production\dashboard\logs\orwell-game"
        self.update_status_bar("Getting latest WLU data from the NAS.")
        log_file = self.get_latest_zip_file(location)
        self.update_status_bar("Parsing WLU data.")
        xml_streams = self.get_xml_from_log_file(log_file)

        for stream in xml_streams:
            root = ET.fromstring(stream)
            category = root.get('category')
            if category is None:
                category = root.get('Name')
            if category != "Near":
                continue

            self.launch_stream_optimizer(stream)

    @QtCore.Slot()
    def on_pushButton_refresh_clicked(self):
        self.refresh_objects()
    
    def refresh_objects(self):        
        self.init_ui()
        self.clear_object_dictionaries()
        
        gc.collect()
        
            # def clicked_refresh(self):
        #adp.clear_tree()
        # adp.d_object.CLEAR_TREE()

        self.ui_data.clear()

        # if self.parse_world:
        del self.world_object
        self.world_object = None #Wipe the world in order to rescan it

        self.init_DDV()
        
    def clear_object_dictionaries(self):
        for dict in self.object_dictionaries:
            dict.clear()
    
    @QtCore.Slot()
    def on_pushButton_advanced_search_clicked(self):
        self.launch_query()
    
    @QtCore.Slot()
    def on_lineEdit_advanced_search_returnPressed(self):
        self.launch_query()
    
    def launch_query(self):
        self.toggle_waitcursor(True)
        self.update_status_bar("Reticulating Queries")
        search_query = self.UI.lineEdit_advanced_search.text()
        if not search_query:
            search_query = self.UI.comboBox_advanced_search.currentText()
            
        output_dict = {}  
        search_query = search_query.lower() # always search in lower case for maximum hits, could add search options for this
        search_tokens = search_query.split()
        search_type = self.UI.comboBox_advanced_search.currentText()
        
        self.progressbar_setmax(len(self.object_dictionaries))
        for dict in self.object_dictionaries:
            self.progressbar_update()
            for key,object in dict.iteritems():
                
                token_not_in_key = False
                for token in search_tokens:
                    if token not in str(key).lower():
                        token_not_in_key = True
                        
                if token_not_in_key:
                    continue
                        
                if search_type != "All":
                    if search_type != object.type:
                        continue
                output_dict[key] = object
        
        self.fill_advanced_search_list(output_dict)
        self.toggle_waitcursor(False)
        self.progressbar_reset(True)
 
    def fill_advanced_search_list(self, object_dict):
        self.update_status_bar("Sorting Potatoes")
        self.UI.listWidget_advanced_search.clear()
        # if len(object_dict) > 9999: # limit search result count to prevent killing the UI
            # self.UI.label_advanced_search.setText("Too many items found (" + str(len(object_dict)) + ").")
            # return
            
        self.UI.label_advanced_search.setText(str(len(object_dict)))

        ordered_object_dict = OrderedDict(sorted(object_dict.items()))
        
        objects_set = set()
        for name, object in ordered_object_dict.iteritems():
            if object in objects_set: # this is to prevent returning multiple times the same object
                continue
            objects_set.add(object)
            item_text = object.name + " | " + object.type
            item = QtGui.QListWidgetItem(item_text)
            item.setFlags(item.flags())
            item.setData(3, object)
            self.UI.listWidget_advanced_search.addItem(item)

        if self.UI.checkBox_send_red.isChecked():
            self.fill_red_square_from_search(objects_set)
            
        if self.UI.checkBox_send_cb.isChecked():
            self.fill_red_square_cb_from_search(objects_set)
            
        if self.UI.checkBox_send_prop.isChecked():
            self.fill_proparazzi_from_search(objects_set)
            
    def fill_proparazzi_from_search(self, objects_set):
        self.update_status_bar("Sending search results to Proparazzi")
        output_dict = {}
        self.progressbar_reset()
        self.progressbar_setmax(len(objects_set))
        for obj in objects_set:
            self.progressbar_update()
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj, "Entity", "up")
            output_dict[obj] = self.recursive_search_items
        
        self.fill_prop_tree(output_dict)
        
        self.update_status_bar("Search results are now in Proparazzi")
        self.progressbar_reset(True)
        
    def fill_red_square_from_search(self, objects_set):
        
        if self.world_object is None:
            return
        
        self.update_status_bar("Sending search results to Red Square")
        self.toggle_waitcursor(True)
        self.UI.tabWidget.setEnabled(False)
        self.model_topview.clearChildren()
        self.UI.label_count.setText("0 item")
        self.topview_selection = (-1, -1) #Reset cell selection        
        self.topview_mode = 0
        self.UI.pushButton_stats.setChecked(True)
        self.UI.pushButton_city_blocks.setChecked(False)
        self.UI.radioButton_ite.setChecked(True)
        
        parent_objects_dict = {}
        for object in objects_set:
            if object.type == "Entity":
                parent_objects_dict[object] = object
                continue
            self.recursive_search_items = [] # empty the list in case it contains somthing else
            self.recursive_search(object, "Entity", "up")
            for item in self.recursive_search_items:
                parent_objects_dict[item] = object

        # empty the cells first
        for y in self.world_object.grid_range:
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
        
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                for entity_in_cell in cell.entities:
                    
                    object = parent_objects_dict.get(entity_in_cell)
                    
                    if object is None:
                        continue
                    
                    if object in cell.resources:
                        continue
                    cell.resources.append(object)
                                    
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
                
        self.create_image_output(table_to_output, ("search" + "_"))
        self.update_view()        
        self.progressbar_reset(True)
        self.UI.tabWidget.setEnabled(True)
        self.toggle_waitcursor(False)        
        self.update_status_bar("Search results are now in Red Square")
      
    def fill_red_square_cb_from_search(self, objects_set):
        
        if self.world_object is None:
            return
        
        self.update_status_bar("Sending search results to Red Square")
        self.toggle_waitcursor(True)
        self.UI.tabWidget.setEnabled(False)
        self.model_topview.clearChildren()
        self.UI.label_count.setText("0 item")
        self.topview_selection = (-1, -1) #Reset cell selection        
        self.topview_mode = 1
        self.UI.pushButton_stats.setChecked(False)
        self.UI.pushButton_city_blocks.setChecked(True)
        self.UI.radioButton_ite.setChecked(True)
        
        parent_objects_dict = {}
        for object in objects_set:
            if object.type == "Entity":
                parent_objects_dict[object] = object
                continue
            self.recursive_search_items = [] # empty the list in case it contains somthing else
            self.recursive_search(object, "Entity", "up")
            for item in self.recursive_search_items:
                parent_objects_dict[item] = object
                
        blocks_set = set()        
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)

        for block in blocks_set:
            block.resources = set()
            self.progressbar_update()
            for entity_in_cell in block.entities:                
                object = parent_objects_dict.get(entity_in_cell)
                if object is None:
                    continue                        
                block.resources.add(object)

        self.set_city_block_cell_colors(blocks_set)
        self.draw_city_blocks_heatmap(blocks_set)        
        self.update_view()        
        self.progressbar_reset(True)
        self.UI.tabWidget.setEnabled(True)
        self.toggle_waitcursor(False)        
        self.update_status_bar("Search results are now in Red Square")
    
    @QtCore.Slot()
    def on_listWidget_advanced_search_itemSelectionChanged(self):
        current_row = self.UI.listWidget_advanced_search.currentRow()
        current_item = self.UI.listWidget_advanced_search.item(current_row)
        self.current_object = current_item.data(3)
        self.set_current_object()

    #Try to return whatever
    def find_something(self, something):
        for d in self.object_dictionaries:
            ret = d.get(something)
            if ret:
                return ret

        try:
            hex_something = something
            if len(something) > 18:
                hex_something = something[16:34] #Keep only Hex part
            return self.geometry_objects[hex_something]
            #for i in self.geometry_objects.keys():
            #    if i in something:
            #        return self.geometry_objects[i]
        except:
            pass

        for d in (self.geometry_objects, self.material_objects, self.texture_objects, self.markup_objects, self.sequence_objects):
            ret = d.get(something)
            if ret:
                return ret

        try:
            return self.markup_objects[something]
        except:
            pass

    #Lightweight version of fill_parents
    def fill_parents_light(self, id):
        meat = self.find_something(id)
        if meat is not None:
            self.ui_data.feed_me("parent", meat._parents.keys())
                    
    def get_current_object(self, search_string):
        search_string = search_string.replace((data_path+"\\"), "")
        search_string = search_string.lower()
        search_string = str(search_string)
        for d in self.object_dictionaries:
            for obj in d.values():
                if search_string in str(obj.identifier).lower():
                    return obj
                if search_string in str(obj.filename).lower():
                    return obj
                if search_string in str(obj.name).lower():
                    return obj
                if obj.special_info is not None:
                    if search_string in str(obj.special_info).lower():
                        return obj
        return adp.bad_object(search_string)

    def update_current_file(self, str_mdata):
        str_mdata = str_mdata.replace(".xbt",".png")
        str_mdata = str_mdata.replace(".xbg",".xml")
        str_mdata = str_mdata.replace(".glm",".xml")
        str_mdata = str_mdata.replace(".hkr",".xml")
        str_mdata = str_mdata.replace(".hkx",".xml")
        str_mdata = str_mdata.replace(".gamex",".xml")
        str_mdata = str_mdata.replace(".lft",".xml")
        str_mdata = str_mdata.replace(".xlf",".xml")
        str_mdata = str_mdata.replace(".material.bin",".material.xml")
        
        self.current_object = self.get_current_object(str_mdata)
        
        self.set_current_object()

    def set_current_object(self):
        self.toggle_waitcursor(True)
        self.ui_data.clear()
        self.ui_data.feed_me("current_item", [self.current_object])
        
        ### top view's line edit update, not sure this should go here
        self.UI.lineEdit_ite.setText(str(self.current_object.filename))
        ###
  
        if self.UI.checkBox_children.isChecked():
            self.ui_data.feed_me("child", self.current_object._children.keys())


        if self.UI.checkBox_grandchildren.isChecked():
            grandchildren_list = []
            for i in self.current_object._children.keys():
                for j in i._children.keys():
                    grandchildren_list.append(j)

            self.ui_data.feed_me("grandchild", grandchildren_list)


        self.update_status_bar(self.current_object.type)

        if self.UI.checkBox_parents.isChecked():
            self.fill_parents_light(self.current_object.identifier)
            
        self.refresh_ui()
        
        #self.history.append(str_mdata)
        #self.history.append(self.current_object.identifier)
        self.history.append(self.current_object)
        
        self.fill_current_object_properties()
        
        self.toggle_waitcursor(False)
        
    def fill_current_object_properties(self):
        self.UI.treeWidget_properties.clear()
        content = self.current_object.get_content("|")
        data = content.split("|")
        for d in data:
            if not d:
                continue
            property_value = d.split("=")
            property = property_value[0]
            if property.startswith("_"):
                continue
            value = str(property_value[1])
            base_item = QtGui.QTreeWidgetItem([property, value])
            self.UI.treeWidget_properties.addTopLevelItem(base_item)
            
        self.UI.treeWidget_properties.header().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.UI.treeWidget_properties.header().setStretchLastSection(False)

    def format_coordinate_string(self, cur_obj):
        pull_back = 4
        
        if cur_obj.type == "Entity":
            if cur_obj.entity_type == "Building":
                pull_back = 30
        
        cur_pos_x = float(cur_obj.position[0])
        cur_pos_y = float(cur_obj.position[1]) - pull_back
        cur_pos_z = float(cur_obj.position[2]) + pull_back

        pos_str = str(cur_pos_x) + "," + str(cur_pos_y) + "," + str(cur_pos_z)
        coord_str = '<Parameters WorldName="%s" CameraPos="%s" CameraAngle="-45,0,0" Type="cmd_ReviewScene" />' % (self.world_name, pos_str)
        return coord_str

    def get_tree_selection(self, current_tree):
        sel_indexes = current_tree.selectedIndexes()
        cur_model = current_tree.model()
        return cur_model.GetObjectsList(sel_indexes)

    def dragEnterEvent(self, event):
        current_tree = event.source()

        if current_tree is None:
            event.accept()
            return

        selection = self.get_tree_selection(current_tree)

        if len(selection) == 1:
            cur_obj = selection[0]
            if cur_obj.type == "Entity" or cur_obj.type == "Range":
                coord_str = self.format_coordinate_string(cur_obj)
                event.mimeData().setText(coord_str)
                event.accept()
                return

        filenames = ""
        for obj in selection:
            filenames += str(obj.filename) + "\n"
        filenames = filenames.rstrip()
        event.mimeData().setText(filenames)
        event.accept()
        return
        

        event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        if len(event.mimeData().urls()) > 1:
            self.update_status_bar("Please drag only one file at a time")
            
        else:
            self.UI.statusbar.clear()
            mdata = event.mimeData().urls()[0]
            str_mdata = mdata.toString()
            str_mdata = str_mdata.replace("file:///", "")
            str_mdata = str_mdata.replace("/", "\\")
            str_mdata = str_mdata.lower()
            if "wlu_near.xml" in str_mdata:
                self.launch_stream_optimizer(str_mdata)
                return
            if (data_path in str_mdata and ".xml") or (data_path in str_mdata and ".png") in str_mdata:
                self.update_current_file(str_mdata)
            else:
                message = str_mdata + " does not come from " + data_path + " or is not a valid file (must be .xml or .png)."
                self.update_status_bar(message)
                
    def get_clipboard_data(self):
        clipboard = QtGui.QClipboard()
        mimeData = clipboard.mimeData()
        reformated_mdata = mimeData.text().lower()
        reformated_mdata = reformated_mdata.replace(".xbt",".png")
        reformated_mdata = reformated_mdata.replace(".xbg",".glm")
        self.update_current_file(reformated_mdata)
        
    def send_selected_text_to_clipboard(self):
        selected_strings = ""

        trees = [self.UI.treeView_0,
                 self.UI.treeView_1,
                 self.UI.treeView_2,
                 self.UI.treeView_3,
                 self.UI.treeView_top,
                 self.UI.treeView_prop]

        selection = {}

        for tree in trees:
            current_tree_selection = self.get_tree_selection(tree)
            if current_tree_selection:
                for i in current_tree_selection:
                    selection[i] = 1 #Removes double entries

        for i in selection.keys():
            instance_count = ""
            try:
                instance_count = str(i._entity_instance_count)
            except:
                pass
            special_info = ""
            if i.special_info is not None:
                special_info = i.special_info
            selected_strings += str(i.name) + ", " + str(instance_count) + ", " + str(i.type) + ", " + str(i.filename) + ", " + str(special_info) + "\n"

        for item in self.UI.treeWidget_properties.selectedItems():
            selected_strings += item.text(1)
            
        clipboard = QtGui.QClipboard()
        clipboard.setText(selected_strings)

    def keyPressEvent(self, input):
        print(1)
        if input.key() == QtCore.Qt.Key_V:
            self.get_clipboard_data()
        if input.key() == QtCore.Qt.Key_C:
            self.send_selected_text_to_clipboard()
        # if input.key() == QtCore.Qt.Key_Return or input.key() == QtCore.Qt.Key_Enter:
            # current_text = self.UI.lineEdit.text()
            # self.update_current_file(current_text.lower())
        if input.key() == QtCore.Qt.Key_F5:
            self.refresh_objects()
            
    def clicked_paste(self):
        self.get_clipboard_data()

    def clicked_search(self):
        self.search_dialog.init_sd()
        self.search_dialog.exec_()

    def double_clicked_parent(self, index):
        self._double_clicked_item(index)
        
    def double_clicked_child(self, index):
        self._double_clicked_item(index)
        
    def double_clicked_grandchild(self, index):
        self._double_clicked_item(index)

    def _double_clicked_item(self, index):
        self.current_object = self.ui_data.get_object(index)
        self.set_current_object()

    def clicked_back(self):
        if len(self.history) <= 1:
            return
        #Take out last 2 entries
        previous_obj = self.history.pop(len(self.history) - 1)
        previous_obj = self.history.pop(len(self.history) - 1)
        self.current_object = previous_obj
        self.set_current_object()

    def clicked_clear_jira(self):
        self.jira_ob_issues = []
        self.jira_city_blocks_issues = []
        
    def changed_0(self):
        self._changed_x(0)

    def changed_1(self):
        self._changed_x(1)

    def changed_2(self):
        self._changed_x(2)

    def changed_3(self):
        self._changed_x(3)

    def changed_top(self):
        self._changed_x(4)

    def changed_prop(self):
        self._changed_x(5)

    def _changed_x(self, x):
        """
        Whenever you click on a tree item, deselect everything from every other trees
        :param x: Arbitrary index to the current tree
        """
        if not self.mute_selection:
            self.mute_selection = True

            trees = [self.UI.treeView_0,
                     self.UI.treeView_1,
                     self.UI.treeView_2,
                     self.UI.treeView_3,
                     self.UI.treeView_top,
                     self.UI.treeView_prop]

            for index, tree in enumerate(trees):
                if x != index:
                    tree.clearSelection()

            self.mute_selection = False

    @staticmethod
    def toggle_waitcursor(bwait):
        if bwait:
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        else:
            QtGui.QApplication.restoreOverrideCursor()

    def callback(self, my_type, my_value=None):
        if my_type == 0:
            if my_value is not None:
                self.progressbar_setmax(my_value)
                #self.progressbar_reset()

        if my_type == 1:
            self.progressbar_update(my_value is not None) #Test to max out bar

        if my_type == 2:
            if my_value is not None:
                self.update_status_bar(my_value)
                self.refresh_ui()

    def progressbar_setmax(self, max, second_bar=False):
        if second_bar:
            self.UI.progressBar_2.setMaximum(max)
        else:
            self.UI.progressBar.setMaximum(max)

    def progressbar_update(self, maxout=False):
        if maxout:
            self.UI.progressBar.setValue(self.UI.progressBar.maximum())
            self.UI.progressBar_2.setValue(self.UI.progressBar_2.value() + 1)
            self.progressbar_reset()
        else:
            self.UI.progressBar.setValue(self.UI.progressBar.value() + 1)
        self.refresh_ui()

    def progressbar_reset(self, second_bar=False):
        self.UI.progressBar.reset()
        if second_bar:
            self.UI.progressBar_2.reset()

    def update_status_bar(self, text):
        self.UI.statusbar.showMessage(text)
        self.UI.label_DDV.setText(text)

    def clear_status_bar(self):
        self.UI.statusbar.clearMessage()

    @staticmethod
    def refresh_ui():
        QtCore.QCoreApplication.processEvents()

    def save_settings(self):
        self.settings.setValue('login', self.UI.lineEdit_jira_login.text())
        self.settings.setValue('password', base64.b64encode(self.UI.lineEdit_jira_pwd.text()))
        self.settings.setValue('filter', self.UI.lineEdit_jira_filter.text())
        
    def check_user(self):
        user = getpass.getuser().lower()
        if "low" in user:
            self.quote = " - Helloooooooooooooo Bruce!"
        if "arcand" in user:
            self.quote = " - Bonjour Gilbert !"
        if "emery" in user:
            self.quote = " - Bonjour Oriane ! :)"
        if "masqui" in user:
            self.quote = " - Mais ils m'ont traite de brute Monsieur le commissaire !"
        if "manseau" in user:
            self.quote = " - *FLIPS A TABLE* GET READY TO ROOOOMMMMBAAAAAAAA"
        if "boac" in user:
            self.quote = " - Buna ziua Mihnea. Nu te aud, am o banana la ureche."
        if "ng" in user:
            self.quote = " - Hello Janice! :)"
        if "jennings" in user:
            self.quote = " - Hey Shaun, I fixed it."
        if "schlichting" in user:
            self.quote = " - Bonjour Ophelie ! Tu gagnes le prix du plus vieux bug dans DDV. :)"
        if "visconti" in user:
            self.quote = " - Hello Pina! (:"
        self.setWindowTitle(self.title + self.world_name + self.version + self.quote)

    def fill_comboboxes(self):
        filters_budgeted = [
                    "Building Kit Points",
                    #"Building Kit (numbers)",
                    #"Building Kit (memory)",
                    "Facades Instance Count",
                    "Geometry",
                    ]
        for filter in filters_budgeted:
            self.UI.comboBox_bud.addItem(filter)
    
        filters_devtest = [
                    "Archetype With Animation Component (CB)",
                    "Batched Objects (not a Proxy) (CB)",
                    "Facade Not In Building (CB)",
                    "Geometry With No JIRA (CB)",
                    "Geometry From BVI Used In London",
                    "Group",
                    "Illegal Archetype (not WD3) (CB)",
                    "Illegal Geometry (int, cin, usr)",
                    "Material With Bink (CB)",
                    "Pink Objects (CB)",
                    "Primitive",
                    "Stairs With No IK (CB)",
                    # "separator",
                    # "Archetype With Animation Component",
                    # "Batched Objects (not a Proxy)",
                    # "Facade Not In Building",
                    # "Geometry With No JIRA",
                    # "Illegal Archetype (not WD3)",
                    # "Material With Bink",
                    # "Pink Objects",
                    # "Stairs With No IK",
                    ]
        for filter in filters_devtest:
            if filter == "separator":
                self.UI.comboBox_devtest.insertSeparator(99)
                continue
            self.UI.comboBox_devtest.addItem(filter)
            
        filters_special = [
                     #"Batched Objects (not a Proxy)",
                     "Breakable",
                     "Breakable Multistate",
                     "Breakable Multistate (entities)",
                     "Building Generating Lowres Using Interior Kit",
                     "Building Not On Building Layer",
                     "Building Not Using Roof_Random",
                     "Building Surface Lower Than n m2",
                     "Building Volume Lower Than n m3",
                     "Building Should Not Generate LLOD",
                     "Building Should Be In FarAway",
                     "Building Should Be In Far",
                     "Building Should Be In Near",
                     "Bad Practice Buildings",
                     "City Life Object",
                     "Compiled Size Per Cell",
                     "Entity By Number Of Class Instances",
                     "Entity Not Batched",
                     "Entity UnderGround",
                     "Entity In Z",
                     "Entity On Interior",
                     "Entity On HMA",
                     "Entity On LMA",
                     "Entity On Mission",
                     "Entity On Progression",
                     "Entity On Sas",
                     # "Entity On Tower Hamlets East",
                     "External References",
                     #"Facade Not In Building",
                     "Gameplay Ingredients",
                     "Geometry By JIRA Filter",
                     "Geometry By Size",
                     "Geometry By Kill Distance",
                     "Geometry In City Block",
                     "Geometry With No JIRA In PropsCatalogs",
                     "Geometry In Unbatched Entity",
                     "Geometry With Uncertain High/Medium (64) LOD Distances",
                     "Geometry With Uncertain Near/Far (256) LOD Distances",
                     "Geometry With Uncertain Medium/Low (383) LOD Distances",
                     "Geometry With Uncertain Far/FarAway (1024) LOD Distances",
                     #"Geometry With No JIRA",
                     "Illegal Geometry",
                     "Insufficient LODs",
                     "Interior Layer Errors",
                     "Interior Object On Normal Layer",
                     "Object With n Instance In The World",
                     "Occluder",
                     #"Pink Objects",
                     "Plaza",
                     "Plaza By Kill Distance",
                     "Plaza Not Using Roof_Random",
                     "Proxy In Legal Folder Not Tracked",
                     # "Primitive",
                     "Primitive Montreal",
                     #"Stairs With No IK",
                     "Spawning Cost",
                     "Vehicle Enticers",
                    ]
        for filter in filters_special:
            self.UI.comboBox_pre.addItem(filter)
            
        filters_type = [
                    "Entity",
                    "Proxy",
                    "Archetype",
                    "Prefab",
                    "Building Facade Prefab Library",
                    "Particle Emitter",
                    "Particle System",
                    "Markup",
                    "Geometry",
                    "Material",
                    "Texture",
                    ]
        for filter in filters_type:
            self.UI.comboBox_typ.addItem(filter)
            
        filters_prop = [
                     "Archetypes",
                     "Breakables",
                     "Breakables Used In MTL E3",
                     "Building",
                     "Building Facade Prefab",
                     "Building Optim",
                     "CLO",
                     "Entity In Region",
                     "Gameplay Ingredients Used In MTL E3",
                     "Geometry",
                     "Geometry In City Block",
                     "Geometry In prop.xml",
                     "Geometry In Road Splines",
                     "Geometry JIRA Status",
                     "Geometry Signs",
                     "Geometry Used In MTL",
                     "Geometry User Set Distances",
                     "Geometry Using Default Logic Material",
                     "Geometry With Duplicated LODs",
                     "Geometry With No Parent",
                     "Geometry With No JIRA In Studio Area",
                     "Geometry With One LOD",
                     "Illegal Geometry",
                     "Logic Materials",
                     "Material",
                     "Material From Media Broadcast References",
                     "Material Has Animated Bink",
                     "Material Has Animated Texture",
                     "Material Is Illegal",
                     "Material Two Sided",
                     "Missing Materials In Geometries",
                     "Missing Textures In Materials",
                     "Pink Objects",
                     "Plaza Duplicates",
                     "Plaza Geometry By Kill Distance",
                     "Prefab Roof",
                     "Prop Library",
                     "PropsCatalogs",
                     "Proxy",
                     "Proxy With Illegal Graphic Data",
                     "Proxy With Missing References",
                     "Proxy With No JIRA",
                     "Proxy With No JIRA In World",
                     "Texture",
                     "Texture Uncompressed In World",
                     "Ranges With Illegal Geometry",
                     "Ranges With No Definition",
                     "Shader Finder",
                     "Splines Using Wrong Road Materials",
                     "Vehicle Enticers Variety",
                     "WD2 Objects",
                     "WD2 Facades",
                     "WD3 Facades",
                     "WD3 Facades in MTL FP",
                    ]
        for filter in filters_prop:
            self.UI.comboBox_prop.addItem(filter)
    
        d_object_types = [
                            "All",
                            "Archetype",
                            "Archetype Library",
                            "Bink",
                            "Building Facade Prefab Item",
                            "Building Facade Prefab Library",
                            "Collection Item",
                            "Entity",
                            "Generic Item",
                            "Generic Library",
                            "Geometry",
                            "Material",
                            "Particle Emitter Library",
                            "Particle Emitter",
                            "Particle System Library",
                            "Particle System",
                            "Prefab",
                            "Prefab Entity",
                            "Prefab Library",
                            "Proxy",
                            "Range",
                            "Sequence",
                            "Spline Layer",
                            "Spline",
                            "Texture",
                            "World",
                            "World Layer",
                            ]
                            
        for type in d_object_types:
            self.UI.comboBox_advanced_search.addItem(type)
    
    def get_zones(self, print_all_existing_zones_values=False):
        self.zones_dict = {
                        (0, 0, 0) : (0,"Default"),
                        (197, 18, 48) : (1,"Montreal"),
                        (1, 62, 128) : (2,"Toronto"),
                        (37, 123, 184) : (3,"Paris"),
                        (252, 209, 22) : (4,"Bucarest"),
                        (0, 30, 98) : (51,"Montreal_FP"),
                        (255, 119, 0) : (52,"Piccadily"),
                        (255, 255, 0) : (53,"Traffalgar"),
                        (62, 164, 118) : (54,"Foodtown"),
                        (174, 220, 64) : (55,"Bishop's Gate"),
                        (174, 43, 216) : (56,"Construction"),
                        (129, 53, 70) : (57,"Montreal Tower Hamlets East"),
                    }
        if not print_all_existing_zones_values:
            return
            
        colors = set()
        for x in range(0,self.game_map_zones_image.width()):
            for y in range(0,self.game_map_zones_image.height()):
                c = self.game_map_zones_image.pixel(x,y)
                rgb = QtGui.QColor(c).red(), QtGui.QColor(c).green(), QtGui.QColor(c).blue()
                colors.add(rgb)
        for color in colors:
            print color
            
    def get_shapes(self, offset, scale, world_layers):
        shape_dict = {}
        for world_layer in world_layers:
            tree = ET.ElementTree(file=world_layer)
            for elem in tree.iter("Object"):
                name = elem.get("Name")
                pos = elem.get("Pos")
                pos = pos.split(",")
                pos_x = float(pos[0]) * -1 *scale
                pos_y = float(pos[1]) * scale
                pos_z = float(pos[2]) * scale
                for sub_elem in elem.iter("DebugAnnotationObject"):
                    points = sub_elem.get("Points")
                    points = points.split(" ")[1]
                    points = points.split(";")
                    qpoints = []
                    for point in points:
                        if point == "":
                            continue
                        point = point.split(",")
                        x,y,z = float(point[0]),float(point[1]),float(point[2])
                        x = x * -1 * scale + offset + pos_x
                        y = y * scale + offset + pos_y
                        z = z * scale + offset + pos_z
                        qpoints.append(QtCore.QPoint(x,y))
                    color = sub_elem.get("clrColor")
                    color = color.split(",")
                    r,g,b = float(color[0])*255,float(color[1])*255,float(color[2])*255
                    qcolor = QtGui.QColor(r,g,b)
                    shape_dict[name] = qpoints, qcolor
        return shape_dict
    
    def draw_city_blocks(self, world_layers):
        city_blocks_bitmap_path = data_path.replace("data", r"\td_tools\PythonTools\DDV\resources\city_blocks_bitmap_white.png")
        city_blocks_bitmap = QtGui.QImage(city_blocks_bitmap_path)
        offset = city_blocks_bitmap.height()/2
        scale = city_blocks_bitmap.height()/float(self.world_object.world_size)
        shape_dict = self.get_shapes(offset,scale,world_layers)
        if len(shape_dict) == 0:
            return
        painter = QtGui.QPainter()
        painter.begin(city_blocks_bitmap) 
        step = 16777215 / len(shape_dict)
        counter = 0
        for name, pointscolor in shape_dict.iteritems():
            hex_color = "#{0:06x}".format(counter)
            self.draw_shape(painter, pointscolor[0], QtGui.QColor(hex_color), 2, True, True, QtGui.QColor(hex_color))
            new_city_block_cell = adp.city_block_cell()
            new_city_block_cell.name = name
            new_city_block_cell.color = hex_color
            new_city_block_cell.identifier = counter #hex_color
            new_city_block_cell.filename = counter #hex_color
            new_city_block_cell.points = pointscolor[0]
            self.city_block_cell_objects[new_city_block_cell.identifier] = new_city_block_cell
            self.city_block_cell_objects[new_city_block_cell.name] = new_city_block_cell
            if counter >= 16777215:
                print name,": Colour exceeded max value, city block will show up black or white, problem!!!"
            counter += step # needs to be at the end
        painter.end()
        ###
        #city_blocks_bitmap.save(city_blocks_bitmap_path.replace(".png","_result.png"))
        ###
        self.city_blocks_image = city_blocks_bitmap
        
        # create default city block with white colour
        default_city_block = adp.city_block_cell()
        default_city_block.name = "Default City Block"
        default_city_block.color = "#ffffff"
        default_city_block.identifier = 16777215 #"#ffffff"
        default_city_block.filename = 16777215 #"#ffffff"
        self.city_block_cell_objects[default_city_block.identifier] = default_city_block
        self.city_block_cell_objects[default_city_block.name] = default_city_block
      
    ###########################################
    # Top View
    ###########################################

    def init_overrides(self):
        self.graphicsviewmousewheeleventbackup = self.UI.graphicsView_top.wheelEvent
        self.UI.graphicsView_top.wheelEvent = self.graphicsviewmousewheeleventoverride
        self.UI.graphicsView_top.fitInView = self.fit_in_view
        self.graphicsviewmousepresseventbackup = self.UI.graphicsView_top.mousePressEvent
        
        self.graphicsviewmousemoveeventbackup = self.UI.graphicsView_top.mouseMoveEvent
        
        self.UI.graphicsView_top.mousePressEvent = self.graphicsviewmousepresseventoverride
        self.UI.graphicsView_top.mouseMoveEvent = self.graphicsviewmousemoveeventoverride
        self.UI.graphicsView_top.mouseReleaseEvent = self.graphicsviewmousereleaseeventoverride
        
#        self.UI.treeView_0.mousePressEvent = self.dependencytabmousepresseventoverride
        self.UI.groupBox_current_item.mousePressEvent = self.dependencytabmousepresseventoverride

    def init_topview(self):
        self.background = QtGui.QGraphicsPixmapItem()
        self.background_image = None
        self.background.setTransformationMode(QtCore.Qt.SmoothTransformation)
        
        self.UI.graphicsView_top._zoom = 0
        self.UI.graphicsView_top.scene = QtGui.QGraphicsScene()        
        self.UI.graphicsView_top.scene.addItem(self.background)        
        self.UI.graphicsView_top.setScene(self.UI.graphicsView_top.scene)        
        self.UI.graphicsView_top.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.UI.graphicsView_top.setResizeAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.UI.graphicsView_top.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.UI.graphicsView_top.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.UI.graphicsView_top.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(30, 30, 30)))
        self.UI.graphicsView_top.setFrameShape(QtGui.QFrame.NoFrame)
        #self.UI.graphicsView_top.setDragMode(QtGui.QGraphicsView.ScrollHandDrag)

        self.selection_in_bitmap = (-1.0,-1.0)
        self.update_view()
        self.fit_in_view()
        
        self.UI.graphicsView_top.scale(50, 50)

    def graphicsviewmousepresseventoverride(self, event):
        pos = self.UI.graphicsView_top.mapToScene(event.pos())
        self.selection_in_bitmap = (pos.x(), pos.y())
        if event.buttons() == QtCore.Qt.LeftButton:
            if self.topview_mode == 0:
                self.compute_selection()
            
            if self.topview_mode == 1:
                self.compute_city_block_cell_selection()
            
        if event.button() == QtCore.Qt.MidButton:
            self.__prevMousePos = event.pos()
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.ClosedHandCursor))
        # else:
            # super(self.UI.graphicsView_top, self).mousePressEvent(event)
            
        #self.graphicsviewmousepresseventbackup(event)
        else:
            QtGui.QApplication.restoreOverrideCursor()
    
    def dependencytabmousepresseventoverride(self, event):
        if event.buttons() == QtCore.Qt.XButton1:
            self.clicked_back()
    
    def graphicsviewmousemoveeventoverride(self, event):
        if event.buttons() == QtCore.Qt.MidButton:
            offset = self.__prevMousePos - event.pos()
            self.__prevMousePos = event.pos()

            self.UI.graphicsView_top.verticalScrollBar().setValue(self.UI.graphicsView_top.verticalScrollBar().value() + offset.y())
            self.UI.graphicsView_top.horizontalScrollBar().setValue(self.UI.graphicsView_top.horizontalScrollBar().value() + offset.x())
        else:
            self.graphicsviewmousemoveeventbackup(event)
            
    def graphicsviewmousereleaseeventoverride(self, event):
        QtGui.QApplication.restoreOverrideCursor()
            
    def compute_selection(self):
        x = int(self.selection_in_bitmap[0])
        y = int(self.selection_in_bitmap[1])
        
        # c = self.game_map_zones_image.pixel(x, y)
        # rgb = QtGui.QColor(c).red(), QtGui.QColor(c).green(), QtGui.QColor(c).blue()
        # print rgb

        if x in range(0,self.background.pixmap().width()) and y in range(0,self.background.pixmap().height()):
            
            x = x / (self.world_object.cell_size / 2) # should 2 be the ratio of meter per pixel...?
            y = y / (self.world_object.cell_size / 2)
            
            x = x + 1
            y = y + 1
            
            x = (self.world_object.cell_count + 1) - x

            world_pos_x = (x*2*64-4096)-64
            world_pos_y = (y*2*64-4096)-64
            world_pos = str(world_pos_x) + ", " + str(world_pos_y)

            self.topview_selection = (x, y)
            self.update_status_bar(str(self.topview_selection) + " " + str(world_pos))
            self.fill_top_tree(self.world_object.world_grid.cells[self.topview_selection[0], self.topview_selection[1]])
            
            # Code useful to test the cell regions:
            # my_cell = self.world_object.world_grid.cells[(self.world_object.cell_size - self.topview_selection[0], self.topview_selection[1] + 1)]
            # print my_cell.x, my_cell.y, my_cell.region
            
            self.update_view()
            
    def compute_city_block_cell_selection(self):
        x = int(self.selection_in_bitmap[0])
        y = int(self.selection_in_bitmap[1])
        color = self.city_blocks_image.pixel(x,y)        
        id = color & 0x00ffffff
        block = self.city_block_cell_objects.get(id)
        self.selected_city_block_cell = block
        self.update_status_bar(block.name.replace("CityBlock_", "CityBlock "))
        self.fill_top_tree(block)
        self.update_view()

    def get_resource_dict(self, cell):

        if len(cell.resources_dict) > 0:  # If the cell already contains its resource dictionary with its instances (entities and/or ranges), no need to generate it! This is much faster.
            return cell.resources_dict

        dict_output = {}
        for res in cell.resources:
            if res.type == "Entity" or res.type == "Range":  # Test if the result of the filter is an entity, no need to look for entities then. Also break because of the patch for the prefab overrides.
                dict_output[res] = []
                continue
            self.recursive_search_items = [] 
            self.recursive_search(res, "Entity", "up")
            self.recursive_search(res, "Range", "up") # do an extra pass to get all the ranges, since those are now considered as entities for world referencing
            entities = []
            for ent in self.recursive_search_items:
                if ent in cell.entities:
                    entities.append(ent)
            if len(entities) == 0:  # patch to fix bugs with weird behaviour with prefab overrides
                continue
            dict_output[res] = entities
        if len(dict_output) == 0:
            return cell.resources_dict
        return dict_output

    def fill_top_tree(self, my_cell):

        # if self.topview_selection[0] < 0:
            # return #No wlu selected

        if self.world_object is None:
            return

        self.toggle_waitcursor(True)
        #my_cell = self.world_object.world_grid.cells[self.topview_selection[0], self.topview_selection[1]]
        resource_dict = dict(self.get_resource_dict(my_cell))

        if self.stream_optimizer_object is not None:
            cell = self.stream_optimizer_object.get_cell(self.topview_selection[0], self.topview_selection[1])
            self.current_total_cost = str(cell.total_cost)
            for key, value in resource_dict.iteritems():
                for i in value:
                    i.special_info = str(i.stream_optimizer_remove_gain)

        if self.UI.checkBox_show_entities.isChecked() == False:  # Hack to empty the values of resource_dict in case the checkbox to see the entities is unchecked
            for k, v in resource_dict.iteritems():
                resource_dict[k] = None

        self.model_topview.clearChildren()

        self.model_topview.setupModelData(data_dict=resource_dict)

        
        count_text = ""
        
        if self.UI.radioButton_pre.isChecked() and str(self.UI.comboBox_pre.currentText()) == "Spawning Cost" or \
            self.UI.radioButton_bud.isChecked() and str(self.UI.comboBox_bud.currentText()) == "Spawning Cost":
            self.UI.label_url.setText("")
            #Hack for loading rings querry
            total_count = len(my_cell.resources)

            total_loading = 0

            for i in my_cell.resources:
                total_loading += i.loading_cost

            count_text = "Instance Count: " + str(total_count)
            count_text += " /// "
            count_text += "Spawning Cost: " + str(total_loading)
            
        elif self.UI.radioButton_bud.isChecked() and str(self.UI.comboBox_bud.currentText()) == "Building Kit Points":
            count_text = "Points: " + str(my_cell.points) + " | " + "Points with coupons: " + str(my_cell.points_compensated)
            url_link = "<a href=\"https://mdc-web-tomcat17.ubisoft.org/confluence/download/attachments/372980897/image2018-3-29_16-53-27.png?version=1&modificationDate=1522356810000&api=v2\"> <font color=white> More info</a>" 
            self.UI.label_url.setText(url_link)
            
        elif self.UI.radioButton_bud.isChecked() and str(self.UI.comboBox_bud.currentText()) == "Facades Instance Count":
            count_text = str(my_cell.facade_instance_count)

        else:
            self.UI.label_url.setText("")
            count = len(resource_dict)

            instance_count = 0
            for i in resource_dict.values():
                if i is None:
                    continue
                instance_count += len(i)

            count_text = str(count) + " item"
            if count > 1:
                count_text += "s"
            count_text += " \ " + str(instance_count) + " instance"
            if instance_count > 1:
                count_text += "s"
            if self.current_total_cost != "0":
                count_text += " \ Streaming Cost: "
                count_text += self.current_total_cost
            if my_cell.special_info is not None:
                count_text += " \ Special Info = " + str(my_cell.special_info)

        self.UI.label_count.setText(count_text)

        self.refresh_ui()
        self.toggle_waitcursor(False)
  
    def fit_in_view(self):
        rect = QtCore.QRectF(self.background.pixmap().rect())
        if not rect.isNull():
            unity = self.UI.graphicsView_top.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
            self.UI.graphicsView_top.scale(1 / unity.width(), 1 / unity.height())
            viewrect = self.UI.graphicsView_top.viewport().rect()
            scenerect = self.UI.graphicsView_top.transform().mapRect(rect)
            factor = min(viewrect.width() / scenerect.width(),
                         viewrect.height() / scenerect.height())
            self.UI.graphicsView_top.scale(factor, factor)
            self.UI.graphicsView_top.centerOn(rect.center())
            self.UI.graphicsView_top._zoom = 0
    
    def graphicsviewmousewheeleventoverride(self, event):
        if event.delta() > 0:
            factor = 1.25
            self.UI.graphicsView_top._zoom += 1
        else:
            factor = 0.8
            self.UI.graphicsView_top._zoom -= 1
        # if self.UI.graphicsView_top._zoom > 0:
            # self.UI.graphicsView_top.scale(factor, factor)
        # elif self.UI.graphicsView_top._zoom == 0:
            # self.UI.graphicsView_top.fitInView()
        # else:
            # self.UI.graphicsView_top._zoom = 0
        if self.UI.graphicsView_top._zoom in range(-2,21):
            self.UI.graphicsView_top.scale(factor, factor)
        self.UI.graphicsView_top._zoom = min(self.UI.graphicsView_top._zoom, 20)
        self.UI.graphicsView_top._zoom = max(self.UI.graphicsView_top._zoom, -2)

    def draw_shape(self, painter, points, color_fill, width, outline=True, fill=False, color_outline=None):
    
        if outline:
            pen = QtGui.QPen()
            pen.setJoinStyle(QtCore.Qt.MiterJoin)
            pen.setWidth(width)
            if color_outline is not None:
                pen.setColor(color_outline)
            painter.setPen(pen)
            
        if fill:
            brush = QtGui.QBrush()
            brush.setColor(color_fill)
            painter.setBrush(color_fill)
        
        shape = QtGui.QPolygon(points)
        painter.drawPolygon(shape)
        
    def draw_ellipse(self, painter, world_position, color, size, outline=True, fill=False):
        brush = QtGui.QBrush()
        brush.setColor(color)
        painter.setBrush(color)
        painter.drawEllipse(world_position[0],world_position[1],size,size)
    
    def draw_donut(self, painter, world_position, color, size):
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        circle_path = QtGui.QPainterPath()
        painter.setPen(QtGui.QPen(color, size))      
        circle_path.addEllipse(QtCore.QPointF(world_position[0],world_position[1]),1500,1500)
        painter.drawPath(circle_path)

    def update_view(self):
        # background = QtGui.QImage(cur_path + r"\\UI\\" + "game_map_london.bmp")
        background = QtGui.QImage(cur_path + r"\\UI\\" + "game_map_none.bmp")
        if isfile(cur_path + r"\\UI\\" + "game_map_" + self.world_name + ".bmp"):
            background = QtGui.QImage(cur_path + r"\\UI\\" + "game_map_" + self.world_name + ".bmp")
            
        if self.UI.pushButton_cb.isChecked():
            background = QtGui.QImage(cur_path + r"\\UI\\" + "game_map_studios.bmp")

        stats_image = QtGui.QImage(self.image_path)
        
        scaled_size = background.height() * self.top_view_scale
        
        world_size = None
        if self.world_object is None:
            world_size = 4096 # patch for multi world support
        else:
            world_size = self.world_object.world_size
            
        ratio_to_world = world_size / scaled_size

        painter = QtGui.QPainter()
        
        ###
        # painter.begin(background)
        # painter.setCompositionMode(QtGui.QPainter.CompositionMode_Screen)
        # shape = [
            # QtCore.QPoint(3500,500),
            # QtCore.QPoint(500,500),
            # QtCore.QPoint(500,3500),
            # QtCore.QPoint(3500,3500)
        # ]
        # self.draw_shape(painter, shape, QtGui.QColor(255,0,0), 150) #outline=True, fill=False, color_outline=None)
        # painter.end()
        # pixmap = QtGui.QPixmap(background)
        # self.background.setPixmap(pixmap)
        # self.refresh_ui()
        # return
        ###

        if self.UI.pushButton_stats.isChecked() and self.topview_mode == 0:        
            painter.begin(background)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
            # painter.setCompositionMode(QtGui.QPainter.CompositionMode_Screen)
            painter.drawImage(0, 0, stats_image)
            painter.end()
        
        if self.UI.pushButton_zones.isChecked():
            painter.begin(background)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Screen)
            painter.drawImage(0, 0, self.game_map_zones_image)
            painter.end()
            
        if self.UI.pushButton_lines.isChecked():
            painter.begin(background)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Screen)
            painter.drawImage(0, 0, self.game_map_cb_image)
            painter.end()
        
        if self.UI.pushButton_city_blocks.isChecked() and self.topview_mode == 1:
            painter.begin(background)
            # painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver) # sourceover won't work, alpha doesn't work
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_Screen)
            painter.drawImage(0, 0, self.city_blocks_heatmap_image)
            painter.end()
            
            # painter.begin(background)
            # painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
            # size = 30
            # for position, color in self.atlas_data_dict_out_2.iteritems():
                # position = position[0]+40, position[1]
                # x = position[0]/ratio_to_world+(scaled_size/2) -size/2
                # y = position[1]/ratio_to_world+(scaled_size/2) -size/2
                # position = (x,y)
                # self.draw_ellipse(painter, position, color, 30)
            # size = 15
            # for position, color in self.atlas_data_dict_out_1.iteritems():
                # position = position[0]+40, position[1]
                # x = position[0]/ratio_to_world+(scaled_size/2) -size/2
                # y = position[1]/ratio_to_world+(scaled_size/2) -size/2
                # position = (x,y)
                # self.draw_ellipse(painter, position, color, 15)
            # painter.setCompositionMode(QtGui.QPainter.CompositionMode_Screen)
            # painter.end()
        if self.UI.pushButton_cl.isChecked():
            painter.begin(background)
            width = 3
            color = QtGui.QColor(255,0,0)
            for loc in self.city_locations:
                position = loc[0]
                points = loc[1]
                converted_points = []
                for point in points:
                    x = -(point[0] + position[0])/ratio_to_world + (scaled_size/2)
                    y = (point[1] + position[1])/ratio_to_world + (scaled_size/2)
                    converted_points.append(QtCore.QPoint(x,y))
                self.draw_shape(painter, converted_points, color, width, False, True)
            painter.end()

        pos = (int(self.selection_in_bitmap[0]), int(self.selection_in_bitmap[1]))
        
        if self.UI.pushButton_stats.isChecked() and self.topview_mode == 0:
            if pos[0] in range(0,background.width()) and pos[1] in range(0,background.height()):
                painter.begin(background)
                painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
                cell_size = background.width() / self.world_object.cell_count
                pos = int(math.ceil(pos[0] / cell_size)) * cell_size, int(math.ceil(pos[1] / cell_size)) * cell_size
                
                shape = [   
                            QtCore.QPoint(pos[0]+0,pos[1]+0), 
                            QtCore.QPoint(pos[0]+cell_size,pos[1]+0), 
                            QtCore.QPoint(pos[0]+cell_size,pos[1]+cell_size), 
                            QtCore.QPoint(pos[0]+0,pos[1]+cell_size),
                        ]
                
                color = QtGui.QColor(50,187,213)
                self.draw_shape(painter, shape, color, 10, True, False, color)
                color = QtGui.QColor(255,255,255)
                self.draw_shape(painter, shape, color, 5, True, False, color)
                painter.end()
        
        if self.selected_city_block_cell is not None:
            if self.selected_city_block_cell.points is not None:
                if self.UI.pushButton_city_blocks.isChecked() and self.topview_mode == 1:
                    painter.begin(background)
                    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
                    color = QtGui.QColor(50,187,213)
                    self.draw_shape(painter, self.selected_city_block_cell.points, color, 10, True, False, color)
                    color = QtGui.QColor(255,255,255)
                    self.draw_shape(painter, self.selected_city_block_cell.points, color, 5, True, False, color)
                    painter.end()
        ####
        
        #background.save(r"w:\main\td_tools\PythonTools\DDV\top_view_dump.bmp")
        
        ####
        pixmap = QtGui.QPixmap(background)
        self.background.setPixmap(pixmap)
        self.refresh_ui()

    def create_image_output(self, list_data, output_name="", colouring="heatmap"):
        self.progressbar_update(True) #Maxout
        self.update_status_bar("Create Image Output...")
        self.progressbar_setmax(len(list_data))

        # verylight =     (0,100,0)
        # verylight2 =    (0,120,0)
        # light =         (0,140,0)
        # light2 =        (100,180,0)
        # good =          (150,200,0)
        # good2 =         (200,200,0)
        # medium =        (220,180,0)
        # medium2 =       (240,180,0)
        # limit =         (240,160,0)
        # bad =           (255,0,0)
        # null =          (0,0,0)
        # verybad =       (100,0,200)
        # outofcontrol =  (64,0,255)
        # maxvaluebad =   (255,0,255)
        # maxvalueok =    (0,255,255)
        
        alpha = 210
        
        verylight =     (0,220,0,105)
        light =         (0,220,0,150)
        good =          (0,220,0,alpha)
        medium =        (240,255,0,alpha)
        limit =         (255,140,0,alpha)
        bad =           (255,0,0,alpha)
        null =          (255,255,255,127)
        verybad =       (192,0,0,alpha)
        outofcontrol =  (128,0,0,alpha)
        maxvaluebad =   (64,0,0,alpha)
        maxvalueok =    (0,255,255,alpha)

        pixel_list = []
        
        max_value = 0
        for list in list_data:
            if len(list) is not 0:
                temp_max_value = max(list)
                if temp_max_value > max_value:
                    max_value = temp_max_value
                    
        if colouring == "binary":
            for i in list_data:
                self.progressbar_update()
                list_y = []
                for j in i:
                    if j > 0:
                        list_y.append(bad)
                    else:
                        list_y.append(null)                
                pixel_list.append(list_y)
        
        elif colouring == "stream optimizer":
            for i in list_data:
                self.progressbar_update()
                list_y = []
                for j in i:
                    if j == max_value:
                        if max_value > 25:
                            list_y.append(maxvaluebad)
                        else:
                            list_y.append(maxvalueok)
                    elif j in range(2,6):
                        list_y.append(verylight)
                    elif j in range(5,11):
                        list_y.append(light)
                    elif j in range(10,16):
                        list_y.append(good)
                    elif j in range(15,21):
                        list_y.append(medium)
                    elif j in range(20,26):
                        list_y.append(limit)
                    elif j > 25:
                        list_y.append(bad)
                    else:
                        list_y.append(null)                  
                pixel_list.append(list_y)
        
        elif colouring == "Geometry":
            for i in list_data:
                self.progressbar_update()
                list_y = []
                for j in i:
                    if j == max_value:
                        if max_value > 525:
                            list_y.append(maxvaluebad)
                        else:
                            list_y.append(maxvalueok)
                    elif j in range(1,226):
                        list_y.append(verylight)
                    elif j in range(225,276):
                        list_y.append(light)
                    elif j in range(275,326):
                        list_y.append(good)
                    elif j in range(325,376):
                        list_y.append(medium)
                    elif j in range(375,426):
                        list_y.append(limit)
                    elif j in range(425, 476):
                        list_y.append(bad)
                    elif j in range(475, 526):
                        list_y.append(verybad)
                    elif j > 525:
                        list_y.append(outofcontrol)
                    else:
                        list_y.append(null)                  
                pixel_list.append(list_y)
            
        elif colouring == "building_kits" or colouring == "Building Facade Prefab Library":
            # print "Building Kits budgets are as follow:"
            # print "Black    = 0         - nothing"
            # print "Green    = 1-7       - all good"
            # print "Yellow   = 8         - close to the limit"
            # print "Orange   = 9         - limit reached"
            # print "Red      = 10-13     - over budget"
            # print "Pink     = 14-18     - massively over budget"
            # print "Purple   = +18       - out of control"
            for i in list_data:
                self.progressbar_update()
                list_y = []
                for j in i:
                    if j == 0:
                        list_y.append(null)
                    if j == 1:
                        list_y.append(verylight)
                    if j == 2:
                        list_y.append(verylight)
                    if j == 3:
                        list_y.append(verylight)
                    if j == 4:
                        list_y.append(light)
                    if j == 5:
                        list_y.append(light)
                    if j == 6:
                        list_y.append(good)
                    if j == 7:
                        list_y.append(medium)
                    if j == 8:
                        list_y.append(limit)
                    if j == 9:
                        list_y.append(bad)
                    if j in range(10,14):
                        list_y.append(bad)            
                    if j in range(14,19):
                        list_y.append(verybad)
                    if j > 18:
                        list_y.append(outofcontrol)
                pixel_list.append(list_y)
                
        elif colouring == "building_kits_points":
            for i in list_data:
                self.progressbar_update()
                list_y = []
                for j in i:
                    if j == 0:
                        list_y.append(null)
                    if j == 1:
                        list_y.append(verylight)
                    if j == 2:
                        list_y.append(verylight)
                    if j == 3:
                        list_y.append(verylight)
                    if j == 4:
                        list_y.append(light)
                    if j == 5:
                        list_y.append(light)
                    if j == 6:
                        list_y.append(good)
                    if j == 7:
                        list_y.append(good)
                    if j == 8:
                        list_y.append(medium)
                    if j == 9:
                        list_y.append(limit)
                    if j in range(10,14):
                        list_y.append(bad)            
                    if j in range(14,19):
                        list_y.append(verybad)
                    if j in range(19,100):
                        list_y.append(outofcontrol)
                    if j > 99:
                        list_y.append(maxvaluebad)
                pixel_list.append(list_y)
                
        elif colouring == "building_memory":
            for i in list_data:
                self.progressbar_update()
                list_y = []
                for j in i:                     
                    if j < 1:
                        list_y.append(null)
                    elif j < 21:
                        list_y.append(verylight)
                    elif j < 41:
                        list_y.append(light)
                    elif j < 61:
                        list_y.append(good)
                    elif j < 81:
                        list_y.append(medium)
                    elif j < 101:
                        list_y.append(limit)
                    elif j < 121:
                        list_y.append(bad)            
                    elif j < 141:
                        list_y.append(verybad)
                    elif j > 140:
                        list_y.append(outofcontrol)
                    else:
                        list_y.append((0,0,255))
                pixel_list.append(list_y)

        elif colouring == "loadingring":
            for i in list_data:
                self.progressbar_update()
                max_value = float(max_value)
                list_y = []
                for j in i:
                    if max_value is not 0 and j is not 0:
                        j = float(j)
                        '''
                        if j == max_value:
                            list_y.append(bad)
                        elif j > max_value * 0.8:
                            list_y.append(limit)
                        elif j > max_value * 0.6:
                            list_y.append(medium)
                        elif j > max_value * 0.4:
                            list_y.append(good)
                        elif j > max_value * 0.2:
                            list_y.append(light)
                        elif j > max_value * 0.1:
                            list_y.append(verylight)
                        else:
                            list_y.append(null)
                        '''
                        if j == max_value:
                            list_y.append(bad)
                        elif j > max_value * 0.75:
                            list_y.append(limit)
                        elif j > max_value * 0.5:
                            list_y.append(medium)
                        elif j > max_value * 0.3:
                            list_y.append(good)
                        elif j > max_value * 0.1:
                            list_y.append(light)
                        elif j > max_value * 0.05:
                            list_y.append(verylight)
                        else:
                            list_y.append(null)

                    else:
                       list_y.append(null)
                pixel_list.append(list_y)

        elif colouring == "loadingringbudgeted":
            for i in list_data:
                self.progressbar_update()
                max_value = float(max_value)
                list_y = []
                for j in i:
                    if j == max_value:
                        list_y.append(maxvaluebad)
                    elif j > 34000:
                        list_y.append(outofcontrol)
                    elif j > 29000:
                        list_y.append(verybad)
                    elif j > 24000:
                        list_y.append(bad)
                    elif j > 19000:
                        list_y.append(limit)
                    elif j > 15000:
                        list_y.append(medium)
                    elif j > 10000:
                        list_y.append(good)
                    elif j > 5000:
                        list_y.append(light)
                    elif j > 2500:
                        list_y.append(verylight)
                    else:
                        list_y.append(null)
                pixel_list.append(list_y)
                
        elif colouring == "facade_instance_count":
            for i in list_data:
                self.progressbar_update()
                max_value = float(max_value)
                list_y = []
                for j in i:
                    if j > 6000:
                        list_y.append(outofcontrol)
                    elif j > 4000:
                        list_y.append(verybad)
                    elif j > 3000:
                        list_y.append(bad)
                    elif j > 2000:
                        list_y.append(limit)
                    elif j > 1000:
                        list_y.append(medium)
                    elif j > 500:
                        list_y.append(good)
                    elif j > 250:
                        list_y.append(light)
                    elif j > 100:
                        list_y.append(verylight)
                    else:
                        list_y.append(null)
                pixel_list.append(list_y)

        else:# colouring == "heatmap":
            for i in list_data:
                self.progressbar_update()
                max_value = float(max_value)
                list_y = []
                for j in i:
                    if max_value is not 0 and j is not 0:
                        j = float(j)
                        if j == 0:
                            list_y.append(null)
                        if j == max_value:
                            list_y.append(bad)
                        elif j > max_value * 0.8:
                            list_y.append(limit)
                        elif j > max_value * 0.6:
                            list_y.append(medium)
                        elif j > max_value * 0.4:
                            list_y.append(good)
                        elif j > max_value * 0.2:
                            list_y.append(light)
                        else:
                            list_y.append(verylight)
                        # else:
                            # current_value = (j/max_value)*255
                            # current_value = int(current_value)
                            # current_value *= 4
                            # if current_value < 10: # this is to catch values that would be too low and set a floor value
                                # current_value = 40 # this is the lowest value used in "verylight"
                            # list_y.append((0, current_value, 0))
                    else:
                       list_y.append(null)
                pixel_list.append(list_y)

        self.progressbar_update(True) #Maxout
        self.progressbar_setmax(self.world_object.cell_count + 1024 * 2)
        self.update_status_bar("Writing Image...")

        # create new bitmap where the stats will be written
        # stats_map = QtGui.QImage(self.world_object.cell_count,self.world_object.cell_count, QtGui.QImage.Format_RGB888)
        stats_map = QtGui.QImage(self.world_object.cell_count,self.world_object.cell_count, QtGui.QImage.Format_ARGB32)

        for i in xrange(self.world_object.cell_count):
            self.progressbar_update()
            for j in xrange(self.world_object.cell_count):
                #self.refresh_ui()
                r = pixel_list[i][j][0]
                g = pixel_list[i][j][1]
                b = pixel_list[i][j][2]
                a = pixel_list[i][j][3]
                
                # long_rgb = r * 65536 + g * 256 + b
                # stats_map.setPixel(i,j, long_rgb)
                
                color = QtGui.qRgba(r,g,b,a)
                stats_map.setPixel(i,j, color)
        
        stats_map = stats_map.transformed(QtGui.QTransform().rotate(90))
        
        # scale it up to 1024x1024
        stats_map = stats_map.scaledToHeight(self.world_object.world_size / 2)
        stats_map = stats_map.scaledToWidth(self.world_object.world_size / 2)

        game_map = QtGui.QImage(self.game_map_path)
        game_map_cb = QtGui.QImage(self.game_map_path_cb)
        
        output = cur_path + r"\\UI\\" + output_name + "result_map.png"
        stats_map.save(output)
        self.image_path = output

        self.progressbar_update(True) #Maxout

    def _compute_screen(self, color, game_map):
        color = (1 - (1 - game_map) * (1 - color))
        color = int(color * 255)
        color = max(0, min(255, color))
        return color

    def _compute_long_rgb(self, value):
        r = value[0]
        g = value[1]
        b = value[2]
        return r * 65536 + g * 256 + b

    def get_entity_density(self):
        self.update_status_bar("Get entity density...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.entities)
                table_to_output_y.append(count)
                cell.resources = cell.entities
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()
        
    def get_group_density(self):
        self.update_status_bar("Get group density...")
        
        blocks_set = set()
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)
        
        for block in blocks_set:
            self.progressbar_update()
            block.resources = [] # empty the list in case it contains something else
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(block, "Entity", "down")
            resource_set = set()
            for item in self.recursive_search_items:
                if item.entity_type == "Group":
                    resource_set.add(item)
            block.resources = resource_set
        return blocks_set

    def merge_images(self, path, width, height):
        """Merge images from a path into one, displayed in a Disrupt logic
        :param path: path to heightmap folder
        :param width: merged image width total size 
        :param height: merged image height total size 
        :return: the merged Image object 
        Merged images are done in bottom up fashion since disrupt piles them up like that,
        and we assume that heightmap images in folder are all same size (power of two) 256x256
        """    
        images = listdir(path)
        images_size = adp.Image.open(path + images[0]).width
        result = adp.Image.new('I', (width,height))
        row = 0 
        column = height-images_size #starts bottom and assume the size of given textures is 256x256
        image_offset = (row,column)
        
        for img in images:
            i = adp.Image.open(path + img).transpose(adp.Image.FLIP_TOP_BOTTOM)
            result.paste(i, image_offset)
            if column > 0:
                column -= images_size #Going up we substract, I don't like magic numbers 256
            else : 
                column = height -images_size #Starting point 
                row +=images_size
            image_offset = (row , column )
        return result

    def get_texture_heightmap(self):       
        heightmap_folder = r"W:\Main\data\worlds\london\terrain\heightmap\\"
        heightmap = self.merge_images(heightmap_folder, 8192, 6144)
        heightmap.save(cur_path + r"\resources\orwell_heightmap.png", "PNG")
        return heightmap
    
    def get_entity_underground(self):
        self.update_status_bar("Getting entities underground...")
        heightmap = self.get_texture_heightmap()
        ## DO STUFF HEREEE !!!!! ||-->> ------------------------

    def get_entity_density_by_z(self):
        self.update_status_bar("Get entity density...")
        table_to_output = []

        try:
            value = self.UI.lineEdit_pre.text()        
            values = value.split(":")        
            begin = int(float(values[0]))
            end = int(float(values[1]))
            range_in_z = set(range(begin, end))
        except:
            self.update_status_bar('Invalid values entered. Enter two integer values separated by ":"')
            return
        
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.entity_class == "VisibilityOcclusionBox":
                        continue
                    pos_z = int(float(entity.position[2]))
                    if pos_z in range_in_z:
                        cell.resources.append(entity)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")#, "binary")
        self.update_view()
        
    def get_entity_density_int_obj_on_normal_layer(self):
        # white_list is a list of objects that we do want to keep in the open world
        white_list = set()
        self.update_status_bar("Get entity density...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.world_layer_type != "Normal":
                        continue
                    self.recursive_search_items = []
                    self.recursive_search(entity, "Geometry")
                    for item in self.recursive_search_items:
                        is_in_white_list = False
                        if "\\graphics\\geometry\\interior" in item.filename:
                            for white_list_item in white_list:
                                if white_list_item in item.filename:
                                    is_in_white_list = True
                            if is_in_white_list == False:
                                cell.resources.append(entity)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()
    
    def get_entity_in_towerhamlets_east(self):
        self.update_status_bar("Get Tower Hamlets East entities...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if "07_towerhamlets_east" in entity.filename:
                        cell.resources.append(entity)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()
    
    def get_clo_density(self):
        self.update_status_bar("Get CLO density...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.entity_type == "CityLifeObject":
                        cell.resources.append(entity)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()
        
    def get_not_batched_density(self):
        self.update_status_bar("Get !batched density...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.entity_type == "Entity" or entity.entity_type == "PrototypeEntity":
                        cell.resources.append(entity)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()

    def recursive_search(self, item, type, direction="down", exclude_entity_type=None, exclude_type=None):
        exclusion_set = set()
        result_list = list()
        self._recursive_search(item, type, direction, exclude_entity_type, exclude_type, exclusion_set, result_list)
        return result_list

    def _recursive_search(self, item, type, direction, exclude_entity_type, exclude_type, exclusion_set, result_list):

        if direction == "down" and item.type == "Entity" and item.entity_type == "Prefab":
            exclusion_set = exclusion_set.union(item.prefab_deleted_children)

        if direction == "down":
            for i in item._children.keys():
                if i.identifier == item.identifier:
                    print "I'm my own child!! " + i.name
                    return
                    # continue
                if i.type == "Entity" and i.entity_type == exclude_entity_type:
                    continue
                if i.type == "Prefab Entity" and i.entity_type == exclude_entity_type:
                    continue
                if i.type == "Prefab Entity":
                    if i.identifier in exclusion_set:
                        continue
                if i.type == exclude_type:
                    continue
                if i.type == type:
                    self.recursive_search_items.append(i)
                    result_list.append(i)
                self._recursive_search(i, type, direction, exclude_entity_type, exclude_type, exclusion_set, result_list)
        
        if direction == "up":
            for i in item._parents.keys():
                if i.identifier == item.identifier:
                    print "I'm my own parent! " + i.name
                    return
                    # continue
                if i.type == "Entity" and i.entity_type == exclude_entity_type:
                    continue
                if i.type == "Prefab Entity" and i.entity_type == exclude_entity_type:
                    continue
                if i.type == "Prefab Entity":
                    exclusion_set.add(i.identifier)
                if i.type == "Entity" and i.entity_type == "Prefab":
                    is_excluded = False
                    for id in i.prefab_deleted_children:
                        if id in exclusion_set:
                            is_excluded = True
                    if is_excluded:
                        continue
                if i.type == exclude_type:
                    continue
                if i.type == type:
                    self.recursive_search_items.append(i)
                    result_list.append(i)
                self._recursive_search(i, type, direction, exclude_entity_type, exclude_type, exclusion_set, result_list)
        
    def get_current_object_density(self, direction):
        self.update_status_bar("Get current object density...")
        table_to_output = []
        self.recursive_search_items = [] # empty the list in case it contains somthing else
        self.recursive_search(self.current_object, "Entity", direction)
        parent_entities = self.recursive_search_items
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                for entity_in_cell in cell.entities:
                    for parent in parent_entities:
                        if entity_in_cell == parent:
                            if parent not in cell.resources:
                                cell.resources.append(parent)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)

        ###################################################
        table_to_output = []  
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1               
                total_instances += count
            table_to_output.append(table_to_output_y)
        print "--------------------------"
        print "Most amount of resources:"
        print max
        print "--------------------------"
        print "Number of populated cells:"
        print populated_cells
        print "--------------------------"
        print "Number of instances:"
        print total_instances
        print "--------------------------"
        ####################################################
        
        return table_to_output            
                         
    def get_resource_density(self, type, direction="down", exclude_entity_type=None, exclude_string=["ThisStringIsNeverUsed"], exclude_type=None): # the weird default parameter "ThisStringIsNeverUsed" is to prevent breaking string comparaisons in certain modes
        self.update_status_bar("Get Resource density...")
        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                self.recursive_search_items = [] # empty the list in case it contains somthing else
                self.recursive_search(cell, type, direction, exclude_entity_type, exclude_type)
                resources = self.recursive_search_items
                count = 0
                for res in resources:
                    if res not in cell.resources:
                        #if exclude_string not in res.filename:
                        keep_it = True
                        for string in exclude_string:
                            if string in res.filename:
                                keep_it = False
                        if keep_it:                                
                            count += 1
                            cell.resources.append(res)

        ###################################################
        table_to_output = []  
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1               
                total_instances += count
            table_to_output.append(table_to_output_y)
        print "--------------------------"
        print "Most amount of resources:"
        print max
        print "--------------------------"
        print "Number of populated cells:"
        print populated_cells
        print "--------------------------"
        print "Number of instances:"
        print total_instances
        print "--------------------------"
        ####################################################
        
        return table_to_output

    def get_geometry_budget_density(self):
        self.update_status_bar("Get Resource density...")
        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.world_layer_type == "Mission":
                        continue
                    if entity.world_layer_type == "LMA":
                        continue
                    if entity.world_layer_type == "HMA":
                        continue
                    if entity.world_layer_type == "Interior":
                        continue
                    if entity.world_layer_type == "Range":
                        continue
                    if entity.entity_type == "EnticerVehicle":
                        continue

                    self.recursive_search_items = [] # empty the list in case it contains somthing else
                    self.recursive_search(entity, "Geometry", "down")
                    resources = self.recursive_search_items
                    count = 0
                    for res in resources:
                        if res.is_facade:
                            continue
                        if res not in cell.resources:                              
                            count += 1
                            cell.resources.append(res)

                        if res not in cell.resources_dict.keys():
                            cell.resources_dict[res] = set()

                        cell.resources_dict[res].add(entity)

        ###################################################
        table_to_output = []  
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1               
                total_instances += count
            table_to_output.append(table_to_output_y)
        print "--------------------------"
        print "Most amount of resources:"
        print max
        print "--------------------------"
        print "Number of populated cells:"
        print populated_cells
        print "--------------------------"
        print "Number of instances:"
        print total_instances
        print "--------------------------"
        ####################################################
        
        return table_to_output

    def get_external_references_from_file(self):
        self.update_status_bar("Get external references...")
        resources_set = self.get_external_file_content()

        formatted_resource_set = set()
        for resource in resources_set:
            resource = resource.replace('"', '')
            resource = resource.replace('.xbt', '.png')
            resource = resource.replace('.xbg', '.xml')
            resource = resource.replace('.tree.bin', '_trunk.xml')
            resource = join(data_path, resource)
            print resource
            formatted_resource_set.add(resource)

        objects_set = set()
        for obj in self.geometry_objects.values():
            objects_set.add(obj)
        for obj in self.texture_objects.values():
            objects_set.add(obj)

        found_objects_dict = dict()
        for obj in objects_set:
            if obj.filename in formatted_resource_set:
                self.recursive_search_items = []
                self.recursive_search(obj, "Entity", "up")
                for entity in self.recursive_search_items:
                    if entity not in found_objects_dict.keys():
                        found_objects_dict[entity] = set()
                    found_objects_dict[entity].add(obj)

        self.update_status_bar("Gathering data done, populating cells.")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in found_objects_dict.keys():
                    if entity in cell.entities:
                        for obj in found_objects_dict[entity]:
                            if obj not in cell.resources_dict.keys():
                                cell.resources_dict[obj] = set()
                            cell.resources_dict[obj].add(entity)
                            cell.resources.append(obj)

                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)

        self.update_status_bar("Finished.")
        self.create_image_output(table_to_output, "external_references_")
        self.update_view()

    def get_resource_density_by_count(self, type, direction="down", exclude_type=None, exclude_string="ThisStringIsNeverUsed"): # the weird default parameter "ThisStringIsNeverUsed" is to prevent breaking string comparaisons in certain modes
        self.update_status_bar("Get Resource density...")
        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains something else
                cell.resources_dict = dict()
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(cell, type, direction, exclude_type)
                resources = self.recursive_search_items
                count = 0
                for res in resources:
                    if res not in cell.resources:
                        if exclude_string not in res.filename:
                            count += 1
                            cell.resources.append(res)
        
        geo_instance_count_dict = {}
        for id, obj in self.geometry_objects.iteritems():
            self.progressbar_update()
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj, "Entity", "up")
            geo_instance_count_dict[obj] = len(self.recursive_search_items)
        
        value = self.convert_line_edit_text_to_int(self.UI.lineEdit_pre.text())
        
        for cell in self.world_object.world_grid.cells.values():
            cell.resources_alt = []
            for res in cell.resources:
                count = geo_instance_count_dict.get(res)
                if count <= value:
                    cell.resources_alt.append(res)
            cell.resources = cell.resources_alt
                    
        
        ###################################################
        table_to_output = []  
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1               
                total_instances += count
            table_to_output.append(table_to_output_y)
        print "--------------------------"
        print "Most amount of resources:"
        print max
        print "--------------------------"
        print "Number of populated cells:"
        print populated_cells
        print "--------------------------"
        print "Number of instances:"
        print total_instances
        print "--------------------------"
        ####################################################
        
        return table_to_output
        
    def get_interior_layer_errors(self, area_size):
        self.update_status_bar("Get interior layer errors...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                filtered_entities_list = []
                for ent in cell.entities:
                    self.recursive_search_items = []
                    self.recursive_search(ent, "World Layer", "up")
                    for wl_item in self.recursive_search_items:
                        if wl_item.type == "World Layer":
                            if wl_item.world_layer_type == "Interior" or wl_item.world_layer_type == "Sas":
                                if wl_item.area > area_size:
                                    filtered_entities_list.append(ent)
                cell.resources = filtered_entities_list
                count = len(filtered_entities_list)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "interior_layer_errors_", "binary")
        self.update_view()
        
    def get_single_LOD_asset_density(self):
        triangle_count_minimum_for_lods = 500
        all_single_lod_assets_dictionary = {}

        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                self.recursive_search_items = [] # empty the list in case it contains somthing else
                self.recursive_search(cell, "Geometry", "down", None)
                #count = 0
                for res in self.recursive_search_items:
                    if res not in cell.resources:
                        if res.is_gamex == False and res.is_speedtree == False:       
                            # Get non-zero LODs (xml data contains zeros for LOD distances, sadly, rather than doing the sensible thing and
                            # just not exporting attributes for non-existant LODs)
                            # Would probably be better to handle zeros and float conversion on reading the data, but don't really want to slow down the startup
                            lods_list = [float(Current) for Current in res.lod_distances if float(Current) != 0]

                            num_lods = len(lods_list)
                            if (num_lods == 1):
                                # Get the triangle count for this asset, assuming we don't already have it
                                lod_triangle_count = all_single_lod_assets_dictionary.get(res.filename)
                                if lod_triangle_count == None:
                                    # Re-get the geometry to get the triangle count
                                    Geometry = adp.d_geometry(res.filename, get_glm_data = True)
                                    try: # it seems that the lofts makes this crash, will investigate later, this fixes it for now
                                        all_single_lod_assets_dictionary[res.filename] = Geometry.lod_triangle_count[0]
                                    except:
                                        pass
                                        #print res.filename

                                # Only track the object if it is over the minumum triangle limit for LODs
                                if (lod_triangle_count > triangle_count_minimum_for_lods):
                                    #count += 1
                                    cell.resources.append(res)

        ###################################################
        table_to_output = []  
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1               
                total_instances += count
            table_to_output.append(table_to_output_y)
        print "--------------------------"
        print "Most amount of resources:"
        print max
        print "--------------------------"
        print "Number of populated cells:"
        print populated_cells
        print "--------------------------"
        print "Number of instances:"
        print total_instances
        print "--------------------------"
        ####################################################

        return table_to_output
        
    def get_primitive_density(self):
        self.update_status_bar("Get primitive density...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.type == "Range":
                        continue
                    if entity.is_primitive:
                        cell.resources.append(entity)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()
        
    def get_primitive_density_montreal(self):
        self.update_status_bar("Get primitive density...")
        
        regions = self.get_region_list("Montreal")
        
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.type == "Range":
                        continue
                    if entity.region not in regions:
                        continue
                    if entity.is_primitive:
                        cell.resources.append(entity)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()

    def get_occluder_density(self):
        self.update_status_bar("Get occluder density...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.entity_class == "VisibilityOcclusionBox":
                        cell.resources.append(entity)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()

    def get_plaza_density(self, area):
        self.update_status_bar("Get plaza density...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.entity_type == "Plaza":
                        if entity.shape_area < area:
                            cell.resources.append(entity)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()

    def get_plaza_kill_distance(self, plaza):
        self.recursive_search_items = []  # empty the list in case it contains somthing else
        self.recursive_search(plaza, "Geometry", "down", None)
        for geo in self.recursive_search_items:
            return int(geo.kill_distance)
        return 0

    def get_plaza_by_kill_distance(self, kill_distance):
        kill_distance = int(kill_distance)
        self.update_status_bar("Get plaza density...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.entity_type != "Plaza":
                        continue

                    plaza_kill_distance = self.get_plaza_kill_distance(entity)

                    if plaza_kill_distance > kill_distance:
                        cell.resources.append(entity)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()

    def get_building_density(self, area):
        self.update_status_bar("Get building density...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.entity_type == "Building":
                        if entity.shape_area < area:
                            cell.resources.append(entity)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()
        
    def get_building_by_volume(self, volume):
        self.update_status_bar("Get building density...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.entity_type == "Building":
                        if entity.building_volume < volume:
                            cell.resources.append(entity)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()
    
    def set_building_ideal_killdistance(self, entity, kill_distance):
        project_plane_d = 1.0/0.77 # assume a 75deg fov: tan(75.0/2) Pixels: 16 HardCoded **
        entity_killDistance = 1
        if entity.building_radius > 0:
            entity_killDistance = project_plane_d / (((math.sqrt(((kill_distance * 2) ** 2) / 3.1416)) / 1600) / entity.building_radius)                        
        #kill Distance falls closely into categories, we apply uncertainty >>
        if entity_killDistance >= 150 and entity_killDistance < 150*1.25:
            entity_killDistance = 149
        if entity_killDistance >= 256 and entity_killDistance < 256*1.25:
            entity_killDistance = 255
        if entity_killDistance >= 1024 and entity_killDistance < 1024*1.25:
            entity_killDistance = 1023
        
        entity.building_ideal_killdistance = entity_killDistance
        
    #get_building_shouldbe_faraway - far - near
    def get_building_shouldbe_cases(self, val, case ):
        self.update_status_bar("Getting buildings that should be in " + case + "loading...")
        table_to_output = []
        building_count = 0
        facade_count = 0        
        buildings_dict = {}

        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                        
                for entity in cell.entities:
                    if entity.entity_type == "Building":
                        #Only values >= 16px are used to recalculate its killDistance
                        if val > 15:
                            self.set_building_ideal_killdistance(entity, val)
                        ideal_klldistance = entity.building_ideal_killdistance
                        
                        #WLU case and should LLOD ||-->>
                        wlu_building_case = "FarAway" #Default <<
                        should_llod = True #Default <<
                        if ideal_klldistance >= 256 and ideal_klldistance < 1024:
                            wlu_building_case = "Far"
                        if ideal_klldistance >= 150 and ideal_klldistance < 256:
                            wlu_building_case = "Near"
                        if ideal_klldistance >= 0 and ideal_klldistance < 150 or self.is_badpractice_building(entity, 4) == False:
                            should_llod = False 
                        
                        #HeatMap ||-->>
                        if case == wlu_building_case and wlu_building_case != entity.building_current_WLU or case == "BadPractice" and self.is_badpractice_building(entity, val) == False :
                            cell.resources.append(entity)
                            building_count += 1
                            facade_count += entity.building_facade_count

                        #Adding to the dictionary >>
                        if wlu_building_case != entity.building_current_WLU or should_llod == False and entity.building_generatelowlod == True :
                            other_params = (entity.filename,wlu_building_case,entity.special_info,entity.building_current_WLU, str(should_llod), str(entity.building_generatelowlod))
                            buildings_dict.update({entity.guid:other_params})


                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        
        output_file = r"W:/Main/td_tools/PythonTools/DDV/resources/BuildingsToIterate.txt"
        with open(output_file, 'w') as outfile:  
            json.dump(buildings_dict, outfile)
        
        print "Buildings that are " + case + " candidates: " + str(building_count) + " Total facade count: " + str(facade_count)
       
        self.create_image_output(table_to_output, "entities_")
        self.update_view()

    def is_badpractice_building(self, entity, agressiveness):
        #CASES:
        if agressiveness == 0 : agressiveness = 1 #Division Zero safeguard        
        if entity.building_volume < agressiveness: #Simple, Volume too small <<
            return False        
        if entity.building_floor_count < agressiveness/2 and entity.building_volume < agressiveness: # Too small anyway <<
            return False
        for i in entity.building_edges_distance:
            if i < 1 and entity.building_volume < agressiveness*agressiveness: #Too flat means that is possible used as facade <<
                return False
        if entity.shape_area <= agressiveness and entity.building_height < agressiveness + agressiveness: #Buidling is used as little column/facade mosltly for deco we can get rid off it <<
            return False
        if entity.shape_area <= 1: #Building as column >> it is most likely a tall column <<
            return False
        if entity.building_height <= 1: #Building as roof >>
            return False

        return True
        
    def get_building_generating_lowres_using_interior_kit(self):
        self.update_status_bar("Get building density...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.entity_type == "Building":
                        if not entity.building_generatelowlod:
                            continue
                            
                        self.recursive_search_items = [] # empty the list in case it contains somthing else
                        self.recursive_search(entity, "Building Facade Prefab Item", "down")
                        for item in self.recursive_search_items:
                            if "int_" in item.filename: 
                                cell.resources.append(entity)
                                break
                                
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()
        
    def get_entity_density_by_world_layer_type(self, wl_type):
        self.update_status_bar("Get Entity density...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.world_layer_type == wl_type:
                        cell.resources.append(entity)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_", "binary")
        self.update_view()        
       
    def get_batched_object_density(self):
        self.update_status_bar("Get Batched Object density...")

        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.type == "Range":
                        continue
                    if entity.is_primitive:
                        continue
                    if entity.is_soundpoint:
                        continue
                    if entity.is_localcubemap:
                        continue
                    if 'catalog' in entity.filename:
                        continue
                        
                    self.recursive_search_items = [] # empty the list in case it contains somthing else
                    self.recursive_search(entity, "Archetype", "down")
                    is_skipped = False
                    for arc in self.recursive_search_items:
                        if "wd3_gameplay_ingredients" in arc.filename:
                            is_skipped = True
                        if "lighting" in arc.filename:
                            is_skipped = True
                        if "wd3_lights" in arc.filename:
                            is_skipped = True
                    if is_skipped:
                        continue
                    
                    if entity.entity_type == "BatchedObject":
                        cell.resources.append(entity)
                    if entity.entity_type == "Prefab":
                        self.recursive_search_items = [] # empty the list in case it contains somthing else
                        self.recursive_search(entity, "Prefab", "down")
                        if len(self.recursive_search_items) == 0:
                            continue
                        for prefab_entity in self.recursive_search_items[0].entities:
                            if prefab_entity.entity_type == "BatchedObject":
                                cell.resources.append(entity)
                                break # no need to continue, already found a BatchedObject and we don't want to add the entity multiple times
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "batched_objects_")
        self.update_view()
        
    def get_batched_object_density_city_block(self):
        self.update_status_bar("Get Batched Object density...")
        blocks_set = set()        
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)
        
        for block in blocks_set:
            self.progressbar_update()
            block.resources = [] # empty the list in case it contains something else
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(block, "Geometry", "down")
            resource_set = set()
            for entity in block.entities:
                if entity.type == "Range":
                    continue
                if entity.is_primitive:
                    continue
                if entity.is_soundpoint:
                    continue
                if entity.is_localcubemap:
                    continue
                if entity.entity_class == 'VisibilityOcclusionBox':
                    continue
                if 'VisibilityOcclusion' in entity.name:
                    continue
                if 'catalog' in entity.filename:
                    continue
                    
                self.recursive_search_items = [] # empty the list in case it contains somthing else
                self.recursive_search(entity, "Archetype", "down")
                is_skipped = False
                for arc in self.recursive_search_items:
                    if "wd3_gameplay_ingredients" in arc.filename:
                        is_skipped = True
                    if "lighting" in arc.filename:
                        is_skipped = True
                    if "wd3_lights" in arc.filename:
                        is_skipped = True
                    if arc.is_multistate:
                        is_skipped = True
                if is_skipped:
                    continue
                    
                if entity.entity_type == "BatchedObject":
                    #block.resources.append(entity)
                    resource_set.add(entity)
                if entity.entity_type == "Prefab":
                    self.recursive_search_items = [] # empty the list in case it contains somthing else
                    self.recursive_search(entity, "Prefab", "down")
                    if len(self.recursive_search_items) == 0:
                        continue
                    for prefab_entity in self.recursive_search_items[0].entities:
                        if prefab_entity.is_primitive:
                            continue
                        if prefab_entity.is_soundpoint:
                            continue
                        if prefab_entity.is_localcubemap:
                            continue
                        if prefab_entity.entity_type == "BatchedObject":
                            block.resources.append(entity)
                            resource_set.add(entity)
            block.resources = resource_set
        return blocks_set
       
    def get_library_density(self, obj_lib):
        self.update_status_bar("Get library items...")
        wanted_entities = []
        for item in obj_lib.lib_items_objects:
            self.recursive_search_items = [] # empty the list in case it contains somthing else
            self.recursive_search(item, "Entity", "up")
            wanted_entities += self.recursive_search_items
        
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity in wanted_entities:
                        cell.resources.append(entity)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_", "binary")
        self.update_view()
        
    def get_archetype_resource_density(self, param_archetype_class="None", check_for_multistate=False,exclude_string=["ThisStringIsNeverUsed"]): # the weird default parameter "ThisStringIsNeverUsed" is to prevent breaking string comparaisons in certain modes
        self.update_status_bar("Get Resource density...")
        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                self.recursive_search_items = [] # empty the list in case it contains somthing else
                self.recursive_search(cell, "Archetype", "down")
                resources = []
                for item in self.recursive_search_items:
                    if param_archetype_class == "None":
                        resources.append(item)
                    else:
                        if item.archetype_class == param_archetype_class:
                            if check_for_multistate == False:
                                resources.append(item)
                            else:
                                if item.is_multistate:
                                    resources.append(item)
                #resources = self.recursive_search_items
                count = 0
                for res in resources:
                    if res not in cell.resources:
                        #if exclude_string not in res.filename:
                        keep_it = True
                        for string in exclude_string:
                            if string in res.filename:
                                keep_it = False
                        if keep_it:                                
                            count += 1
                            cell.resources.append(res)

        ###################################################
        table_to_output = []  
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1               
                total_instances += count
            table_to_output.append(table_to_output_y)
        print "--------------------------"
        print "Most amount of resources:"
        print max
        print "--------------------------"
        print "Number of populated cells:"
        print populated_cells
        print "--------------------------"
        print "Number of instances:"
        print total_instances
        print "--------------------------"
        ####################################################
        
        return table_to_output

    def get_breakable_multistate_entity_density(self):
        self.update_status_bar("Get entity density...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                self.recursive_search_items = [] # empty the list in case it contains somthing else
                self.recursive_search(cell, "Archetype", "down")
                for item in self.recursive_search_items:
                    if item.archetype_class == "BreakableObject" and item.is_multistate:
                        cell.resources.append(item)

                resource_dict = self.get_resource_dict(cell)
                count = 0
                for entities in resource_dict.itervalues():
                    count += len(entities)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)

        return table_to_output
        
    def get_pink_objects_density(self):
        self.update_status_bar("Role out the Pinkifier! Or should I say... The Jamesifier!")
        
        pink_materials = []
        for mat_obj in self.material_objects.values():
            for val in mat_obj.parameters.values():
                if val == "999,0,999":
                    pink_materials.append(mat_obj)
                    break
        
        for obj_mat in pink_materials:
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj_mat, "Geometry", "up")
            for item in self.recursive_search_items:
                item.is_pink = True
        
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    #if entity.is_pink:
                    self.recursive_search_items = [] # empty the list in case it contains something else
                    self.recursive_search(entity, "Geometry", "down")
                    for item in self.recursive_search_items:
                        if item.is_pink:
                            if item not in cell.resources:
                                cell.resources.append(item)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "pink_")
        self.update_view()

    def get_pink_objects_density_city_block(self):
        self.update_status_bar("Get pink... PINK!?... Pink is the new black.")
        
        pink_materials = set()
        for mat_obj in self.material_objects.values():
            if "tag_illegal_mesh_pink_" in mat_obj.name:
                pink_materials.add(mat_obj)
                continue
            for val in mat_obj.parameters.values():
                if val == "999,0,999":
                    pink_materials.add(mat_obj)
                    break        
        for obj_mat in pink_materials:
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj_mat, "Geometry", "up")
            for item in self.recursive_search_items:
                item.is_pink = True
                
        blocks_set = set()        
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)
        
        for block in blocks_set:
            self.progressbar_update()
            block.resources = [] # empty the list in case it contains something else

            self.recursive_search_items = [] # empty the list in case it contains something else
            for entity in block.entities:
                if 'catalog' in entity.filename:
                    continue
                self.recursive_search(entity, "Geometry", "down", None, "Collection Item") # ignoring pink objects in buildings

            resource_set = set()
            for item in self.recursive_search_items:
                if not item.is_pink:
                    continue
                resource_set.add(item)
            block.resources = resource_set
        return blocks_set
        
    def get_stairs_with_no_ik_density(self):
        self.update_status_bar("Get stairs with no IK")
        
        white_list = ["facade", "pillar", "ladder", "balcony", "railing", "fence", "stairs_platform", "stairs_frame", "stairs_tarp", "stairs_railing", "col_fenchurch_under_stair_01"]
        
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    self.recursive_search_items = [] # empty the list in case it contains something else
                    self.recursive_search(entity, "Geometry", "down")
                    for geo in self.recursive_search_items:
                        if "stair" not in str(geo.name).lower():
                            if self.is_not_in_white_list(geo.filename, white_list):
                                is_ok = False
                                self.recursive_search_items = [] # empty the list in case it contains something else
                                self.recursive_search(geo, "Archetype", "up")
                                for arc in self.recursive_search_items:
                                    if arc.is_used_for_foot_ik:
                                        is_ok = True
                                if is_ok == False:
                                    if geo not in cell.resources:
                                        cell.resources.append(geo)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "pink_")
        self.update_view()
        
    def get_stairs_with_no_ik_density_city_block(self):
        self.update_status_bar("Get stairs with no IK")
        
        white_list = ["facade", "pillar", "ladder", "balcony", "railing", "fence", "stairs_platform", "stairs_frame", "stairs_tarp", "stairs_railing"]
        
        blocks_set = set()        
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)
        
        for block in blocks_set:
            self.progressbar_update()
            block.resources = [] # empty the list in case it contains something else
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(block, "Geometry", "down")
            resource_set = set()
            for item in self.recursive_search_items:
                if "stair" not in str(item.name).lower():
                    continue
                if self.is_not_in_white_list(item.filename, white_list):
                    is_ok = False
                    self.recursive_search_items = [] # empty the list in case it contains something else
                    self.recursive_search(item, "Archetype", "up")
                    for arc in self.recursive_search_items:
                        if arc.is_used_for_foot_ik:
                            is_ok = True
                    if is_ok == False:
                        resource_set.add(item)
            block.resources = resource_set
        return blocks_set
        
    def is_not_in_white_list(self, string_to_test, list_of_strings):
        for string in list_of_strings:
            if string in string_to_test:
                return False
        return True

    def find_streamoptimizer_reference(self, reference):
        for d in self.object_dictionaries:
            for obj in d.values():
                if reference in obj.filename:
                    return obj

    def get_reference_dict(self):
        reference_dict = dict()
        for geo in self.geometry_objects.values():
            reference_dict[r"{}".format(geo.filename)] = geo.identifier
        for tex in self.texture_objects.values():
            reference_dict[r"{}".format(tex.filename)] = tex.identifier
        return reference_dict

    def launch_stream_optimizer(self, file):
        self.UI.radioButton_ite.setChecked(True)
        self.stream_optimizer_object = stream_optimizer(file)
        reference_dict = self.get_reference_dict()
        for coord, cell in self.stream_optimizer_object.cells.iteritems():
            for resource_file, remove_gain in cell.resource_files.iteritems():
                if "lightprobes" in resource_file:
                    continue
                if "localcubemaps" in resource_file:
                    continue

                resource_file = join(data_path, resource_file)
                resource_file = resource_file.replace(".xbt", ".png")
                resource_file = resource_file.replace(".xbg", ".xml")
                resource_file = r"{}".format(resource_file)

                obj = self.find_something(reference_dict.get(resource_file))
                if obj is None:
                    continue

                cell.resource_objects[obj] = remove_gain
            
        self.update_status_bar("Updating Stream Optimizer Stats...")

        for entity in self.entity_objects.values():
            entity.stream_optimizer_remove_gain = 0

        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                so_cell = self.stream_optimizer_object.get_cell(x, y)
                total_cost = 0
                if so_cell is not None:
                    total_cost = so_cell.total_cost
                    cell.resources = so_cell.resource_objects.keys()
                    
                    for resource, remove_gain in so_cell.resource_objects.iteritems():
                        self.recursive_search_items = [] # empty the list in case it contains something else
                        self.recursive_search(resource, "Entity", "up")
                        for entity in self.recursive_search_items:
                            if entity in cell.entities:
                                entity.stream_optimizer_remove_gain += remove_gain
                    
                table_to_output_y.append(total_cost)
                    
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "stream_optimizer_", "stream optimizer")
        self.update_view()
    
    def get_geometry_by_kill_distance(self, kill_distance):
        self.update_status_bar("Get geometry by kill distance density...")
        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                self.recursive_search_items = [] # empty the list in case it contains somthing else
                self.recursive_search(cell, "Geometry", "down")
                for geo in self.recursive_search_items:
                    if geo not in cell.resources:
                        if geo.kill_distance > kill_distance:
                            cell.resources.append(geo)

        table_to_output = []  
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1               
                total_instances += count
            table_to_output.append(table_to_output_y)
        
        return table_to_output

    def get_geometry_by_bbox_old(self, bounding_box_volume):
        self.update_status_bar("Get geometry by kill distance density...")
        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []  # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                self.recursive_search_items = []  # empty the list in case it contains somthing else
                self.recursive_search(cell, "Geometry", "down")
                for geo in self.recursive_search_items:

                    bbox_min = geo.bbox_min.split(',')
                    bbox_max = geo.bbox_max.split(',')
                    size_x = (float(bbox_max[0]) - float(bbox_min[0])) / 100
                    size_y = (float(bbox_max[1]) - float(bbox_min[1])) / 100
                    size_z = (float(bbox_max[2]) - float(bbox_min[2])) / 100
                    current_bounding_box_volume = (size_x * size_y * size_z)

                    if current_bounding_box_volume > bounding_box_volume:

                        cell.resources.append(geo)

                        # if geo not in cell.resources_dict.keys():
                        #     cell.resources_dict[geo] = set()
                        #
                        # cell.resources_dict[geo].add(entity)

        table_to_output = []
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1
                total_instances += count
            table_to_output.append(table_to_output_y)

        return table_to_output

    def get_geometry_by_size(self, entered_value):

        self.update_status_bar("Get geometry by bounding box...")

        white_set = set([
            '0x8000000b16c1b8bd',
            '0x800000027184c16f',
            '0x800000090a616cfb',
            '0x800000027184c160',
            '0x8000000b14046da6',
            '0x800000027184c16e',
            '0x8000000b2d244faf',
            '0x8000000aefdd5921',
            '0x800000109dee900d',
            '0x800000109dee900f',
        ])
        entered_value = float(entered_value)

        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)

                cell.resources = []  # empty the list in case it contains somthing else
                cell.resources_dict = dict()

                for entity in cell.entities:

                    self.recursive_search_items = []  # empty the list in case it contains somthing else
                    self.recursive_search(entity, "Geometry", "down")
                    for geo in self.recursive_search_items:

                        if 'decals' in geo.filename:
                            continue

                        if 'oob' in geo.filename:
                            continue

                        if geo.identifier in white_set:
                            continue

                        bbox_min = geo.bbox_min.split(',')
                        bbox_max = geo.bbox_max.split(',')
                        size_x = abs((float(bbox_max[0])) + abs(float(bbox_min[0])))
                        size_y = abs((float(bbox_max[1])) + abs(float(bbox_min[1])))
                        size_z = abs((float(bbox_max[2])) + abs(float(bbox_min[2])))
                        current_bounding_box_volume = (size_x * size_y * size_z)

                        if current_bounding_box_volume > 250000.0:  # skip meshes that have their BBOX in cm rather than in m.
                            continue

                        # if current_bounding_box_volume > entered_value:
                        if size_x > entered_value or size_y > entered_value or size_z > entered_value:

                            if geo not in cell.resources_dict.keys():
                                cell.resources_dict[geo] = set()

                            cell.resources_dict[geo].add(entity)

                table_to_output_y.append(len(cell.resources_dict))
            table_to_output.append(table_to_output_y)

        return table_to_output
     
    def get_resources_compiled_size_per_cell(self):
        self.update_status_bar("Get resource compiled size per cell...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                
                cell.special_info = 0
                
                for entity in cell.entities:
                    self.recursive_search_items = []
                    self.recursive_search(entity, "Geometry", "down")
                    geometries = self.recursive_search_items
                    self.recursive_search_items = []
                    self.recursive_search(entity, "Texture", "down")
                    textures = self.recursive_search_items

                    for geo in geometries:
                        if geo.compiled_size == None:
                            geo.get_compiled_size()
                        geo.special_info = geo.compiled_size
                        entity.dependencies_compiled_size += geo.compiled_size
                        if geo not in cell.resources:                            
                            cell.resources.append(geo)
                            cell.special_info += geo.compiled_size
                        
                    for tex in textures:
                        if tex.compiled_size == None:
                            tex._texture_profiles = self.texture_profiles
                            tex.get_compiled_size()
                        tex.special_info = tex.compiled_size
                        entity.dependencies_compiled_size += tex.compiled_size
                        if tex not in cell.resources: 
                            cell.resources.append(tex)
                            cell.special_info += tex.compiled_size
                            
                table_to_output_y.append(cell.special_info)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "compiled_")
        self.update_view()
        
    def get_building_kit_numbers(self):
        self.update_status_bar("Get resource compiled size per cell...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                
                for entity in cell.entities:
                    self.recursive_search_items = []
                    self.recursive_search(entity, "Building Facade Prefab Item", "down")
                    bfpis = self.recursive_search_items

                    for bfpi in bfpis:
                        if bfpi.parent_object not in cell.resources_dict.keys():
                            cell.resources_dict[bfpi.parent_object] = []
                        if entity not in cell.resources_dict[bfpi.parent_object]:
                            cell.resources_dict[bfpi.parent_object].append(entity)
                            #cell.resources.append(bfpi.parent_object)                       
 
                table_to_output_y.append(len(cell.resources_dict))
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "kit_number_", "building_kits")
        self.update_view()
        
    def set_building_kit_points(self):
        buildingkitpoints_file = cur_path + r"\resources\buildingkitpoints.xml"
        tree = ET.ElementTree(file=buildingkitpoints_file)
        
        building_kit_points_dict = {}
        for elem in tree.iter("buildingkit"):
            building_kit_points_dict[elem.get("name")] = elem.get("points"), elem.get("group")
            
        for bfp in self.building_facade_prefab_libraries_objects.values():
            name = bfp.name.lower()
            values = building_kit_points_dict.get(name)
            if values is not None:
                bfp.points = float(values[0])
                bfp.group  = values[1]
            bfp.special_info = str(bfp.points)
            if bfp.special_info == "100":
                bfp.special_info = "ILLEGAL = 100"

    def get_building_kit_points(self):
        self.update_status_bar("Get building kit points...")
        
        self.set_building_kit_points()
        
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                
                bfpi_list = []
                cell.points = 0
                cell.points_compensated = 0
                
                for entity in cell.entities:
                    if entity.world_layer_type != "Normal": 
                        continue
                    self.recursive_search_items = []
                    self.recursive_search(entity, "Building Facade Prefab Item", "down")
                    bfpi_list += self.recursive_search_items
                    
                    for bfpi in self.recursive_search_items:
                        if bfpi.parent_object not in cell.resources_dict.keys():
                            cell.resources_dict[bfpi.parent_object] = []
                        if entity not in cell.resources_dict[bfpi.parent_object]:
                            cell.resources_dict[bfpi.parent_object].append(entity)
                    
                bfps = set()
                for bfpi in bfpi_list:
                    bfps.add(bfpi.parent_object)
                    
                bfp_groups = {}
                for bfp in bfps:
                    cell.points += bfp.points
                    bfp_groups[bfp.group] = bfp

                for group, bfp in bfp_groups.iteritems():
                    cell.points_compensated += bfp.points
                
                cell.points = int(cell.points + 0.5)
                
                cell.points_compensated = int(cell.points_compensated + 0.5)

                table_to_output_y.append(cell.points_compensated)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "kit_number_", "building_kits_points")
        self.update_view()
        
    def get_building_kit_memory(self):
        self.update_status_bar("Get resource compiled size per cell...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                
                cell.special_info = 0
                
                for entity in cell.entities:
                    self.recursive_search_items = []
                    self.recursive_search(entity, "Geometry", "down")
                    geometries = self.recursive_search_items
                    self.recursive_search_items = []
                    self.recursive_search(entity, "Texture", "down")
                    textures = self.recursive_search_items

                    for geo in geometries:
                        if "hard_mesh" in geo.filename:
                            continue
                        if "geometry" in geo.filename and "building_kit" in geo.filename:
                            if geo.compiled_size == None:
                                geo.get_compiled_size()
                            geo.special_info = geo.compiled_size
                            entity.dependencies_compiled_size += geo.compiled_size
                            if geo not in cell.resources:                            
                                cell.resources.append(geo)
                                cell.special_info += geo.compiled_size
                        
                    for tex in textures:
                        if "hard_mesh" in tex.filename:
                            continue
                        if "geometry" in tex.filename and "building_kit" in tex.filename:
                            if tex.compiled_size == None:
                                tex.get_compiled_size()
                            tex.special_info = tex.compiled_size
                            entity.dependencies_compiled_size += tex.compiled_size
                            if tex not in cell.resources: 
                                cell.resources.append(tex)
                                cell.special_info += tex.compiled_size
                            
                table_to_output_y.append(cell.special_info)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "compiled_", "building_memory")
        self.update_view()

    def get_component_add_to_world_cost(self):
        add_to_world_cost_file = join(dirname(__file__), "resources/Component_AddToWorld_Cost.txt")
        add_to_world_cost = {}
        opened_file = open(add_to_world_cost_file, "r")
        for line in opened_file:
            line_list = line.replace("\n", "").split("\t")
            add_to_world_cost[line_list[0].lower()] = float(line_list[1])
        opened_file.close()
        return add_to_world_cost

    def get_graphic_components_overrides(self):
        file_driver = join(data_path, r'engine\Driver.entityregistry.xml')
        file_engine = join(data_path, r'engine\Engine.entityregistry.xml')
        graphic_components_dict = dict()

        def parse_file(file_to_parse):
            tree = ET.ElementTree(file=file_to_parse)
            for class_elem in tree.iter('Class'):
                for component_elem in class_elem.iter('CGraphicComponent'):
                    override = component_elem.get('hidOverwriteComponentClassName', None)
                    if override is None:
                        continue
                    graphic_components_dict[class_elem.get('Name')] = override

        parse_file(file_driver)
        parse_file(file_engine)
        return graphic_components_dict

    def swap_graphic_component(self, graphic_components_overrides_dict, component, d_class):
        if not d_class:
            return component
        if component != 'CGraphicComponent':
            return component
        return graphic_components_overrides_dict.get(d_class, component)

    def recursive_search_spawning_cost(self, search_item, item_type, entity_types_to_ignore, search_list):
        # print search_item.type, search_item.name, search_item.identifier
        # print search_item._children
        # print '-'*60

        for child in search_item._children.keys():

            if child.identifier == search_item.identifier:
                print "I'm my own child!! " + child.name
                continue

            if child.type == 'Proxy': # If item is a proxy containing a batchedobject, bail out.
                if child.proxy_type == 'geometry' or child.proxy_type == 'archetype':
                    continue

            if child.type == 'Entity' or child.type == 'Prefab Entity':
                if child.entity_type in entity_types_to_ignore:  #  == 'BatchedObject':  # If item is a batchedobject (in a prefab), bail out.
                    continue

            if child.type == item_type:
                search_list.append(child)
            self.recursive_search_spawning_cost(child, item_type, entity_types_to_ignore, search_list)

    def get_spawning_cost(self):
        self.update_status_bar("Getting spawning costs... for real.")

        add_to_world_cost_dict = self.get_component_add_to_world_cost()
        graphic_components_overrides_dict = self.get_graphic_components_overrides()
        entity_types_to_ignore = {'EnticerVehicle', 'BatchedObject', 'CityLifeObject'}

        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                cell.special_info = 0

                for entity in cell.entities:

                    # if entity.guid.lower() != "{7977d83a-2a69-4075-bae2-bfdb97ab9f11}":
                    #     continue

                    component_list = []

                    entity.special_info = None  # Reset the spawning cost
                    entity.loading_cost = None  # Reset the spawning cost

                    if entity.entity_type in entity_types_to_ignore:
                        continue

                    if entity.world_layer_type != "Normal":
                        continue

                    wlu_categories_to_skip = '0', '1', '2', '4', '5', '6', '7', '10', '11', '15'  # must not contain 3, as it is "Near"
                    # if entity.wlu_category is not None:
                    if entity.wlu_category != 'None':
                        if entity.wlu_category in wlu_categories_to_skip:
                            continue

                    entity.special_info = 0  # Set the spawning cost to 0 to add it up later
                    entity.loading_cost = 0  # Set the spawning cost to 0 to add it up later

                    for component in entity.components:
                        component = self.swap_graphic_component(graphic_components_overrides_dict, component, entity.entity_class)
                        component_cost = add_to_world_cost_dict.get(component.lower(), 0)
                        entity.loading_cost += component_cost
                        entity.special_info += component_cost
                        cell.special_info += component_cost
                        component_list.append((entity.name, component))

                    archetype_list = list()
                    self.recursive_search_spawning_cost(entity, "Archetype", entity_types_to_ignore, archetype_list)

                    for archetype in archetype_list:
                        for component in archetype.components:
                            component = self.swap_graphic_component(graphic_components_overrides_dict, component, archetype.archetype_class)
                            component_cost = add_to_world_cost_dict.get(component.lower(), 0)
                            entity.loading_cost += component_cost
                            entity.special_info += component_cost
                            cell.special_info += component_cost
                            component_list.append((archetype.name, component))

                    if entity.entity_type == 'Prefab':
                        # for prefab in entity._children:
                        #     for prefab_entity in prefab._children:
                        self.recursive_search_items = []  # empty the list in case it contains something else
                        self.recursive_search(entity, "Prefab Entity", "down")
                        for prefab_entity in self.recursive_search_items:
                            # if prefab_entity.type != 'Prefab Entity':
                            #     continue
                            # if prefab_entity.entity_type != 'Entity':
                            #     continue
                            if prefab_entity.entity_type in entity_types_to_ignore:
                                continue
                            if prefab_entity.wlu_category != 'None':
                                if prefab_entity.wlu_category in wlu_categories_to_skip:
                                    continue
                            for component in prefab_entity.components:
                                component = self.swap_graphic_component(graphic_components_overrides_dict, component, prefab_entity.entity_class)
                                component_cost = add_to_world_cost_dict.get(component.lower(), 0)
                                entity.loading_cost += component_cost
                                entity.special_info += component_cost
                                cell.special_info += component_cost
                                component_list.append((prefab_entity.name, component))

                    if entity.special_info == 0:
                        continue

                    # DEBUG
                    if entity.guid.lower() == "{8f7d979c-18f3-412f-8727-1cc43e3383d6}":
                        print 'Start debug'
                        entity_component_cost = 0
                        file_path = join(dirname(abspath(__file__)), 'debug.log')
                        debug_output_file = open(file_path, "w+")
                        for stuff in component_list:
                            name = stuff[0]
                            component = stuff[1]
                            component_cost = add_to_world_cost_dict.get(component.lower(), 0)
                            entity_component_cost += component_cost
                            line = name + '\t' + '"' + component + '"' + '\t' + str(component_cost) + '\n'
                            debug_output_file.write(line)
                        # for arc in archetype_list:
                        #     debug_output_file.write(arc.name + '\n')
                        #     for comp in arc.components:
                        #         cost = add_to_world_cost_dict.get(comp.lower(), 0)
                        #         info = [comp, str(cost), '\n']
                        #         line = ', '.join(info)
                        #         debug_output_file.write(line)
                        #     debug_output_file.write(('-'*60) + '\n')
                        debug_output_file.close()
                        print entity_component_cost
                        print 'End debug'
                    # END DEBUG

                    cell.resources.append(entity)
                table_to_output_y.append(cell.special_info)
            table_to_output.append(table_to_output_y)

        return table_to_output

    def get_loading_rings(self): # DEPRECATED, needs to be replaced
        self.update_status_bar("Get spawning costs...")
        
        # patch to reset the entities in case the function is called multiple times
        entity_set = set()
        for entity in self.entity_objects.values():
            entity_set.add(entity)
            
        for entity in entity_set:
            # entity.wlu_category = "None"
            entity.components_prefab = []
            entity.special_info = None
            entity.loading_cost = None

        #Loading loading stats
        addtoworld_cost_file = join(dirname(__file__), "resources/Component_AddToWorld_Cost.txt")
        addtoworld_cost = {}

        opened_file = open(addtoworld_cost_file, "r")

        for line in opened_file:
            line_list = line.replace("\n", "").split("\t")
            addtoworld_cost[line_list[0]] = float(line_list[1])

        opened_file.close()

        #scan all cells only one time
        temp_ressources = [] #3D array, X, Y, Ressources

        for x in self.world_object.grid_range:
            temp_ressources.append([])
            for y in self.world_object.grid_range:
                temp_ressources[x-1].append([])
                temp_ressources[x-1][y-1] = []

                cell = self.world_object.get_cell(x, y)

                self.recursive_search_items = []  # empty the list in case it contains something else
                self.recursive_search(cell, "Entity", "down")

                search_result_backup = []
                for i in self.recursive_search_items:
                    search_result_backup.append(i)

                for item in search_result_backup:
                    if item.world_layer_type != "Normal": #Ignore hma,lma and the likes
                        continue

                    # Unbatched archetypes
                    if item.entity_type == "PrototypeEntity":

                        self.recursive_search_items = []  # empty the list in case it contains somthing else
                        self.recursive_search(item, "Archetype", "down")

                        if len(self.recursive_search_items) > 0:

                            wlucat = self.recursive_search_items[0].wlu_category #Can a prototype entity reference more than one archetype??

                            item.wlu_category = wlucat #Write it into this specific entity, for display in tree

                            item.components = self.recursive_search_items[0].components

                            #if wlucat == "2" or wlucat == "3":  # Near or far
                            if wlucat == "3":  # Near
                                temp_ressources[x - 1][y - 1].append(item)

                    # Unbatched geometries
                    #if item.wlu_category == "2" or item.wlu_category == "3":  # Near or far
                    elif item.wlu_category == "3":  # Near
                        temp_ressources[x-1][y-1].append(item)                        

                    # Prefabs and Proxy
                    elif item.entity_type == "Prefab" or item.entity_type == "Proxy":

                        self.recursive_search_items = []  # empty the list in case it contains somthing else
                        self.recursive_search(item, "Prefab Entity", "down")

                        if len(self.recursive_search_items) > 0:

                            entity_search_result = []
                            for i in self.recursive_search_items:
                                entity_search_result.append(i)

                            for ent in entity_search_result:
                                # Unbatched archetypes
                                if ent.entity_type == "PrototypeEntity":

                                    self.recursive_search_items = []  # empty the list in case it contains somthing else
                                    self.recursive_search(ent, "Archetype", "down")

                                    if len(self.recursive_search_items) > 0:

                                        wlucat = self.recursive_search_items[0].wlu_category  # Can a prototype entity reference more than one archetype??

                                        ent.wlu_category = wlucat  # Write it into this specific entity, for display in tree

                                        if len(ent.components) == 0: #Several archetypes will be used more than once
                                            ent.components = self.recursive_search_items[0].components

                                        # if wlucat == "2" or wlucat == "3":  # Near or far
                                        if wlucat == "3":  # Near
                                            for comp in ent.components:
                                                item.components_prefab.append(comp)

                                # Unbatched geometries
                                # if item.wlu_category == "2" or item.wlu_category == "3":  # Near or far
                                elif ent.wlu_category == "3":  # Near
                                    for comp in ent.components:
                                        item.components_prefab.append(comp)

                            if len(item.components) > 0:
                                temp_ressources[x - 1][y - 1].append(item)

        # compute loading cost
        for x in temp_ressources:
            for y in x:
                for z in y:
                    z.loading_cost = 0
                    for comp in z.components:
                        cost = addtoworld_cost.get(comp)
                        if cost:
                            z.loading_cost += cost
                    for comp in z.components_prefab:
                        cost = addtoworld_cost.get(comp)
                        if cost:
                            z.loading_cost += cost
                    z.special_info = z.loading_cost

        '''
        loading_ring = [(-1, 1), (0, 1), (1, 1),
                        (-1, 0), (0, 0), (1, 0),
                        (-1, -1), (0, -1), (1, -1)]

        loading_ring = [(-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2),
                        (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1),
                        (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
                        (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1),
                        (-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2)]

        loading_ring = [(-1, 2), (0, 2), (1, 2), (2, 2),
                        (-1, 1), (0, 1), (1, 1), (2, 1),
                        (-1, 0), (0, 0), (1, 0), (2, 0),
                        (-1, -1), (0, -1), (1, -1), (2, -1)]

        '''

        loading_ring = [(0, 0)]

        entity_class_to_ignore = ["DebugAnnotationTextEntity",
                                  "GraphicTestPhotographerEntity"]

        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:

                cell = self.world_object.get_cell(x, y)
                cell.resources = []  # empty the list in case it contains something else
                cell.resources_dict = dict()

                for z in loading_ring:
                    new_x = x - z[0]
                    if new_x < 1 or new_x > self.world_object.cell_count:
                        continue

                    new_y = y - z[1]
                    if new_y < 1 or new_y > self.world_object.cell_count:
                        continue

                    for item in temp_ressources[new_x-1][new_y-1]:
                        if item.entity_class in entity_class_to_ignore:
                            continue

                        cell.resources.append(item)

        ###################################################
        table_to_output = []
        max = 0
        populated_cells = 0
        total_instances = 0
        above1000 = 0
        above800 = 0
        above600 = 0
        above400 = 0
        above200 = 0
        above100 = 0
        above50 = 0
        above20 = 0
        above10 = 0
        above0 = 0

        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)

                count = 0

                for i in cell.resources:
                    count += i.loading_cost

                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1
                total_instances += count

                if count > 25000:
                    above1000 += 1
                elif count > 20000:
                    above800 += 1
                elif count > 15000:
                    above600 += 1
                elif count > 10000:
                    above400 += 1
                elif count > 7500:
                    above200 += 1
                elif count > 5000:
                    above100 += 1
                elif count > 2500:
                    above50 += 1
                elif count > 1000:
                    above20 += 1
                else:
                    above0 += 1

            table_to_output.append(table_to_output_y)
        print "--------------------------"
        print "Most amount of resources:"
        print max
        print "--------------------------"
        print "Number of populated cells:"
        print populated_cells
        print "--------------------------"
        print "Number of instances:"
        print total_instances
        print "--------------------------"
        print "Average unbatched entities:"
        if populated_cells > 0:
            print str(float(total_instances) / populated_cells)
        else:
            print "0"
        print "--------------------------"
        print "Number of cells above...:"
        print "25000: " + str(above1000)
        print "20000: " + str(above800)
        print "15000: " + str(above600)
        print "10000: " + str(above400)
        print " 7500: " + str(above200)
        print " 5000: " + str(above100)
        print " 2500: " + str(above50)
        print " 1000: " + str(above20)
        print "    0: " + str(above0)
        print "--------------------------"
        ####################################################

        return table_to_output

    def get_entity_by_class(self):
        entity_set = set()
        for entity in self.entity_objects.values():
            entity_set.add(entity)

        output_dict = {}
        for entity in entity_set:
        
            if entity.entity_type == "Prefab":
                self.recursive_search_items = []
                self.recursive_search(entity, "Prefab Entity", "down")
                prefab_entities = self.recursive_search_items
                
                for prefab_entity in prefab_entities:
                    if prefab_entity.entity_class not in output_dict.keys():
                        output_dict[prefab_entity.entity_class] = 0
                        
                    output_dict[prefab_entity.entity_class] += 1
                    
            if entity.entity_class == "":
                continue
            
            if entity.entity_class not in output_dict.keys():
                output_dict[entity.entity_class] = 0              
            output_dict[entity.entity_class] += 1
            
        for k,v in output_dict.iteritems():
            print k,v
        
        try:
            threshold = int(self.UI.lineEdit_pre.text())
        except:
            self.update_status_bar("Bad value entered in Entity By Number Of Class Instances.")
        
        table_to_output = []        
        for y in self.world_object.grid_range:
            table_to_output_y = []
            self.progressbar_update()            
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                
                entity_classes_dict = {}
                for entity in cell.entities:
                    
                    if entity.entity_type == "Prefab":
                        self.recursive_search_items = []
                        self.recursive_search(entity, "Prefab Entity", "down")
                        prefab_entities = self.recursive_search_items
                        for prefab_entity in prefab_entities:
                            if prefab_entity.entity_class == "":
                                continue
                            if prefab_entity.entity_class not in entity_classes_dict.keys():
                                entity_classes_dict[prefab_entity.entity_class] = set()
                            entity_classes_dict[prefab_entity.entity_class].add(prefab_entity)
                            
                    if entity.entity_class == "":
                        continue
                    
                    if entity.entity_class not in entity_classes_dict.keys():
                        entity_classes_dict[entity.entity_class] = set()
                        
                    entity_classes_dict[entity.entity_class].add(entity)
                    
                for entity_class, entity_set in entity_classes_dict.iteritems():
                    if len(entity_set) > threshold:
                        for ent in entity_set:
                            ent.special_info = ent.entity_class
                            cell.resources.append(ent)
                        
                
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                
            table_to_output.append(table_to_output_y)

        self.create_image_output(table_to_output, "entities_")
        self.update_view()
    
    def get_geometry_with_no_jira(self):
        if len(self.jira_ob_issues) == 0:
            self.get_geometry_status_from_jira()
        
        self.update_status_bar("Get geometry with no JIRA...")
        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                self.recursive_search_items = [] # empty the list in case it contains somthing else
                self.recursive_search(cell, "Geometry", "down")
                for geo in self.recursive_search_items:
                    if geo.is_facade:
                        continue
                    if geo.jira_issue is not None:
                        continue
                    if "metrics" in geo.filename:
                        continue
                    if "leveldesign" in geo.filename:
                        continue
                    if "vehicles_nexus" in geo.filename:
                        continue
                    if "vegetation" in geo.filename:
                        continue
                    if geo not in cell.resources:
                        cell.resources.append(geo)
                            
        ###################################################
        table_to_output = []  
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1               
                total_instances += count
            table_to_output.append(table_to_output_y)
        print "--------------------------"
        print "Most amount of resources:"
        print max
        print "--------------------------"
        print "Number of populated cells:"
        print populated_cells
        print "--------------------------"
        print "Number of instances:"
        print total_instances
        print "--------------------------"
        ####################################################
        
        return table_to_output
      
    def get_geometry_with_no_jira_city_block(self):
        if len(self.jira_ob_issues) == 0:
            self.get_geometry_status_from_jira()
        
        self.update_status_bar("Get geometry with no JIRA...")
        blocks_set = set()        
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)
        
        for block in blocks_set:
            self.progressbar_update()
            block.resources = set() # empty the list in case it contains something else
            for entity in block.entities:
                if "catalog" in entity.filename:
                    continue
                if entity.entity_type == "Plaza":
                    continue
                if entity.entity_type == "Range":
                    continue
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(entity, "Geometry", "down", "Plaza", "Range")
                resource_set = set()
                for item in self.recursive_search_items:
                    if item.is_facade:
                        continue
                    if item.jira_issue is not None:
                        continue
                    if "metrics" in item.filename:
                        continue
                    if "leveldesign" in item.filename:
                        continue
                    if "vehicles_nexus" in item.filename:
                        continue
                    if "vegetation" in item.filename:
                        continue
                    resource_set.add(item)
                block.resources = block.resources.union(resource_set)
        return blocks_set
        
    def get_geometry_with_no_jira_propscatalogs_city_block(self):
        if len(self.jira_ob_issues) == 0:
            self.get_geometry_status_from_jira()
        
        self.update_status_bar("Get geometry with no JIRA...")
        blocks_set = set()        
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)
        
        for block in blocks_set:
            self.progressbar_update()
            block.resources = set() # empty the list in case it contains something else
            for entity in block.entities:
                if "catalog" not in entity.filename:
                    continue
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(entity, "Geometry", "down", "Plaza", "Range")
                resource_set = set()
                for item in self.recursive_search_items:
                    if item.is_facade:
                        continue
                    if item.jira_issue is not None:
                        continue
                    if "metrics" in item.filename:
                        continue
                    if "leveldesign" in item.filename:
                        continue
                    if "vehicles_nexus" in item.filename:
                        continue
                    if "vegetation" in item.filename:
                        continue
                    resource_set.add(item)
                block.resources = block.resources.union(resource_set)
        return blocks_set
        
    def get_geometry_from_bvi_used_in_london(self):
   
        self.update_status_bar("Get geometry from BVI used in London...")
        blocks_set = set()        
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)
        
        for block in blocks_set:
            self.progressbar_update()
            block.resources = [] # empty the list in case it contains something else
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(block, "Geometry", "down")
            resource_set = set()
            for item in self.recursive_search_items:
                if "bvi" not in item.filename:
                    continue
                resource_set.add(item)
            block.resources = resource_set
        return blocks_set
        
    def get_geometry_with_uncertain_lod_distances(self, type):
        self.update_status_bar("Get geometry with uncertain LOD distances...")
        table_to_output = []
        
        high_quality = 64
        near = 256
        low_quality = 383
        far = 1024
        uncertainty = 1.25
        
        bad_range = None
        
        if type == 1:  
            bad_range = range(high_quality,int(high_quality*uncertainty))
        if type == 2:        
            bad_range = range(near,int(near*uncertainty))
        if type == 3:
            bad_range = range(low_quality,int(low_quality*uncertainty))
        if type == 4:
            bad_range = range(far,int(far*uncertainty))
        
        for y in self.world_object.grid_range:
            table_to_output_y = []
            self.progressbar_update()
            
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                
                for entity in cell.entities:
                    if entity.world_layer_type != "Normal":
                        continue
                    self.recursive_search_items = [] # empty the list in case it contains somthing else
                    self.recursive_search(entity, "Geometry", "down")
                    
                    for geo in self.recursive_search_items:
                        if geo not in cell.resources:
                            
                            if type == 1 or type == 3: # test LOD values, but not the kill distance
                                for distance in geo.lod_distances[:-1]: # skipping kill distance
                                    i_distance = int(float(distance))
                                    if i_distance in bad_range:
                                        cell.resources.append(geo)
                                        
                            if type == 2 or type == 4:
                                if int(float(geo.kill_distance)) in bad_range:
                                    cell.resources.append(geo)
                
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                
            table_to_output.append(table_to_output_y)

        self.create_image_output(table_to_output, "geometry_")
        self.update_view()

    def get_geometry_in_unbatched_entity(self):
    
        self.update_status_bar("Get geometry in unbatched entity...")
        blocks_set = set()
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)
        
        for block in blocks_set:
            self.progressbar_update()
            block.resources = [] # empty the list in case it contains something else
            for entity in block.entities:
                
                # if entity.entity_type == "Proxy":
                    # continue
                # if entity.entity_type == "Prefab":
                    # continue
                # if entity.entity_type == "BatchedObject":
                    # continue
                # if entity.entity_type == "Plaze":
                    # continue
                # if entity.entity_type == "CityLocation":
                    # continue
                # if entity.entity_type == "Building":
                    # continue
                # if entity.entity_type == "EnticerVehicle":
                    # continue
                if entity.entity_type == "Entity" or entity.entity_type == "PrototypeEntity":
                    self.recursive_search_items = [] # empty the list in case it contains something else
                    self.recursive_search(entity, "Geometry", "down")
                    resource_set = set()
                    for item in self.recursive_search_items:
                        resource_set.add(item)
                    block.resources = resource_set
        return blocks_set

    #  WIP
    def get_instances_with_physics(self):
        self.update_status_bar("Getting Instances With Physics")

        geo_set = set()

        for geo in self.geometry_objects.values():
            geo_set.add(geo)

        instances_set = set()
        for geo in geo_set:
            if not geo.has_physics:
                continue
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(geo, "Entity", "up")
            for entity in self.recursive_search_items:
                if entity.entity_type == "Prefab":
                    continue
                instances_set.add(entity)

            self.recursive_search_items = []  # empty the list in case it contains something else
            self.recursive_search(geo, "Prefab Entity", "up")
            for entity in self.recursive_search_items:
                if entity.entity_type == "Prefab":
                    continue
                instances_set.add(entity)

    def generate_table_result(self, result_set):
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    #if entity.is_pink:
                    self.recursive_search_items = [] # empty the list in case it contains something else
                    self.recursive_search(entity, "Geometry", "down")
                    for item in self.recursive_search_items:
                        if item.is_pink:
                            if item not in cell.resources:
                                cell.resources.append(item)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "pink_")
        self.update_view()


    def get_clo_lib_names(self):
        names = []
        for obj in self.generic_libraries_objects.values():
            if obj.isCLO():
                names.append(obj.name)
        names.sort()
        return names
    
    def get_facades_not_in_buildings(self):
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.entity_type == "Building":
                        continue
                    
                    if entity.entity_type == "Prefab":
                        prefab = self.prefab_item_objects[entity.resource]
                        for prefab_entity in prefab.entities:
                            if prefab_entity.entity_type == "Building":
                                continue
                            self.recursive_search_items = [] # empty the list in case it contains something else
                            self.recursive_search(prefab_entity, "Geometry", "down")
                            for item in self.recursive_search_items:
                                if item.is_facade:
                                    if item not in cell.resources:
                                        cell.resources.append(item)
                        continue
                                
                    self.recursive_search_items = [] # empty the list in case it contains something else
                    self.recursive_search(entity, "Geometry", "down")
                    for item in self.recursive_search_items:
                        if item.is_facade:
                            if item not in cell.resources:
                                cell.resources.append(item)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "facade_")
        self.update_view()
        
    def get_facades_not_in_buildings_city_block(self):
        self.update_status_bar("Facade not in building...")
        blocks_set = set()        
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)
        
        for block in blocks_set:
            self.progressbar_update()
            block.resources = [] # empty the list in case it contains something else
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(block, "Geometry", "down")
            resource_set = set()
            for entity in block.entities:
                if entity.entity_type == "Building":
                    continue
                
                if entity.entity_type == "Prefab":
                    try:
                        prefab = self.prefab_item_objects[entity.resource]
                    except:
                        continue
                    for prefab_entity in prefab.entities:
                        if prefab_entity.entity_type == "Building":
                            continue
                        self.recursive_search_items = [] # empty the list in case it contains something else
                        self.recursive_search(prefab_entity, "Geometry", "down")
                        for item in self.recursive_search_items:
                            if item.is_facade:
                                if item not in block.resources:
                                    resource_set.add(item)
                    continue
                            
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(entity, "Geometry", "down")
                for item in self.recursive_search_items:
                    if item.is_facade:
                        if item not in block.resources:
                            resource_set.add(item)
            block.resources = resource_set
        return blocks_set
    
    def get_geometry_by_jira_filter(self):
        if len(self.jira_ob_issues) == 0:
            self.get_geometry_status_from_jira()
            
        search_string = self.UI.lineEdit_pre.text()
        
        if search_string == "":
            self.update_status_bar('Please enter a filter and separate items with "|".')
            return
            
        tokens = search_string.split("|")
        
        self.update_status_bar("Get geometry by JIRA filter...")
        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                self.recursive_search_items = [] # empty the list in case it contains somthing else
                self.recursive_search(cell, "Geometry", "down")
                for geo in self.recursive_search_items:
                    # if "metrics" in geo.filename:
                        # continue
                    # if geo.is_facade:
                        # continue

                    found = 0
                    for k, v in geo.__dict__.iteritems():
                        if v == None:
                            continue
                        if "jira" in k:                            
                            for t in tokens:
                                if t.lower() == v.lower():
                                    found += 1
                                    
                    if found < len(tokens):
                        continue                            
                        
                    if geo not in cell.resources:
                        cell.resources.append(geo)
                            
        ###################################################
        table_to_output = []  
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1               
                total_instances += count
            table_to_output.append(table_to_output_y)
        print "--------------------------"
        print "Most amount of resources:"
        print max
        print "--------------------------"
        print "Number of populated cells:"
        print populated_cells
        print "--------------------------"
        print "Number of instances:"
        print total_instances
        print "--------------------------"
        ####################################################
        
        return table_to_output
    
    def get_data_from_atlas_layer(self, xml_file):
        output_dict = {}    
        tree = ET.ElementTree(file=xml_file)
        for elem in tree.iter("entity"):
            w = 0
            h = 0            
            for sub_elem in elem.iter("symbol"):
                w = float(sub_elem.get("width"))
                h = float(sub_elem.get("height"))
            position = elem.get("position")
            position_split = position.split(",")
            position_tup = float(position_split[0]), float(position_split[1])
            text = elem.get("text")
            output_dict[text] = position_tup
        return output_dict
    
    def transfer_jira_status_from_geometry_to_proxy(self, geo_set):
        for geo in geo_set:
            self.recursive_search_items = []
            self.recursive_search(geo, "Proxy", "up")
            proxies = self.recursive_search_items
            
            for proxy in proxies:
                if proxy.jira_issue == "ILLEGAL": # Certain proxies need to be set ILLEGAL because some reference prefabs that contain illegal geometries.
                    continue
                if geo.jira_issue is None:
                    proxy.jira_issue = "ILLEGAL"
                    continue
                if geo.jira_status == "Deleted Request":
                    proxy.jira_issue = "ILLEGAL"
                    continue
                if geo.jira_status == "Request Denied":
                    proxy.jira_issue = "ILLEGAL"
                    continue
                if geo.jira_status == "Deleted Prototype":
                    proxy.jira_issue = "ILLEGAL"
                    continue
                if geo.jira_status == "Mock-up Request":
                    proxy.jira_issue = "ILLEGAL"
                    continue
  
                proxy.jira_issue = geo.jira_issue
                proxy.jira_status = geo.jira_status
                proxy.jira_studio = geo.jira_studio
                proxy.jira_loq = geo.jira_loq
                proxy.jira_borough = geo.jira_borough
    
    def get_proxy_in_legal_folder_not_tracked(self):
        geo_set = set()
        for geo in self.geometry_objects.values():
            geo_set.add(geo)
        if not self.link_geometry_to_jira_issue():
            return []
        self.update_status_bar("Get Proxy In Legal Folder Not Tracked.")
        self.transfer_jira_status_from_geometry_to_proxy(geo_set)
        
        white_list = ["geometry", "character_props", "gameplay_ingredients", "gfx", "lights"]
        
        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                self.recursive_search_items = []
                self.recursive_search(cell, "Proxy", "down")
                proxies = self.recursive_search_items
                for proxy in proxies:
                    is_not_in_white_list = self.is_not_in_white_list(proxy.filename.lower(), white_list)
                    if is_not_in_white_list:
                        continue
                    # if "_geometries" in geo.filename:
                        # continue
                    # if "_texture" in geo.filename:
                        # continue
                    # if "Characters" in geo.filename:
                        # continue
                    # if "Cinematics" in geo.filename:
                        # continue
                    # if "loft" in geo.filename:
                        # continue
                    # if "Metrics" in geo.filename:
                        # continue
                    # if "Tech" in geo.filename:
                        # continue
                    # if "techart" in geo.filename:
                        # continue
                    # if "Test" in geo.filename:
                        # continue
                    if proxy.jira_issue == "ILLEGAL":                        
                        if proxy not in cell.resources:
                            cell.resources.append(proxy)
                            
        ###################################################
        table_to_output = []  
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1               
                total_instances += count
            table_to_output.append(table_to_output_y)
        print "--------------------------"
        print "Most amount of resources:"
        print max
        print "--------------------------"
        print "Number of populated cells:"
        print populated_cells
        print "--------------------------"
        print "Number of instances:"
        print total_instances
        print "--------------------------"
        ####################################################
        
        return table_to_output
    
    def get_archetype_with_animation_component(self): # DEPRECATED
        self.update_status_bar("Archetypes instances with animation component...")
        
        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                self.recursive_search_items = [] # empty the list in case it contains somthing else
                self.recursive_search(cell, "Archetype", "down")
                for item in self.recursive_search_items:
                    if not item.has_animated_component:
                        continue
                    if "wd3_gameplay_ingredients" in item.filename:
                        continue
                    if "wd3_cityactivities" in item.filename:
                        continue
                    if "prefab_setup" in item.filename:
                        continue
                    if "vehicle_" in item.filename:
                        continue
                    cell.resources.append(item)

        table_to_output = []  
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1               
                total_instances += count
            table_to_output.append(table_to_output_y)
        
        return table_to_output
        
    def get_archetype_with_animation_component_city_block(self):
        self.update_status_bar("Archetypes instances with animation component...")
        
        blocks_set = set()        
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)
        
        for block in blocks_set:
            self.progressbar_update()
            block.resources = set() # empty the list in case it contains something else
            for entity in block.entities:
            
                if entity.world_layer_type == "LMA":
                    continue
                if entity.world_layer_type == "HMA":
                    continue
                if entity.world_layer_type == "Mission":
                    continue
            
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(entity, "Archetype", "down")
                resource_set = set()
                for item in self.recursive_search_items:
                    if not item.has_animated_component:
                        continue
                    if "wd3_gameplay_ingredients" in item.filename:
                        continue
                    if "wd3_cityactivities" in item.filename:
                        continue
                    if "prefab_setup" in item.filename:
                        continue
                    if "vehicle" in item.filename:
                        continue
                    if "wd3_op_ingredients" in item.filename:
                        continue
                    if "wd3_tropes_ingredients" in item.filename:
                        continue
                    if "wd3_tropes_ingredients_tor" in item.filename:
                        continue
                    resource_set.add(item)
                    block.resources = block.resources.union(resource_set)
        return blocks_set
        
    def get_illegal_archetype(self):
        self.update_status_bar("Illegal archetypes...")
        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                self.recursive_search_items = [] # empty the list in case it contains somthing else
                self.recursive_search(cell, "Archetype", "down")
                for item in self.recursive_search_items:
                    if item.is_legal:
                        continue
                    cell.resources.append(item)

        table_to_output = []
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1               
                total_instances += count
            table_to_output.append(table_to_output_y)
        
        return table_to_output
    
    def get_illegal_archetype_city_block(self):
        self.update_status_bar("Illegal archetypes...")
        blocks_set = set()        
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)
        
        for block in blocks_set:
            self.progressbar_update()
            block.resources = [] # empty the list in case it contains something else

            self.recursive_search_items = []  # empty the list in case it contains something else
            for entity in block.entities:
                if entity.entity_type == 'Range':
                    continue
                self.recursive_search(entity, "Archetype", "down")

            resource_set = set()
            for item in self.recursive_search_items:
                # if item.is_legal:
                if 'wd2' in item.filename:
                    resource_set.add(item)
            block.resources = resource_set
        return blocks_set

    def get_illegal_geometry_city_block(self):
        self.update_status_bar("Illegal geometry...")

        exclusion_set = set(['\\cin_', '\\users'])

        blocks_set = set()
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)
            block.resources = set()  # empty the list in case it contains something else

        for block in blocks_set:
            self.progressbar_update()
            # block.resources = set()  # empty the list in case it contains something else

            self.recursive_search_items = []  # empty the list in case it contains something else
            for entity in block.entities:
                if 'catalog' in entity.filename:
                    continue
                self.recursive_search(entity, "Geometry", "down")

            resource_set = set()
            for item in self.recursive_search_items:
                is_illegal = False
                for token in exclusion_set:
                    if token in item.filename:
                        is_illegal = True
                        break
                if is_illegal:
                    resource_set.add(item)
            block.resources = block.resources.union(resource_set)

        for block in blocks_set:
            self.progressbar_update()

            self.recursive_search_items = []  # empty the list in case it contains something else
            for entity in block.entities:
                if 'catalog' in entity.filename:
                    continue
                if entity.world_layer_type == 'Interior':
                    continue
                if entity.world_layer_type == 'HMA':
                    continue
                self.recursive_search(entity, "Geometry", "down")

            resource_set = set()
            for item in self.recursive_search_items:
                if '\\int_' in item.filename:
                    resource_set.add(item)
            block.resources = block.resources.union(resource_set)

        return blocks_set

    
    def get_vehicle_enticers(self):
        self.update_status_bar("Vehicle enticers...")
        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                self.recursive_search_items = [] # empty the list in case it contains somthing else
                self.recursive_search(cell, "Generic Item", "down")
                for item in self.recursive_search_items:
                    if "vehiclespawninfo" not in item.filename:
                        continue
                    cell.resources.append(item)

        table_to_output = []
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1               
                total_instances += count
            table_to_output.append(table_to_output_y)
        
        return table_to_output
    
    def get_building_not_on_building_layer(self):
        self.update_status_bar("Buildings not on building layers...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.world_layer_type != "Normal":
                        continue
                    if entity.entity_type != "Building":
                        continue
                    if "building" in entity.filename.lower():
                        continue
                    cell.resources.append(entity)                        
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()
        
    def get_facade_density(self):
    
        count_buildings = 0
        count_facades = 0
        count_populated_cell = 0
    
        self.update_status_bar("Facades...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                
                count = 0                
                for entity in cell.entities:
                    if not entity.building_generatelowlod:
                        continue
                    
                    if entity.entity_type == "Building":
                        count_buildings += 1
                        count += entity.building_facade_count
                        count_facades += entity.building_facade_count
                        entity.special_info = str(entity.building_facade_count).zfill(4)
                        cell.resources.append(entity)
                        cell.resources_dict[entity] = set()
                    
                    if entity.entity_type == "Prefab":
                        self.recursive_search_items = [] # empty the list in case it contains somthing else
                        self.recursive_search(entity, "Prefab Entity", "down")
                        
                        prefab_entities_facade_count = 0
                        for prefab_entity in self.recursive_search_items:
                            if prefab_entity.entity_type == "Building":
                                count_buildings += 1
                                prefab_entities_facade_count += prefab_entity.building_facade_count
                                count_facades += prefab_entity.building_facade_count
                                
                                if entity not in cell.resources:
                                    cell.resources.append(entity)
                                if entity not in cell.resources_dict.keys():
                                    cell.resources_dict[entity] = set()
                        
                        entity.special_info = str(prefab_entities_facade_count).zfill(4)                        
                        count += prefab_entities_facade_count
                if count > 0:
                    count_populated_cell += 1
                cell.facade_instance_count = count
                
                # self.recursive_search_items = [] # empty the list in case it contains somthing else
                # self.recursive_search(cell, "Geometry", "down")
                
                # for geo in self.recursive_search_items:
                    # if geo.is_facade:                
                        # cell.resources.append(geo)  
                    
                #count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "facades_", "facade_instance_count")
        self.update_view()
        
        print "buildings:", count_buildings
        print "facades:", count_facades
        print "cells containing facades:", count_populated_cell
        
    def get_building_not_using_roof_random(self):
        self.update_status_bar("Buildings not using Roof_Random...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.entity_type != "Building":
                        continue
                    if entity.building_roof_material is None:
                        continue
                    if entity.plaza_roof_material == '{00000000-0000-0000-0000-000000000000}':
                        continue
                    if entity.building_roof_material == "{a6934283-b71a-4162-9601-8396e326831c}": # test in lowercase
                        continue
                    if entity.building_roof_material == "{e72286b4-288c-47b8-b32e-e23e7897988a}":
                        continue
                    if entity.building_roof_material == "{fef1fcfc-e577-472f-800a-6b36783e6b96}":
                        continue
                    cell.resources.append(entity)

                    cell.resources_dict[entity] = set()

                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()

    def get_plaza_not_using_roof_random(self):
        self.update_status_bar("Plazas not using Roof_Random...")
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.entity_type != "Plaza":
                        continue
                    if entity.plaza_roof_material is None:
                        continue
                    if entity.plaza_roof_material == '{00000000-0000-0000-0000-000000000000}':
                        continue
                    if entity.building_roof_material == "{a6934283-b71a-4162-9601-8396e326831c}": # test in lowercase
                        continue
                    if entity.building_roof_material == "{e72286b4-288c-47b8-b32e-e23e7897988a}":
                        continue
                    if entity.building_roof_material == "{fef1fcfc-e577-472f-800a-6b36783e6b96}":
                        continue
                    cell.resources.append(entity)

                    cell.resources_dict[entity] = set()

                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "entities_")
        self.update_view()
    
    def get_material_with_bink(self):
        self.update_status_bar("Materials with binks...")
    
        mat_set = set()
        
        for mat in self.material_objects.values():
            mat_set.add(mat)
            
        for mat in mat_set:
            for dep in mat.dependencies:
                if ".bik" in dep:
                    mat.has_bink = True
                    break
                    
        table_to_output = []
        for y in self.world_object.grid_range:
            self.progressbar_update()
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = []
                cell.resources_dict = dict()
                for entity in cell.entities:
                    if entity.entity_type == "CityLifeObject":
                        continue
                    self.recursive_search_items = [] # empty the list in case it contains something else
                    self.recursive_search(entity, "Material", "down")
                    for item in self.recursive_search_items:
                        if not item.has_bink:
                            continue
                        if item not in cell.resources:
                            cell.resources.append(item)
                count = len(cell.resources)
                table_to_output_y.append(count)
            table_to_output.append(table_to_output_y)
        self.create_image_output(table_to_output, "bink_")
        self.update_view()
    
    def get_material_with_bink_city_block(self):
        self.update_status_bar("Materials with binks...")
        
        mat_set = set()        
        for mat in self.material_objects.values():
            mat_set.add(mat)            
        for mat in mat_set:
            for dep in mat.dependencies:
                if ".bik" in dep:
                    mat.has_bink = True
                    break
        
        blocks_set = set()        
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)
        
        for block in blocks_set:
            self.progressbar_update()
            block.resources = [] # empty the list in case it contains something else

            self.recursive_search_items = [] # empty the list in case it contains something else
            for entity in block.entities:
                if entity.entity_type == "CityLifeObject":
                    continue
                self.recursive_search(block, "Material", "down")

            resource_set = set()
            for item in self.recursive_search_items:
                if not item.has_bink:
                    continue
                resource_set.add(item)
            block.resources = resource_set
        return blocks_set
    
    def get_gameplay_ingredients(self):
        self.update_status_bar("Gameplay Ingredients...")
        
        for y in self.world_object.grid_range:
            self.progressbar_update()
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                cell.resources = [] # empty the list in case it contains somthing else
                cell.resources_dict = dict()
                self.recursive_search_items = [] # empty the list in case it contains somthing else
                self.recursive_search(cell, "Geometry", "down")
                for item in self.recursive_search_items:
                    if "gameplay_ingredients" not in item.filename:
                        continue
                    cell.resources.append(item)

        table_to_output = []  
        max = 0
        populated_cells = 0
        total_instances = 0
        for y in self.world_object.grid_range:
            table_to_output_y = []
            for x in self.world_object.grid_range:
                cell = self.world_object.get_cell(x, y)
                count = len(cell.resources)
                table_to_output_y.append(count)
                if max < count:
                    max = count
                if count is not 0:
                    populated_cells += 1               
                total_instances += count
            table_to_output.append(table_to_output_y)
        
        return table_to_output 
    
    def changed_top_radio(self):
        if self.UI.radioButton_bud.isChecked():
            self.UI.comboBox_bud.setEnabled(True)
            self.UI.comboBox_pre.setEnabled(False)
            self.UI.comboBox_typ.setEnabled(False)
            self.UI.comboBox_devtest.setEnabled(False)
            self.UI.lineEdit_ite.setEnabled(False)
            return
            
        if self.UI.radioButton_pre.isChecked():
            self.UI.comboBox_pre.setEnabled(True)
            self.UI.comboBox_bud.setEnabled(False)
            self.UI.comboBox_typ.setEnabled(False)
            self.UI.comboBox_devtest.setEnabled(False)
            self.UI.lineEdit_ite.setEnabled(False)
            return

        if self.UI.radioButton_typ.isChecked():
            self.UI.comboBox_pre.setEnabled(False)
            self.UI.comboBox_bud.setEnabled(False)
            self.UI.comboBox_typ.setEnabled(True)
            self.UI.comboBox_devtest.setEnabled(False)
            self.UI.lineEdit_ite.setEnabled(False)
            return
            
        if self.UI.radioButton_devtest.isChecked():
            self.UI.comboBox_pre.setEnabled(False)
            self.UI.comboBox_bud.setEnabled(False)
            self.UI.comboBox_typ.setEnabled(False)
            self.UI.comboBox_devtest.setEnabled(True)
            self.UI.lineEdit_ite.setEnabled(False)
            return

        self.UI.comboBox_bud.setEnabled(False)
        self.UI.comboBox_pre.setEnabled(False)
        self.UI.comboBox_typ.setEnabled(False)
        self.UI.comboBox_devtest.setEnabled(False)
        self.UI.lineEdit_ite.setEnabled(True)

    def changed_special_item(self):
        if str(self.UI.comboBox_pre.currentText()) == "Object With n Instance In The World":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("1")
        elif str(self.UI.comboBox_pre.currentText()) == "Entity In Z":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("0:100000")
        elif str(self.UI.comboBox_pre.currentText()) == "Entity UnderGround" :
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("10")
        elif str(self.UI.comboBox_pre.currentText()) == "Entity By Number Of Class Instances":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("20")
        elif str(self.UI.comboBox_pre.currentText()) == "Interior Layer Errors":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("8000")
        elif str(self.UI.comboBox_pre.currentText()) == "Plaza":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("20000")
        elif str(self.UI.comboBox_pre.currentText()) == "Plaza By Kill Distance":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("256")
        elif str(self.UI.comboBox_pre.currentText()) == "Building Surface Lower Than n m2":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("20000")
        elif str(self.UI.comboBox_pre.currentText()) == "Building Volume Lower Than n m3":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("20000")
        elif str(self.UI.comboBox_pre.currentText()) == "Building Should Not Generate LLOD": 
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("32")
        elif str(self.UI.comboBox_pre.currentText()) == "Building Should Be In FarAway":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("32")
        elif str(self.UI.comboBox_pre.currentText()) == "Building Should Be In Far":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("32")
        elif str(self.UI.comboBox_pre.currentText()) == "Building Should Be In Near":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("32")
        elif str(self.UI.comboBox_pre.currentText()) == "Bad Practice Buildings":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("4")
        elif str(self.UI.comboBox_pre.currentText()) == "Geometry By Kill Distance":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("0")

        elif str(self.UI.comboBox_pre.currentText()) == "Geometry By Size":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("0")

        elif str(self.UI.comboBox_pre.currentText()) == "Geometry By JIRA Filter":
            self.UI.lineEdit_pre.setVisible(True)
            self.UI.lineEdit_pre.setText("")
        else:
            self.UI.lineEdit_pre.setVisible(False)

    def changed_top_search(self):
        pass

    def convert_line_edit_text_to_int(self, line_edit_object_name):
        try:
            return int(line_edit_object_name)
        except:
            print "Value cannot be converted to an integer, returning 0."
            return 0
    
    def geometry_in_city_block(self):
        self.update_status_bar("Geometry in City Blocks...")
        blocks_set = set()        
        for block in self.city_block_cell_objects.values():
            blocks_set.add(block)
        
        for block in blocks_set:
            self.progressbar_update()
            block.resources = [] # empty the list in case it contains something else
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(block, "Geometry", "down")
            resource_set = set()
            for item in self.recursive_search_items:
                resource_set.add(item)
            block.resources = resource_set
        return blocks_set
                
    def set_city_block_cell_colors(self, blocks_set):

        alpha = 210        
        verylight =     QtGui.QColor(0,220,0,105)
        light =         QtGui.QColor(0,220,0,150)
        good =          QtGui.QColor(0,220,0,alpha)
        medium =        QtGui.QColor(240,255,0,alpha)
        limit =         QtGui.QColor(255,140,0,alpha)
        bad =           QtGui.QColor(255,0,0,alpha)
        null =          QtGui.QColor(0,0,0,0)
        verybad =       QtGui.QColor(100,0,200,alpha)
        outofcontrol =  QtGui.QColor(64,0,255,alpha)
        maxvaluebad =   QtGui.QColor(255,0,255,alpha)
        maxvalueok =    QtGui.QColor(0,255,255,alpha)

        max_value = 0
        for block in blocks_set:
            if block.points is None: # skip over Default that has no points
                continue
            value = len(block.resources)
            if value > max_value:
                max_value = value
                
        max_value = float(max_value)
                
        for block in blocks_set:
            if block.points is None: # skip over Default that has no points
                continue
            value = float(len(block.resources))

            if max_value == 0:
                block.heatmap_qcolor = null
            else:            
                if value == 0:
                    block.heatmap_qcolor = null
                elif value == max_value:
                    block.heatmap_qcolor = bad
                elif value > max_value * 0.8:
                    block.heatmap_qcolor = limit
                elif value > max_value * 0.6:
                    block.heatmap_qcolor = medium
                elif value > max_value * 0.4:
                    block.heatmap_qcolor = good
                elif value > max_value * 0.2:
                    block.heatmap_qcolor = light
                else:
                    block.heatmap_qcolor = verylight

                # else:                
                    # current_value = (value/max_value)*255.0
                    # current_value = int(current_value)
                    # current_value *= 4.0
                    # if current_value < 10.0: # this is to catch values that would be too low and set a floor value
                        # current_value = 40.0 # this is the lowest value used in "verylight"
                    # current_value = int(current_value)
                    # block.heatmap_qcolor = QtGui.QColor(0,current_value,0)

    def draw_city_blocks_heatmap(self, blocks_set):
        city_blocks_bitmap_path = data_path.replace("data", r"\td_tools\PythonTools\DDV\resources\city_blocks_bitmap_black.png")
        city_blocks_bitmap = QtGui.QImage(city_blocks_bitmap_path)
        # city_blocks_bitmap = city_blocks_bitmap.convertToFormat(QtGui.QImage.Format.Format_ARGB32)
        painter = QtGui.QPainter()
        painter.begin(city_blocks_bitmap)
        for block in blocks_set:
            if block.points is None: # skip over Default that has no points
                # self.draw_donut(painter, (self.world_object.world_size/4, self.world_object.world_size/4), block.heatmap_qcolor, 250)
                # shape = [
                    # QtCore.QPoint(3500,500),
                    # QtCore.QPoint(500,500),
                    # QtCore.QPoint(500,3500),
                    # QtCore.QPoint(3500,3500)
                # ]
                # self.draw_shape(painter, shape, block.heatmap_qcolor, 150)
                continue
            self.draw_shape(painter, block.points, block.heatmap_qcolor, 0, True, True, QtGui.QColor(51,196,224,255))
        painter.end()
        ###
        city_blocks_bitmap.save(city_blocks_bitmap_path.replace(".png","_heatmap.png"))
        ###
        self.city_blocks_heatmap_image = city_blocks_bitmap
    
    def clicked_top_gen(self):
        if self.world_object is None:
            return
        self.toggle_waitcursor(True)
        self.UI.tabWidget.setEnabled(False)

        self.model_topview.clearChildren()
        self.UI.label_count.setText("0 item")
        self.progressbar_setmax(len(self.world_object.world_grid.cells))
        self.progressbar_setmax(2, True)

        self.topview_selection = (-1, -1) #Reset cell selection
        
        self.topview_mode = 0
        self.UI.pushButton_stats.setChecked(True)
        
        current_item = ""
        
        if self.UI.radioButton_bud.isChecked():
            current_item = str(self.UI.comboBox_bud.currentText()) 
        if self.UI.radioButton_devtest.isChecked():
            current_item = str(self.UI.comboBox_devtest.currentText())
        if self.UI.radioButton_pre.isChecked():
            current_item = str(self.UI.comboBox_pre.currentText())
            
        if current_item == "Geometry In City Block":
            self.topview_mode = 1
            self.UI.pushButton_stats.setChecked(False)
            self.UI.pushButton_city_blocks.setChecked(True)
            blocks_set = self.geometry_in_city_block()
            self.set_city_block_cell_colors(blocks_set)
            self.draw_city_blocks_heatmap(blocks_set)
            self.update_view()
            
        if current_item == "Archetype With Animation Component":
            table_result = self.get_archetype_with_animation_component()
            self.create_image_output(table_result, ("Archetype" + "_"))
            self.update_view()
        if current_item == "Archetype With Animation Component (CB)":
            self.topview_mode = 1
            self.UI.pushButton_stats.setChecked(False)
            self.UI.pushButton_city_blocks.setChecked(True)
            blocks_set = self.get_archetype_with_animation_component_city_block()
            self.set_city_block_cell_colors(blocks_set)
            self.draw_city_blocks_heatmap(blocks_set)
            self.update_view()
            
        if current_item == "Batched Objects (not a Proxy)":
            self.get_batched_object_density()
        if current_item == "Batched Objects (not a Proxy) (CB)":
            self.topview_mode = 1
            self.UI.pushButton_stats.setChecked(False)
            self.UI.pushButton_city_blocks.setChecked(True)
            blocks_set = self.get_batched_object_density_city_block()
            self.set_city_block_cell_colors(blocks_set)
            self.draw_city_blocks_heatmap(blocks_set)
            self.update_view()

        if current_item == "Facade Not In Building":
            self.get_facades_not_in_buildings()
        if current_item == "Facade Not In Building (CB)":   
            self.topview_mode = 1
            self.UI.pushButton_stats.setChecked(False)
            self.UI.pushButton_city_blocks.setChecked(True)
            blocks_set = self.get_facades_not_in_buildings_city_block()
            self.set_city_block_cell_colors(blocks_set)
            self.draw_city_blocks_heatmap(blocks_set)
            self.update_view()

        if current_item == "Geometry With No JIRA":
            table_result = self.get_geometry_with_no_jira()
            self.create_image_output(table_result, ("Geometry_with_no_JIRA" + "_"))
            self.update_view()
        if current_item == "Geometry With No JIRA (CB)":
            self.topview_mode = 1
            self.UI.pushButton_stats.setChecked(False)
            self.UI.pushButton_city_blocks.setChecked(True)
            blocks_set = self.get_geometry_with_no_jira_city_block()
            self.set_city_block_cell_colors(blocks_set)
            self.draw_city_blocks_heatmap(blocks_set)
            self.update_view()
            
        if current_item == "Geometry With No JIRA In PropsCatalogs":
            self.topview_mode = 1
            self.UI.pushButton_stats.setChecked(False)
            self.UI.pushButton_city_blocks.setChecked(True)
            blocks_set = self.get_geometry_with_no_jira_propscatalogs_city_block()
            self.set_city_block_cell_colors(blocks_set)
            self.draw_city_blocks_heatmap(blocks_set)
            self.update_view()

        if current_item == "Geometry From BVI Used In London":
            self.topview_mode = 1
            self.UI.pushButton_stats.setChecked(False)
            self.UI.pushButton_city_blocks.setChecked(True)
            blocks_set = self.get_geometry_from_bvi_used_in_london()
            self.set_city_block_cell_colors(blocks_set)
            self.draw_city_blocks_heatmap(blocks_set)
            self.update_view()
            
        if current_item == "Illegal Archetype (not WD3)":
            table_result = self.get_illegal_archetype()
            self.create_image_output(table_result, ("Archetype" + "_"))
            self.update_view()
        if current_item == "Illegal Archetype (not WD3) (CB)":
            self.topview_mode = 1
            self.UI.pushButton_stats.setChecked(False)
            self.UI.pushButton_city_blocks.setChecked(True)
            blocks_set = self.get_illegal_archetype_city_block()
            self.set_city_block_cell_colors(blocks_set)
            self.draw_city_blocks_heatmap(blocks_set)
            self.update_view()

        if current_item == "Illegal Geometry (int, cin, usr)":
            self.topview_mode = 1
            self.UI.pushButton_stats.setChecked(False)
            self.UI.pushButton_city_blocks.setChecked(True)
            blocks_set = self.get_illegal_geometry_city_block()
            self.set_city_block_cell_colors(blocks_set)
            self.draw_city_blocks_heatmap(blocks_set)
            self.update_view()
            
        if current_item == "Material With Bink":
            self.get_material_with_bink()
        if current_item == "Material With Bink (CB)":
            self.topview_mode = 1
            self.UI.pushButton_stats.setChecked(False)
            self.UI.pushButton_city_blocks.setChecked(True)
            blocks_set = self.get_material_with_bink_city_block()
            self.set_city_block_cell_colors(blocks_set)
            self.draw_city_blocks_heatmap(blocks_set)
            self.update_view()
            
        if current_item == "Pink Objects":
            self.get_pink_objects_density()
        if current_item == "Pink Objects (CB)":
            self.topview_mode = 1
            self.UI.pushButton_stats.setChecked(False)
            self.UI.pushButton_city_blocks.setChecked(True)
            blocks_set = self.get_pink_objects_density_city_block()
            self.set_city_block_cell_colors(blocks_set)
            self.draw_city_blocks_heatmap(blocks_set)
            self.update_view()
            
        if current_item == "Stairs With No IK":
            self.get_stairs_with_no_ik_density()
        if current_item == "Stairs With No IK (CB)":
            self.topview_mode = 1
            self.UI.pushButton_stats.setChecked(False)
            self.UI.pushButton_city_blocks.setChecked(True)
            blocks_set = self.get_stairs_with_no_ik_density_city_block()
            self.set_city_block_cell_colors(blocks_set)
            self.draw_city_blocks_heatmap(blocks_set)
            self.update_view()
            
                    
        if current_item == "Group":
            self.topview_mode = 1
            self.UI.pushButton_stats.setChecked(False)
            self.UI.pushButton_city_blocks.setChecked(True)
            blocks_set = self.get_group_density()
            self.set_city_block_cell_colors(blocks_set)
            self.draw_city_blocks_heatmap(blocks_set)
            self.update_view()
            
        if current_item == "Entity On Tower Hamlets East":
            self.get_entity_in_towerhamlets_east()

        if current_item == "City Life Object":
            self.get_clo_density()
        if current_item == "Entity Not Batched":
            self.get_not_batched_density()
        if current_item == "Occluder":
            self.get_occluder_density()
        if current_item == "Plaza":
            value = self.convert_line_edit_text_to_int(self.UI.lineEdit_pre.text())
            self.get_plaza_density(value)

        if current_item == "Plaza By Kill Distance":
            value = self.convert_line_edit_text_to_int(self.UI.lineEdit_pre.text())
            self.get_plaza_by_kill_distance(value)

        if current_item == "Building Surface Lower Than n m2":
            value = self.convert_line_edit_text_to_int(self.UI.lineEdit_pre.text())
            self.get_building_density(value)
           
        if current_item == "Building Volume Lower Than n m3":
            value = self.convert_line_edit_text_to_int(self.UI.lineEdit_pre.text())
            self.get_building_by_volume(value)

        if current_item == "Building Should Not Generate LLOD":
            value = self.convert_line_edit_text_to_int(self.UI.lineEdit_pre.text())
            self.get_building_shouldbe_cases(value, "LLOD")
            
        if current_item == "Bad Practice Buildings":
            value = self.convert_line_edit_text_to_int(self.UI.lineEdit_pre.text())
            self.get_building_shouldbe_cases(value,"BadPractice")
                   
        if current_item == "Building Should Be In FarAway":
            value = self.convert_line_edit_text_to_int(self.UI.lineEdit_pre.text())
            self.get_building_shouldbe_cases(value, "FarAway")

        if current_item == "Building Should Be In Far":
            value = self.convert_line_edit_text_to_int(self.UI.lineEdit_pre.text())
            self.get_building_shouldbe_cases(value, "Far")

        if current_item == "Building Should Be In Near":
            value = self.convert_line_edit_text_to_int(self.UI.lineEdit_pre.text())
            self.get_building_shouldbe_cases(value, "Near")

        if current_item == "Building Generating Lowres Using Interior Kit":
            self.get_building_generating_lowres_using_interior_kit()
            
        if current_item == "Illegal Geometry":
            exclude_strings = ["geometry", "lofts", "gfx", "wire_proto_01", "dealership_invisible_wall_01"]
            table_result = self.get_resource_density("Geometry", "down", "Proxy", exclude_strings, "Proxy")
            self.create_image_output(table_result, ("WD1_Geometry" + "_"))
            self.update_view()
        if current_item == "Insufficient LODs":
            table_result = self.get_single_LOD_asset_density()
            self.create_image_output(table_result, ("Single_LOD_Assets" + "_"))
            self.update_view()
        
        if current_item == "Geometry In Unbatched Entity":
            self.topview_mode = 1
            self.UI.pushButton_stats.setChecked(False)
            self.UI.pushButton_city_blocks.setChecked(True)
            blocks_set = self.get_geometry_in_unbatched_entity()
            self.set_city_block_cell_colors(blocks_set)
            self.draw_city_blocks_heatmap(blocks_set)
            self.update_view()

        if current_item == "Geometry With Uncertain High/Medium (64) LOD Distances":
            self.get_geometry_with_uncertain_lod_distances(1)
        if current_item == "Geometry With Uncertain Near/Far (256) LOD Distances":
            self.get_geometry_with_uncertain_lod_distances(2)
        if current_item == "Geometry With Uncertain Medium/Low (383) LOD Distances":
            self.get_geometry_with_uncertain_lod_distances(3)
        if current_item == "Geometry With Uncertain Far/FarAway (1024) LOD Distances":
            self.get_geometry_with_uncertain_lod_distances(4)
            
        if current_item == "Primitive":
            self.get_primitive_density()
        
        if current_item == "Primitive Montreal":
            self.get_primitive_density_montreal()
            
        if current_item == "Object With n Instance In The World":
            table_result = self.get_resource_density_by_count("Geometry", "down", "")
            self.create_image_output(table_result, ("n_Instance" + "_"))
            self.update_view()
        if current_item == "Entity By Number Of Class Instances":
            self.get_entity_by_class()
        if current_item == "Interior Layer Errors":
            value = self.convert_line_edit_text_to_int(self.UI.lineEdit_pre.text())
            self.get_interior_layer_errors(value)
            self.update_view()
        if current_item == "Entity On Interior": 
            self.get_entity_density_by_world_layer_type("Interior")
        if current_item == "Entity On HMA":
            self.get_entity_density_by_world_layer_type("HMA")
        if current_item == "Entity On LMA": 
            self.get_entity_density_by_world_layer_type("LMA")
        if current_item == "Entity On Mission": 
            self.get_entity_density_by_world_layer_type("Mission")
        if current_item == "Entity On Progression": 
            self.get_entity_density_by_world_layer_type("Progression")
        if current_item == "Entity On Sas": 
            self.get_entity_density_by_world_layer_type("Sas")
        if current_item == "Entity UnderGround": 
            self.get_entity_underground()
        if current_item == "Entity In Z": 
            self.get_entity_density_by_z()
            
        if current_item == "Interior Object On Normal Layer":
            self.get_entity_density_int_obj_on_normal_layer()
        if current_item == "Breakable":
            table_result = self.get_archetype_resource_density("BreakableObject")
            self.create_image_output(table_result, ("archetype" + "_"))
            self.update_view()
        if current_item == "Breakable Multistate":
            table_result = self.get_archetype_resource_density("BreakableObject", True)
            self.create_image_output(table_result, ("archetype" + "_"))
            self.update_view()
        if current_item == "Breakable Multistate (entities)":
            table_result = self.get_breakable_multistate_entity_density()
            self.create_image_output(table_result, ("archetype" + "_"))
            self.update_view()
        if current_item == "Geometry By Kill Distance":
            value = self.convert_line_edit_text_to_int(self.UI.lineEdit_pre.text())
            table_result = self.get_geometry_by_kill_distance(value)
            self.create_image_output(table_result, ("Geometry_by_kill_distance" + "_"))
            self.update_view()

        if current_item == "Geometry By Size":
            value = self.convert_line_edit_text_to_int(self.UI.lineEdit_pre.text())
            table_result = self.get_geometry_by_size(value)
            self.create_image_output(table_result, ("Geometry_by_size" + "_"))
            self.update_view()

        if current_item == "Spawning Cost":
            # table_result = self.get_loading_rings()
            table_result = self.get_spawning_cost()
            self.create_image_output(table_result, ("loadingring" + "_"), "loadingringbudgeted")
            self.update_view()
        if current_item == "Compiled Size Per Cell":
            self.get_resources_compiled_size_per_cell()
        if current_item == "Geometry By JIRA Filter":
            table_result = self.get_geometry_by_jira_filter()
            self.create_image_output(table_result, ("Geometry_with_no_JIRA" + "_"))
            self.update_view()
        if current_item == "Proxy In Legal Folder Not Tracked":
            table_result = self.get_proxy_in_legal_folder_not_tracked()
            self.create_image_output(table_result, ("Proxy" + "_"))
            self.update_view()
        if current_item == "Vehicle Enticers":
            table_result = self.get_vehicle_enticers()
            self.create_image_output(table_result, ("Vehicles" + "_"))
            self.update_view()
            
        if current_item == "Building Not On Building Layer":
            self.get_building_not_on_building_layer()
        
        if current_item == "Building Not Using Roof_Random":
            self.get_building_not_using_roof_random()

        if current_item == "Plaza Not Using Roof_Random":
            self.get_plaza_not_using_roof_random()
            
        if current_item == "Facades Instance Count":
            self.get_facade_density()
   
        if current_item == "Building Kit (numbers)":
            self.get_building_kit_numbers()
        if current_item == "Building Kit (memory)":
            self.get_building_kit_memory()                  
        if current_item == "Building Kit Points":
            self.get_building_kit_points()       
        if current_item == "Geometry":
            #table_result = self.get_resource_density(current_item, "down", "Building")
            table_result = self.get_geometry_budget_density()
            self.create_image_output(table_result, (current_item + "_"), current_item)
            self.update_view()
        if current_item == "Gameplay Ingredients":
            table_result = self.get_gameplay_ingredients()
            self.create_image_output(table_result, ("Gameplay_ingredients" + "_"))
            self.update_view()

        if current_item == 'External References':
            self.get_external_references_from_file()

        if self.UI.radioButton_typ.isChecked():
            current_item = str(self.UI.comboBox_typ.currentText())
            table_result = self.get_resource_density(current_item)
            self.create_image_output(table_result, (current_item + "_"))
            self.update_view()

        if self.UI.radioButton_ite.isChecked():
            if self.current_object.type == "World Layer": # this is special case if the current obj is a world layer, recursive search needs to go down and the colorize mode is set to binary
                table_result = self.get_current_object_density("down")
                self.create_image_output(table_result, (self.current_object.name + "_"), "binary")
            elif "Library" in self.current_object.type:
                table_result = self.get_library_density(self.current_object)
                #self.create_image_output(table_result, (self.current_object.name + "_"), "binary")
            else:
                table_result = self.get_current_object_density("up")
                self.create_image_output(table_result, (self.current_object.name + "_"))
            self.update_view()

        self.progressbar_reset(True)
        self.clear_status_bar()
        self.UI.tabWidget.setEnabled(True)
        self.toggle_waitcursor(False)

    def export_top_csv(self):
        if self.UI.radioButton_bud.isChecked():
            search_cat = "Budgeted"
            search_type = str(self.UI.comboBox_bud.currentText()).replace(" ", "")
        elif self.UI.radioButton_pre.isChecked():
            search_cat = "Special"
            search_type = str(self.UI.comboBox_pre.currentText()).replace(" ", "")
        elif self.UI.radioButton_typ.isChecked():
            search_cat = "Resource"
            search_type = str(self.UI.comboBox_typ.currentText()).replace(" ", "")
        elif self.UI.radioButton_devtest.isChecked():
            search_cat = "DevTest"
            search_type = str(self.UI.comboBox_devtest.currentText()).replace(" ", "")
        else:# self.UI.radioButton_ite.isChecked():
            search_cat = "CurrentItem"
            search_type = str(self.UI.lineEdit_ite.currentText()).replace(" ", "")
            search_type = search_type + "-" + self.UI.lineEdit_search.currentText()

        #Format a nice file name
        selection = "DDV-Topview-" + search_cat +  "-" + search_type

        fname, ok = QtGui.QFileDialog.getSaveFileName(self, 'Save Comma-separated values file', selection, "CSV Files (*.csv)")

        if ok:
            with open(fname, 'w') as csvfile:
                fn_ite = 'Item'
                fn_cnt = 'Count'
                fn_typ = 'Type'
                fn_wor = 'WorldLayer'
                fn_wlu = 'WLU'
                fn_spe = 'SpecialInfo'

                fieldnames = [fn_ite, fn_cnt, fn_typ, fn_wor, fn_wlu, fn_spe]
                writer = csv_writer(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for row in range(self.model_topview.rowCount()):
                    index_ite = self.model_topview.index(row, 0)
                    index_cnt = self.model_topview.index(row, 1)
                    index_typ = self.model_topview.index(row, 2)
                    index_wor = self.model_topview.index(row, 3)
                    index_wlu = self.model_topview.index(row, 4)
                    index_spe = self.model_topview.index(row, 5)
                    text_ite = self.model_topview.data(index_ite)
                    text_cnt = self.model_topview.data(index_cnt)
                    text_typ = self.model_topview.data(index_typ)
                    text_wor = self.model_topview.data(index_wor)
                    text_wlu = self.model_topview.data(index_wlu)
                    text_spe = self.model_topview.data(index_spe)

                    writer.writerow({fn_ite: text_ite,
                                     fn_cnt: text_cnt,
                                     fn_typ: text_typ,
                                     fn_wor: text_wor,
                                     fn_wlu: text_wlu,
                                     fn_spe: text_spe})

    def export_prop_csv(self):
        #Format a nice file name
        search_cat = str(self.UI.comboBox_prop.currentText()).replace(" ", "")
        search_type = str(self.UI.comboBox_filter.currentText()).replace(" ", "")
        selection = "DDV-Proparazzi-" + search_cat
        if search_type != "":
            selection += "-" + search_type

        fname, ok = QtGui.QFileDialog.getSaveFileName(self, 'Save Comma-separated values file', selection, "CSV Files (*.csv)")

        if ok:
            with open(fname, 'w') as csvfile:
                fn_ite = 'Item'
                fn_cnt = 'Count'
                fn_typ = 'Type'
                fn_fil = 'Filename'
                fn_wor = 'WorldLayer'
                fn_wlu = 'WLU'
                fn_dra = 'Size'
                fn_spe = 'SpecialInfo'

                fieldnames = [fn_ite, fn_cnt, fn_typ, fn_fil, fn_wor, fn_wlu, fn_dra, fn_spe]
                writer = csv_writer(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for row in range(self.model_proparazzi.rowCount()):
                    index_ite = self.model_proparazzi.index(row, 0)
                    index_cnt = self.model_proparazzi.index(row, 1)
                    index_typ = self.model_proparazzi.index(row, 2)
                    index_fil = self.model_proparazzi.index(row, 3)
                    index_wor = self.model_proparazzi.index(row, 4)
                    index_wlu = self.model_proparazzi.index(row, 5)
                    index_dra = self.model_proparazzi.index(row, 6)
                    index_spe = self.model_proparazzi.index(row, 7)
                    text_ite = self.model_proparazzi.data(index_ite)
                    text_cnt = self.model_proparazzi.data(index_cnt)
                    text_typ = self.model_proparazzi.data(index_typ)
                    text_fil = self.model_proparazzi.data(index_fil)
                    text_wor = self.model_proparazzi.data(index_wor)
                    text_wlu = self.model_proparazzi.data(index_wlu)
                    text_dra = self.model_proparazzi.data(index_dra)
                    text_spe = self.model_proparazzi.data(index_spe)

                    writer.writerow({fn_ite: text_ite,
                                     fn_cnt: text_cnt,
                                     fn_typ: text_typ,
                                     fn_fil: text_fil,
                                     fn_wor: text_wor,
                                     fn_wlu: text_wlu,
                                     fn_dra: text_dra,
                                     fn_spe: text_spe})
                                     
    def clicked_top_csv(self):
        self.export_top_csv()
    
    @QtCore.Slot()
    def on_pushButton_prop_csv_clicked(self):
        #self.export_prop_csv()
        if self.proparazzi_stats_dict is None:
            return
        system("start " + self.write_csv_from_dict(self.proparazzi_stats_dict, self.UI.checkBox_include_children.isChecked()))
        
    @QtCore.Slot()
    def on_pushButton_link_geo_with_jira_clicked(self):
        self.link_geometry_to_jira_issue()

    def clicked_top_clr(self):
        pass

    def clicked_cb(self):
        self.update_view()
        
    def clicked_city_locations(self):
        self.city_locations = []
        for entity in self.entity_objects.values():
            if entity.entity_type == "CityLocation":
                if "LM" not in entity.name:
                    continue
                entity_pos_f = float(entity.position[0]), float(entity.position[1])
                pos = (entity_pos_f, entity.points)
                self.city_locations.append(pos)
        self.update_view()
        
    def clicked_city_blocks(self):
        ###
        self.update_view()
        return
        ###
        if len(self.jira_city_blocks_issues_la) > 0:
            self.update_view()
            return
    
        filter_la = 'text ~ "DA2JRI"' #'type = "Story " and text ~ World and assignee = "joel.bertrand@ubisoft.com" and status = Open'
        filter_ld = 'text ~ "82BJ9X"'
        
        self.get_jira_issues(filter_la, self.jira_city_blocks_issues_la)
        self.get_jira_issues(filter_ld, self.jira_city_blocks_issues_ld)
        
        self.atlas_data_dict_in = self.get_data_from_atlas_layer(join(dirname(__file__), "resources/Atlas_CityBlocks_Layer_London.xml"))
        
        self.progressbar_setmax(len(self.jira_city_blocks_issues_la))
        for issue in self.jira_city_blocks_issues_la:
            self.progressbar_update()
            found = None 
            
            current_summary = issue.fields.summary.replace(" ","")
                
            for k, v in self.atlas_data_dict_in.iteritems():                
                if k.lower() in current_summary.lower():

                    if "CL" in issue.fields.summary:
                        self.atlas_data_dict_out_1[v] = QtGui.QColor(255,0,0,192)
                    if "IH" in issue.fields.summary:
                        self.atlas_data_dict_out_1[v] = QtGui.QColor(255,0,0,192)
                    if "TW" in issue.fields.summary:
                        self.atlas_data_dict_out_1[v] = QtGui.QColor(255,0,0,192)
                    if "TE" in issue.fields.summary:
                        self.atlas_data_dict_out_1[v] = QtGui.QColor(255,0,0,192)
                        
        self.progressbar_setmax(len(self.jira_city_blocks_issues_ld))
        for issue in self.jira_city_blocks_issues_ld:
            self.progressbar_update()
            found = None 
            
            current_summary = issue.fields.summary.replace(" ","")
                
            for k, v in self.atlas_data_dict_in.iteritems():                
                if k.lower() in current_summary.lower():

                    if "CL" in issue.fields.summary:
                        self.atlas_data_dict_out_2[v] = QtGui.QColor(0,255,0,192)
                    if "IH" in issue.fields.summary:
                        self.atlas_data_dict_out_2[v] = QtGui.QColor(0,255,0,192)
                    if "TW" in issue.fields.summary:
                        self.atlas_data_dict_out_2[v] = QtGui.QColor(0,255,0,192)
                    if "TE" in issue.fields.summary:
                        self.atlas_data_dict_out_2[v] = QtGui.QColor(0,255,0,192)

        self.update_view()
    
    @QtCore.Slot()
    def on_pushButton_zones_clicked(self):
        self.update_view()
    
    @QtCore.Slot()
    def on_pushButton_stats_clicked(self):
        self.update_view()
        
    @QtCore.Slot()
    def on_pushButton_lines_clicked(self):
        self.update_view()
    
    ###########################################
    # Proparazzi
    ###########################################
    
    def fill_prop_tree(self, resource_dict):
        self.toggle_waitcursor(True)

        for i in resource_dict.keys():
            try:
                if i.isCLO():
                    i.special_info = i.lib_type
            except:
                pass

        self.model_proparazzi.clearChildren()
        self.model_proparazzi.setupModelData(data_dict=resource_dict)

        count = len(resource_dict)

        instance_count = 0
        for i in resource_dict.values():
            instance_count += len(i)

        count_text = str(count) + " item"
        if count > 1:
            count_text += "s"
        count_text += " \ " + str(instance_count) + " instance"
        if instance_count > 1:
            count_text += "s"
        self.UI.label_prop_count.setText(count_text)

        self.progressbar_reset(True)
        self.refresh_ui()
        self.toggle_waitcursor(False)

    def get_proxy_stats(self):
        geo_instance_count_dict = {}
        self.progressbar_setmax(len(self.proxy_objects))
        for id, obj in self.proxy_objects.iteritems():
            self.progressbar_update()
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj, "Entity", "up")
            geo_instance_count_dict[obj] = self.recursive_search_items
        return geo_instance_count_dict
        
    def get_geometry_stats(self):
    
        gx = adp.import_gamex(r"W:\main\python")# import gamex lib from root EPA
    
        current_studio = str(self.UI.comboBox_filter.currentText())
        regions = self.get_region_list(current_studio)
        
        geometry_output_dict = {}
        
        geo_set = set()
        for geo in self.geometry_objects.values():
            geo_set.add(geo)
        
        self.progressbar_setmax(len(geo_set))
        for geo in geo_set:
            self.progressbar_update()
            geo._entity_instance_count = 0
            
            if not gx:
                continue
                
            geo.get_geometry_type(geo.filename.replace(".xml", ".gamex"), gx)            
            # geo.special_info = geo.geometry_type
            geo.special_info = str(geo.kill_distance).zfill(8)

        entity_set = set()
        for entity in self.entity_objects.values():
            entity_set.add(entity)
        
        self.progressbar_setmax(len(entity_set))
        for entity in entity_set:
            self.progressbar_update()
            if entity.region in regions:
                self.recursive_search_items = []
                self.recursive_search(entity, "Geometry", "down")
                for geo in self.recursive_search_items:
                    if geo not in geometry_output_dict.keys():
                        geometry_output_dict[geo] = []
                    geometry_output_dict[geo].append(entity)
                    geo._entity_instance_count += 1
        return geometry_output_dict
        
    def get_geometry_user_set_distances(self):
        current_studio = str(self.UI.comboBox_filter.currentText())
        regions = self.get_region_list(current_studio)
        
        geometry_output_dict = {}
        
        geo_set = set()
        for geo in self.geometry_objects.values():
            geo_set.add(geo)
        
        for geo in geo_set:
            geo._entity_instance_count = 0
        
        for entity in self.entity_objects.values():
            if entity.region in regions:
                self.recursive_search_items = []
                self.recursive_search(entity, "Geometry", "down")
                for geo in self.recursive_search_items:
                    if not geo.is_lod_distances_override:
                        continue
                    if geo not in geometry_output_dict.keys():
                        geometry_output_dict[geo] = []
                    geometry_output_dict[geo].append(entity)
                    geo._entity_instance_count += 1
        return geometry_output_dict

    def get_archetype_stats(self):
        arch_instance_count_dict = {}
        self.progressbar_setmax(len(self.archetype_item_objects))
        for id, obj in self.archetype_item_objects.iteritems():
            self.progressbar_update()
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj, "Entity", "up")
            arch_instance_count_dict[obj] = self.recursive_search_items
        return arch_instance_count_dict
        
    def get_material_stats(self):
        geo_instance_count_dict = {}
        self.progressbar_setmax(len(self.material_objects))
        for id, obj in self.material_objects.iteritems():
            self.progressbar_update()
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj, "Entity", "up")
            geo_instance_count_dict[obj] = self.recursive_search_items
        return geo_instance_count_dict
        
    def get_material_two_sided_stats(self):
        geo_instance_count_dict = {}
        self.progressbar_setmax(len(self.material_objects))
        for id, obj in self.material_objects.iteritems():
            is_twosided = obj.parameters.get("TwoSided")
            if not is_twosided: # test if None
                continue
            if is_twosided == "0":
                continue
            self.progressbar_update()
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj, "Entity", "up")
            geo_instance_count_dict[obj] = self.recursive_search_items
        return geo_instance_count_dict

    def get_material_with_animated_texture(self):
        geo_instance_count_dict = {}
        self.progressbar_setmax(len(self.material_objects))

        geometry_objects_set = set()
        for id, obj in self.material_objects.iteritems():

            is_bad = False

            anim_type = obj.parameters.get("AnimType")
            if anim_type:
                if anim_type == '2' or anim_type == '5' or anim_type == '6':
                    is_bad = True

            if is_bad == False:
                continue

            self.progressbar_update()
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj, "Geometry", "up")

            for item in self.recursive_search_items:
                geometry_objects_set.add(item)

        for geometry_object in geometry_objects_set:

            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(geometry_object, "Entity", "up")

            geo_instance_count_dict[geometry_object] = self.recursive_search_items

        return geo_instance_count_dict

    def get_material_with_bink(self):
        geo_instance_count_dict = {}
        self.progressbar_setmax(len(self.material_objects))

        geometry_objects_set = set()
        for id, obj in self.material_objects.iteritems():

            is_bad = False

            video_texture = obj.parameters.get("VideoTexture1")
            if video_texture:
                if ".bik" in video_texture:
                    is_bad = True

            if is_bad == False:
                continue

            self.progressbar_update()
            self.recursive_search_items = []  # empty the list in case it contains something else
            self.recursive_search(obj, "Geometry", "up")

            for item in self.recursive_search_items:
                geometry_objects_set.add(item)

        for geometry_object in geometry_objects_set:
            self.recursive_search_items = []  # empty the list in case it contains something else
            self.recursive_search(geometry_object, "Entity", "up")

            geo_instance_count_dict[geometry_object] = self.recursive_search_items

        return geo_instance_count_dict

    def get_media_broadcast_material_references(self):
        output_dict = dict()
        materials_ids = set([
                            r'graphics\_materials\mabelleau-m-9223372083440701876.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372083440701873.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372083440701874.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372083440701875.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372084067849691.material.xml',
                            r'graphics\_materials\nlepine-m-20130709174151.material.xml',
                            r'graphics\_materials\paulmaidens-m-9223372094509410101.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372122833424970.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372122833434827.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372122833434828.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372122833434829.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372083440701880.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372083440701879.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372083440701878.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372083440701877.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372083440868941.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372083440868940.material.xml',
                            r'graphics\_materials\nlepine-m-20130709174957.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372122833424973.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372122833430154.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372084492172848.material.xml',
                            r'graphics\_materials\tat-sinleau-m-9223372089684354630.material.xml',
                            r'graphics\_materials\nlepine-m-20130709175000.material.xml',
                            r'graphics\_materials\mabelleau-m-9223372122833431387.material.xml',
                            ])

        self.progressbar_setmax(len(materials_ids))
        geometry_objects_set = set()
        for materials_id in materials_ids:
            self.progressbar_update()
            material_obj = self.material_objects.get(materials_id)

            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(material_obj, "Geometry", "up")

            for item in self.recursive_search_items:
                geometry_objects_set.add(item)

        print len(geometry_objects_set)

        self.progressbar_setmax(len(geometry_objects_set))
        for geometry_object in geometry_objects_set:
            self.progressbar_update()
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(geometry_object, "Entity", "up")
            output_dict[geometry_object] = self.recursive_search_items

        return output_dict

    def get_material_is_illegal(self):
        geo_instance_count_dict = {}
        self.progressbar_setmax(len(self.material_objects))
        for id, obj in self.material_objects.iteritems():
            is_illegal = obj.parameters.get("isillegal")
            if not is_illegal: # test if None
                continue
            if is_illegal == "0":
                continue
            self.progressbar_update()
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj, "Entity", "up")
            geo_instance_count_dict[obj] = self.recursive_search_items
        return geo_instance_count_dict
        
    def get_texture_stats(self):
        geo_instance_count_dict = {}
        self.progressbar_setmax(len(self.texture_objects))
        
        texture_set = set()
        for id, obj in self.texture_objects.iteritems():
            texture_set.add(obj)
            
        for obj in texture_set:
            obj._texture_profiles = self.texture_profiles
            obj.get_compiled_size()
            obj.size = str(obj.compiled_size)
            obj.special_info = str(obj.profile)
            self.progressbar_update()
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj, "Entity", "up")
            geo_instance_count_dict[obj] = self.recursive_search_items
        return geo_instance_count_dict

    def get_uncompressed_texture_used_in_world(self):
        output_dict = {}

        texture_set = set()
        for id, obj in self.texture_objects.iteritems():
            texture_set.add(obj)

        self.progressbar_setmax(len(texture_set))

        for obj in texture_set:
            self.progressbar_update()

            self.recursive_search_items = list()  # empty the list in case it contains something else
            self.recursive_search(obj, "Entity", "up")

            if len(self.recursive_search_items) == 0: #  skip all textures not referenced in the world
                continue

            obj._texture_profiles = self.texture_profiles
            obj.get_compiled_size()
            obj.size = str(obj.compiled_size)
            obj.special_info = str(obj.profile)

            if obj.profile is None:
                print obj.filename
                continue

            if obj.compression_enabled == '0' or '32bpp' in obj.profile:
                output_dict[obj] = list() #  self.recursive_search_items

        return output_dict

    def get_bfp_stats(self):
        geo_instance_count_dict = {}
        self.progressbar_setmax(len(self.building_facade_prefab_libraries_objects))
        for id, obj in self.building_facade_prefab_libraries_objects.iteritems():
            self.progressbar_update()
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj, "Entity", "up")
            geo_instance_count_dict[obj] = self.recursive_search_items
        return geo_instance_count_dict
        
    def get_illegal_geometry_stats(self):
        geo_instance_count_dict = {}
        self.progressbar_setmax(len(self.geometry_objects))
        for id, obj in self.geometry_objects.iteritems():
            if "geometry" not in obj.filename and "lofts" not in obj.filename and "gfx" not in obj.filename:
                self.progressbar_update()
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(obj, "Entity", "up", "Proxy", "Proxy")
                geo_instance_count_dict[obj] = self.recursive_search_items
        return geo_instance_count_dict
        
    def get_wd2_geometry_stats(self):
        geo_instance_count_dict = {}
        self.progressbar_setmax(len(self.geometry_objects))
        for id, obj in self.geometry_objects.iteritems():
            if "_geometries" in obj.filename and "facade" not in obj.filename:
                self.progressbar_update()
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(obj, "Entity", "up")
                geo_instance_count_dict[obj] = self.recursive_search_items
        return geo_instance_count_dict
        
    def get_wd2_facade_stats(self):
        geo_instance_count_dict = {}
        self.progressbar_setmax(len(self.geometry_objects))
        for id, obj in self.geometry_objects.iteritems():
            if "_geometries" in obj.filename and "facade" in obj.filename:
                self.progressbar_update()
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(obj, "Entity", "up")
                geo_instance_count_dict[obj] = self.recursive_search_items
        return geo_instance_count_dict
        
    def get_wd3_facade_stats(self):
        current_studio = str(self.UI.comboBox_filter.currentText())
        regions = self.get_region_list(current_studio)
        
        geometry_output_dict = {}
        
        geo_set = set()
        for geo in self.geometry_objects.values():
            geo_set.add(geo)
        
        for geo in geo_set:
            geo._entity_instance_count = 0
        
        entity_set = set()
        for entity in self.entity_objects.values():
            entity_set.add(entity)
        
        for entity in entity_set:
            if entity.region in regions:
                self.recursive_search_items = []
                self.recursive_search(entity, "Geometry", "down")
                for geo in self.recursive_search_items:
                
                    if not geo.is_facade:
                        continue
                    if "building_kit" not in geo.filename:
                        continue
                    
                    if geo not in geometry_output_dict.keys():
                        geometry_output_dict[geo] = []
                    geometry_output_dict[geo].append(entity)
                    geo._entity_instance_count += 1
        return geometry_output_dict
        
        '''
        geo_instance_count_dict = {}
        self.progressbar_setmax(len(self.geometry_objects))
        for id, obj in self.geometry_objects.iteritems():
            #if "geometry" in obj.filename and "building_kit" in obj.filename:
            if obj.is_facade and "building_kit" in obj.filename:
                self.progressbar_update()
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(obj, "Entity", "up")
                geo_instance_count_dict[obj] = self.recursive_search_items
                obj._entity_instance_count = len(self.recursive_search_items)
        return geo_instance_count_dict
        '''
        
        
    def get_wd3_facade_stats_in_mtl_fp(self):
        for geo in self.geometry_objects.values():
            geo._entity_instance_count = 0
        geo_instance_count_dict = {}
        for entity in self.entity_objects.values():
            if entity.region == 51:
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(entity, "Geometry", "down")
                for geo in self.recursive_search_items:
                    if "geometry" in geo.filename and "building_kit" in geo.filename:
                        if geo not in geo_instance_count_dict.keys():
                            geo_instance_count_dict[geo] = []
                        geo._entity_instance_count += 1
                        geo_instance_count_dict[geo].append(entity)
        return geo_instance_count_dict
    
    def shader_finder(self, shader_type):
        shader_type = shader_type.lower()
        shader_dict = {}
        self.progressbar_setmax(len(self.material_objects))
        for id, obj in self.material_objects.iteritems():
            if shader_type in obj.shader.lower():
                self.progressbar_update()
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(obj, "Entity", "up")
                shader_dict[obj] = self.recursive_search_items
        return shader_dict
        
    def get_plaza_stats(self):
        output_dict = {}
        plazas_dict = {}
        self.progressbar_setmax(len(self.entity_objects))
        for obj in self.entity_objects.values():
            if obj.entity_type == "Plaza":
                try:
                    self.progressbar_update()
                    self.recursive_search_items = [] # empty the list in case it contains something else
                    self.recursive_search(obj, "Geometry", "down")
                    plaza_resource = "None"
                    plaza_resource = self.recursive_search_items[0]
                    plaza_id = self.recursive_search_items[0], obj.special_info
                    if plaza_id not in plazas_dict.keys():
                        plazas_dict[plaza_id] = []
                    plazas_dict[plaza_id].append(obj)
                except:
                    print obj.identifier + " failed in get_plaza_stats()"
        for tuple_id, list in plazas_dict.iteritems():
            if len(list) > 1:
                try:
                    output_dict[tuple_id[0]] += list                    
                except:
                    output_dict[tuple_id[0]] = []
        return output_dict

    def get_plaza_geometry_by_kill_distance(self):
        self.update_status_bar("Get plaza geometry...")
        output_dict = {}
        for entity in self.entity_objects.values():
            if entity.entity_type != "Plaza":
                continue

            kill_distance = 0
            self.recursive_search_items = []  # empty the list in case it contains somthing else
            self.recursive_search(entity, "Geometry", "down", None)
            for geo in self.recursive_search_items:
                geo.special_info = int(geo.kill_distance)

                if geo not in output_dict.keys():
                    output_dict[geo] = list()

                output_dict[geo].append(entity)

        return output_dict
        
    def get_building_stats(self, area):
        output_dict = {}

        for obj in self.entity_objects.values():
            if obj.entity_type == "Building":
                obj.special_info = str(int(obj.building_ideal_killdistance)).zfill(4)
                # obj.special_info = str(int(obj.building_surface_area)).zfill(5) + " " + "{:.2f}".format(obj.building_facade_ratio) + " " + str(obj.building_facade_count)
                #obj.special_info = str(int(obj.building_surface_area)).zfill(5)
                if obj.shape_area < area:
                    output_dict[obj] = [obj]
        return output_dict
    
    def get_geometry_used_in_mtl(self):
        geo_instance_count_dict = {}
        for entity in self.entity_objects.values():
            if entity.entity_type == "Building":
                continue
            if entity.region == 1 or entity.region == 51:
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(entity, "Geometry", "down")
                for geo in self.recursive_search_items:
                    if geo not in geo_instance_count_dict.keys():
                        geo_instance_count_dict[geo] = []
                    geo_instance_count_dict[geo].append(entity)
        return geo_instance_count_dict
        
    def get_gameplay_ingredients_used_in_mtl_e3(self):
        arc_instance_count_dict = {}
        for entity in self.entity_objects.values():
            if entity.region == 51:
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(entity, "Archetype", "down")
                for arc in self.recursive_search_items:
                    if "wd2_gameplay_ingredients" in arc.filename:
                        if arc not in arc_instance_count_dict.keys():
                            arc_instance_count_dict[arc] = []
                        arc_instance_count_dict[arc].append(entity)
        return arc_instance_count_dict
        
    def get_breakables(self):
        arc_instance_count_dict = {}
        for entity in self.entity_objects.values():
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(entity, "Archetype", "down")
            for arc in self.recursive_search_items:
                if "Breakable" in arc.archetype_class:
                    if arc not in arc_instance_count_dict.keys():
                        arc_instance_count_dict[arc] = []
                    arc_instance_count_dict[arc].append(entity)
        return arc_instance_count_dict
    
    def get_breakables_used_in_mtl_e3(self):
        arc_instance_count_dict = {}
        for entity in self.entity_objects.values():
            if entity.region == 51:
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(entity, "Archetype", "down")
                for arc in self.recursive_search_items:
                    if "Breakable" in arc.archetype_class:
                        if arc not in arc_instance_count_dict.keys():
                            arc_instance_count_dict[arc] = []
                        arc_instance_count_dict[arc].append(entity)
        return arc_instance_count_dict
    
    def get_proxy_with_illegal_graphic_data(self):
        bad_proxies = {}
        for proxy in self.proxy_objects.values():
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(proxy, "Geometry", "down")
            for item in self.recursive_search_items:
                if "_geometries" not in item.filename:
                    if "gfx" not in item.filename:
                        if "lofts" not in item.filename:
                            if item not in bad_proxies.keys():
                                bad_proxies[item] = []
                                if proxy not in bad_proxies[item]:
                                    bad_proxies[item].append(proxy)
                            else:
                                if proxy not in bad_proxies[item]:
                                    bad_proxies[item].append(proxy)
                                    
        for proxy in self.proxy_objects.values():
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(proxy, "Texture", "down")
            for item in self.recursive_search_items:
                if "_geometries" not in item.filename:
                    if "gfx" not in item.filename:
                        if "_generic_textures" not in item.filename:
                            if item not in bad_proxies.keys():
                                bad_proxies[item] = []
                                if proxy not in bad_proxies[item]:
                                    bad_proxies[item].append(proxy)
                            else:
                                if proxy not in bad_proxies[item]:
                                    bad_proxies[item].append(proxy)
                    
        return bad_proxies

    def get_clo_stats(self, filter):
        clo_count_dict = {}
        self.progressbar_setmax(len(self.generic_item_objects))
        for obj in self.generic_item_objects.values():
            if filter and filter != obj.lib_name:
                continue
            if obj.isCLO():
                self.progressbar_update()
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(obj, "Entity", "up")
                clo_count_dict[obj] = self.recursive_search_items
        return clo_count_dict
    
    def get_missing_resource(self, type):
        res_dict = None
        if type == "materials":
            res_dict = self.geometry_objects
        elif type == "textures":
            res_dict = self.material_objects
            
        output_dict = {}
        
        exclusion_list = [".glm",".hkx",".lft",".gamex","_cg_",".impostor."]
            
        self.progressbar_setmax(len(res_dict))          
        for res in res_dict.values():
            self.progressbar_update()
            deps = set()
            for dep in res.dependencies:
                is_in_list = False
                for string in exclusion_list:
                    if string in dep:
                        is_in_list = True
                        break
                if is_in_list:
                    continue
                if self.find_something(dep) is not None:
                    continue
                deps.add(dep)
            
            if len(deps) > 0:
                output_dict[res] = []
                for dep in deps:
                    output_dict[res].append(adp.d_missing(dep))
           
        return output_dict
        
    def get_proxy_with_missing_reference(self):
        output_dict = {}
        
        proxy_set = set()
        for proxy in self.proxy_objects.values():
            proxy_set.add(proxy)

        for proxy in proxy_set:
            self.progressbar_update()
            deps = set()
            for dep in proxy.dependencies:
                if self.find_something(dep) is not None:
                    continue
                deps.add(dep)
            
            if len(deps) > 0:
                output_dict[proxy] = []
                for dep in deps:
                    output_dict[proxy].append(adp.d_missing(dep))


        return output_dict
        
    def get_geometry_with_no_parent(self):
        output_dict = {}
        
        for geo in self.geometry_objects.values():
            if len(geo._parents) == 0:
                output_dict[geo] = []
        
        return output_dict
  
    def spawn_messagebox(self, text):
        confirmation_box = QtGui.QMessageBox()
        confirmation_box.setWindowTitle("Yikes...")
        confirmation_box.setText(text)
        confirmation_box.setStandardButtons(QtGui.QMessageBox.Ok)# | QtGui.QMessageBox.Cancel)
        confirmation_box.setDefaultButton(QtGui.QMessageBox.Ok)
        confimation_status = confirmation_box.exec_()
  
    def get_jira_issues(self, filter, container_dict, issue_fields=[]):
        self.update_status_bar("Sniffing JIRA issues. DDV will stop responding, it's normal and it will come back after a few minutes. Time for a bathroom break.")
        jira_wd3 = {
            'server': 'https://mdc-tomcat-jira88.ubisoft.org/jira/',
            'verify':False,
        }
        
        try:
            jira = JIRA(jira_wd3,basic_auth=(self.UI.lineEdit_jira_login.text(), self.UI.lineEdit_jira_pwd.text()),max_retries=0) 
        # except:
            # self.spawn_messagebox(
            # '''JIRA login or password is incorrect.
            # Did you recently change your Windows password...?''')
            # return False
        except JIRAError as e:
            if e.status_code == 401:
                self.spawn_messagebox("JIRA login or password is incorrect.<br />Did you recently change your Windows password...?<br />Go to the Control Panel and make sure your JIRA password is correct.")
            return False
            
        projects = jira.projects()
        
        search_amount = 1000
        got = search_amount
        total = 0
        while got==search_amount:
            issues = jira.search_issues(filter, startAt = total, maxResults=search_amount, fields=issue_fields)
            container_dict += issues
            got = len(issues)
            total += got
            self.refresh_ui()
        
        self.update_status_bar("JIRA issues sniffed.")
        return True
    
    def get_geometry_with_no_jira_in_studio(self):
        current_studio = str(self.UI.comboBox_filter.currentText())
        regions = self.get_region_list(current_studio)
        
        geometry_jira_output_dict = {}
        if not self.link_geometry_to_jira_issue():
            return geometry_jira_output_dict 
        
        geo_set = set()
        for geo in self.geometry_objects.values():
            geo_set.add(geo)
        
        for geo in geo_set:
            geo._entity_instance_count = 0
        
        for entity in self.entity_objects.values():
            if entity.region in regions:
                self.recursive_search_items = []
                self.recursive_search(entity, "Geometry", "down")
                for geo in self.recursive_search_items:
                    if geo.is_facade:
                        continue
                    if geo.jira_issue is not None:
                        continue
                    if "metrics" in geo.filename:
                        continue
                    if "leveldesign" in geo.filename:
                        continue
                    if "vehicles_nexus" in geo.filename:
                        continue
                    if "vegetation" in geo.filename:
                        continue
                    if geo not in geometry_jira_output_dict.keys():
                        geometry_jira_output_dict[geo] = []
                    geometry_jira_output_dict[geo].append(entity)
                    geo._entity_instance_count += 1
        return geometry_jira_output_dict                      
        
    def get_splines_using_wrong_road_materials(self):
        output_dict = {}
        
        for spline in self.spline_objects.values():
            if "thw" in spline.filename:
                continue
            for range in spline._children:
                for item in range._children:
                    if "TOWER" in item.name:
                        if spline not in output_dict.keys():
                            output_dict[spline] = []
                        output_dict[spline].append(item)                     

        return output_dict
    
    def get_geometry_status_from_jira(self):
        geometry_jira_output_dict = {}
        
        if not self.link_geometry_to_jira_issue():
            return geometry_jira_output_dict
        
        geo_set = set()
        for geo in self.geometry_objects.values():
            geo_set.add(geo)
            
        self.progressbar_setmax(len(geo_set))
        for geo in geo_set:
            self.progressbar_update()
            if geo.jira_issue is not None:
                geo.special_info = geo.jira_status + ", " + geo.jira_issue + ", " + geo.jira_studio + ", " + geo.jira_loq + ", " + geo.jira_borough
                self.recursive_search_items = [] # empty the list in case it contains something else
                self.recursive_search(geo, "Entity", "up")
                geometry_jira_output_dict[geo] = self.recursive_search_items
                geo._entity_instance_count = len(self.recursive_search_items)
        
        return geometry_jira_output_dict
        
    def link_geometry_to_jira_issue(self):
        self.jira_ob_issues = []
        
        fields_list = ["summary","status","customfield_11067","customfield_11354","customfield_11241","customfield_10886"]
        if not self.get_jira_issues(self.UI.lineEdit_jira_filter.text(), self.jira_ob_issues, fields_list):
            return False
            
        self.update_status_bar("Linking JIRA issues to geometries. Yes, it is now MUCH faster.")
            
        geo_dict = {}
        for geo in self.geometry_objects.values():
            geo_dict[geo.name.lower()] = geo

        self.progressbar_setmax(len(self.jira_ob_issues))
        summaries_set = set()
        unlinked_issues_set = set()
        for issue in self.jira_ob_issues:
            self.progressbar_update()
            found_obj = None

            current_id = issue.fields.customfield_10886            
            summary = issue.fields.summary.replace(" ","").lower()
                
            if current_id is not None:
                try:
                    current_id = hex(int(current_id)).replace("L","").lower()
                    found_obj = self.geometry_objects.get(current_id, None)
                    summaries_set.add(summary)
                except:
                    pass
                    #print str(issue), "has a bad FileID."
                    
            if found_obj is None:
                unlinked_issues_set.add(issue)
                continue

            found_obj.jira_issue = str(issue)
            found_obj.jira_status = str(issue.fields.status)
            found_obj.jira_studio = str(issue.fields.customfield_11067)
            found_obj.jira_loq = str(issue.fields.customfield_11354)
            found_obj.jira_borough = str(issue.fields.customfield_11241)
            found_obj.jira_id = str(issue.fields.customfield_10886)
            
            # add entry in geometry dict so that search queries find the new parameters (important for JIRA)
            found_obj._content = found_obj.get_content("|")
            self.geometry_objects[found_obj._content] = found_obj
        self.progressbar_reset(True)
        
        # do a second loop with the unlinked issues to get them by name
        self.update_status_bar("Linking JIRA issues by name.")
        self.progressbar_setmax(len(unlinked_issues_set))
        for issue in unlinked_issues_set:
            self.progressbar_update()
            summary = issue.fields.summary.replace(" ","").lower()
            if summary in summaries_set:
                continue
            found_obj = geo_dict.get(summary)
            
            if found_obj is None:
                continue
                
            found_obj.jira_issue = str(issue)
            found_obj.jira_status = str(issue.fields.status)
            found_obj.jira_studio = str(issue.fields.customfield_11067)
            found_obj.jira_loq = str(issue.fields.customfield_11354)
            found_obj.jira_borough = str(issue.fields.customfield_11241)
            found_obj.jira_id = str(issue.fields.customfield_10886)
            
            # add entry in geometry dict so that search queries find the new parameters (important for JIRA)
            found_obj._content = found_obj.get_content("|")
            self.geometry_objects[found_obj._content] = found_obj 
                
        self.update_status_bar("Linking JIRA issues DONE.")
        self.progressbar_reset(True)
        return True
    
    def get_proxy_with_no_jira(self):
        bad_proxies = {}
        if not self.link_geometry_to_jira_issue():
            return bad_proxies
        
        for proxy in self.proxy_objects.values():
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(proxy, "Geometry", "down")
            for geo in self.recursive_search_items:
                is_bad = False
                if geo.jira_issue == None:
                    is_bad = True
                if geo.jira_status == "Deleted Request":
                    is_bad = True
                if geo.jira_status == "Request Denied":
                    is_bad = True
                if geo.jira_status == "Deleted Prototype":
                    is_bad = True
                if geo.jira_status == "Mock-up Request":
                    is_bad = True

                if is_bad:
                    if proxy not in bad_proxies.keys():
                        bad_proxies[proxy] = []
                    if geo not in bad_proxies[proxy]:
                        bad_proxies[proxy].append(geo)
                
        return bad_proxies
        
    def get_proxy_with_no_jira_in_world(self):
        bad_proxies = {}
        if not self.link_geometry_to_jira_issue():
            return bad_proxies
        for proxy in self.proxy_objects.values():
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(proxy, "Geometry", "down")
            geos = self.recursive_search_items
            for geo in geos:
                is_bad = False
                if geo.jira_issue == None:
                    is_bad = True
                if geo.jira_status == "Deleted Request":
                    is_bad = True
                if geo.jira_status == "Request Denied":
                    is_bad = True
                if geo.jira_status == "Deleted Prototype":
                    is_bad = True
                if geo.jira_status == "Mock-up Request":
                    is_bad = True

                if is_bad:
                    if proxy not in bad_proxies.keys():
                        self.recursive_search_items = [] # empty the list in case it contains something else
                        self.recursive_search(proxy, "Entity", "up")
                        bad_proxies[proxy] = self.recursive_search_items
                        # bad_proxies[proxy] = []
                    # if geo not in bad_proxies[proxy]:
                        # bad_proxies[proxy].append(geo)
                
        return bad_proxies
    
    def get_vehicle_enticers_variety(self):
        current_studio = str(self.UI.comboBox_filter.currentText())
        regions = self.get_region_list(current_studio)
        
        self.reset__entity_instance_count()
    
        instance_count_dict = {}
        for entity in self.entity_objects.values():
            if entity.region not in regions:
                continue
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(entity, "Generic Item", "down")
            for item in self.recursive_search_items:
                if "vehiclespawninfo" not in item.filename:
                    continue
                if item not in instance_count_dict.keys():
                    instance_count_dict[item] = []
                instance_count_dict[item].append(entity)
                item._entity_instance_count += 1
        return instance_count_dict
    
    def get_pink_objects_list(self):
        self.update_status_bar("Get pink... PINK!?... Pink is the new black.")
        
        current_studio = str(self.UI.comboBox_filter.currentText())
        regions = self.get_region_list(current_studio)
        
        pink_materials = []
        for mat_obj in self.material_objects.values():
            for val in mat_obj.parameters.values():
                if val == "999,0,999":
                    pink_materials.append(mat_obj)
                    break
        
        for obj_mat in pink_materials:
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj_mat, "Geometry", "up")
            for item in self.recursive_search_items:
                item.is_pink = True
                
        self.reset__entity_instance_count()
        
        geometry_jira_output_dict = {}
        for entity in self.entity_objects.values():
            if entity.region not in regions:
                continue
            if entity.region in regions:
                self.recursive_search_items = []
                self.recursive_search(entity, "Geometry", "down")
                for geo in self.recursive_search_items:
                    if not geo.is_pink:
                        continue
                    if geo not in geometry_jira_output_dict.keys():
                        geometry_jira_output_dict[geo] = []
                    geometry_jira_output_dict[geo].append(entity)
                    geo._entity_instance_count += 1
        return geometry_jira_output_dict
    
    def get_entity_in_region(self):
        self.update_status_bar("Get entity in region...")
        
        output_dict = {}
        
        current_studio = str(self.UI.comboBox_filter.currentText())
        regions = self.get_region_list(current_studio)
        
        for entity in self.entity_objects.values():
            if entity.region in regions:
                output_dict[entity] = []
                
        return output_dict
    
    def get_props_catalogs(self):
        if len(self.jira_ob_issues) == 0:
            self.get_geometry_status_from_jira()
            
        output_dict = {}
        for world_layer in self.world_layer_objects.values():
            layer_name = str(self.UI.comboBox_filter.currentText())
            if layer_name == "All":
                if "catalog" not in world_layer.filename:
                    continue
            else:
                if world_layer.name != layer_name:
                    continue
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(world_layer, "Geometry", "down")
            for geo in self.recursive_search_items:
                if "leveldesign" in geo.filename:
                    continue
                if world_layer not in output_dict.keys():
                    output_dict[world_layer] = []
                output_dict[world_layer].append(geo)
        return output_dict
        
    def get_list_separator(self):
        '''Retrieves the Windows list separator character from the registry'''
        aReg = ConnectRegistry(None, HKEY_CURRENT_USER)
        aKey = OpenKey(aReg, r"Control Panel\International")
        val = QueryValueEx(aKey, "sList")[0]
        return val
    
    def get_geometry_using_default_logic_mat(self):
        geo_instance_count_dict = {}
        gx = adp.import_gamex(r"W:\main\python")# import gamex lib from root EPA
        if not gx:
            return geo_instance_count_dict  # return empty dict if importing of gamex failed
        
        geo_set = set()
        for geo in self.geometry_objects.values():
            geo_set.add(geo)
                
        self.progressbar_setmax(len(geo_set))
                
        for geo in geo_set:
            self.progressbar_update()
            if not geo.is_gamex:
                continue

            logic_mat_set = geo.get_logic_material_ids(gx)

            if logic_mat_set is None:
                continue

            if 0 not in logic_mat_set:
                continue
            
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(geo, "Entity", "up")
            
            if geo not in geo_instance_count_dict.keys():
                geo_instance_count_dict[geo] = set()
                
            for entity in self.recursive_search_items:
                geo_instance_count_dict[geo].add(entity)
                
        return geo_instance_count_dict
    
    def get_range_with_no_definition(self):
        output_dict = {}
        
        range_set = set()
        for range in self.range_objects.values():
            range_set.add(range)
        
        for range in range_set:
        
            if range.definition != "18446744073709551615":
                continue
        
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(range, "Spline", "up")
        
            for spline in self.recursive_search_items:
                if spline not in output_dict.keys():                    
                    output_dict[spline] = set()
                output_dict[spline].add(range)
        
        return output_dict

    def get_range_with_illegal_geometry(self):
        output_dict = {}

        range_set = set()
        for range_object in self.range_objects.values():
            range_set.add(range_object)

        for range_object in range_set:
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(range_object, "Geometry", "down")

            for item in self.recursive_search_items:
                if 'geometry' in item.filename:
                    continue
                if 'lights' in item.filename:
                    continue
                if 'gameplay_ingredients' in item.filename:
                    continue
                if item not in output_dict.keys():
                    output_dict[item] = set()
                # output_dict[item].add(range_object)

        for geo in output_dict.keys():
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(geo, "Generic Item", "up")

            for item in self.recursive_search_items:
                if 'splinedefinition' not in item.filename:
                    continue
                output_dict[geo].add(item)

        return output_dict


    def get_logic_materials(self):
        output_dict = {}
        gx = adp.import_gamex(r"W:\main\python")# import gamex lib from root EPA
        if not gx:
            return output_dict  # return empty dict if importing of gamex failed

        logic_materials = {}        
        for generic_item in self.generic_item_objects.values():
            if "logicmaterials" not in generic_item.filename:
                continue
            logic_materials[generic_item.custom_id] = generic_item
            output_dict[generic_item] = set()
            
        geo_set = set()
        for geo in self.geometry_objects.values():
            geo_set.add(geo)
                
        
        self.progressbar_setmax(len(geo_set))      
        for geo in geo_set:
            self.progressbar_update()
            
            # if not geo.is_gamex:
            #     continue
                
            if r"\graphics\users" in geo.filename:
                continue
                
            if r"\graphics\metrics" in geo.filename:
                continue
            
            if r"\graphics\editor" in geo.filename:
                continue

            logic_mat_set = geo.get_logic_material_ids(gx)
            if logic_mat_set is None:
                continue

            for logic_material_id in logic_mat_set:
                logic_material_id = str(logic_material_id)
                if logic_material_id == "-1": # prevent a crash caused by test data made by Carlos
                    continue
                current_logic_material = logic_materials.get(logic_material_id)
                if not current_logic_material:
                    print geo.filename, "contains logic material ID", logic_material_id, "is that normal?"
                    continue
                if current_logic_material not in output_dict:
                    output_dict[logic_materials[logic_material_id]] = set()
                output_dict[logic_materials[logic_material_id]].add(geo)
        
        return output_dict
    
    def get_prop_library(self):
        output_dict = {}
        
        object_set = set()
        for object in self.generic_item_objects.values():
            object_set.add(object)
        
        total_bad_geo = 0
        for object in object_set:
            if "prop.xml" not in object.filename:
                continue
        
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(object, "Geometry", "down")
        
            for item in self.recursive_search_items:
                if item not in output_dict.keys():
                    lods = set()
                    for value in item.lod_distances:
                        value = int(float(value))
                        if value == 0:
                            continue
                        lods.add(value)

                    item.get_compiled_size()
                    
                    if len(lods) == 1:
                        total_bad_geo += item.compiled_size
                    
                    item.special_info =  str(len(lods)) + " - " + str(item.compiled_size)
                    
                    output_dict[item] = set()
                output_dict[item].add(object)
                
        print "Total compiled size of objects that have no LOD:", total_bad_geo
        
        return output_dict
        
    def get_geometry_with_one_lod(self):
        output_dict = {}
        
        object_set = set()
        for object in self.geometry_objects.values():
            object_set.add(object)
            
        for object in object_set:
            if object in output_dict.keys():
                continue

            lods = set()
            for value in object.lod_distances:
                value = int(float(value))
                if value == 0:
                    continue
                lods.add(value)
            if len(lods) != 1:
                continue
                
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(object, "Entity", "up")
        
            output_dict[object] = self.recursive_search_items
            
        return output_dict
    
    def get_building_optim(self):
        output_dict = {}
        
        building_id_set = set()
        file = r"W:\main\td_tools\PythonTools\DDV\resources\building_optim.txt"
        with open(file) as f:
            lines = f.readlines()            
        for line in lines:
            if line.isspace():
                continue
            line = line.lower()
            line = line.strip()
            building_id_set.add(line)
        
        object_set = set()
        for object in self.entity_objects.values():
            if object.entity_type != "Building":
                continue
            if object.identifier not in building_id_set:
                continue
            object_set.add(object)
            
        for object in object_set:
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(object, "Geometry", "down")
            
            for item in self.recursive_search_items:
                
                if not output_dict.get(item):
                    output_dict[item] = []
                
                output_dict[item].append(object)
        
        return output_dict
    
    def get_geometry_in_city_block_prop(self):
        output_dict = {}
        
        for city_block in self.city_block_cell_objects.values():
            
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(city_block, "Geometry", "down")
            
            for item in self.recursive_search_items:
                if city_block not in output_dict.keys():                    
                    output_dict[city_block] = set()
                output_dict[city_block].add(item)
        
        return output_dict

    def get_external_file_content(self):
        content = set()
        opened_file = open(join(dirname(__file__), "resources/input_external_file.txt"), "r")
        for line in opened_file:
            content.add(line.replace("\n", ""))
        return content

    def get_geometry_from_external_file(self):
        output_dict = {}

        external_file_content = self.get_external_file_content()
        print external_file_content

        for city_block in self.city_block_cell_objects.values():

            self.recursive_search_items = []  # empty the list in case it contains something else
            self.recursive_search(city_block, "Geometry", "down")

            for item in self.recursive_search_items:
                if item.default_id_int not in external_file_content:
                    continue
                if city_block not in output_dict.keys():
                    output_dict[city_block] = set()
                output_dict[city_block].add(item)

        return output_dict
        
    def get_geometry_with_duplicated_lods(self):
        self.update_status_bar("Getting geometries with duplicated LODs.")
        output_dict = {}
        gx = adp.import_gamex(r"W:\main\python")# import gamex lib from root EPA
        if not gx:
            return output_dict  # return empty dict if importing of gamex failed        
        
        geo_set = set()
        for geo in self.geometry_objects.values():
            geo_set.add(geo)
            
        for geo in geo_set:
            # if "\\geometry" not in geo.filename:
                # continue
                
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(geo, "Entity", "up")
            
            entities = self.recursive_search_items
            if len(entities) == 0:
                continue
                
            if not geo.is_gamex:
                continue
            
            current_file = geo.filename.replace(".xml",".gamex")
            
            if not isfile(current_file):
                print current_file, "does not exist."
                continue
            
            geo.lod_triangle_count = geo.get_triangle_count_per_lod_from_gamex(current_file, gx)
            
            lod_triangle_count_list = geo.lod_triangle_count.values()
            lod_triangle_count_list.sort()
            for i in range (len (lod_triangle_count_list) -1):
                if lod_triangle_count_list[i] == lod_triangle_count_list[i+1]:
                    output_dict[geo] = entities
        
        return output_dict
        
    def get_geometry_in_propxml(self):
        output_dict = {}
        gx = adp.import_gamex(r"W:\main\python")# import gamex lib from root EPA
        if not gx:
            return output_dict  # return empty dict if importing of gamex failed        
        
        item_set = set()
        
        
        for item in self.generic_item_objects.values():
            if "prop.xml" not in item.filename:
                continue
            item_set.add(item)
            
        for item in item_set:
            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(item, "Geometry", "down")
            
            for geo in self.recursive_search_items:
            
                geo.get_compiled_size()
                geo.size = geo.compiled_size
                
                current_file = geo.filename.replace(".xml",".gamex")
            
                if isfile(current_file):                
                    geo.lod_triangle_count = geo.get_triangle_count_per_lod_from_gamex(current_file, gx)
                else:
                    geo.get_glm_data(geo.filename)
                geo.special_info = str(len(geo.lod_triangle_count))
                    
                if not output_dict.get(geo):
                    output_dict[geo] = []
                
                output_dict[geo].append(item)

        return output_dict

    def get_prefab_roof(self):
        output_dict = dict()

        for obj in self.prefab_item_objects.values():

            is_wanted = False

            if 'art_exterior_generic_rooftop_dressing' in obj.filename:
                is_wanted = True

            if 'art_exterior_generic_building_dressing' in obj.filename:
                is_wanted = True

            if not is_wanted:
                continue

            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj, "Entity", "up")

            entities = self.recursive_search_items

            self.recursive_search_items = [] # empty the list in case it contains something else
            self.recursive_search(obj, "Material", "down")

            materials = set(self.recursive_search_items)

            obj.special_info = str(len(materials))
            obj._entity_instance_count = len(entities)

            output_dict[obj] = entities

        return output_dict

    def get_geometry_in_road_splines(self):
        output_dict = {}

        spline_set = set()
        for spline in self.spline_objects.values():
            spline_set.add(spline)

        for spline in spline_set:
            self.recursive_search_items = []  # empty the list in case it contains something else
            self.recursive_search(spline, "Geometry", "down")

            for geo in self.recursive_search_items:
                # if 'lofts' in geo.filename:
                #     continue
                # if 'decals' in geo.filename:
                #     continue

                geo.special_info = str(geo.kill_distance).zfill(8)

                if geo not in output_dict.keys():
                    output_dict[geo] = []
                output_dict[geo].append(spline)

        return output_dict

    def get_geometry_signs(self):
        output_dict = {}

        entity_set = set()
        for entity in self.entity_objects.values():
            entity_set.add(entity)

        for entity in entity_set:
            self.recursive_search_items = []  # empty the list in case it contains something else
            self.recursive_search(entity, "Geometry", "down")

            for geo in self.recursive_search_items:
                if 'sign' not in geo.filename:
                    continue

                geo.special_info = str(geo.kill_distance).zfill(8)

                if geo not in output_dict.keys():
                    output_dict[geo] = []
                output_dict[geo].append(entity)

        return output_dict

    def write_csv_from_dict(self, dict, include_children):
        #output_file = r"C:\Users\gcassel\Desktop\test.csv"
        output_file = join(expanduser("~\.DDV"), "export.csv")
        output_string = ""
        
        separator = self.get_list_separator()
        
        # header = dict.values()[0][0].get_content_header(True)
        # output_string += header
        # output_string += "\n"
        
        # for parent, children in dict.iteritems():
            # for child in children:
                # header = child.get_content_header(True)
                # output_string += header
                # output_string += "\n"
                # break
            # break
        
        for parent, children in dict.iteritems():
            output_string += parent.get_content(separator, True)
            output_string += "SUBITEMS:"+str(len(children))
            output_string += "\n"
            if include_children:
                for child in children:
                    output_string += "    "
                    output_string += child.get_content(separator, True)
                    output_string += "\n"
            output_string += "\n"
            
        with open(output_file, "w") as myfile:
            myfile.write(output_string)
        
        return output_file
        
    def reset__entity_instance_count(self):
        item_set = set()
        
        for item in self.generic_item_objects.values():
            item_set.add(item)
        
        for item in self.geometry_objects.values():
            item_set.add(item)
        
        for item in item_set:
            item._entity_instance_count = 0
            
    def get_region_list(self, current_studio):
        regions = []
        if current_studio == "Default":
            regions += [0]
        if current_studio == "Montreal":
            regions += [1,51, 54, 55, 56, 57]
        if current_studio == "Montreal_FP":
            regions += [51, 54, 55, 56]
        if current_studio == "Toronto":
            regions += [2, 52, 53]
        if current_studio == "Paris":
            regions += [3]
        if current_studio == "Bucharest":
            regions += [4]
        if current_studio == "Piccadily":
            regions += [52]
        if current_studio == "Traffalgar":
            regions += [53]
        if current_studio == "Foodtown":
            regions += [54]
        if current_studio == "Bishop's Gate":
            regions += [55]
        if current_studio == "Construction":
            regions += [56]
        if current_studio == "Montreal Tower Hamlets East":
            regions += [57]
        if current_studio == "All":
            regions = range(0,100)
        return regions
    
    def changed_prop_combo(self):
        self.UI.comboBox_filter.clear()
        if str(self.UI.comboBox_prop.currentText()) == "CLO":
            lib_names = [""]
            lib_names.extend(self.get_clo_lib_names())
            for name in lib_names:
                self.UI.comboBox_filter.addItem(name)
       
        if (str(self.UI.comboBox_prop.currentText()) == "WD3 Facades" 
        or str(self.UI.comboBox_prop.currentText()) == "Geometry User Set Distances" 
        or str(self.UI.comboBox_prop.currentText()) == "Entity In Region" 
        or str(self.UI.comboBox_prop.currentText()) == "Geometry" 
        or str(self.UI.comboBox_prop.currentText()) == "Geometry With No JIRA In Studio Area" 
        or str(self.UI.comboBox_prop.currentText()) == "Vehicle Enticers Variety" 
        or str(self.UI.comboBox_prop.currentText()) == "Pink Objects"):
            self.UI.comboBox_filter.addItem("All")
            for site_tuple in self.zones_dict.values():
                self.UI.comboBox_filter.addItem(site_tuple[1])
                
        if str(self.UI.comboBox_prop.currentText()) == "PropsCatalogs":
            self.UI.comboBox_filter.addItem("All")
            for world_layer in self.world_layer_objects.values():
                if "catalog" not in world_layer.filename:
                    continue
                self.UI.comboBox_filter.addItem(world_layer.name)
                
        self.refresh_ui()

    def clicked_prop_gen(self):
        self.toggle_waitcursor(True)
        self.UI.tabWidget.setEnabled(False)
        
        stats = None

        current_item = str(self.UI.comboBox_prop.currentText())
        if current_item == "Proxy":
            stats = self.get_proxy_stats()
            self.fill_prop_tree(stats)
        elif current_item == "Geometry":
            stats = self.get_geometry_stats()
            self.fill_prop_tree(stats)
        elif current_item == "Geometry User Set Distances":
            stats = self.get_geometry_user_set_distances()
            self.fill_prop_tree(stats)
        elif current_item == "Material":
            stats = self.get_material_stats()
            self.fill_prop_tree(stats)
        elif current_item == "Material Has Animated Bink":
            stats = self.get_material_with_bink()
            self.fill_prop_tree(stats)
        elif current_item == "Material Has Animated Texture":
            stats = self.get_material_with_animated_texture()
            self.fill_prop_tree(stats)

        elif current_item == "Material From Media Broadcast References":
            stats = self.get_media_broadcast_material_references()
            self.fill_prop_tree(stats)

        elif current_item == "Material Two Sided":
            stats = self.get_material_two_sided_stats()
            self.fill_prop_tree(stats)
        elif current_item == "Material Is Illegal":
            stats = self.get_material_is_illegal()
            self.fill_prop_tree(stats)
        elif current_item == "Texture":
            stats = self.get_texture_stats()
            self.fill_prop_tree(stats)
        elif current_item == "Texture Uncompressed In World":
            stats = self.get_uncompressed_texture_used_in_world()
            self.fill_prop_tree(stats)
        elif current_item == "Building Facade Prefab":
            stats = self.get_bfp_stats()
            self.fill_prop_tree(stats)
        elif current_item == "Illegal Geometry":
            stats = self.get_illegal_geometry_stats()
            self.fill_prop_tree(stats)
        elif current_item == "WD2 Objects":
            stats = self.get_wd2_geometry_stats()
            self.fill_prop_tree(stats)
        elif current_item == "WD2 Facades":
            stats = self.get_wd2_facade_stats()
            self.fill_prop_tree(stats)
        elif current_item == "WD3 Facades":
            stats = self.get_wd3_facade_stats()
            self.fill_prop_tree(stats)
        elif current_item == "WD3 Facades in MTL FP":
            stats = self.get_wd3_facade_stats_in_mtl_fp()
            self.fill_prop_tree(stats)
        elif current_item == "Shader Finder":
            stats = self.shader_finder(self.UI.lineEdit_prop.text())
            self.fill_prop_tree(stats)
        elif current_item == "Plaza Duplicates":
            stats = self.get_plaza_stats()
            self.fill_prop_tree(stats)
        elif current_item == "Plaza Geometry By Kill Distance":
            stats = self.get_plaza_geometry_by_kill_distance()
            self.fill_prop_tree(stats)
        elif current_item == "Building":
            stats = self.get_building_stats(self.convert_line_edit_text_to_int(self.UI.lineEdit_prop.text()))            
            self.fill_prop_tree(stats)
        elif current_item == "Geometry Used In MTL":
            stats = self.get_geometry_used_in_mtl()
            self.fill_prop_tree(stats)
        elif current_item == "Gameplay Ingredients Used In MTL E3":
            stats = self.get_gameplay_ingredients_used_in_mtl_e3()
            self.fill_prop_tree(stats)            
        elif current_item == "Breakables":
            stats = self.get_breakables()
            self.fill_prop_tree(stats)
        elif current_item == "Breakables Used In MTL E3":
            stats = self.get_breakables_used_in_mtl_e3()
            self.fill_prop_tree(stats)
        elif current_item == "Proxy With Illegal Graphic Data":
            stats = self.get_proxy_with_illegal_graphic_data()
            self.fill_prop_tree(stats)
        elif current_item == "CLO":
            filter = str(self.UI.comboBox_filter.currentText())
            stats = self.get_clo_stats(filter)
            self.fill_prop_tree(stats)
        elif current_item == "Archetypes":
            stats = self.get_archetype_stats()
            self.fill_prop_tree(stats)
        elif current_item == "Missing Materials In Geometries":
            stats = self.get_missing_resource("materials")
            self.fill_prop_tree(stats)
        elif current_item == "Missing Textures In Materials":
            stats = self.get_missing_resource("textures")
            self.fill_prop_tree(stats)
        elif current_item == "Geometry JIRA Status":
            stats = self.get_geometry_status_from_jira()
            self.fill_prop_tree(stats)            
        elif current_item == "Splines Using Wrong Road Materials":
            stats = self.get_splines_using_wrong_road_materials()
            self.fill_prop_tree(stats)
        elif current_item == "Geometry With No JIRA In Studio Area":
            stats = self.get_geometry_with_no_jira_in_studio()
            self.fill_prop_tree(stats)
        elif current_item == "Proxy With No JIRA":
            stats = self.get_proxy_with_no_jira()
            self.fill_prop_tree(stats)
        elif current_item == "Proxy With No JIRA In World":
            stats = self.get_proxy_with_no_jira_in_world()
            self.fill_prop_tree(stats)
        elif current_item == "Vehicle Enticers Variety":
            stats = self.get_vehicle_enticers_variety()
            self.fill_prop_tree(stats)
        elif current_item == "Pink Objects":
            stats = self.get_pink_objects_list()
            self.fill_prop_tree(stats)
        elif current_item == "Geometry With No Parent":
            stats = self.get_geometry_with_no_parent()
            self.fill_prop_tree(stats)
        elif current_item == "Proxy With Missing References":
            stats = self.get_proxy_with_missing_reference()
            self.fill_prop_tree(stats)
        elif current_item == "Entity In Region":
            stats = self.get_entity_in_region()
            self.fill_prop_tree(stats)
        elif current_item == "PropsCatalogs":
            stats = self.get_props_catalogs()
            self.fill_prop_tree(stats)
        elif current_item == "Geometry Using Default Logic Material":
            stats = self.get_geometry_using_default_logic_mat()
            self.fill_prop_tree(stats)
        elif current_item == "Ranges With Illegal Geometry":
            stats = self.get_range_with_illegal_geometry()
            self.fill_prop_tree(stats)
        elif current_item == "Ranges With No Definition":
            stats = self.get_range_with_no_definition()
            self.fill_prop_tree(stats)
        elif current_item == "Logic Materials":
            stats = self.get_logic_materials()
            self.fill_prop_tree(stats)
        elif current_item == "Prop Library":
            stats = self.get_prop_library()
            self.fill_prop_tree(stats)
        elif current_item == "Geometry With One LOD":
            stats = self.get_geometry_with_one_lod()
            self.fill_prop_tree(stats)
        elif current_item == "Building Optim":
            stats = self.get_building_optim()
            self.fill_prop_tree(stats)
        elif current_item == "Geometry In City Block":
            stats = self.get_geometry_in_city_block_prop()
            self.fill_prop_tree(stats)
        elif current_item == "Geometry With Duplicated LODs":
            stats = self.get_geometry_with_duplicated_lods()
            self.fill_prop_tree(stats)
        elif current_item == "Geometry In prop.xml":
            stats = self.get_geometry_in_propxml()
            self.fill_prop_tree(stats)
        elif current_item == "Prefab Roof":
            stats = self.get_prefab_roof()
            self.fill_prop_tree(stats)
        elif current_item == "Geometry In Road Splines":
            stats = self.get_geometry_in_road_splines()
            self.fill_prop_tree(stats)
        elif current_item == "Geometry Signs":
            stats = self.get_geometry_signs()
            self.fill_prop_tree(stats)

        if stats is not None:
            self.proparazzi_stats_dict = stats
            
        self.UI.tabWidget.setEnabled(True)
        self.toggle_waitcursor(False)

    def closeEvent(self, event):
        list = ["Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Quit DDV?",
                "Don't leave me!",
                "Please don't go!",
                "Traitor!!",
                "Please stay!",
                "I already miss you...",
                "I'll be back...",
                "Off to never never land...",
                "I order you not to go!",
                "Talk to the hand...",
                "You need me more than I need you..."]

        random_value = randrange(len(list))

        ok = QtGui.QMessageBox.question(self, list[random_value], 'Are you sure you want to quit?',
                                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.Yes)
        if ok == QtGui.QMessageBox.Yes:
            self.save_settings()
            event.accept()
        else:
            event.ignore()

def main():
    app = QtGui.QApplication(argv)
    
    start = time()
    splash = QtGui.QSplashScreen(QtGui.QPixmap(r"W:\main\td_tools\PythonTools\DDV\UI\sauron.jpg"))
    user = getpass.getuser().lower()
    if "boac" in user:
        splash = QtGui.QSplashScreen(QtGui.QPixmap(r"W:\main\td_tools\PythonTools\DDV\UI\sauron_mb.jpg"))
    splash.show()
    app.processEvents()
    sleep(3)

    disrupt_stylesheet.set_stylesheet(app)
    mySW = ControlMainWindow()
    mySW.show()
    splash.finish(mySW)
    mySW.init_DDV()
    
    '''
    ### memory debugger
    deeper_set = set()
    output_dict = {}

    print "Total memory size (MB):", deeper.deep_getsizeof(mySW, deeper_set, output_dict)/1048576.0
    print "-"*30
    t = 0
    for k,v in output_dict.iteritems():
        print str(k).ljust(50),v#/1048576.0
        t += v
    #print t
    ###
    '''
    
    exit(app.exec_())

if __name__ == "__main__":
    main()