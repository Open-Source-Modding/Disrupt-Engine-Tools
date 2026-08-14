import xml.etree.cElementTree as ET
import sys, os, csv, time, ConfigParser
from ULib import UPerforce


'''Set some path contstants'''
BLENDTREE_PATH = r'w:\main\data\move\blendtrees'
DECISION_TREE_PATH = r'W:\Main\data\move\DecisionTrees'  #r'W:\main\data\move\DecisionTrees\civilians\locomotion' #r'w:\main\data\move\DecisionTrees'
MARKUP_PATH = r'W:\Main\data\animations\civilians\idles'

#Civ_Paths = [r'W:\Main\data\move\DecisionTrees\civilians\Reactions']
Civ_Paths = [r'W:\Main\data\move\DecisionTrees\civilians\locomotion', r'W:\Main\data\move\DecisionTrees\civilians\Reactions', r'W:\Main\data\move\DecisionTrees\Common\Reactions', r'W:\Main\data\move\DecisionTrees\Common\behavior']


'''Get Perforce info from an ini file'''
config = ConfigParser.ConfigParser()
config.read(r"C:\Users\sdiehl\Desktop\p4config.ini")
P4_SERVER = config.get('Perforce', 'P4_SERVER')
P4_PATH = config.get('Perforce', 'P4_PATH')
P4_CLIENT = config.get('Perforce', 'P4_CLIENT')
P4_USER = config.get('Perforce', 'P4_USER')


def get_files(pFilePath, pExtension, pLower = False):
    if os.path.exists(pFilePath):
        # Look for all markups in the IOP directory
        for path, subdirs, files in os.walk(pFilePath):
            for name in files:
                if name.endswith(pExtension):
                    sFullName = os.path.join(path, name)
                    if pLower:
                        sFullName = sFullName.lower()
                    yield sFullName


########################################################################################################################

def get_blendtree_list(path):
    lBlendTrees = []
    for blendTree in get_files(path, "move.xml", pLower=True):
        lBlendTrees.append(blendTree)
    return lBlendTrees

########################################################################################################################

def get_movestate_list(path):
    '''
    Get a list of all the movestates the live under DECISION_TREE_PATH folder
    :rtype: list
    '''
    lMoveStates = []

    for moveState in get_files(path, "move.xml"):
        lMoveStates.append(moveState)
    return lMoveStates

# civ_states_list = []
# for path in Civ_Paths:
#     for moveState in get_movestate_list(path):
#         civ_states_list.append(moveState)

########################################################################################################################

def find_staterefs():
    lStateRefs = []
    for moveState in get_movestate_list(DECISION_TREE_PATH):
        oDocTree = ET.parse(moveState)
        oRoot = oDocTree.getroot()

        for child in oRoot.findall(".//ChildNode[@hid_DTCTH_ClassName='CMoveStateRef']"):
            lStateRefs.append(child.find("MoveStateParam").attrib['MoveStateID'])

    for i in (set(lStateRefs)):
        print i
    print len(set(lStateRefs))

#find_staterefs()
lMoveStates = get_movestate_list(DECISION_TREE_PATH)

def find_lookats(lMoveStates):
    lLookAts = []
    count = 0
    for moveState in lMoveStates:
        oDocTree = ET.parse(moveState)
        oRoot = oDocTree.getroot()

        for multiBlend in oRoot.findall(".//ChildNode[@hid_DTCTH_ClassName='CMoveMultiBlendRef'].//ChildNode"):
            if "lookat" in multiBlend.attrib['LocalName']:
                try:
                    lLookAts.append(multiBlend.attrib['LocalName'])
                except KeyError:
                    pass

    for i in list(set(lLookAts)):
        print i
    print len(list(set(lLookAts)))

#find_lookats(lMoveStates)


########################################################################################################################

def search_blendtree_params(lBlendTrees):
    count = 0

    with open(r"C:\Users\sdiehl\Desktop\blendperbone_results.txt", "w") as f:
        for blendTree in lBlendTrees:
            oDocTree = ET.parse(blendTree)
            oRoot = oDocTree.getroot()

            for child in oRoot.findall(".//BlendAdjustParam"):
                if child.attrib["BlendAdjustPerBone"] == "1":
                    print blendTree
                    f.write(blendTree + "\n")
                    count += 1

        print count

search_blendtree_params(get_blendtree_list(BLENDTREE_PATH))


########################################################################################################################

def find_gender_branch_refs(lMoveStates):
    gender_branches = {"Female":None, "Male":None}
    count = 0
    maleResults = []
    for moveState in lMoveStates:
        oDocTree = ET.parse(moveState)
        oRoot = oDocTree.getroot()

        for moveBlend in oRoot.findall("*//MoveBlendParam[@MoveBlendID]"):
            if not "fcivi" in moveBlend.attrib['MoveBlendID']:
                if not "fciv" in moveBlend.attrib['MoveBlendID']:
                    if not "female" in moveBlend.attrib['MoveBlendID']:
                        if not "hciv" in moveBlend.attrib['MoveBlendID']:
                            maleResults.append(moveBlend.attrib['MoveBlendID'])
                            count += 1
                            gender_branches["Female"] = count

    print "male done"
    print len(list(set(maleResults)))
    print ""

    femResults = []
    for moveState in lMoveStates:
        oDocTree = ET.parse(moveState)
        oRoot = oDocTree.getroot()

        for moveBlend in oRoot.findall("*//MoveBlendParam[@MoveBlendID]"):
            if not moveBlend.attrib['MoveBlendID'] in list(set(maleResults)):
                femResults.append(moveBlend.attrib['MoveBlendID'])

    print "female done"
    print len(list(set(femResults)))


#find_gender_branch_refs(lMoveStates)

########################################################################################################################

def find_blendrefs_in_branch(lMoveStates):
    BlendRef_Instances = 0
    with open(r'C:\Users\sdiehl\Documents\Scripts\civ_states.csv', "wb") as csv_file:
        for moveState in lMoveStates:
            oDocTree = ET.parse(moveState)
            oRoot = oDocTree.getroot()

            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow([moveState.split('\\')[-1].replace(".move.xml", "").upper()])

            for childNode in oRoot.findall(".//ChildNode[@hid_DTCTH_ClassName='CMoveBlendRef']/../..[@hid_DTCTH_ClassName='CMoveBranch']"):
                singleAnim = childNode.find("Children/ChildNode[@hid_DTCTH_ClassName='CMoveBlendRef']")
                if singleAnim.attrib["LocalName"] != "axb_driving-reaction-suprise":
                    writer.writerow([singleAnim.attrib["LocalName"]])
                    #print childNode.find("Children/ChildNode[@hid_DTCTH_ClassName='CMoveBlendRef']").attrib["LocalName"]
                    BlendRef_Instances += 1

            for childNode in oRoot.findall(".//ChildNode[@hid_DTCTH_ClassName='CMoveMultiBlendRef']/../..[@hid_DTCTH_ClassName='CMoveBranch']"):
                multiBlendRef = childNode.find("Children/ChildNode[@hid_DTCTH_ClassName='CMoveMultiBlendRef']")
                moveBlend = multiBlendRef.find("Children/ChildNode[@hid_DTCTH_ClassName='CMoveBlendRef']")
                BlendRef_Instances += 1
                if moveBlend:
                    writer.writerow([multiBlendRef.attrib["LocalName"] + " ({})".format(moveBlend.attrib["LocalName"])])
                    # print multiBlendRef.attrib["LocalName"]
                    # print "\t" + moveBlend.attrib["LocalName"]
            writer.writerow([" "])

        writer.writerow(["Total Count: " + str(BlendRef_Instances)])

########################################################################################################################

def find_PMS_refs(lMoveStates, sName):
    '''
    Search through a list of MoveStates and print ComparisonOpe's decision tree path
    '''
    for moveState in lMoveStates:
        oDocTree = ET.parse(moveState)
        oRoot = oDocTree.getroot()

        for item in oRoot.findall(".//PMSValueParam[@PMSValue='%s']...." % (sName)):
            print item.attrib["NodeID"]
#find_PMS_refs(get_movestate_list(), "ArchetypeStyleNav")

########################################################################################################################

def get_prop_movestates():
    '''
    Get a dict of ever prop layer, and the move states that are using them
    :return:
    '''

    dPropLayers = {}

    for MoveState in get_files(DECISION_TREE_PATH, "xml"):
        if os.path.exists(MoveState):
            oDocTree = ET.parse(MoveState)
            oRoot = oDocTree.getroot()

            for item in oRoot.findall('.//ChildNode[@LocalName]'):
                propLayerName = item.attrib['LocalName']

                if propLayerName.startswith('proplayer'):
                    if not propLayerName in dPropLayers:
                        dPropLayers[propLayerName] = [MoveState]
                    else:
                        if not MoveState in dPropLayers[propLayerName]:
                            dPropLayers[propLayerName].append(MoveState)

    path = r'E:\_ORWELL\PropLayer_MoveStates.csv'
    with open(path, "wb") as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(['Prop Layer', 'Count', 'Move States'])

        for k, v in sorted(dPropLayers.iteritems()):
            writer.writerow([k, len(v), v])

    return dPropLayers


def get_movestate_proplayers(ignoreDuplicates=True, createCSV=False, replaceProplayer=False):
    '''
    Get a dictionary of move states and the prop layers within them

    :param ignoreDuplicates: Only list a proplayer once per move state
    :param createCSV: export data to csv file
    :param replaceProplayer: replace all found prop layers with PropLayer_Generic, checking out all
                             relevant movestates
    '''

    dMoveStates = {}
    moveStatesToEdit = []

    for MoveState in get_files(DECISION_TREE_PATH, "xml"):

        if os.path.exists(MoveState):
            oDocTree = ET.parse(MoveState)
            oRoot = oDocTree.getroot()

            for item in oRoot.findall('.//ChildNode'):
                # Find LocalName attribute in the xml
                propLayerName = item.attrib['LocalName']

                # Make sure it's a prop layer
                if 'proplayer' in propLayerName:

                    # Add the current move state to our dictionary as a key,
                    # and for the value, add the prop layer to a list of other prop layers
                    # being used by the same move state
                    if not MoveState in dMoveStates:
                        dMoveStates[MoveState] = [propLayerName]

                    else:

                        if ignoreDuplicates:
                            # Only add the proplayer if it's not already in the list
                            # for the current move state
                            if not propLayerName in dMoveStates[MoveState]:
                                dMoveStates[MoveState].append(propLayerName)
                        else:
                            dMoveStates[MoveState].append(propLayerName)

                    if replaceProplayer:
                        # Replace all of the found prop layers with 'proplayer_generic'
                        if not propLayerName.startswith('proplayer_generic'):
                            splitLayer = propLayerName.split("_")

                            nodeID = os.path.split(item.attrib['NodeID'])[0]
                            blendID = item.find('MoveBlendParam')
                            blendPath = os.path.split(blendID.attrib['MoveBlendID'])[0]


                            if 'female' in splitLayer[-1]:
                                if splitLayer[-2] == 'rhand':
                                    item.set('LocalName', 'proplayer_generic_rhand')
                                    item.set('NodeID', (nodeID + r'\proplayer_generic_rhand'))
                                    blendID.set('MoveBlendID', (blendPath + r'\proplayer_generic_rhand.move.bin'))
                                else:
                                    item.set('LocalName', 'proplayer_generic_lhand')
                                    item.set('NodeID', (nodeID + r'\proplayer_generic_lhand'))
                                    blendID.set('MoveBlendID', (blendPath + r'\proplayer_generic_lhand.move.bin'))
                            else:
                                if splitLayer[-1] == 'rhand':
                                    item.set('LocalName', 'proplayer_generic_rhand')
                                    item.set('NodeID', (nodeID + r'\proplayer_generic_rhand'))
                                    blendID.set('MoveBlendID', (blendPath + r'\proplayer_generic_rhand.move.bin'))
                                else:
                                    item.set('LocalName', 'proplayer_generic_lhand')
                                    item.set('NodeID', (nodeID + r'\proplayer_generic_lhand'))
                                    blendID.set('MoveBlendID', (blendPath + r'\proplayer_generic_lhand.move.bin'))

                        if not MoveState in moveStatesToEdit:
                            moveStatesToEdit.append(MoveState)

        if replaceProplayer and (MoveState in moveStatesToEdit):
            try:
                # Check out the move state xml and write the changes
                p4_checkout_files([MoveState], False)
                print ('EDITING: ' + MoveState)
                oDocTree.write(MoveState)
            except:
                raise

    if createCSV:
        # export data to external file
        path = r'E:\_ORWELL\MoveState_PropLayers.csv'
        with open(path, "wb") as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(['Move State', 'Count', 'Prop Layers Used'])

            for k, v in sorted(dMoveStates.iteritems()):
                writer.writerow([k, len(v), v])

    return dMoveStates


def get_proplayer_markup(pPropLayerPath):
    '''
    Get a list of all of the markup files used within the given blend ref, which you could then check out
    with p4_checkout_files
    '''

    animList = []
    if os.path.exists(pPropLayerPath):
        oDocTree = ET.parse(pPropLayerPath)
        oRoot = oDocTree.getroot()

        for item in oRoot.findall('.//AnimParam'):
            # replace .mac with .markup, and switch all backslashes to forward slashes
            # switched slashes for perforce path
            animMarkupFile = (os.path.splitext(item.attrib['AnimID'])[0]+'.markup').replace('\\', '/')
            animList.append(animMarkupFile)

    return animList


def get_stims():
    
    stimList=[]
    databasePath=r'W:\main\data\Databases\Generic\stims.xml'
    if os.path.exists(databasePath):
        oDocTree = ET.parse(databasePath)
        oRoot = oDocTree.getroot()

        for item in oRoot.findall('.//Generic'):
            if "ReactionStim" in item.attrib['Name']:
                stim = item.attrib['Name'].split('.')[1:]

                if not stim[0] in stimList:
                    stimList.append(stim[0])

    return stimList


def p4_checkout_files(pFileList, addP4Path=True):
    try:
        pf = UPerforce.UPerforce(sServer=P4_SERVER, sUser=P4_USER, sClient=P4_CLIENT)
    except:
        print "Cannot connect to Perforce"
        #raise

    for item in pFileList:
        if addP4Path:
            # This is needed for when we have a list of mac or markup files, since their path will be
            # 'animations\blah\blahblah\', and we need the FULL path
            item = (P4_PATH + item)
        if pf.IsFileOnPerforce(item):
            try:
                pf.Update(item)
                if not pf.Checkout(item, bAllowMultiUserCheckOuts=False):
                    print ("Unable to check out: " + item)
                # return pf.GetDiscPath(item)
            except:
                #raise
                print 'Error checking out file from Perforce'
                return False
        else:
            print ('File not found on Perforce: ' + item)
            return False


def showData(data, lvl=0):

    if type(data) == dict:
        for k,v in sorted(data.iteritems()):
            if hasattr(v, '__iter__'):
                print k
                showData(v)
            else:
                print '%s : %s' % (k,v)
            print '\n'


    elif type(data) == list:
        for v in data:
            if hasattr(v, '__iter__'):
                showData(v)
            else:
                print v
    else:
        print data


# Find and replace Prop Markups
lPropIDs_Old = ["9223372080840946963",
                "9223372048344620520",
                "9223372048779324467",
                "9223372048779324468",
                "9223372048779324469",
                "9223372048779324470",
                "9223372048779324471",
                "9223372048779324473"]
def replace_prop_markup(lPropIDs_Old, propID_New):

    for markupFile in get_files(MARKUP_PATH, "markup", pLower=True):
        if os.path.exists(markupFile):
            oDocTree = ET.parse(markupFile)
            oRoot = oDocTree.getroot()

            for item in oRoot.findall('.//CPawnPropEvent[@propPropDbName]'):
                currentPropID = item.attrib['propPropDbName']

                if "talking" in markupFile:
                    propID_New = "9223372048779324469"
                elif "texting" in markupFile:
                    propID_New = "9223372048779324471"
                else:
                    propID_New = "9223372080002080304"


                if currentPropID in lPropIDs_Old:
                    print "Editing file: " + markupFile
                    p4_checkout_files([markupFile], False)
                    print "Before: " + item.attrib['propPropDbName']
                    item.attrib['propPropDbName'] = propID_New
                    print "After: " + item.attrib['propPropDbName']
                    try:
                        oDocTree.write(markupFile)
                    except IOError:
                        f = open('failed_files_report.txt', 'a')
                        f.write(markupFile + '\n')
                        f.close()
                        print "Permission denied on file: " + markupFile


def find_cellphone_prop_anims():

    for markupFile in get_files(MARKUP_PATH, "markup", pLower=True):
        if os.path.exists(markupFile):
            oDocTree = ET.parse(markupFile)
            oRoot = oDocTree.getroot()





start_time = time.time()

# region Run commands
# === Get all prop layers and the move states that use them ==
# data = get_prop_movestates()
# showData(data)
#
#replace_prop_markup("9223372080002080304", "9223372082273689074")

# === Check out all markup associated with prop layer ========

# animList = get_proplayer_markup(r'W:\main\data\move\blendtrees\Civilians\layeredprops\PropLayer_Curious_LHand_Female.move.xml')
# p4_checkout_files(animList)

# ============================================================
#
#
# # ==== Replace all prop layers with PropLayer_Generic =======
# data = get_movestate_proplayers(ignoreDuplicates=False, replaceProplayer=True, createCSV=False)
#
#
# # === Print list of stims from database ======================
# data = get_stims()
# showData(data)

# # ==== Find and replace PawnPropEvent prop markups ===========
# replace_prop_markup(["9223372082273689074"],"9223372048344620520")
# endregion

#print ('Search completed successfully in %s seconds' % (time.time() - start_time))