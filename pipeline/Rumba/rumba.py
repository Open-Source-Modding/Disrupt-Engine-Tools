from sys import argv, exit, path
import os
from os import getcwd, system
from os.path import join, dirname
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from winreg import ConnectRegistry, OpenKey, QueryValueEx, HKEY_CURRENT_USER
from time import time
import ctypes
from operator import *
import webbrowser
from importlib import reload
myappid = u'mycompany.myproduct.subproduct.version' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
path.append('..')
from Rumba.rumba_parser import parse_all, get_rumba_data_classes
from Rumba.rumba_grid import WorldGrid
# from Rumba.rumba_filters import *
import Rumba.rumba_filters
from Rumba.rumba_progress_bar import RumbaProgressWindow
from Common import disrupt_stylesheet
from Common.progress_bar import ProgressWindow
import xml.etree.cElementTree as ET
import xml.dom.minidom

class RumbaWindow(QWidget):

    def __init__(self):
        super().__init__()
        
        ui_file = os.path.join(os.path.realpath(os.path.dirname(__file__)), r'UI\rumba_UI.ui')
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)
        self.ui = QUiLoader().load(ui_file)
        self.ui.installEventFilter(self)
        ui_file.close()

        self.connect_signals()
        self.initialize_ui()
        self.load_settings()
        self.tree_view_in_focus = None
        self.stats_item = None
        self.stats_item_with_text = None
        self.separator = self.get_list_separator()
        self.background_image = None
        self.operators = (['=', '!=', '<', '>', '~', '!~'])
        self.initialize_satellite()
        self.satellite_has_focus = False
        self.satellite_text_items = None
        self.satellite_selected_cells = set()
        self.satellite_selected_world_instances = set()
        self.satellite_world_object_selection = None
        self.world_name = 'London'  # THIS NEEDS TO NOT BE HARDCODED
        self.history = list()
        self.world_grid = WorldGrid()
        self.initialize_world_grid()
        self.save_settings()  # this installs all event filters too

    # STARTUP
    def load_data(self):
        start = time()

        data_classes = get_rumba_data_classes()

        print('load_data start')
        progress_window = RumbaProgressWindow()
        progress_window.ui.show()
        progress_window.ui.bar_1.setMaximum(len(data_classes) + 4) # all classes will be parsed, adding 4 because there a 5 other jobs and I want the bar to reach 100% :)

        progress_window.ui.label_1.setText('Loading Data')
        progress_window.update_bar_1()
        print('parse_all start')
        self.d_objects_by_types = parse_all(data_classes, progress_window)
        print(time() - start)

        progress_window.ui.label_1.setText('Unpacking Libraries')
        progress_window.update_bar_1()
        print('unpack_libraries start')
        self.unpack_libraries()
        print(time() - start)

        progress_window.ui.label_1.setText('Reticulating Splines')
        progress_window.update_bar_1()
        print('build_genealogy start')
        self.identified_d_objects = self.build_genealogy()
        print(time() - start)

        progress_window.ui.label_1.setText('Building Search Dictionary')
        progress_window.update_bar_1()
        print('build_search_dictionary start')
        self.search_dictionary = self.build_search_dictionary()
        print(time() - start)

        progress_window.ui.label_1.setText('Filling World Grid')
        progress_window.update_bar_1()
        print('fill_world_grid start')
        self.fill_world_grid()
        print(time() - start)

        print('load_data end')
        self.fill_combobox_r_classes() # this needs to be here because load_data is called after init
        self.fill_combobox_filters()

        progress_window.ui.close()

    def unpack_libraries(self):
        library_objects = dict()
        world_instances = set()
        for class_type, d_objects in self.d_objects_by_types.items():

            for d_object in d_objects:

                if not hasattr(d_object, 'IS_CONTAINER'):
                    continue

                for library_object in d_object.library_objects:

                    if library_object.TYPE not in library_objects.keys():
                        library_objects[library_object.TYPE] = set()
                    library_objects[library_object.TYPE].add(library_object)

                    if hasattr(library_object, 'IS_WORLD_INSTANCE'):
                        world_instances.add(library_object)

                    if not hasattr(library_object, 'elements'):
                        continue

                    for element in library_object.elements:
                        if element.TYPE not in library_objects.keys():
                            library_objects[element.TYPE] = set()
                        library_objects[element.TYPE].add(element)

        self.d_objects_by_types = {**self.d_objects_by_types, **library_objects}
        self.d_objects_by_types['World_Instance'] = world_instances

    def initialize_ui(self):
            self.ui.dockWidget_search.setFeatures(self.ui.dockWidget_search.DockWidgetFloatable | self.ui.dockWidget_search.DockWidgetMovable)
            self.ui.dockWidget_satellite.setFeatures(self.ui.dockWidget_satellite.DockWidgetFloatable | self.ui.dockWidget_satellite.DockWidgetMovable)

    def initialize_satellite(self):
        bitmap_path = join(getcwd(), r'UI\game_map_london.png')
        self.background_image = QImage(bitmap_path)
        self.ui.graphicsView_satellite.scene = QGraphicsScene()
        self.ui.graphicsView_satellite.setScene(self.ui.graphicsView_satellite.scene)
        self.satellite_fit_in_view()

    def build_genealogy(self):
        identified_d_objects = dict()

        for d_objects in self.d_objects_by_types.values():
            for d_object in d_objects:
                for identifier in d_object.identifiers:
                    identified_d_objects[identifier] = d_object

        for d_objects in self.d_objects_by_types.values():
            for parent_d_object in d_objects:
                for dependency in parent_d_object.dependencies:
                    child_d_object = identified_d_objects.get(dependency)
                    if child_d_object is None:
                        continue
                    # if child_d_object.TYPE == 'Prefab_Element': # prefab elements' genealogy is built at initialization to fix duplicated prefabs
                    #     continue
                    parent_d_object.add_child(child_d_object)
                    child_d_object.add_parent(parent_d_object)
                
                for relative in parent_d_object.relatives:
                    parent = identified_d_objects.get(relative)
                    if parent is None:
                        continue
                    parent_d_object.add_parent(parent)
                    parent.add_child(parent_d_object)

            

        return identified_d_objects

    def build_search_dictionary(self):
        search_dictionary = dict()
        for d_objects in self.d_objects_by_types.values():
            for d_object in d_objects:
                search_dictionary[d_object._search_data] = d_object
                d_object.search_values = d_object._search_data # redundant?
        return search_dictionary

    def initialize_world_grid(self):
        self.generate_polygons()

    def fill_world_grid(self):
        world_instances = self.d_objects_by_types.get('World_Instance')
        if world_instances is None:
            return
        for world_instance in world_instances:
            if world_instance.position is None:
                continue
            position_split = world_instance.position.split(',')
            x, y = position_split[0], position_split[1]
            x, y = float(x), float(y)
            x, y = x + WorldGrid.WORLD_OFFSET_X, y + WorldGrid.WORLD_OFFSET_Y
            x, y = x / WorldGrid.CELL_SIZE, y / WorldGrid.CELL_SIZE
            x, y = int(x), int(y)
            world_instance.cell_coord = (x, y)
            world_cell = self.world_grid.cells.get(world_instance.cell_coord)
            if world_cell is None:
                print(world_instance.cell_coord, 'was not found')
                continue
            world_cell.world_instances.add(world_instance)
            world_instance.cell = world_cell

    def fill_combobox_r_classes(self):
        class_list = ['All'] + sorted(list(self.d_objects_by_types.keys()))
        for class_name in class_list:
            self.ui.comboBox_r_classes.addItem(class_name)

    def fill_combobox_filters(self):
        for object_name in dir(Rumba.rumba_filters):
            if object_name.startswith('__'):
                continue
            if 'filter_' in object_name:
                self.ui.comboBox_filters.addItem(object_name)

    def on_comboBox_filters_changed(self, value):
        if  "filter_extra" in value:
            self.ui.spinBox_custom_filters.show()
        else: self.ui.spinBox_custom_filters.hide()

    # SEARCH
    def search_something(self, search_string=None):
        text = search_string
        if text is None:
            text = self.ui.lineEdit_search.text().lower()
            text = text.strip()
            text = text.replace('xbt', 'png')
        if not text:
            return

        result_data_set = set()
        queries = text.split(',')
        for query in queries:
            query_tokens = query.split('&')
            first_token = query_tokens[0]
            other_tokens = query_tokens[1:]

            if '*' in first_token:
                first_token = first_token.strip('*')
                query_tokens[0] = first_token
                self.search_many(query_tokens, result_data_set)
            else:
                found_one = self.search_one(first_token, result_data_set)
                if not found_one:
                    self.search_many(query_tokens, result_data_set)

        if search_string is None: # search_string means the search is internal and not from the ui, ignore the filtering or double click search will feel broken
            result_data_set = self.filter_search_result(result_data_set)

        result_data_dict = self.populate_search_result(result_data_set)

        if self.ui.radioButton_search_world_instances.isChecked():
            self.fill_tree_view(self.ui.treeView_search, result_data_dict, True)
        else:
            self.fill_tree_view(self.ui.treeView_search, result_data_dict)
        self.ui.treeView_search.selectionModel().selectionChanged.connect(self.clicked_tree_view_model)

        if self.ui.checkBox_mirror_search_result.isChecked():
            self.send_search_result_to_satellite(result_data_dict)

        self.ui.lineEdit_search.setText(text)
        self.history.append((text, result_data_dict))

        if self.ui.treeView_properties.model():
            self.ui.treeView_properties.model().clear()

        if self.ui.treeView_search.model().rowCount() == 1:
            flags = QItemSelectionModel.Select
            selection = QItemSelection(self.ui.treeView_search.model().index(0, 0), self.ui.treeView_search.model().index(0, 0))
            self.ui.treeView_search.selectionModel().clear()
            self.ui.treeView_search.selectionModel().select(selection, flags)

    def search_operators(self, operator, token, result_data_set):

        name, value = token.split(operator)

        if operator == '=':
            for keys, d_object in self.search_dictionary.items():
                for key in keys:
                    if token in key:
                        result_data_set.add(d_object)
        elif operator == '!=':
            for keys, d_object in self.search_dictionary.items():
                for key in keys:
                    key_name, key_value = key.split('=')
                    if key_name == name and key_value != value:
                        result_data_set.add(d_object)
        elif operator == '<' or operator == '>':
            if operator == '<':
                real_operator = lt
            else:
                real_operator = gt
            index_request = None
            if '[' in token and ']' in token:
                index_request = token.split(operator)[0].split('[')[1].strip(']')
                name = name.split('[')[0]
            for keys, d_object in self.search_dictionary.items():
                for key in keys:
                    key_name, key_value = key.split('=')
                    if key_name == name:
                        if index_request != None and self.is_number(index_request) and "," in key_value:
                            key_value = key_value.split(',')
                            if int(index_request) < len(key_value):
                               key_value = key_value[int(index_request)]

                        if self.is_number(key_value) and self.is_number(value):
                            if real_operator(float(key_value), float(value)):
                                result_data_set.add(d_object)
        elif operator == '~':
            for keys, d_object in self.search_dictionary.items():
                found = False
                for key in keys:
                    key_name, key_value = key.split('=')
                    if key_name == value:
                        found = True
                if found == False : result_data_set.add(d_object)

        elif operator == '!~':
            print(operator)

    @staticmethod
    def is_number(value):
        if value is None or type(value) != str: return False
        try:
            float(value)
            return True
        except ValueError:
            return False

    def search_one(self, first_token, result_data_set):
        found_one = self.identified_d_objects.get(first_token)
        if found_one:
            result_data_set.add(found_one)
            return True
        return False

    def search_token(self, token, results):
        _operator = None

        for operator in self.operators:
            if operator in token:
                _operator = operator
        if _operator != None:
            self.search_operators(_operator, token, results)
            return 

        for identifiers, d_object in self.search_dictionary.items():
            for identifier in identifiers:
                if token in str(identifier):
                    results.add(d_object)
        

    def search_many(self, tokens, result_data_set):
        results = list()
        for token in tokens:
            token_results = set()
            self.search_token(token,token_results)
            results.append(token_results)

        results_intersection = set()
        if len(results) > 0:
            results_intersection = set.intersection(*map(set,results))

        for found in results_intersection:
            result_data_set.add(found)

    def filter_search_result(self, result_data):
        # the following is slow, but easier to implement - remove unwanted items from the result_data
        class_type = self.ui.comboBox_r_classes.currentText()
        if class_type != 'All':
            items_to_delete = set()
            for d_object in result_data:
                if d_object.TYPE != class_type:
                    items_to_delete.add(d_object)
            for item in items_to_delete:
                result_data.remove(item)
        return result_data

    def populate_search_result(self, d_objects_set):
        return_dict = dict()

        z_range = None
        if self.ui.groupBox_filter_z.isChecked():
            z_range = range(self.ui.spinBox_z_min.value(), self.ui.spinBox_z_max.value()+1)

        checked_set = None
        if self.ui.groupBox_filter_layer.isChecked():
            checked_set = self.get_world_layer_type_filter()

        for d_object in d_objects_set:

            if self.ui.radioButton_search_children.isChecked():
                return_dict[d_object] = d_object.get_children()

            else:
                world_instances = self.find_parents(d_object, 'World_Object').union(self.find_parents(d_object, 'Range').union(self.find_parents(d_object, 'Intersection')))
                for world_instance in world_instances:

                    if z_range is not None:
                        if int(float(world_instance.position.split(',')[2])) not in z_range:
                            continue

                    if checked_set is not None:
                        if self.ui.radioButton_layer_include.isChecked():
                            if world_instance.layer_type not in checked_set:
                                continue
                        else:
                            if world_instance.layer_type in checked_set:
                                continue

                    if d_object not in return_dict.keys():
                        return_dict[d_object] = set()
                    return_dict[d_object].add(world_instance)

        return return_dict

    def send_search_result_to_satellite(self, result_data):

        z_range = None
        if self.ui.groupBox_filter_z.isChecked():
            z_range = range(self.ui.spinBox_z_min.value(), self.ui.spinBox_z_max.value()+1)

        checked_set = None
        if self.ui.groupBox_filter_layer.isChecked():
            checked_set = self.get_world_layer_type_filter()

        self.clear_cell_results()

        for d_object in result_data.keys():

            if self.ui.radioButton_search_children.isChecked():
                world_instances = self.find_parents(d_object, 'World_Object').union(self.find_parents(d_object, 'Range').union(self.find_parents(d_object, 'Intersection')))
            else:
                world_instances = result_data[d_object]

            for world_object in world_instances:

                if z_range is not None:
                    if int(float(world_object.position.split(',')[2])) not in z_range:
                        continue

                if checked_set is not None:
                    if self.ui.radioButton_layer_include.isChecked():
                        if world_object.layer_type not in checked_set:
                            continue
                    else:
                        if world_object.layer_type in checked_set:
                            continue

                if not hasattr(world_object, 'cell'):
                    continue
                if d_object not in world_object.cell.filter_result.keys():
                    world_object.cell.filter_result[d_object] = set()

                world_object.cell.filter_result[d_object].add(world_object)

        self.set_cell_colors()
        self.generate_polygons()

    def get_world_layer_type_filter(self):
        checked_set = set()
        if self.ui.checkBox_filter_int.isChecked():
            checked_set.add('Interior')
        if self.ui.checkBox_filter_lma.isChecked():
            checked_set.add('LMA')
        if self.ui.checkBox_filter_hma.isChecked():
            checked_set.add('HMA')
        if self.ui.checkBox_filter_mission.isChecked():
            checked_set.add('Mission')
        if self.ui.checkBox_filter_world.isChecked():
            checked_set.add('World')
        return checked_set

    def clear_cell_results(self):
        for cell in self.world_grid.cells.values():
            cell.filter_result = dict()

    @staticmethod
    def find_parents(d_object, d_type):
        result_list = list()

        if d_object.TYPE == d_type:
            result_list.append(d_object)

        def _find_parents(current_result_list, current_object, current_type):

            for parent in current_object.get_parents():
                if parent.TYPE == current_type:
                    current_result_list.append(parent)

                _find_parents(current_result_list, parent, current_type)

        _find_parents(result_list, d_object, d_type)

        result_set = set(result_list)
        return result_set

    @staticmethod
    def find_children(d_object, d_type):
        result_list = list()

        if d_object.TYPE == d_type:
            result_list.append(d_object)

        def _find_children(current_result_list, current_object, current_type):

            for child in current_object.get_children():
                if child.TYPE == current_type:
                    current_result_list.append(child)

                _find_children(current_result_list, child, current_type)

        _find_children(result_list, d_object, d_type)

        result_set = set(result_list)
        return result_set

    def run_filter(self):
        reload(Rumba.rumba_filters)  # Reload module to iterate on filter code without closing Rumba.
        if "filter_extra"  in self.ui.comboBox_filters.currentText():
            result_data = getattr(Rumba.rumba_filters, self.ui.comboBox_filters.currentText())(self.d_objects_by_types, self.find_parents, self.find_children, self.ui.spinBox_custom_filters.value() )
        else : result_data = getattr(Rumba.rumba_filters, self.ui.comboBox_filters.currentText())(self.d_objects_by_types, self.find_parents, self.find_children )
        result_data_set = result_data[0]
        custom_column = result_data[1]
        result_data_dict = self.populate_search_result(result_data_set)
        self.fill_tree_view(self.ui.treeView_search, result_data_dict, True, custom_column)
        self.send_search_result_to_satellite(result_data_dict)

    # UI
    def clicked_tree_view_model(self):
        if self.ui.radioButton_show_properties.isChecked():
            d_objects = self.get_d_objects_from_items(self.get_tree_view_selected_items(self.ui.treeView_search))
            self.fill_tree_view_properties(self.ui.treeView_properties, d_objects)
        if self.ui.radioButton_show_children.isChecked():
            d_objects = self.get_tree_view_selection_children(self.ui.treeView_search)
            self.fill_tree_view(self.ui.treeView_properties, d_objects)
        if self.ui.radioButton_show_parents.isChecked():
            d_objects = self.get_tree_view_selection_parents(self.ui.treeView_search)
            self.fill_tree_view(self.ui.treeView_properties, d_objects)
        if self.ui.radioButton_satellite.isChecked():
            cells_content = self.get_selected_cells_content()
            self.fill_tree_view(self.ui.treeView_properties, cells_content, True)
        self.ui.label_properties.setText(str(self.ui.treeView_properties.model().rowCount()) + ' items')

    def show_tree_view_context_menu(self, tree_view):
        items = self.get_tree_view_selected_items(tree_view)
        selected_d_objects = self.get_d_objects_from_items(items)

        is_d_objects = True
        if len(selected_d_objects) == 0:
            is_d_objects = False

        # if len(items) > 1:
        #     return # don't know how to support multi selection yet, lambda functions are not passed like they should and overwrite each other

        context_menu = QMenu()

        if not is_d_objects:

            for item in items:

                action_search = QAction()
                action_search.triggered.connect(lambda: self.search_something(items[0].text() + '=' + items[1].text()))
                action_search.setText('Search For: ' + items[0].text() + '=' + items[1].text())
                context_menu.addAction(action_search)

                action_copy_value = QAction()
                action_copy_value.triggered.connect(lambda: self.action_copy_to_clipboard(item.text()))
                action_copy_value.setText('Copy: ' + item.text())
                context_menu.addAction(action_copy_value)

            action_copy_value = QAction()
            action_copy_value.triggered.connect(
                lambda: self.action_copy_to_clipboard(items[0].text() + '=' + items[1].text()))
            action_copy_value.setText('Copy: ' + items[0].text() + '=' + items[1].text())
            context_menu.addAction(action_copy_value)

        for selected_d_object in selected_d_objects.keys():

            action_search = QAction()
            action_search.triggered.connect(
                lambda: self.search_something(selected_d_object.identifier))
            action_search.setText('Search For: ' + selected_d_object.name)
            context_menu.addAction(action_search)

            action_copy_id = QAction()
            action_copy_id.triggered.connect(lambda: self.action_copy_to_clipboard(selected_d_object.identifier))
            action_copy_id.setText('Copy Identifier: ' + selected_d_object.identifier)
            context_menu.addAction(action_copy_id)

            action_copy_name = QAction()
            action_copy_name.triggered.connect(lambda: self.action_copy_to_clipboard(selected_d_object.name))
            action_copy_name.setText('Copy Name: ' + selected_d_object.name)
            context_menu.addAction(action_copy_name)

            action_copy_filename = QAction()
            action_copy_filename.triggered.connect(lambda: self.action_copy_to_clipboard(selected_d_object.filename))
            action_copy_filename.setText('Copy Filename: ' + selected_d_object.filename)
            context_menu.addAction(action_copy_filename)

            action_open_with_default_program = QAction()
            action_open_with_default_program.triggered.connect(
                lambda: self.action_open_file(selected_d_object.filename))
            action_open_with_default_program.setText('Open With Default Program: ' + selected_d_object.filename)
            context_menu.addAction(action_open_with_default_program)

            action_open_file_location = QAction()
            action_open_file_location.triggered.connect(
                lambda: self.action_open_file(dirname(selected_d_object.filename)))
            action_open_file_location.setText('Open File Location: ' + dirname(selected_d_object.filename))
            context_menu.addAction(action_open_file_location)

            if selected_d_object.TYPE == 'World_Object':
                action_copy_coordinates = QAction()
                action_copy_coordinates.triggered.connect(
                    lambda: self.action_copy_coords(selected_d_object))
                action_copy_coordinates.setText('Copy Coords To Clipboard: ' + selected_d_object.position)
                context_menu.addAction(action_copy_coordinates)


        context_menu.exec_(QCursor.pos())

    def show_satellite_context_menu(self):
        if self.satellite_world_object_selection is None:
            return
        context_menu = QMenu()

        action_satellite_selection_1 = QAction()
        action_satellite_selection_1.triggered.connect(lambda: self.search_something(self.satellite_world_object_selection[0].identifier))
        action_satellite_selection_1.setText('Search For ' + self.satellite_world_object_selection[0].TYPE + ': '+ self.satellite_world_object_selection[0].name)
        context_menu.addAction(action_satellite_selection_1)

        action_copy_id_1 = QAction()
        action_copy_id_1.triggered.connect(
            lambda: self.action_copy_to_clipboard(self.satellite_world_object_selection[0].identifier))
        action_copy_id_1.setText('Copy Identifier: ' + self.satellite_world_object_selection[0].identifier)
        context_menu.addAction(action_copy_id_1)

        action_copy_name_1 = QAction()
        action_copy_name_1.triggered.connect(
            lambda: self.action_copy_to_clipboard(self.satellite_world_object_selection[0].name))
        action_copy_name_1.setText('Copy Name: ' + self.satellite_world_object_selection[0].name)
        context_menu.addAction(action_copy_name_1)

        action_copy_filename_1 = QAction()
        action_copy_filename_1.triggered.connect(
            lambda: self.action_copy_to_clipboard(self.satellite_world_object_selection[0].filename))
        action_copy_filename_1.setText('Copy Filename: ' + self.satellite_world_object_selection[0].filename)
        context_menu.addAction(action_copy_filename_1)

        action_open_with_default_program_1 = QAction()
        action_open_with_default_program_1.triggered.connect(
            lambda: self.action_open_file(self.satellite_world_object_selection[0].filename))
        action_open_with_default_program_1.setText(
            'Open With Default Program: ' + self.satellite_world_object_selection[0].filename)
        context_menu.addAction(action_open_with_default_program_1)

        context_menu.addSeparator()

        action_satellite_selection_2 = QAction()
        action_satellite_selection_2.triggered.connect(lambda: self.search_something(self.satellite_world_object_selection[1].identifier))
        action_satellite_selection_2.setText('Search For ' + self.satellite_world_object_selection[1].TYPE + ': ' + self.satellite_world_object_selection[1].name)
        context_menu.addAction(action_satellite_selection_2)

        action_copy_id_2 = QAction()
        action_copy_id_2.triggered.connect(lambda: self.action_copy_to_clipboard(self.satellite_world_object_selection[1].identifier))
        action_copy_id_2.setText('Copy Identifier: ' + self.satellite_world_object_selection[1].identifier)
        context_menu.addAction(action_copy_id_2)

        action_copy_name_2 = QAction()
        action_copy_name_2.triggered.connect(lambda: self.action_copy_to_clipboard(self.satellite_world_object_selection[1].name))
        action_copy_name_2.setText('Copy Name: ' + self.satellite_world_object_selection[1].name)
        context_menu.addAction(action_copy_name_2)

        action_copy_filename_2 = QAction()
        action_copy_filename_2.triggered.connect(lambda: self.action_copy_to_clipboard(self.satellite_world_object_selection[1].filename))
        action_copy_filename_2.setText('Copy Filename: ' + self.satellite_world_object_selection[1].filename)
        context_menu.addAction(action_copy_filename_2)

        action_open_with_default_program_2 = QAction()
        action_open_with_default_program_2.triggered.connect(
            lambda: self.action_open_file(self.satellite_world_object_selection[1].filename))
        action_open_with_default_program_2.setText('Open With Default Program: ' + self.satellite_world_object_selection[1].filename)
        context_menu.addAction(action_open_with_default_program_2)

        action_copy_coordinates = QAction()
        action_copy_coordinates.triggered.connect(
            lambda: self.action_copy_coords(self.satellite_world_object_selection[1]))
        action_copy_coordinates.setText('Copy Coords To Clipboard: ' + self.satellite_world_object_selection[1].position)
        context_menu.addAction(action_copy_coordinates)

        context_menu.exec_(QCursor.pos())

    @staticmethod
    def action_copy_to_clipboard(data):
        clipboard = QClipboard()
        clipboard.setText(data)

    @staticmethod
    def action_open_file(file):
        system("start " + file)

    def action_copy_coords(self, world_instance):
        pull_back = 4
        if world_instance.TYPE == 'World_Object':
            if world_instance.object_type == "Building":
                pull_back = 30
        current_position = world_instance.position.split(',')

        cur_pos_x = float(current_position[0])
        cur_pos_y = float(current_position[1]) - pull_back
        cur_pos_z = float(current_position[2]) + pull_back

        pos_str = str(cur_pos_x) + "," + str(cur_pos_y) + "," + str(cur_pos_z)
        coord_str = '<Parameters WorldName="%s" CameraPos="%s" CameraAngle="-45,0,0" Type="cmd_ReviewScene" />' % (self.world_name, pos_str)
        clipboard = QClipboard()
        clipboard.setText(coord_str)

    def export_xml(self):
        if len(self.history) == 0 or len(self.history[-1][1]) == 0 : return
        filename, extension = QFileDialog.getSaveFileName(self, 'Export Items', '', ".xml(*.xml)")
        if filename == "" : return
        xml_export = ET.Element('RumbaSearch', {'name': self.history[-1][0]})
        
        for d_object in self.history[-1][1]:
            parents_len = len(d_object.get_parents())
            children_len = len(d_object.get_children())

            item = ET.SubElement(xml_export,'item', {
                'type': d_object.type, 
                'name' : d_object.name, 
                'path' : d_object.filename.replace("\\","/") })

            parents = ET.SubElement(item,'parents', {'count' : str(parents_len)})
            for parent in d_object.get_parents():
                ET.SubElement(parents,'parent', {'type' : parent.type, 
                                                 'name' : parent.name, 
                                                 'path' : parent.filename.replace("\\","/")})

            children = ET.SubElement(item,'children', {'count' : str(children_len)})
            for child in d_object.get_children():
                ET.SubElement(children,'child', {'type' : child.type, 
                                                 'name' : child.name, 
                                                 'path' : child.filename.replace("\\","/")})
        
            to_export = ET.tostring(xml_export, encoding='utf8', method='xml')
            parsed_xml = xml.dom.minidom.parseString(to_export)
            pretty_xml = parsed_xml.toprettyxml()
            outfile = open(filename, 'w')
            outfile.write(pretty_xml)
            outfile.close()

    def connect_signals(self):
        QObject.connect(self.ui.pushButton_search, SIGNAL('clicked()'), self.search_something)
        QObject.connect(self.ui.pushButton_export, SIGNAL('clicked()'), self.export_xml)
        QObject.connect(self.ui.radioButton_satellite_resources, SIGNAL('clicked()'), self.search_something)
        QObject.connect(self.ui.radioButton_satellite_world_instances, SIGNAL('clicked()'), self.search_something)
        # QObject.connect(self.ui.pushButton_back, SIGNAL('clicked()'), self.progress_window)
        # QObject.connect(self.ui.pushButton_back, SIGNAL('clicked()'), lambda: self.select_tree_view_item_from_d_object(self.ui.treeView_search, None))
        QObject.connect(self.ui.pushButton_save_layout, SIGNAL('clicked()'), self.save_settings)
        QObject.connect(self.ui.pushButton_fit_view, SIGNAL('clicked()'), self.satellite_fit_in_view)
        QObject.connect(self.ui.pushButton_filter, SIGNAL('clicked()'), self.run_filter)
        QObject.connect(self.ui.pushButton_back, SIGNAL('clicked()'), self.pressed_back)
        QObject.connect(self.ui.pushButton_help, SIGNAL('clicked()'), self.pressed_help)
        QObject.connect(self.ui.pushButton_execute_code, SIGNAL('clicked()'), self.pressed_execute_code)
        QObject.connect(self.ui.treeView_search, SIGNAL('clicked(QModelIndex)'), self.clicked_tree_view_model)
        QObject.connect(self.ui.treeView_search, SIGNAL('doubleClicked(QModelIndex)'),
                        lambda: self.search_on_double_click(self.ui.treeView_search))
        QObject.connect(self.ui.treeView_properties, SIGNAL('doubleClicked(QModelIndex)'),
                        lambda: self.search_on_double_click(self.ui.treeView_properties))
        QObject.connect(self.ui.radioButton_show_properties, SIGNAL('clicked()'), self.clicked_tree_view_model)
        QObject.connect(self.ui.radioButton_show_children, SIGNAL('clicked()'), self.clicked_tree_view_model)
        QObject.connect(self.ui.radioButton_show_parents, SIGNAL('clicked()'), self.clicked_tree_view_model)
        QObject.connect(self.ui.radioButton_satellite, SIGNAL('clicked()'), self.clicked_tree_view_model)
        self.ui.comboBox_filters.currentTextChanged.connect(self.on_comboBox_filters_changed)
        self.ui.treeView_search.customContextMenuRequested.connect(
            lambda: self.show_tree_view_context_menu(self.ui.treeView_search))
        self.ui.treeView_properties.customContextMenuRequested.connect(
            lambda: self.show_tree_view_context_menu(self.ui.treeView_properties))
        # self.ui.graphicsView_satellite.customContextMenuRequested.connect(
        #     lambda: self.show_satellite_context_menu())
        QShortcut(QKeySequence('Ctrl+C'), self.ui, activated=self.copy_selection_to_clipboard)
        QShortcut(QKeySequence('Enter'), self.ui, activated=self.search_something)
        QShortcut(QKeySequence('Return'), self.ui, activated=self.search_something)

    def search_on_double_click(self, tree_view):
        items = self.get_tree_view_selected_items(tree_view)
        selected_d_objects = self.get_d_objects_from_items(items)
        for selected_d_object in selected_d_objects.keys():
            self.search_something(selected_d_object.identifier)

    def pressed_back(self):
        if len(self.history) == 0:
            return
        del self.history[-1]
        if len(self.history) == 0:
            return

        self.ui.lineEdit_search.setText(self.history[-1][0])
        result_data_dict = self.history[-1][1]

        if self.ui.radioButton_search_world_instances.isChecked():
            self.fill_tree_view(self.ui.treeView_search, result_data_dict, True)
        else:
            self.fill_tree_view(self.ui.treeView_search, result_data_dict)
        self.ui.treeView_search.selectionModel().selectionChanged.connect(self.clicked_tree_view_model)

        if self.ui.checkBox_mirror_search_result.isChecked():
            self.send_search_result_to_satellite(result_data_dict)

    @staticmethod
    def pressed_help():
        webbrowser.open(join(getcwd(), r'UI\Rumba_Reference_Guide.htm'))

    def pressed_execute_code(self):
        code = self.ui.textEdit_code.toPlainText()
        if not code:
            return
        exec(code)

    @staticmethod
    def get_list_separator():
        """Retrieves the Windows list separator character from the registry"""
        reg = ConnectRegistry(None, HKEY_CURRENT_USER)
        key = OpenKey(reg, r"Control Panel\International")
        value = QueryValueEx(key, "sList")[0]
        return value

    def copy_selection_to_clipboard(self):
        list_of_strings = list()
        column_count = self.tree_view_in_focus.model().columnCount()
        counter = 0
        item_string = str()
        for index in self.tree_view_in_focus.selectedIndexes():
            counter += 1
            item = index.model().itemFromIndex(index)
            item_string += item.text() + self.separator
            if counter == column_count:
                item_string = item_string[:-1]
                list_of_strings.append(item_string)
                counter = 0
                item_string = str()
        data_string = str()
        for string in list_of_strings:
            data_string += string + '\n'
        QClipboard().setText(data_string)

    @staticmethod
    def get_d_objects_from_items(items):
        d_objects = dict()
        for item in items:
            data = item.data()
            if data is None:
                continue
            d_objects[data] = None
        return d_objects

    @staticmethod
    def get_tree_view_selected_items(tree_view):
        items = list()
        for index in tree_view.selectedIndexes():
            item = index.model().itemFromIndex(index)
            if item is None:
                continue
            items.append(item)
        return items

    @staticmethod
    def get_tree_view_selection_children(tree_view):
        d_objects = dict()
        for index in tree_view.selectedIndexes():
            data = index.model().itemFromIndex(index).data()
            if data is None:
                continue
            for child in data.get_children():
                d_objects[child] = child.get_children()
        return d_objects

    @staticmethod
    def get_tree_view_selection_parents(tree_view):
        d_objects = dict()
        for index in tree_view.selectedIndexes():
            data = index.model().itemFromIndex(index).data()
            if data is None:
                continue
            for parent in data.get_parents():
                d_objects[parent] = parent.get_children()
        return d_objects

    def fill_tree_view(self, tree_view, d_objects, is_filter_result=False, custom_column=None):
        columns = list()
        for parent, children in d_objects.items():
            for name, value in parent.__dict__.items():
                if name in columns:
                    continue
                if name == custom_column:
                    columns.append(name)
                if name not in parent.EXPOSED_VALUES:
                    continue
                columns.append(name)

        columns = sorted(columns)

        if is_filter_result:
            model = QStandardItemModel(0, len(columns) + 1)
        else:
            if custom_column is None:
                model = QStandardItemModel(0, len(columns) + 2)
            else:
                model = QStandardItemModel(0, len(columns) + 3)

        tree_view.setModel(model)
        root_item = model.invisibleRootItem()

        for parent, children in d_objects.items():
            item = []
            for name in columns:
                value = parent.__dict__.get(name)
                if RumbaWindow.is_number(value):
                    value = float(value)
                    value = round(value, 1)
                    value = '{:>10}'.format(str(value))
                value_item = QStandardItem(value)
                value_item.setData(parent)
                item.append(value_item)
            parents_count = '{:>10}'.format(str(len(parent.get_parents())))
            children_count = '{:>10}'.format(str(len(parent.get_children())))
            if is_filter_result:
                item.append(QStandardItem('{:>10}'.format(str(len(children)))))
            else:
                item.append(QStandardItem(parents_count))
                item.append(QStandardItem(children_count))
            root_item.appendRow(item)

            for child in children:
                child_item = []
                for name in columns:
                    value = QStandardItem(child.__dict__.get(name))
                    value.setData(child)
                    child_item.append(value)
                parents_count = '{:>10}'.format(str(len(child.get_parents())))
                children_count = '{:>10}'.format(str(len(child.get_children())))
                child_item.append(QStandardItem(parents_count))
                child_item.append(QStandardItem(children_count))
                item[0].appendRow(child_item)

        if is_filter_result:
            columns.append('count')
            # columns.append(custom_column)
        else:
            columns.append('parents')
            columns.append('children')
        model.setHorizontalHeaderLabels(columns)
        for i in range(model.columnCount()):
            tree_view.resizeColumnToContents(i)

        self.ui.label_search.setText(str(self.ui.treeView_search.model().rowCount()) + ' items')

    @staticmethod
    def fill_tree_view_properties(tree_view, d_objects):
        columns = ['Property', 'Value']
        model = QStandardItemModel(0, len(columns))
        tree_view.setModel(model)
        root_item = model.invisibleRootItem()
        for d_object in d_objects.keys():
            for name, value in d_object.__dict__.items():
                if name.startswith('_'):
                    continue
                item_value = QStandardItem(str(value))
                if type(value) is dict:
                    continue
                if type(value) is set or type(value) is list or type(value) is tuple:
                    value_iter_str = ''
                    for item in value:
                        value_iter_str += str(item) + ', '
                    value_iter_str = value_iter_str[:-2] # trim last two characters, comma and empty space
                    item_value = QStandardItem(value_iter_str)
                item = [QStandardItem(name), item_value]
                root_item.appendRow(item)
        model.setHorizontalHeaderLabels(columns)
        for i in range(model.columnCount()):
            tree_view.resizeColumnToContents(i)

    def save_settings(self):
        settings = QSettings('Ubisoft', 'Rumba')
        def get_children(item):
            item.installEventFilter(self)
            for child_item in item.children():
                if type(child_item) is QDockWidget or type(child_item) is QTreeView:
                    child_item.saveGeometry()
                get_children(child_item)
        get_children(self.ui)
        settings.setValue('geometry', self.ui.saveGeometry())
        settings.setValue('state', self.ui.saveState())

    def load_settings(self):
        settings = QSettings('Ubisoft', 'Rumba')
        self.ui.restoreGeometry(settings.value('geometry'))
        self.ui.restoreState(settings.value('state'))

    def eventFilter(self, obj, event):

        # print(obj, event)

        if obj is self.ui.graphicsView_satellite:
            if event.type() == QEvent.FocusIn:
                self.satellite_has_focus = True
            if event.type() == QEvent.FocusOut:
                self.satellite_has_focus = False
            if event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.MouseButton.MidButton:
                    self.__prevMousePos = event.pos()
                    QApplication.setOverrideCursor(QCursor(Qt.ClosedHandCursor))

        if event.type() == QEvent.Wheel:
            if self.satellite_has_focus:
                self.zoom_satellite(event)
                return True

        # try:
        if isinstance(obj.parent(), QGraphicsView):
            if event.type() == QEvent.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton:
                    modifiers = QApplication.keyboardModifiers()
                    if modifiers == Qt.ShiftModifier:
                        self.get_satellite_items_selection(False)
                    else:
                        self.get_satellite_items_selection(True)
        # except:
        #     pass

        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.MouseButton.MidButton:
                QApplication.restoreOverrideCursor()

        if event.type() == QEvent.MouseMove:
            if event.buttons() == Qt.MouseButton.MidButton:
                self.satellite_panning(event)

        if obj is self.ui:
            if event.type() == QEvent.Close:
                self.save_settings()
        if obj is self.ui.treeView_properties:
            if event.type() == QEvent.FocusIn:
                self.tree_view_in_focus = self.ui.treeView_properties
        elif obj is self.ui.treeView_search:
            if event.type() == QEvent.FocusIn:
                self.tree_view_in_focus = self.ui.treeView_search
        try: # need to do this to prevent a weird random C++ crash when closing
            return super(RumbaWindow, self).eventFilter(obj, event)
        except:
            return True

    def progress_window(self):
        bar = ProgressWindow(10000)
        print(bar)

    # Satellite UI

    def satellite_panning(self, event):
        offset = self.__prevMousePos - event.pos()
        self.__prevMousePos = event.pos()
        self.ui.graphicsView_satellite.verticalScrollBar().setValue(
            self.ui.graphicsView_satellite.verticalScrollBar().value() + offset.y())
        self.ui.graphicsView_satellite.horizontalScrollBar().setValue(
            self.ui.graphicsView_satellite.horizontalScrollBar().value() + offset.x())

    def satellite_fit_in_view(self):
        rect = QRectF(self.background_image.rect())
        if not rect.isNull():
            unity = self.ui.graphicsView_satellite.transform().mapRect(QRectF(0, 0, 1, 1))
            self.ui.graphicsView_satellite.scale(1 / unity.width(), 1 / unity.height())
            viewrect = self.ui.graphicsView_satellite.viewport().rect()
            scenerect = self.ui.graphicsView_satellite.transform().mapRect(rect)
            factor = min(viewrect.width() / scenerect.width(),
                         viewrect.height() / scenerect.height())
            self.ui.graphicsView_satellite.scale(factor, factor)
            self.ui.graphicsView_satellite.centerOn(rect.center())
            self.ui.graphicsView_satellite._zoom = 0

    def zoom_satellite(self, event):
        if event.delta() > 0:
            factor = 1.25
            self.ui.graphicsView_satellite._zoom += 1
        else:
            factor = 0.8
            self.ui.graphicsView_satellite._zoom -= 1
        if self.ui.graphicsView_satellite._zoom in range(-2, 21):
            self.ui.graphicsView_satellite.scale(factor, factor)
        self.ui.graphicsView_satellite._zoom = min(self.ui.graphicsView_satellite._zoom, 20)
        self.ui.graphicsView_satellite._zoom = max(self.ui.graphicsView_satellite._zoom, -2)

        if self.ui.graphicsView_satellite._zoom > 4:
            for item in self.satellite_text_items:
                item.setVisible(True)
        else:
            for item in self.satellite_text_items:
                item.setVisible(False)

        selection_color = QColor(0,0,0,192)
        inverted_zoom = self.inverted_zoom()

        for item in self.ui.graphicsView_satellite.scene.items():
            if hasattr(item, 'is_selection'):
                pen = QPen(selection_color)
                pen.setWidth(inverted_zoom)
                item.setPen(pen)

            if hasattr(item, 'is_world_object_icon'):
                item.setRect((inverted_zoom/2)*-1, (inverted_zoom/2)*-1, inverted_zoom, inverted_zoom)

    def inverted_zoom(self):
        inverted_zoom = 20 - self.ui.graphicsView_satellite._zoom
        if inverted_zoom == 0:
            inverted_zoom = 0.5
        return inverted_zoom

    def generate_polygons(self):
        self.ui.graphicsView_satellite.scene.clear()
        self.ui.graphicsView_satellite.scene.addItem(QGraphicsPixmapItem(QPixmap(self.background_image)))
        self.satellite_text_items = set()
        font = QFont()
        font.setPointSize(12)
        for cell in self.world_grid.cells.values():
            cell.qt_points = []
            for point in cell.points:
                cell.qt_points.append(QPoint(point[0], point[1]))
            q_polygon = QPolygon(cell.qt_points)
            color = QColor(cell.stat_color[0], cell.stat_color[1], cell.stat_color[2], cell.stat_color[3])
            brush = QBrush(color)
            pen = QPen(color)
            pen.setWidth(0)
            polygon_item = PolygonItem()
            polygon_item.setPolygon(q_polygon)
            polygon_item.setBrush(brush)
            polygon_item.setPen(pen)
            self.ui.graphicsView_satellite.scene.addItem(polygon_item)
            polygon_item.setFlag(polygon_item.ItemIsSelectable, True)
            polygon_item.cell = cell
            resources_text_item = self.ui.graphicsView_satellite.scene.addText(str(cell.stat_resources), font)
            resources_text_item.setPos(cell.generation_position[0], cell.generation_position[1])
            resources_text_item.setVisible(False)
            self.satellite_text_items.add(resources_text_item)

            instances_text_item = self.ui.graphicsView_satellite.scene.addText(str(cell.stat_instances), font)
            instances_text_item.setPos(cell.generation_position[0], cell.generation_position[1] + 15)
            instances_text_item.setVisible(False)
            self.satellite_text_items.add(instances_text_item)

    def get_satellite_items_selection(self, clear_selection):

        cell = None
        for item in self.ui.graphicsView_satellite.scene.selectedItems():
            if hasattr(item, 'is_world_object_icon'):
                # self.satellite_world_object_selection = item.world_object
                self.satellite_world_object_selection = item.data_combo
                self.show_satellite_context_menu()
                continue
            cell = item.cell

        if cell is None:
            return

        if clear_selection:
            self.satellite_selected_cells = set()
            self.satellite_selected_world_instances = set()

            for item in self.ui.graphicsView_satellite.scene.items():
                if hasattr(item, 'is_selection'):
                    self.ui.graphicsView_satellite.scene.removeItem(item)
                if hasattr(item, 'is_world_object_icon'):
                    self.ui.graphicsView_satellite.scene.removeItem(item)

        inverted_zoom = self.inverted_zoom()

        if self.ui.checkBox_satellite_selection.isChecked():
            q_polygon = QPolygon(cell.qt_points)
            pen = QPen(QColor(0,0,0,192))
            pen.setWidth(inverted_zoom)
            selection_item = self.ui.graphicsView_satellite.scene.addPolygon(q_polygon, pen)
            selection_item.is_selection = True
        self.satellite_selected_cells.add(cell)

        color = QColor(100, 255, 255, 128)
        brush = QBrush(color)
        pen = QPen(color)
        pen.setWidth(0)
        cells_content = self.get_selected_cells_content()
        for cell in self.satellite_selected_cells:
            if self.ui.checkBox_satellite_world_instances.isChecked():
                for d_object, world_instances in cell.filter_result.items():
                    for world_instance in world_instances:
                        if world_instance in self.satellite_selected_world_instances:
                            continue
                        self.satellite_selected_world_instances.add(world_instance)
                        position_split = world_instance.position.split(',')
                        position = (float(position_split[0]), float(position_split[1]))
                        position = self.convert_world_pos_to_ui_pos(position)
                        instance_item = self.ui.graphicsView_satellite.scene.addEllipse((inverted_zoom/2)*-1,(inverted_zoom/2)*-1,inverted_zoom,inverted_zoom)
                        instance_item.setPen(pen)
                        instance_item.setBrush(brush)
                        instance_item.setPos(position[0], position[1])
                        instance_item.is_world_object_icon = True
                        instance_item.setFlag(instance_item.ItemIsSelectable, True)
                        instance_item.world_object = world_instance
                        instance_item.data_combo = (d_object, world_instance)

        if self.ui.radioButton_satellite.isChecked():
            self.fill_tree_view(self.ui.treeView_properties, cells_content, True)

    def get_selected_cells_content(self):
        cells_content = dict()
        for cell in self.satellite_selected_cells:

            if self.ui.radioButton_satellite.isChecked():
                # cells_content = {**cells_content, **cell.filter_result} # BAD!!!

                for key, value_list in cell.filter_result.items():
                    if key not in cells_content.keys():
                        cells_content[key] = set()
                    for value in value_list:
                        cells_content[key].add(value)
        return cells_content

    def convert_world_pos_to_ui_pos(self, position):
        x = position[0]
        y = position[1]
        x = ((self.world_grid.WORLD_OFFSET_X * -1) + self.world_grid.WORLD_OFFSET_X) - x
        x += self.world_grid.WORLD_OFFSET_X
        y += self.world_grid.WORLD_OFFSET_Y
        ui_position = (x, y)
        return ui_position

    def set_cell_colors(self):
        alpha = 210
        very_light =        (0,220,0,105)
        light =             (0,220,0,150)
        good =              (0,220,0,alpha)
        medium =            (240,255,0,alpha)
        limit =             (255,140,0,alpha)
        bad =               (255,0,0,alpha)
        null =              (0,0,0,0)
        very_bad =          (100,0,200,alpha)
        out_of_control =    (64,0,255,alpha)
        max_value_bad =     (255,0,255,alpha)
        max_value_ok =      (0,255,255,alpha)

        max_value = 0
        for cell in self.world_grid.cells.values():
            cell.stat_resources = len(cell.filter_result)
            cell.stat_instances = 0
            for world_instances in cell.filter_result.values():
                cell.stat_instances += len(world_instances)

            if self.ui.radioButton_satellite_resources.isChecked():
                value = cell.stat_resources
            else:
                value = cell.stat_instances

            if value > max_value:
                max_value = value

        max_value = float(max_value)

        for cell in self.world_grid.cells.values():

            if self.ui.radioButton_satellite_resources.isChecked():
                value = cell.stat_resources
            else:
                value = cell.stat_instances

            value = float(value)

            if max_value == 0.0:
                cell.stat_color = null
            else:
                if value == 0.0:
                    cell.stat_color = null
                elif value == max_value:
                    cell.stat_color = bad
                elif value > max_value * 0.8:
                    cell.stat_color = limit
                elif value > max_value * 0.6:
                    cell.stat_color = medium
                elif value > max_value * 0.4:
                    cell.stat_color = good
                elif value > max_value * 0.2:
                    cell.stat_color = light
                else:
                    cell.stat_color = very_light


class PolygonItem(QGraphicsPolygonItem):
    def paint(self, painter, option, widget):
        option.state &= ~QStyle.State_Selected
        super(PolygonItem, self).paint(painter, option, widget)


if __name__ == '__main__':
    app = QApplication(argv)
    disrupt_stylesheet.set_stylesheet(app)
    rumba_window = RumbaWindow()
    rumba_window.ui.show()
    q_pixmap = QPixmap(join(getcwd(), r'UI\rumba_cat_icon.png'))
    q_icon = QIcon(q_pixmap)
    rumba_window.ui.setWindowIcon(q_icon)
    rumba_window.load_data()
    rumba_window.satellite_fit_in_view()
    exit(app.exec_())
