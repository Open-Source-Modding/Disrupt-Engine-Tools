#gilbert.arcand@ubisoft.com
#March 29 2018
#A script made to provide a liste of material dependencies xml attributes

from os import walk
from os.path import join
import xml.etree.cElementTree as ET

#Material Parameters Type
#W:\dev\wd3-prod\main\code\GraphicsToolbox\DynamicProvider\MaterialDescriptorManager.cpp
mat_param_types = [
        "sampler2D",
        "samplerCUBE",
        #"float",
        #"float2",
        #"float3",
        #"float4",
        #"color3",
        #"color4",
        #"int",
        #"bool",
        #"samplerState",
        "bink",
        #"gradient",
        "sampler3D",
        "sampler2DArray",
        ]

#Material Descriptor folder
mat_desc_path = r"W:\main\data\engine\shaders\materialdescriptors"
mat_desc_ext = r".xml"

mat_dep_attrib_list = set()

for root, dirs, files in walk(mat_desc_path):
    for _file in files:
        if _file.lower().endswith(mat_desc_ext):
            mat_desc_file = join(root, _file)
            tree = ET.ElementTree(file=mat_desc_file)
            for elem in tree.iter("parameter"):
                my_type = elem.get("type")
                if my_type:  # is not none
                    if my_type in mat_param_types:
                        my_name = elem.get("name")
                        if my_name:
                            mat_dep_attrib_list.add(my_name)  #Pas sur si tu les veux en lower case

list_to_sort = []

for i in mat_dep_attrib_list:
    list_to_sort.append(i)

list_to_sort.sort()

print "---"
print str(len(mat_dep_attrib_list))
print "---"

for i in list_to_sort:
    print i

file = open("mat_dep_attrib_list.txt", "w")

for i in list_to_sort:
    file.write('"' + i + '",\n')

file.close()
