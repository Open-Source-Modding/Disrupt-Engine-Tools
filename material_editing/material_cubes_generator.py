# ------LIBRARY------

import ipdb as pdb
from lxml import etree


import nomadtools
import numpy
import math
import os
import uuid
import scandir
import sys
from automatedocclusion.SonarKeyManager import CSonarKeyManager



# ------VARIABLE------


meshFolder = r"w:\main\data\graphics\TechArt\MaterialBlocks"
materialFolder = r"w:\main\data\graphics\_materials"
worldFolder = r"w:\main\data\Worlds\ftr_graphic_material\objects\user\Materials"

materialTypes = [
    "Brick",
    "Ceramic",
    # "Common",
    "Concrete",
    # "Emissive",
    #"Fabric",
    # "Generic_Unique",
    "Glass",
    "Marble",
    "Metal",
    "Plaster",
    "Plastic",
    # "Plaza_Wall",
    # "Rock",
    "Wood"
]

materialLayers = []
materialLayerPaths = []
materialCategories = []



# ------FUNCTION------

def openXML(filePath):
    # use a parser which ignores whitespace so we can pretty_print back later
    parser = etree.XMLParser(remove_blank_text=True)
    with open(filePath) as fo:
        content = fo.read()
        return etree.fromstring(content, parser=parser)


def WriteXml(filename, xmlContent):
    et = etree.ElementTree(xmlContent)
    et.write(filename, pretty_print=True)


def generateLayerPath(directory, name):
    layerPath = os.path.join(directory, (str(name) + ".xml"))
    return layerPath


def generateMeshPath(directory, name):
    meshPath = os.path.join(directory, ("material_cube_" + str(name).lower() + "_01.xml"))
    print(meshPath)
    return meshPath


def generateMetadataPath(meshPath):
    metadataPath = meshPath + ".metadata"
    return metadataPath


def generateCategory(name):
    category = "Base/Generic/" + name
    return category


def searchDirectory(directory):
    for root, dirs, files in scandir.walk(directory):
        for file in files:
            if file.endswith(".xml"):
                print(os.path.join(root, file))


# findall() from lxml, returns a list of matching elements
# find() from lxml, returns the first matching element
# findtext() from lxml, will return the text between start and end tags
# .// is the tagged type, i.e. .//category will look for <category>
def sortByCategory(material, path, categories, sorted):
    category = material.findtext('.//category')
    for index, i in enumerate(categories):
        if category != None:
            if category.find(i) > -1:
                sorted[index].append(path)


def newObjectCategory(objId, catName, catVal):
    object = etree.Element("object", hex_id=str(objId), id=str(objId))
    category = etree.Element("category", name=catName)
    category.text = catVal
    object.append(category)
    return object

def populateLayer(meshName, meshID, worldPosition, localPosition):

    guid = "{" + str(uuid.uuid4()) + "}"
    model = str('graphics\models\\')+str(meshID)+".model"

    element = etree.Element("Object", 
                            Type="BatchedObject",
                            Id=guid,
                            Name=meshName,
                            Pos=worldPosition,
                            WorldPos=worldPosition,
                            gigGIGroup="4294967295",
                            ConvertedEntityId="18446744073709551615")

    etree.SubElement(element, "BatchModel",
                    hid_DTCTH_ClassName="CGraphicBatchModel",
                    fileModel=model,
                    bCastShadow="1",
                    uiShadowGroup="4294967295",
                    bShowInReflection="1",
                    bUseMinSizeDetailCurrentGen="0",
                    bElectric="1",
                    bElectricBackup="0",
                    bRainOccluder="0",
                    bIgnorePhysics="0",
                    bHideable="0")
    
    return element

def generateUniqueID():
    uniqueKey = int(CSonarKeyManager.get_key()) #get unique ID and convert to HEX #pyMetaDataService.CreateUniqueKey()
    uniqueID = "0x" + format(uniqueKey, "016X") #convert HEX to string and add the 0x we have on everything
    values = [uniqueKey, uniqueID]
    return values #uniqueID



def createGraphicModels(mesh, meshPath, category, counter):

    name = category
    IDs = generateUniqueID()
    objID = IDs[0]
    hexID = IDs[1]

    Log_UUID = str(uuid.uuid4().time_mid)

    #graphicModels is the root of all models
    GraphicModels = mesh.find('.//GraphicModels')
	
    if counter < 10:
        currentOverride = "0"+str(counter)
    else:
        currentOverride = str(counter)
	
	
    #create a new graphicModel element with unique IDs
    graphicModel = etree.Element("GraphicModel", 
                                UniqueID=hexID, 
                                DisplayName=str(name)+currentOverride, 
                                IsEditable="1")

    #create a material subelement
    #material = etree.SubElement(materialSlot, "Material")
    material = etree.Element("Material", disSlotName="", matMaterial="")
    
    #create a material slot subelement
    materialSlot = etree.SubElement(graphicModel, "MaterialSlots")

    #attach all elements together
    materialSlot.append(material)
    newModel = GraphicModels.append(graphicModel)

    WriteXml(meshPath, mesh)

    # metadata
    metadataPath = meshPath + ".metadata"
    metadata = openXML(metadataPath)
    print("METADATA"+metadataPath)

    # object id = decimal id, id_hex = same id in hex
    # <category name="GraphicModelIsEditable">0</category>
    object = newObjectCategory(objID, "GraphicModelIsEditable", "1")
    metadata.append(object)


    WriteXml(metadataPath, metadata)


def updateGraphicModels(graphicModel, materialPath, category, meshPath, mesh, count):
    print("updateGraphicModels")
    print(graphicModel, materialPath, category, meshPath, mesh, count)

    # find materialslots
    # findall material, if doesnt exist create material
    # disSlotName="category" matMaterial="materialPath"

    disSlotName = str.lower(category)

    materialPathRelative = "graphics/_materials/" + os.path.basename(materialPath)

    materialSlots = graphicModel.find("MaterialSlots")

    if(materialSlots == None):
        materialSlots = etree.Element("MaterialSlots")
        graphicModel.append(materialSlots)

    material = materialSlots.find("Material")

#    pdb.set_trace()

    if(material == None):
        material = etree.Element("Material", disSlotName=disSlotName, matMaterial=str(materialPathRelative))
        materialSlots.append(material)
    else:
        material.set("disSlotName", disSlotName)
        material.set("matMaterial", materialPathRelative)


    WriteXml(meshPath,mesh)



def updateMaterialOverrides(meshPath, category, materialPaths):
    # get xml from meshPath
    # get metadata from meshPath

    mesh = openXML(meshPath)

    pathCount = len(materialPaths)
    modelCount = len(mesh.findall('.//GraphicModel'))
    if pathCount > modelCount:
        for i in range(pathCount - modelCount):
            createGraphicModels(mesh, meshPath, category, i)


    for j, (models,materialPath) in enumerate(zip(mesh.findall('.//GraphicModel'), materialPaths)):
        updateGraphicModels(models, materialPath, category, meshPath, mesh, j)

# ------------MAIN-----------------

def generateMaterialCubes(matDir, layerDir, types, meshDir):
    sortedMaterials = []
    meshPaths = []
    
    for i in range(0, len(types)):
        sortedMaterials.append([])

    # Fill out list of categories and layers
    for i in types:
        currentCategory = generateCategory(i)
        currentLayerPath = generateLayerPath(layerDir, i)
        currentMeshPath = generateMeshPath(meshDir, i)

        # Use append, extend will add each string as an individual character
        materialCategories.append(currentCategory)
        materialLayerPaths.append(currentLayerPath)

        meshPaths.append(currentMeshPath)


    for root, dirs, files in scandir.walk(matDir):
        for file in files:
            if file.endswith(".xml"):
                materialPath = os.path.join(root, file)
                material = openXML(materialPath)
                # in xml, check categories,
                sortByCategory(material, materialPath, materialCategories, sortedMaterials)

    #print "sorted list"
    #print(sortedMaterials)

    meshPath = meshDir 

    for meshPath, category, materialSet in zip(meshPaths, materialTypes, sortedMaterials):
        updateMaterialOverrides(meshPath, category, materialSet)


    origin = (145,-3,0.5)
    sOffset = -15.0
    cOffset = -2.0
    rOffset = -2.0
    col = 6
    
    for k, (meshPath,layerPath) in enumerate(zip(meshPaths, materialLayerPaths)):
    #for meshPath, layerPath in zip(meshPaths, materialLayerPaths):
        mesh = openXML(meshPath)
        print("::::::::::::::::::::::::::::::::::::::::")
        print(meshPath, mesh, layerPath)
    

        #create temp layer object
        root = etree.Element("LayerContent",
                            BBoxMin=str([-100,-100]),
                            BBoxMax=str([100,100]))

        print("root",root)

        #instead of cycling through overrides should we go through metadata objects instead?
        #would have id_hex right there
        overrides = mesh.findall('.//GraphicModel')
    
        #populate appends to this object
        for j, override in enumerate(overrides):
            meshName = "meshName" #+material category count

            section = k*sOffset
            column = j%col
            row = (j-column)/col

            xPos = (cOffset*column)+origin[0]+section
            yPos = (rOffset*row)+origin[1]
            zPos = origin[2]

            worldPos = str(xPos) + ',' + str(yPos) + ',' + str(zPos)
            localPos = "0,0,0"
            meshID = override.get("UniqueID")
            
            element = populateLayer(meshName, meshID, worldPos, localPos)
            root.append(element)

        layer = openXML(layerPath)
        layerRoot = layer.find('.//LayerContent')

        #pdb.set_trace()
        layer = root
        WriteXml(layerPath, layer)
 

def main():
    # searchDirectory(materialFolder)
    generateMaterialCubes(materialFolder, worldFolder, materialTypes, meshFolder)
if __name__ == '__main__':
    main()