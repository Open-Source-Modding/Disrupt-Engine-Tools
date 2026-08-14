# ------LIBRARY------
#ORWELL-263270
import os
import sys
from math import floor

from xml.etree import ElementTree as ET
from collections import OrderedDict

# ------VARIABLE------

rootPath = r"w:\main\data\graphics\geometry\Interior\Assets"

#rootPath = r"w:\main\data\graphics\geometry\Activities\Bareknuckle"
#rootPath = r"w:\main\data\graphics\geometry\exterior\\boroughs\camden"
#rootPath = r"w:\main\data\graphics\geometry\exterior\\boroughs\southwark\incinerator"
#rootPath = r"w:\main\data\graphics\geometry\Interior\Assets\micro_drone"
#rootPath = r"w:\main\data\graphics\geometry\interior\structure\iop\cinema"
#rootPath = r"w:\main\data\graphics\geometry\Interior\structure\\rds_140"
#rootPath = r"w:\main\data\graphics\geometry\interior\structure\\tube\occluders"
#rootPath = r"w:\main\data\graphics\geometry\Landmarks\City_of_London"
#rootPath = r"w:\main\data\graphics\geometry\Landmarks\Hackney"
#rootPath = r"w:\main\data\graphics\geometry\Landmarks\Islington"
#rootPath = r"w:\main\data\graphics\geometry\Landmarks\southwark"
#rootPath = r"w:\main\data\graphics\geometry\Landmarks\tower_hamlets_west"
#rootPath = r"w:\main\data\graphics\geometry\Landmarks\westminster"
#rootPath = r"w:\main\data\graphics\geometry\LKL"

#"w:\main\data\graphics\geometry\\branding\generic\shops"
    #r"w:\main\data\graphics\geometry\Interior\Assets\shops"  #include subfolders (gatherall)
    #r"w:\main\data\graphics\geometry\exterior\generic\commercial\holograms"

dirPath = r"w:\main\data\graphics\geometry\Interior\Assets\Generic\\"

LODrange = [64.0, 256.0, 383.0, 1024.0]
maxDistance = 63.0
lockedFiles = []
overrideFiles = []


#interactiontypes

interactionType = {
    'nogen': 'nogen',
    'nogen_cover': 'nogen_cover',
    'nogen_interaction': 'nogen_interaction',
    'player_only_cover': 'player_only_cover',
    'low_cover': 'low_cover',
    'nogen_interaction_player_only_cover': 'nogen_interaction_player_only_cover'

}


#navmesh surface flags

navMeshSurface = {
    'default': "0",
    'furniture': "1",
    'road': "2"
}

#seethrough flags

seeThrough = {
    'opaque': "0",
    'seeThrough': "1"
}




# -----------------------------FUNCTION------------------------

#def openXML(filePath):
#    parser = etree.XMLParser(remove_blank_text=True)
#    with open(filePath) as fo:
#        content = fo.read()
#        return etree.fromstring(content, parser=parser)


# def writeXML(fileName, xmlContent):
#
#     try:
#         et = etree.ElementTree(xmlContent)
#         et.write(fileName, encoding='utf-8', pretty_print=True)
#
#     except IOError:
#         print "Could not write to file: "+fileName+" , make sure it is checked out from repository"
#         lockedFiles.append(str(fileName) + "\n")
# ========================================================================

def ordered_serialize_xml(write, elem, encoding, qnames, namespaces):
    tag = elem.tag
    text = elem.text
    if tag is ET.Comment:
        write("<!--%s-->" % ET._encode(text, encoding))
    elif tag is ET.ProcessingInstruction:
        write("<?%s?>" % ET._encode(text, encoding))
    else:
        tag = qnames[tag]
        if tag is None:
            if text:
                write(ET._escape_cdata(text, encoding))
            for e in elem:
                ordered_serialize_xml(write, e, encoding, qnames, None)
        else:
            write("<" + tag)
            items = elem.items()
            if items or namespaces:
                if namespaces:
                    for v, k in sorted(namespaces.items(),
                                       key=lambda x: x[1]):  # sort on prefix
                        if k:
                            k = ":" + k
                        write(" xmlns%s=\"%s\"" % (
                            k.encode(encoding),
                            ET._escape_attrib(v, encoding)
                        ))
                for k, v in items:  # lexical order
                    if isinstance(k, ET.QName):
                        k = k.text
                    if isinstance(v, ET.QName):
                        v = qnames[v.text]
                    else:
                        v = ET._escape_attrib(v, encoding)
                    write(" %s=\"%s\"" % (qnames[k], v))
            if text or len(elem):
                write(">")
                if text:
                    write(ET._escape_cdata(text, encoding))
                for e in elem:
                    ordered_serialize_xml(write, e, encoding, qnames, None)
                write("</" + tag + ">")
            else:
                write(" />")
    if elem.tail:
        write(ET._escape_cdata(elem.tail, encoding))


class OrderedXmlTreeBuilder(ET.XMLTreeBuilder):
    def _start_list(self, tag, attrib_in):
        fixname = self._fixname
        tag = fixname(tag)
        attrib = OrderedDict()
        if attrib_in:
            for i in range(0, len(attrib_in), 2):
                attrib[fixname(attrib_in[i])] = self._fixtext(attrib_in[i+1])
        return self._target.start(tag, attrib)


def setInteraction(lodFile, interactionType):
    root = lodFile.getroot()
    interactionTypes = lodFile.find('.//InteractionTypes')

    #get children
    #GenericInteraction

    #< GenericInteraction GenericInteractionName = "" / >
    #		<GenericInteraction GenericInteractionName="nogen" />
    print("set interaction")
    #interactionTypes.set("lod0", str(maxDistance))


def setSeeThrough(lodFile, isSeeThrough):

    root = lodFile.getroot()
    seeThrough = lodFile.find('.//SeeThrough')  #flag whether or not AI see through this asset,
                                                # bIsSeeThrough = 0 means no

    seeThrough.set("SeeThrough", isSeeThrough)



def setNavMesh(lodPath, lodFile, surfaceType):

    navMesh = lodFile.find('.//Navmesh')

    updated = False

    print(lodPath)
    try:
        currentType = navMesh.get("NavmeshSurfaceType")
        print("Attribute does exist")

        print("currentType", currentType)
        print("surfaceType", surfaceType)
        if (currentType != surfaceType):
            print("Attribute does NOT match")
            navMesh.set("NavmeshSurfaceType", surfaceType)
            updated = True
            print(navMesh)
            currentType = navMesh.get("NavmeshSurfaceType")
            print(currentType)

    except AttributeError as e:

        navMeshElement = ET.Element("NavMesh",
                                       NavMeshSurfaceType="1")

        root = lodFile.getroot()
        #root.append(navMeshElement)

        interactionTypes = root.find("InteractionTypes")

        if(interactionTypes != None and interactionTypes != 0):
            index = root.getchildren().index(interactionTypes)
            root.insert(index, navMeshElement)

        else:
            descriptor = root.find("descriptor")
            index = root.getchildren().index(descriptor)

            interactionElement = ET.Element("InteractionTypes")
            #genericInteractionElement = ET.Element("GenericInteraction", GenericInteractionName="0")

            #interactionTypes = interactionElement.append(genericInteractionElement)

            root.insert(index+1, interactionElement)
            root.insert(index+2, navMeshElement)

        #graphicsModels = root.find("GraphicModels")
        #index = root.getchildren().index(graphicsModels)
        #root.insert(index, navMeshElement)


        print("Attribute does NOT exist")
        updated = True

    #< Navmesh NavmeshSurfaceType = "1" / >
    #default = 0
    #furniture = 1
    #road = 2

    if(updated):
        updateFile(lodPath, lodFile)

def updateFile(lodPath, lodFile):
    try:
        command = 'p4 edit "{}"'.format(lodPath)
        result = os.system(command)
        print(result)
        # writeXML(lodPath, lodFile)
        lodFile.write(lodPath)#, pretty_print=True)
    except StandardError as e:
        print"filed locked {} \n".format(lodPath)
        lockedFiles.append(lodPath)

    return 0

def collectLODs(lodFile):

    primitiveLOD = lodFile.find('.//primitivelod')

    override = False
    LODs = []
    for j in range(0, 6):
        currentLOD = "lod" + str(j)
        LODs.append(primitiveLOD.get(currentLOD))

    if primitiveLOD.get("lod_distances_override") == "1":
        override = True

    #print "override is {}\n".format(override)


    #lod_distances_override
    values = [LODs,  primitiveLOD, override]
    return values

def capLODs(lodPath, lodFile, ignoreOverride):
    values = collectLODs(lodFile)
    LODs = values[0]
    primitiveLOD = values[1]
    overrideStatus = values[2]
    updated = False

    oneLOD = True
    LOD1 = float(LODs[1])

    if(LOD1 > 0.0):
        print(LODs[1])
        oneLOD = False

    if(ignoreOverride or (overrideStatus == False)):

        if (oneLOD == True):
            if( float(LODs[0]) > float(maxDistance)):
                primitiveLOD.set("lod0", str(maxDistance))
                print("updating "+lodPath+" lod0 from "+str(LODs[0])+" to "+str(maxDistance))
                updated = True

        # if only LOD0 has a value
        # cap it to maxDistance

        else:
            print("There is more than one LOD")

            LODCounter = 0
            overMaxCounter = 0

            #get total LODs
            #get number of LODs over max distance
            for LOD in LODs:
                print LOD
                if (float(LOD) > 0.0):
                    LODCounter += 1
                    #print("LOD is "+str(LOD)+"\n")
                    #print("LOD is not 0\n")

                    if(float(LOD) >= float(maxDistance)):
                        overMaxCounter += 1

            print("LODCounter is "+str(LODCounter)+"\n")

            if(overMaxCounter > 0):

                #set highest LOD to max Distance
                currentLOD = "lod" + str(LODCounter-1)
                primitiveLOD.set(currentLOD, str(maxDistance))


                if(overMaxCounter > 1):
                    firstOverLOD = (LODCounter - overMaxCounter)

                    if firstOverLOD > 0:
                        lastGoodValue = float(primitiveLOD.get("lod"+str(firstOverLOD - 1)))
                    else:
                        lastGoodValue = 0.0

                    LODValueInc = floor((maxDistance - lastGoodValue) / (LODCounter - firstOverLOD))

                    print("firstOverLOD "+str(firstOverLOD)+"\n")
                    print("lastGoodValue "+str(lastGoodValue)+"\n")
                    print("LODCounter "+str(LODCounter)+"\n")
                    print("LODValueInc "+str(LODValueInc)+"(maxDistance - lastGoodValue) / (LODCounter - firstOverLOD)\n")

                    incCount = 1

                    for j in range(firstOverLOD, LODCounter-1):
                        currentLOD = "lod" + str(j)
                        primitiveLOD.set(currentLOD, str(lastGoodValue+(LODValueInc*incCount)))
                        incCount += 1

                updated = True



        if (updated):
            # lod_distances_override, 1 = true
            primitiveLOD.set("lod_distances_override", "1")
            updateFile(lodPath, lodFile)

def compareLODs(lodPath, lodFile, ignoreOverride):

    values = collectLODs(lodFile)
    LODs = values[0]
    primitiveLOD = values[1]
    newLODs = []
    overrideStatus = values[2]
    updated = False


    if(ignoreOverride or overrideStatus == False):
        # print(LODs)
        for LOD in LODs:
            for j in LODrange:
                if LOD == None:
                    return
                elif float(LOD) > j and float(LOD) < (j * 1.25):
                    print("LOD is " + LOD)
                    LOD = float(j - 1.0)
                    updated = True
                    print("LOD has been set to " + str(LOD))
                # else:
                # print("LOD is good.")

            newLODs.append(str(LOD))

        for j in range(0, 6):
            currentLOD = "lod" + str(j)
            primitiveLOD.set(currentLOD, newLODs[j])
            # print(primitiveLOD.get(currentLOD))

        if (updated):
            # lod_distances_override, 1 = true
            primitiveLOD.set("lod_distances_override", "1")
            updateFile(lodPath, lodFile)
    else:
        print("LODs were overriden, skipping file")


def writeLog(logPath, logData):
    logText = ""
    for data in logData:
        logText += data

    logFile = open(logPath, 'w')
    logFile.write(logText)

def checkOutFile(filePath):
    print("checkoutFile")

def setLODs(lodPath, lodFile, ignoreOverride):
    compareLODs(lodPath, lodFile, ignoreOverride)
    capLODs(lodPath, lodFile, ignoreOverride)

def gatherXML(adjustmentFunc, dirPath, *adjustmentValue):
    #*because we dont know how many arguments will be received

    print("We are in " + str(dirPath))

    if (os.path.exists(dirPath)):
        filePaths = os.listdir(dirPath)
        dirFiles = []

        for filePath in filePaths:
            dirFiles.append(filePath)
            # print("match " + filePath)

        modelFiles = []

        # print(dirFiles)
        for curFile in dirFiles:
            # print("curFile "+ curFile)

            modelExt = os.path.splitext(curFile)[1]
            if (modelExt == ".gamex"):
                piece = curFile.replace("gamex", "xml")
                modelFiles.append(piece)
            if (modelExt == ".glm"):
                piece = curFile.replace("glm", "xml")
                modelFiles.append(piece)

        for model in modelFiles:
            # print("Match!")
            print("\n"+dirPath+model)

            lodPath = os.path.join(dirPath, model)

            if os.path.exists(lodPath):
                lodFile = ET.parse(lodPath, OrderedXmlTreeBuilder())
                root = lodFile.getroot()
                adjustmentFunc(lodPath, lodFile, *adjustmentValue)

            else:
                print("File % does not exist", lodPath)
        print("Complete")

        # writeLog(r"w:\logs\log.txt", lockedFiles)
    else:
        print("Directory " + str(dirPath) + " does not exist.")


    return 0


def gatherAllXML(adjustmentFunc, rootDir, *adjustmentValue):
    subDirs = []
    # exclude = set(['Activities', 'AR', 'building_kit', 'building_kit_hard_mesh', 'building_kit_interior', 'decals', 'gfx', 'lofts', 'npc_interior', 'oob', 'Ops', 'poi', 'Vegetation'])

    # for subDir, dir, files in os.walk(rootDir):
    for subDir, dir, files in os.walk(rootDir, topdown=True):
        # subDir[:] = [d for d in subDir if d not in exclude]
        print(subDir + "\n")
        subDirs.append(str(subDir) + "\\")

    for dir in subDirs:
        gatherXML(adjustmentFunc, dir, *adjustmentValue)

    writeLog(r"w:\logs\lockedFiles.txt", lockedFiles)
    writeLog(r"w:\logs\overridenFiles.txt", overrideFiles)


def main():
    ET._serialize_xml = ordered_serialize_xml

    #gatherXML(setNavMesh, dirPath, navMeshSurface['furniture'])
    gatherAllXML(setNavMesh, rootPath, navMeshSurface['furniture'])

    #gatherAllXML(capLODs, rootPath, True) #capLODs from rootPath, edit even if override is true
    #gatherXML(setLODs, rootPath, False)
    #gatherAllXML(setLODs, rootPath, False)
    #gatherAllXML(setNavMesh, rootPath, navMeshSurface['furniture'])
    testPath = r"w:\main\data\graphics\geometry\exterior\Generic\Commercial\holograms\hologram_hydrangea_kit_med_01.xml"
    #setNavMesh(testPath, navMeshSurface['furniture'])

if __name__ == '__main__':
    main()