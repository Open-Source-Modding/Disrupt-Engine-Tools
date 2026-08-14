# ------LIBRARY------

import os


import sys
#from nomadtools.resources import PyMetaDataService
from lxml import etree
from automatedocclusion.SonarKeyManager import CSonarKeyManager

#import pyMetaDataService27_x64 as pyMetaDataService

# ------VARIABLE------

dirPath = r"w:\main\data\graphics\geometry\exterior\Generic\structures\modular\platforms\\"
kitString = "platform_modern_kit_02"
#kitString = "platform_kit_05_railing"

meshPath = r"w:\main\data\graphics\geometry\exterior\Generic\structures\modular\platforms\platform_modern_kit_02_stairs_1x3_closed_01.xml"

# template
o1Slots = (
    "concrete_steel_01",
    ["step", "svarma-m-9223372070385130107.material.xml"],
    ["tile", "svarma-m-9223372070385130107.material.xml"],
    ["frame", "hxu-m-9223372082304576530.material.xml"],
    ["slab", "svarma-m-9223372070385107977.material.xml"],
    ["rail", "rbews-m-9223372081623994236.material.xml"]
)

o2Slots = (
    "wood_01",
    ["step", "yotsu-m-9223372063889607279.material.xml"],
    ["tile", "yotsu-m-9223372063889607279.material.xml"],
    ["frame", "mwenrui-m-9223372083020225827.material.xml"],
    ["slab", "mwenrui-m-9223372083020225827.material.xml"],
    ["rail", "rbews-m-9223372081623994236.material.xml"]
)

o3Slots = (
    "wood_steel_01",
    ["step", "ymzhang-m-9223372080262413261.material.xml"],
    ["tile", "ymzhang-m-9223372080262413261.material.xml"],
    ["frame", "apiacob-m-9223372086343968322.material.xml"],
    ["slab", "rlaudico-m-9223372083155665011.material.xml"],
    ["rail", "mlapierre-m-9223372083751152968.material.xml"]
)


o4Slots = (
    "wood_steel_01",
    ["step", "ymzhang-m-9223372080262413261.material.xml"],
    ["tile", "ymzhang-m-9223372080262413261.material.xml"],
    ["frame", "apiacob-m-9223372086343968322.material.xml"],
    ["slab", "rlaudico-m-9223372083155665011.material.xml"],
    ["rail", "mlapierre-m-9223372083751152968.material.xml"]
)

a1Slots = (
   "blue_01",
    ["frame", "pvisconti-m-9223372095772491925.material.xml"],
    ["floor", "pvisconti-m-9223372095772491928.material.xml"]
)

a2Slots = (
    "yellow_01",
    ["frame", "pvisconti-m-9223372095772491926.material.xml"],
    ["floor", "pvisconti-m-9223372095772491927.material.xml"]
)



# -----------------------------FUNCTION------------------------

def openXML(filePath):
    parser = etree.XMLParser(remove_blank_text=True)
    with open(filePath) as fo:
        content = fo.read()
        return etree.fromstring(content, parser=parser)


def writeXML(fileName, xmlContent):
    et = etree.ElementTree(xmlContent)
    et.write(fileName, encoding='utf-8', pretty_print=True)

#def normalizeFormatting(filePath):
#    file = openXML(filePath)
#    file.replace('  ', '\t')


#-----------------------------MetaData Service-----------------


# def generateUniqueID():
#     dpath = PyMetaDataService.dist_path()
#     sys.path[0:0] = [dpath]
#     exe_path = r"W:\Main\bin\tools\MetadataService\MetadataService_ServiceLauncher.exe"
#
#     pyMetaDataServiceIsMine = False
#     if not pyMetaDataService.IsInitialized():
#
#         # Initialize the fake MetaDataService. No need provide a source data path.
#         pyMetaDataService.InitializeFake(exe_path, r"W:\sourcedata_nexus")
#         pyMetaDataServiceIsMine = True
#
#     if pyMetaDataService.IsInitialized():
#         uniqueKey = pyMetaDataService.CreateUniqueKey()
#         uniqueID = "0x" + format(uniqueKey, "016X")
#
#         values = [uniqueKey, uniqueID]
#         return values


def generateUniqueID():
   #uniqueKey = pyMetaDataService.CreateUniqueKey()
   uniqueKey = int(CSonarKeyManager.get_key())  # get unique ID and convert to HEX #pyMetaDataService.CreateUniqueKey()
   uniqueID = "0x" + (format(uniqueKey, "016X")).upper()  # convert HEX to string and add the 0x we have on everything

   values = [uniqueKey, uniqueID]
   return values  # uniqueID

#========================================================================


def proxyFromGraphicModel(proxyName, destination, graphicModel):
    # proxyName = name

    proxyPath = destination + "\\" + proxyName + ".proxy.xml"
    metadataPath = proxyPath + ".metadata"

    # proxy already exists use existing ID
    if (os.path.exists(metadataPath) == True):
        metadataFile = openXML(metadataPath)
        objID = metadataFile.find("object").get("id")
        hexID = metadataFile.find("object").get("id_hex")
        print("Proxy already exists, reuse ID"+hexID)

    else:
        IDs = generateUniqueID()
        objID = str(IDs[0])
        hexID = str(IDs[1])
        print("New proxy, creating new ID"+hexID)
        # Log_UUID = str(uuid.uuid4().time_mid)

    graphicModelElement = etree.Element("BatchModel",
                                        fileModel="graphics\model\\" + graphicModel.lower() + ".model",
                                        hid_DTCTH_ClassName="CGraphicBatchModel")
    impl = etree.Element("Impl",
                         vectorScale="1,1,1")

    proxy = etree.Element("ProxyObjectDescriptor")
    metadata = etree.Element("metadata")

    proxyContents = etree.Element("Object",
                                  ProxyObjectType="BatchedObject",
                                  gigGIGroup="4294967295",
                                  ConvertedEntityId="18446744073709551615"
                                  )
    proxyContents.append(graphicModelElement)
    proxyContents.append(impl)

    proxyContentsMetadata = etree.Element("Metadata")
    atlasproperties = etree.Element("AtlasProperties",
                                    bExportToAtlas="0",
                                    atlastypeElementType="")
    minimapProperties = etree.Element("MinimapProperties",
                                      bExport="0")
    tags = etree.Element("tagcategoryselectionblackboardTags")
    tagsArray = etree.Element("TagCategorySelectionArray")
    tagsArraySel = etree.SubElement(tagsArray,
                                    "TagCategorySelection",
                                    hid_DTCTH_ClassName="CTagCategorySingleSelectionWithVisibleTagCategory",
                                    UITagCategorySelectionClassID="CTagCategorySingleSelectionWithVisibleTagCategory",
                                    tagcategoryUITagCategory="9223372052208491228",
                                    tagcategoryTagCategory="9223372052208491228",
                                    tagTag="18446744073709551615"
                                    )

    tagDescriptorUI = etree.Element("TagDescriptorUI",
                                    hid_DTCTH_ClassName="CTagCategorySelectionBlackboardDescriptor")

    tagDescriptorCategory = etree.Element("TagCategorySelectionDescriptors")
    tagDescriptorCatSel = etree.SubElement(tagDescriptorCategory,
                                           "TagCategorySelectionDescriptor",
                                           tagcategoryTagCategory="9223372052208491228",
                                           bMultiSelect="0"
                                           )

    metadataContents = etree.Element("object",
                                     id=objID,
                                     id_hex=hexID.lower())
    # print(hexID)
    metaDataCategory = etree.Element("category", name="ResourceId")
    metaDataCategory.text = hexID

    tagDescriptorUI.append(tagDescriptorCategory)

    tags.append(tagsArray)
    tags.append(tagDescriptorUI)

    minimapProperties.append(tags)

    proxyContentsMetadata.append(atlasproperties)
    proxyContentsMetadata.append(minimapProperties)

    proxy.append(proxyContents)
    proxy.append(proxyContentsMetadata)

    metadataContents.append(metaDataCategory)
    metadata.append(metadataContents)

    # print("proxy path is: " + proxyPath)
    writeXML(proxyPath, proxy)
    writeXML(metadataPath, metadata)
    return 0


def newObjectCategory(objId, catName, catVal):
    object = etree.Element("object", hex_id=str(objId), id=str(objId))
    category = etree.Element("category", name=catName)
    category.text = catVal
    object.append(category)
    return object


def createGraphicModel(mesh, meshPath, template):
    IDs = generateUniqueID()
    objID = IDs[0]
    hexID = IDs[1]

    # graphicModels is the root of all models
    GraphicModels = mesh.find('.//GraphicModels')
    templateUsed = False

    referenceList = mesh.find('.//material_reference_list')
    references = (referenceList.findall('.//material'))

    disSlotNames = []
    templateID = None
    existingOverrides = []

    for reference in references:
        # print(reference.get("slot_name"))
        disSlotNames.append(reference.get("slot_name"))

    for model in GraphicModels:
        # print(model.get("DisplayName"))
        # print(model.get("disSlotName"))
        if (model.get("DisplayName") == template[0]):
            templateUsed = True
            templateID = model.get("UniqueID")
            root = model.getparent()
            root.remove(model)
        elif (model.get("DisplayName") != "Default"):
            existingOverrides.append(model)

    if (templateUsed == True):
        hexID = templateID

    matMaterial = ""
    newGraphicModel = etree.Element("GraphicModel", UniqueID=hexID, DisplayName=str(template[0]), IsEditable="1")

    materialSlot = etree.SubElement(newGraphicModel, "MaterialSlots")
    for disSlotName in disSlotNames:

        for slot in template[1::]:
            if (str(slot[0]) == str(disSlotName)):
                matMaterial = "graphics\_materials\\" + str(slot[1])
                # print("slot is " + slot[0] + " mat is " + slot[1])

        material = etree.Element("Material", disSlotName=disSlotName, matMaterial=matMaterial)

        # attach all elements together
        materialSlot.append(material)

        # attach new override
        GraphicModels.append(newGraphicModel)

        # attach previous overrides
        for model in existingOverrides:
            GraphicModels.append(model)

    print("meshPath is " + meshPath)
    writeXML(meshPath, mesh)

    metadataPath = meshPath + ".metadata"
    metadata = openXML(metadataPath)

    object = newObjectCategory(objID, "GraphicModelIsEditable", "1")
    metadata.append(object)
    writeXML(metadataPath, metadata)
    return str(hexID)


def overrideFile(meshPath, templateArray):
    if os.path.exists(meshPath):
        # p4.edit(meshPath)
        # print("meshPath is" + meshPath)
        mesh = openXML(meshPath)

        for template in templateArray:
            override = createGraphicModel(mesh, meshPath, template)
            if (override != None):
                # print("override is " + override)
                directory = meshPath.replace("graphics", "editor\proxy")
                proxyPath = os.path.dirname(directory)
                object = os.path.basename(meshPath).split(".")
                proxyName = (object[0]) + "_" + str(template[0]).lower()
                # print("Proxy name is " + proxyName)
                proxyFromGraphicModel(proxyName, proxyPath, override)
            else:
                print("Override failed to write, this override name may already exist.")
    else:
        print("The path " + str(meshPath) + " does not exist.")
    return 0


def overrideKit(dirPath, kitString, templateArray):
    filePaths = os.listdir(dirPath)
    kitMatches = []

    for filePath in filePaths:
        if (filePath.find(kitString) != -1):
            kitMatches.append(filePath)
            # print("match " + filePath)

    kitPieces = []

    # print(kitMatches)
    for kitMatch in kitMatches:
        # print("kitmatch "+ kitMatch)

        kit_Extension = os.path.splitext(kitMatch)[1]
        if (kit_Extension == ".gamex"):
            piece = kitMatch.replace("gamex", "xml")
            kitPieces.append(piece)
        if (kit_Extension == ".glm"):
            piece = kitMatch.replace("glm", "xml")
            kitPieces.append(piece)

    for kitPiece in kitPieces:
        # print("Match!")
        # print(dirPath+kitPiece)
        overrideFile(dirPath + kitPiece, templateArray)

    print("Complete")
    return 0


def main():
    templateArray = []#[o1Slots, o2Slots, o3Slots]
    templateArray.append(o1Slots)
    templateArray.append(o2Slots)
    templateArray.append(o3Slots)

    #templateArray = [a1Slots, a2Slots]
    #print(str(get_unique_nomad_id()))
    #print(str(generateUniqueID()[0]))
    overrideKit(dirPath,
                kitString,
                templateArray)
    # p4 = P4Setup()
    # overrideFile(meshPath)

if __name__ == '__main__':
    main()