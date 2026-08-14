import uuid
import xml.etree.cElementTree as ET
from xml.dom import minidom
import random

complete = '''
     |\__/,|   (`\ \nmeow |_ _  |.--.) )\n     ( t   )     /\n    (((^_(((/(((_>\n
'''

# --> EXPORT ATLAS SOURCES
MTL_source_atlas_xml = r"W:\Main\td_tools\dbeaulieu\get_atlas_shapes\mtl_atlas_shape_export.xml"
PAR_source_atlas_xml = r"W:\Main\td_tools\dbeaulieu\get_atlas_shapes\par_atlas_shape_export.xml"
BUC_source_atlas_xml = r"W:\Main\td_tools\dbeaulieu\get_atlas_shapes\buc_atlas_shape_export.xml"
TOR_source_atlas_xml = r"W:\Main\td_tools\dbeaulieu\get_atlas_shapes\tor_atlas_shape_export.xml"
# _____


#TODO: Should make this append to selected xml layer instead of wipping and creating totally new. Avoid wipping prewritten data
# --> PREFIXES ASSOCIATION TO LAYERS
MTL_borough_layers = {	"CL": r"W:\Main\data\Worlds\London\Objects\User\01_CityOfLondon\00_COL_Subdivisions\00_COL_City_Blocks.xml",
				  		"IH": r"W:\Main\data\Worlds\London\Objects\User\05_Hackney_Islington\00_HAC_Subdivisions\00_HAC_City_Blocks.xml",
				  		"TW": r"W:\Main\data\Worlds\London\Objects\User\06_TowerHamlets_West\00_THW_Subdivisions\00_THW_City_Blocks.xml",
				  		"TE": r"W:\Main\data\Worlds\London\Objects\User\07_TowerHamlets_East\00_THE_Subdivisions\00_THE_City_Blocks.xml",
					  }

PAR_borough_layers = {	"NEL": r"W:\Main\data\Worlds\London\Objects\User\08_Wandsworth\00_WAN_DebugAnnotShape\08_Wandsworth_City_Block_Shapes.xml", # Wandsworth -> Nine Elms
						"LBT": r"W:\Main\data\Worlds\London\Objects\User\09_Lambeth\00_LAM_DebugAnnotShape\09_LambethNorth_City_Block_Shapes.xml", # Lambeth North South
						"SBK": r"W:\Main\data\Worlds\London\Objects\User\09_Lambeth\00_LAM_DebugAnnotShape\09_SouthBank_City_Block_Shapes.xml", # Lambeth North -> Southbank
						"STW": r"W:\Main\data\Worlds\London\Objects\User\09_Lambeth\00_LAM_DebugAnnotShape\09_LambethSouth_City_Block_Shapes.xml", # Lambeth South -> Stockwell
						"KNT": r"W:\Main\data\Worlds\London\Objects\User\09_Lambeth\00_LAM_DebugAnnotShape\09_Kennington_City_Block_Shapes.xml", # Lambeth South -> Kennington North South
						"BXT": r"W:\Main\data\Worlds\London\Objects\User\09_Lambeth\00_LAM_DebugAnnotShape\09_Brixton_City_Block_Shapes.xml", # Lambeth South -> Brixton
					  }

BUC_borough_layers = {	"SW": r"W:\Main\data\Worlds\London\Objects\User\10_Southwark\00_SWK_Subdivisions\00_SWK_City_Block_Shapes.xml"}

TOR_borough_layers = {	"CBB": r"W:\Main\data\Worlds\London\Objects\User\04_Camden\00_cam_subdivisions\00_Bloomsbury_City_Block_Shapes.xml",
						"CCT": r"W:\Main\data\Worlds\London\Objects\User\04_Camden\00_cam_subdivisions\00_CamdenTown_City_Block_Shapes.xml",
				  		"CHB": r"W:\Main\data\Worlds\London\Objects\User\04_Camden\00_cam_subdivisions\00_Holborn_City_Block_Shapes.xml",
				  		"CKC": r"W:\Main\data\Worlds\London\Objects\User\04_Camden\00_cam_subdivisions\00_KingsCross_City_Block_Shapes.xml",
						"CMB": r"W:\Main\data\Worlds\London\Objects\User\04_Camden\00_cam_subdivisions\00_Marylebone_City_Block_Shapes.xml",
				  		"CRP": r"W:\Main\data\Worlds\London\Objects\User\04_Camden\00_cam_subdivisions\00_RegentsPark_City_Block_Shapes.xml",
				  		"CSP": r"W:\Main\data\Worlds\London\Objects\User\04_Camden\00_cam_subdivisions\00_StPancras_City_Block_Shapes.xml",
				  		"WGP": r"W:\Main\data\Worlds\London\Objects\User\03_Westminster\00_wes_subdivisions\00_GreenPark_City_Block_Shapes.xml",
						"WPL": r"W:\Main\data\Worlds\London\Objects\User\03_Westminster\00_wes_subdivisions\00_Pimilco_City_Block_Shapes.xml",
				  		"WSJ": r"W:\Main\data\Worlds\London\Objects\User\03_Westminster\00_wes_subdivisions\00_StJames_City_Block_Shapes.xml",
				  		"WWE": r"W:\Main\data\Worlds\London\Objects\User\03_Westminster\00_wes_subdivisions\00_WestEnd_City_Block_Shapes.xml",
				  		"WWM": r"W:\Main\data\Worlds\London\Objects\User\03_Westminster\00_wes_subdivisions\00_Westminster_City_Block_Shapes.xml"
					  }

# _____

# --> CITY BLOCK PREDEFINED COLORS
MTL_city_block_colors = {"CLBL": "#c00000", "CLS1": "#c00000", "CLCH": "#c00000",
					 	"TELH": "#ff0000", "TEPP": "#ff0000",
					 	"TWTL": "#ffc000", "TWW1": "#ffc000", "TWW2": "#ffc000",
					 	"IHC1": "#ffff00", "IHC2": "#ffff00", "IHS1": "#ffff00",
					 	"CLSF": "#92d050", "CLSP": "#92d050", "CLBB": "#92d050",
					 	"IHF1": "#00b050", "IHF2": "#00b050",
					 	"TWS1": "#00b0f0", "TWWC": "#00b0f0",
					 	"TEC1": "#0070c0", "TEC2": "#0070c0", "TEC3": "#0070c0",
					 	"CLDT": "#002060", "CLS2": "#002060",
					 	"IHS2": "#7030a0", "IHH1": "#7030a0", "IHH2": "#7030a0",
					 	"TWB1": "#000000", "TWB2": "#000000", "TWS2": "#000000",
					 	"TEMW": "#ed7d31", "TECT": "#ed7d31"}
# _____

# --> PREDEFINED BOROUGH HEIGHTS
MTL_borough_height = {	"CL": "105",
				  		"TW": "102",
				  		"TE": "99",
				  		"IH": "100"}
PAR_borough_height = {	"NEL": "100",
				  		"LBT": "100",
				  		"SBK": "100",
				  		"STW": "100",
						"KNT": "100",
				  		"BXT": "100"}
BUC_borough_height = {	"SW": "100"}
TOR_borough_height = {	"CBB": "110",
					  	"CCT": "107",
					  	"CHB": "108",
					  	"CKC": "107",
					  	"CMB": "110",
					  	"CRP": "108",
					  	"CSP": "106",
					  	"WGP": "100",
					  	"WPL": "100",
						"WSJ": "106",
						"WWE": "108",
						"WWM": "108"
					  }
# _____

debug_annotation_shape_list = []

### GLOBAL VARIABLES
global_export_to_atlas = "0" # Bool: 0=False, 1=True
atlastypeElementType = "" # TODO: Define this before enabling global export

global_multiple_rounding_value = 7 # Multiple to round position integers to
global_volume_height = "20" # Bounding of volume height
global_volume_alpha = "0.5" # Alpha channel for volume transparency
in_editor_prefix = "CityBlock_"


class Debug_Annotation_Shape(object):
	def __init__(self, name, position, color_rgb, point_string, point_list, z_pos = "96"):
		self.name = name
		self.position = position
		self.world_position = position
		self.color = color_rgb
		self.point_string = point_string
		self.point_list = point_list
		self.height = global_volume_height
		self.z_pos = z_pos

	def print_elem(self):
		print self.name, self.position, self.color, self.point_string, self.point_list, self.height

def create_xml_file():
	parse_atlas_xml(TOR_source_atlas_xml)

	root_list = []
	if debug_annotation_shape_list is not None:
		for annotation_shape in debug_annotation_shape_list:
			generated_guid = "{" + str(uuid.uuid4()) + "}"
			generated_nomad_id = str(random.randint(9000000000000000000, 9999999999999999999))

			if annotation_shape != None:
				Object = ET.Element("Object",
									   Type="DebugAnnotationShape",
									   Id=generated_guid,
									   Name=annotation_shape.name,
									   Pos="{},{},{}".format(annotation_shape.position.get("x"),
															 annotation_shape.position.get("y"),
															 annotation_shape.z_pos),
									   WorldPos="{},{},{}".format(annotation_shape.position.get("x"),
															 	annotation_shape.position.get("y"),
														  		annotation_shape.z_pos),
									   ColorRGB=annotation_shape.color,
									   EntityClass="DebugAnnotationShape",
									   Height=annotation_shape.height
									   )

				Entity = ET.SubElement(Object, "Entity",
							  disNomadObjectId=generated_nomad_id, #(9223372086765691240)
							  hidName=annotation_shape.name,
							  hidEntityClass="CEntity",
							  hidResourceCount="1",
							  hidPos="0,0,0",
							  hidAngles="0,0,0",
							  hidPos_precise="0,0,0",
							  hidConstEntity="0",
							  hidFakeArchetypeId="debugannotationshape",
							  wlucatLoadingUnitCategoryV3="3",
							  bPoolable="0",
							  bEnableLocalProperties="0",
							  bPoolClearOnUnused="1"
							  )

				ET.SubElement(Entity, "hidGroupIds")

				ET.SubElement(Entity, "hidBBox",
							  vectorBBoxMin="0,0,0",
							  vectorBBoxMax="0,0,0"
							  )

				Components = ET.SubElement(Entity, "Components")

				CDebugAnnotationShapeComponent = ET.SubElement(Components, "CDebugAnnotationShapeComponent",
							  hidHasAliasName="0")

				ET.SubElement(CDebugAnnotationShapeComponent, "DebugAnnotationObject",
							  	bEnabled="1",
							  	bEnableVisibilityDistanceTest="1",
							  	fVisibilityDistance="3333",
							  	Points=annotation_shape.point_string,
							  	fHeight="10",
								clrColor=annotation_shape.color,
							  	fAlpha=global_volume_alpha
								)

				CEditableComponent = ET.SubElement(Components, "CEditableComponent",
							  hidHasAliasName="0",
							  gigGIGroup="4294967295"
							  )

				ET.SubElement(CEditableComponent, "TerrainModifier",
							  bEnabled="0",
							  fFlatRadius="1",
							  fFalloff="0",
							  fHeightModifier="0"
							  )
				ET.SubElement(CEditableComponent, "Atlas",
							  bExportToAtlas=global_export_to_atlas,
							  atlastypeElementType=""
							  )
				ET.SubElement(CEditableComponent, "AdjustToCurvedRoad",
							  bAdjustToCurvedRoad="0"
							  )

				CEventComponent = ET.SubElement(Components, "CEventComponent",
							  hidHasAliasName="0"
							  )
				ET.SubElement(CEventComponent, "hidLinks")
				ET.SubElement(CEventComponent, "hidBatchedLinks")

				points = ET.SubElement(Object, "Points")
				for i in range (len(annotation_shape.point_list)):
					ET.SubElement(points,"Point",
								  Pos="{},{},0".format
								  (
									  (float(annotation_shape.point_list[i].get("x")) - float(annotation_shape.position.get("x"))),
									  (float(annotation_shape.point_list[i].get("y")) - float(annotation_shape.position.get("y"))))
								  )

				new_item = (annotation_shape.name, Object)
				root_list.append(new_item)

	construct_list_to_write(root_list)

def create_new_debug_annotation_shape(name, position, color_rgb, point_string, point_list, height):
	new_annotation = Debug_Annotation_Shape(name, position, color_rgb, point_string, point_list, height)
	new_annotation.print_elem()
	debug_annotation_shape_list.append(new_annotation)

def parse_atlas_xml(xml):
	tree = ET.ElementTree(file=xml)

	for layer in tree.iter("layer"):
		for entity in layer.iter("entity"):
			atlas_name = entity.get("atlasName")

			if "text" and "bridge" and "oob" not in atlas_name.lower():
				debug_annotation_name = in_editor_prefix + atlas_name
				height = get_height(debug_annotation_name)

				point_vectors = []
				point_string = "Count()"
				x_pos_array = []
				y_pos_array = []

				for point in entity.iter("point"):
					x_pos = point.get("x")
					y_pos = point.get("y")

					if x_pos and y_pos is not None:
						rounded_x = round_to_multiple(float(x_pos), global_multiple_rounding_value)
						x_pos = str(float(rounded_x) * -1) # invert x position from atlas to editor
						x_pos_array.append(float(x_pos))

						rounded_y = round_to_multiple(float(y_pos), global_multiple_rounding_value)
						y_pos_array.append(rounded_y)
						volume_center = get_bounding_box_center(x_pos_array, y_pos_array)
						vector = {"x": str(x_pos), "y": str(rounded_y)}

						point_vectors.append(vector)
						point_string += "{},{},0;".format(x_pos, y_pos)

				for symbol in entity.iter("symbol"):
					atlas_color = symbol.get("colorFill")

					if atlas_color is not None:
						convert_atlas_color = convert_hex_to_rgb(atlas_color)
						red = str(round(convert_atlas_color[0] / 255.0, 1))
						green = str(round(convert_atlas_color[1] / 255.0, 1))
						blue = str(round(convert_atlas_color[2] / 255.0, 1))
						new_atlas_color = "{},{},{}".format(red, green, blue)

				for k, v in MTL_city_block_colors.iteritems():
					if k in debug_annotation_name:
						rgb_color = convert_hex_to_rgb(v)
						red = str(round(rgb_color[0] / 255.0, 1))
						green = str(round(rgb_color[1] / 255.0, 1))
						blue = str(round(rgb_color[2] / 255.0, 1))
						color = "{},{},{}".format(red, green, blue)

				point_string = point_string.replace("Count()", "Count({}) ".format(str(len(point_vectors))))

				if len(point_vectors) > 1:
					create_new_debug_annotation_shape(debug_annotation_name, volume_center, new_atlas_color, point_string, point_vectors, height)

def get_height(name):
	for k, v in TOR_borough_height.iteritems():
		if k in name:
			return v

def round_to_multiple(x, multiple_factor):
	return int(multiple_factor * round(float(x)/multiple_factor))

def convert_hex_to_rgb(hex_color_code):
	if "#" in hex_color_code:
		hex_color_code = hex_color_code.lstrip('#')

	lv = len(hex_color_code)
	return tuple(int(hex_color_code[i:i + lv / 3], 16) for i in range(0, lv, lv / 3))

def get_bounding_box_center(x_pos_list, y_pos_list):
	min_x_value = min(x_pos_list)
	max_x_value = max(x_pos_list)
	x_diff = (max_x_value - min_x_value) / 2
	x_center = min_x_value + x_diff

	min_y_value = min(y_pos_list)
	max_y_value = max(y_pos_list)
	y_diff = (max_y_value - min_y_value) / 2
	y_center = min_y_value + y_diff

	pivot_position = {"x": x_center, "y": y_center}
	return pivot_position

def write_xml(root, file_to_write):
	for elem in root.iter('*'):
		if elem.text is not None:
			elem.text = elem.text.strip()
		if elem.tail is not None:
			elem.tail = elem.tail.strip()

	# TODO: Need to reasign root...
	rough_string = ET.tostring(root, "utf-8")
	reparsed = minidom.parseString(rough_string)
	pretty_xml = reparsed.toprettyxml(indent="\t")

	file = open(file_to_write, "w")
	file.write(pretty_xml.replace('<?xml version="1.0" ?>\n', ""))
	file.close()

def construct_list_to_write(root_list):
	#TODO: Associate same names to same root list
	dict_to_write_list = []
	root_list_to_write = {}

	# Create dictionary with initials and root -> adding them to a general list
	for index in range (len(root_list)):
		initials = (root_list[index])[0].replace(in_editor_prefix, "")[:3] # 2 for MTL and BUC - 3 for PAR and TOR
		root = (root_list[index])[1]
		dict_to_write = {initials: root}
		dict_to_write_list.append(dict_to_write)

	# iterating through all dictionnary array for keys (initials) to compare and associate value (root)
	for i in range (len(dict_to_write_list)):
		for k, v in dict_to_write_list[i].iteritems():
			if k not in root_list_to_write:
				root_list_to_write[k] = ET.Element("LayerContent", BBoxMin="0,0", BBoxMax="0,0")
			root_list_to_write[k].append(v)

	for initials, root in root_list_to_write.iteritems():
		rough_string = ET.tostring(root, "utf-8")
		reparsed = minidom.parseString(rough_string)
		pretty_xml = reparsed.toprettyxml(indent="\t")

		for elem in root.iter('*'):
			if elem.text is not None:
				elem.text = elem.text.strip()
			if elem.tail is not None:
				elem.tail = elem.tail.strip()

		file = open(TOR_borough_layers[initials], "w")
		file.write(pretty_xml.replace('<?xml version="1.0" ?>\n', ""))
		file.close()

###
create_xml_file()
# parse_atlas_xml(TOR_source_atlas_xml)
print complete

