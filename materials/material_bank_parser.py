import xml.etree.ElementTree as ET
import re
from PySide import *


# XML files to parse...
road_mat_bank_xml = "W:\main\data\Databases\Generic\RoadMaterialBank.xml"  # Road Material Bank Override
sidewalk_mat_bank_xml = "W:\main\data\Databases\Generic\SidewalkMaterialBank.xml"  # Sidewalk Material Bank Override
building_roof_mat_bank_xml = "W:\Main\data\Databases\Generic\BuildingRoofMaterialBanks.xml"	# Roofs Material Bank
building_foot_mat_bank_xml = "W:\Main\data\Databases\Generic\BuildingFootingMaterialBanks.xml" # Foot Material Bank

class RoofMaterial():
	# TODO: Add type of material (Building Roof, Building Footing, Road Material, Sidewalk Material)
	def __init__(self, name, unique_id, logic_mat, material):
		self.name = name
		self.unique_id = unique_id
		self.logic_mat = logic_mat
		self.material = material

	def find_by_id(self, id_to_find):
		if id_to_find != "":
			if self.unique_id == id_to_find:
				print "ID: < {} > is referenced in Material named: < {} >".format(self.unique_id, self.name)
		else:
			print "if_to_find variable not set"

	def find_by_name(self, name_to_find):
		if name_to_find != "":
			if self.name == name_to_find:
				print "Name: < {} > is referenced in Material ID: < {} >".format(self.name, self.unique_id)
		else:
			print "name_to_find variable not set"

	def print_material(self):
		print "Material name: {}, Unique ID: {}, Logic Material: {}, Material: {}".format(self.name, self.unique_id, self.logic_mat, self.material)

class LoftMaterial():
	def __init__(self, name):
		self.name = name

	def find_mat_prefix(self, name):
		# TODO: Need to refactor this function to find a better way to get Prefix
		mat_prefix = str(name[:3])
		return mat_prefix

	def find_mat_type(self):
		if "Asphalt" in self.name:
			return "Asphalt"

		elif "Brick" in self.name:
			return "Brick"

		elif "Cobblestone" in self.name:
			return "Cobblestone"

		elif "Stone" in self.name:
			return "Stone"

		elif "Concrete" in self.name:
			return "Concrete"

	def find_mat_prefix(self):
		mat_prefix = str(self.name[:3])
		return mat_prefix


def add_to_list(list_name=[], *args):
	if args not in list_name:
		list_name.append(args)
	else:
		print "{} is already in {} list !".format(args, list_name)

def print_list_updates():
	if len(GEN_list) > 0:
		print "-> Added {} to GEN_list".format(GEN_list)

	if len(WD2_list) > 0:
		print "-> Added {} to WD2_list".format(WD2_list)

	if len(USE_list) > 0:
		print "-> Added {} to USE_list".format(USE_list)

	if len(THW_list) > 0:
		print "-> Added {} to THW_list".format(THW_list)

def spline_material_bank_parser(id_to_find = "", name_to_find = ""):
	t_road = {"Name": "Road", "Tag": "Generic", "Attribute": "matRoadMaterial",
			  "Path": "W:\main\data\Databases\Generic\RoadMaterialBank.xml"}

	t_sidewalk = {"Name": "Sidewalk","Tag": "Generic", "Attribute": "matSidewalkMaterial",
				  "Path": "W:\Main\data\Databases\Generic\SidewalkMaterialBank.xml"}

	t_blding_roof = {"Name": "Roof","Tag": "MaterialBank", "Attribute": "matRoadMaterial",
				  "Path": "W:\Main\data\Databases\Generic\BuildingRoofMaterialBanks.xml"}

	t_blding_footing = {"Name": "Footing","Tag": "MaterialBank", "Attribute": "matRoadMaterial",
				  "Path": "W:\Main\data\Databases\Generic\BuildingFootingMaterialBanks.xml"}

	mat_xml_list = [t_road, t_sidewalk, t_blding_roof, t_blding_footing]


	material_db_list =\
		["W:\main\data\Databases\Generic\RoadMaterialBank.xml",
		 "W:\main\data\Databases\Generic\SidewalkMaterialBank.xml",
		 "W:\Main\data\Databases\Generic\BuildingRoofMaterialBanks.xml"]

	for xml in mat_xml_list:
		tree = ET.ElementTree(file= xml.get("Path"))
		cur_xml_name = xml.get("Name")
		tag = xml.get("Tag")
		attribute = xml.get("Attribute")
		path = xml.get("Path")
		for item in tree.iter(tag):
			if cur_xml_name == "Road":
				continue
			elif cur_xml_name == "Sidewalk":
				continue
			elif cur_xml_name == "Roof":
				name = item.get("BankName")
				print name
			elif cur_xml_name == "Footing":
				continue


	# for xml in material_db_list:
	# 	tree = ET.ElementTree(file=xml)
	#
	# 	for item in tree.iter('Generic'):
	# 		# -> Search By IDs
	# 		if id_to_find != "":
	# 			# -> Search The Road Material Bank
	# 			if xml == "W:\main\data\Databases\Generic\RoadMaterialBank.xml":
	# 				road_mat = item.get("matRoadMaterial")
	# 				mat_id = re.sub("[^0-9]", "", road_mat)
	#
	# 				if str(mat_id) == str(id_to_find):
	# 					name = item.get("hidName")
	# 					print name
	#
	# 			# -> Search The Sidewalk Material Bank
	# 			elif xml == "W:\main\data\Databases\Generic\SidewalkMaterialBank.xml":
	# 				sidewalk_mat = item.get("matSidewalkMaterial")
	# 				mat_id = re.sub("[^0-9]", "", sidewalk_mat)
	#
	# 				if str(mat_id) == str(id_to_find):
	# 					name = item.get("hidName")
	# 					print name
	#
	# 		print "No references to material {} found.".format(id_to_find)


				# found_prefix = find_mat_prefix(mat_name)
		# print "Material name: < {} > is prefixed with < {} >".format(mat_name, found_prefix)

		# if found_prefix in prefix_list:
		# 	index = 1
		# 	found_type = find_mat_type(mat_name)

		# 	if found_type != None:
		# 		if found_prefix == "GEN":
		# 			add_to_list(GEN_list, mat_name)
		# 			for i in GEN_list:
		# 				item.set("Name", "GENERIC."+found_type+"_0"+str(index))
		# 				tree.write(road_mat_bank_xml)
		# 				index = index + 1
		#
		# 		elif found_prefix == "WD2":
		# 			add_to_list(WD2_list, mat_name)
		# 			for i in WD2_list:
		# 				item.set("Name", "WD2."+found_type+"_0"+str(index))
		# 				tree.write(road_mat_bank_xml)
		# 				index = index + 1
		#
		# 		elif found_prefix == "USE":
		# 			add_to_list(USE_list, mat_name)
		# 			for i in USE_list:
		# 				item.set("Name", "USER."+found_type+"_0"+str(index))
		# 				tree.write(road_mat_bank_xml)
		# 				index = index + 1
		#
		# 		elif found_prefix == "THW":
		# 			add_to_list(THW_list, mat_name)
		# 			for i in THW_list:
		# 				item.set("Name", "TOWER_HAMLET_WEST."+found_type+"_0"+str(index))
		# 				tree.write(road_mat_bank_xml)
		# 				index = index + 1

def backup():
	for xml in material_db_list:
		tree = ET.ElementTree(file=xml)
		tree_tag = ""
		if xml == "W:\main\data\Databases\Generic\RoadMaterialBank.xml" or "W:\main\data\Databases\Generic\SidewalkMaterialBank.xml":
			tree_tag = "Generic"
		elif xml == "W:\Main\data\Databases\Generic\BuildingRoofMaterialBanks.xml" or "W:\Main\data\Databases\Generic\BuildingFootingMaterialBanks.xml":
			tree_tag = "MaterialBank"

		for item in tree.iter('Generic'):
			# -> Search By IDs
			if id_to_find != "":
				# -> Search The Road Material Bank
				if xml == "W:\main\data\Databases\Generic\RoadMaterialBank.xml":
					road_mat = item.get("matRoadMaterial")
					mat_id = re.sub("[^0-9]", "", road_mat)

					if str(mat_id) == str(id_to_find):
						name = item.get("hidName")
						print name

				# -> Search The Sidewalk Material Bank
				elif xml == "W:\main\data\Databases\Generic\SidewalkMaterialBank.xml":
					sidewalk_mat = item.get("matSidewalkMaterial")
					mat_id = re.sub("[^0-9]", "", sidewalk_mat)

					if str(mat_id) == str(id_to_find):
						name = item.get("hidName")
						print name

			print "No references to material {} found.".format(id_to_find)


def write_xml(item, prefix, type, index, xml_output):
	item.set("Name", str(prefix) + type + "_0" + str(index))
	tree.write(xml_output)

def material_bank_parser(xml, id_to_find = "", name_to_find = ""):
	tree = ET.ElementTree(file=xml)

	for item in tree.iter("MaterialBank"):
		mat_name = item.get("BankName")
		mat_id = item.get("uniqueguididBankId")
		logic_mat = item.get("logmatLogicMaterialV2")
		material = item.get("matMaterial")

		new_material = RoofMaterial(mat_name, mat_id, logic_mat, material)
		new_material.print_material()


# {A6934283-B71A-4162-9601-8396E326831C} -> Roof_Random
# material_bank_parser(building_roof_mat_bank_xml, "", "Roof_Random")

spline_material_bank_parser("9223372080543076447", "")

#TODO: Need to have a way to parse material banks for specific ID to return a list of where the ID is used


