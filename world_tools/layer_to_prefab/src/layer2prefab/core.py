import logging


# import ipdb as pdb
import os
import uuid
from lxml import etree
from PySide import QtCore, QtGui


# from P4 import P4, P4Exception


# import numpy
# import scandir


# -----------------------------FUNCTION------------------------


# def connectP4():
#    p4 = P4()
#    p4.port = ""
#    p4.user = ""
#    p4.client = ""
#
#    result = "Checkout Succeeded"
#
#    try:
#        p4.connect()
#        info = p4.run("info")
#        p4.run("edit", file)
#
#    except P4Exception:
#        result = "Checkout Failed"
#        for error in p4.errors:
#            print error
#    return result


def openXML(filePath):
    parser = etree.XMLParser(remove_blank_text=True)
    with open(filePath) as fo:
        content = fo.read()
        return etree.fromstring(content, parser=parser)


def writeXML(fileName, xmlContent):
    et = etree.ElementTree(xmlContent)
    et.write(fileName, pretty_print=True)


def getDirectoryFiles(directoryPath):
    # for kits folder = kit, glm/gamex files containing "shop" are sources, xml.metadata has ids
    # brands same as above where folder is brand
    # TODO: add something to sort file extension?

    # parent folder
    folder = os.path.basename(directoryPath)

    directoryNames = [folder]
    directoryFiles = []

    for root, dirs, files in (os.walk(directoryPath)):  # scandir.walk from import scandir is probably faster
        directoryNames.extend(dirs)
        directoryFiles.append(files)

    print(directoryNames, directoryFiles)
    fullDirectory = (directoryNames, directoryFiles)

    return (fullDirectory)


def writeModelElement(meshName, meshID):
    guid = "(" + str(uuid.uuid()) + ")"
    model = str('graphics\models\\') + str(meshID) + "model"
    localPos = [0, 0, 0]
    element = etree.Element("Object",
                            Type="BatchedObject",
                            Id=guid,  # "123",#
                            Name=meshName,
                            Pos=str(localPos),  # probably dont need for prefab version
                            WorldPos=str("[0,0,0]"),
                            gigGIGroup="4294967295",
                            ConvertedEntityId="18446744073709551615"
                            )

    etree.SubElement(element,
                     "BatchModel",
                     hid_DTCH_ClassName="CGraphicBatchModel",
                     fileModel=model,
                     bCastShadow="1",
                     uiShadowGroup="4294967295",
                     bShowInReflection="1",
                     bUseMinSizeDetailCurrentGen="0",
                     bElectric="1",
                     bElectricBackup="0",
                     bRainOccluder="0",
                     bIgnorePhysics="0",
                     bHideable="0"
                     )
    return element


def writeProxyPrefabContents(destinateion, proxyName, contents):
    proxyContents = etree.Element("Object",
                                  ProxyObjectType="Prefab",
                                  PrefabGUID="{FCC8DA63-8A02-4ABE-A9BF-14CC8DAB6AF4}",
                                  id=contents)  # batched info

    return 0


def generateUniqueID():
    uniqueKey = int(CSonarKeyManager.get_key())  # get unique ID and convert to HEX #pyMetaDataService.CreateUniqueKey()
    uniqueID = "0x" + format(uniqueKey, "016X")  # convert HEX to string and add the 0x we have on everything
    values = [uniqueKey, uniqueID]
    return values  # uniqueID


def writeProxy(destination, proxyName, contents):
    IDs = generateUniqueID()
    objID = IDs[0]
    hexID = IDs[1]

    # Log_UUID = str(uuid.uuid4().time_mid)

    path = destination + "\\" + proxyName + ".xml"
    metadataPath = path + ".metadata"
    print(path, " ", metadataPath)

    proxy = etree.Element("ProxyObjectDescriptor")
    metadata = etree.Element("Metadata")

    proxyContents = etree.Element("Object",
                                  name=proxyName,
                                  id=contents)  # batched info

    metadataContents = etree.Element("object",
                                     name=proxyName,
                                     id=objID,
                                     id_hex=hexID)

    metaDataCategory = etree.SubElement("category",
                                        name="ResourceID")

    metaDataCategory.text = hexID

    proxy.append(proxyContents)
    metadataContents.append(metaDataCategory)
    metadata.append(metadataContents)

    writeXML(path, proxy)
    writeXML(metadataPath, metadata)
    return 0


def proxyFromPrefabdef(prefabPath):
    library = openXML(prefabPath)
    root = etree.Element("PrefabLibrary")
    prefabs = library.findall('Prefab')
    for prefab in prefabs:
        attributes = prefab.attrib
        name = attributes["Name"]
        id = attributes["Id"]
        prefabName = str(name).split(".")
        print(prefabName[1])
        writeProxy(r"E:\Code", prefabName[1], id)

    return 0


def writePrefabMeshElement(group, meshName, brand, variant):
    guid = "{" + str(uuid.uuid4()) + "}"
    model = str('graphics\models\\') + str(meshID) + ".model"

    prefabElement = etree.Element("Prefab",
                                  Name=group + "." + meshName + "_" + brand + "_" + variant,
                                  Id="5",
                                  Unbreakable="0"
                                  )

    objectsElement = etree.SubElement(prefabElement, "Objects")
    modelObjectElement = writeModelElement(meshName, meshID)
    objectsElement.append(modelObjectElement)

    return prefabElement


def writePrefabElement(prefabName):
    guid = "{" + str(uuid.uuid4()) + "}"

    prefabElement = etree.Element("Prefab",
                                  Name=prefabName,
                                  Id=guid,
                                  Unbreakable="0"
                                  )
    objectsElement = etree.SubElement(prefabElement, "Objects")
    modelObjectElement = writeModelElement(meshName, meshID)
    objectsElement.append(modelObjectElement)

    return prefabElement


def updatePrefabFromLayer(prefabLibPath, layerPath, groupName):
    # get and store all layer objects

    layer = openXML(layerPath)
    objects = layer.findall("Object")
    subElementList = list()

    for object in objects:
        subElementList.append(object)

    tempName = (os.path.basename(layerPath)).split(".")
    layerName = tempName[0].lower()



    prefabElement = None
    existingPrefab = None
    existingName = ""
    existingID = ""

    library = openXML(prefabLibPath)
    # root = etree.Element("PrefabLibrary")
    root = library.find('.//PrefabLibrary')

    prefabs = library.findall('Prefab')



    for prefab in prefabs:
        attributes = prefab.attrib
        name = attributes["Name"]
        id = attributes["Id"]
        tempName = str(name).split(".")
        curGroupName = tempName[0].lower()
        prefabName = tempName[1].lower()

        if groupName == None:
            if (prefabName == layerName):
                existingPrefab = prefab
                existingID = id
                existingName = name
        else:
            if ((groupName == curGroupName) and (prefabName == layerName)):
                existingPrefab = prefab
                existingID = id
                existingName = name

    if groupName == None:
        groupName = "_ungrouped"


    if (existingPrefab is None):
        # just write new prefab
        thisName = (str(groupName).lower() + "." + layerName)
        guid = str(uuid.uuid4())  # "(" + str(uuid.uuid()) + ")"
        prefabElement = etree.Element("Prefab", Name=thisName, Id=guid, Unbreakable="0", ExportToAtlas="0",
                                      AtlasElementType="")
    else:
        prefabElement = etree.Element(existingName)
        prefabElement.clear()

        prefabElement = etree.Element("Prefab")
        prefabElement.set("Name", existingName)
        prefabElement.set("Id", existingID)
        prefabElement.set("Unbreakable", "0")
        prefabElement.set("ExportToAtlas", "0")
        prefabElement.set("AtlasElementType", "")

    # we want to kill all sub elements and replace with layer sub elements
    # we want to reuse ID and Name

    # Now add all the sub elements
    objectsElement = etree.Element("Objects")

    for subElement in subElementList:
        objectsElement.append(subElement)
        print(objectsElement.get('Name'))

    prefabElement.append(objectsElement)

    if (existingPrefab == None):
        print("we are adding to library now")
        library.append(prefabElement)

    # testElement = etree.Element("test", text = "hmmmm")
    # library.append(testElement)

    writeXML(prefabLibPath, library)
    return 0

def updateGroups(prefabLibPath):
    print("we are listening in group updates")

    library = openXML(prefabLibPath)
    prefabs = library.findall('Prefab')
    groupNames =  list()

    for prefab in prefabs:
        attributes = prefab.attrib
        name = attributes["Name"]
        tempName = str(name).split(".")
        groupNames.append(tempName[0].lower())

    return groupNames

def my_script(prefab, world, group):
    print("we are listening in core")
    if group == None or group == " " or group == "":
        group = "_default"
    else:
        print("group name is valid")

    logging.info("%s %s %s"% (prefab, world, str(group)))
    updatePrefabFromLayer(prefab, world, str(group))


def main():
    # getDirectoryFiles(r"E:\Code\bang",'.txt')
    # element = writeModelElement("meshy", "123")
    print("test")
    # updatePrefabFromLayer(r"w:\main\data\Databases\Prefabs\PythonTestFile.xml", r"w:\main\data\worlds\_blank\Objects\User\PythonTestLayer.xml", "test_01")


if __name__ == '__main__':
    main()