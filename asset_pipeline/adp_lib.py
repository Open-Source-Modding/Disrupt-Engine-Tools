try:
    import Pillow
except ImportError:
    pass
from PIL import Image
from os.path import splitext, basename, join, split, isfile, getsize, getctime
import xml.etree.cElementTree as ET
# import xml.etree.ElementTree as ET
import sys
import os
import math
import uuid
from PySide import QtGui
from shapely.geometry import Polygon, Point
from collections import OrderedDict
from scipy.spatial import distance
import sqlite3
import cPickle

DIR_WALK_FN = os.walk
try:
    import scandir
    DIR_WALK_FN = scandir.walk
except ImportError:
    pass

def _get_files_iter(path, filter_extensions, b_subfolder=True):
    if isinstance(filter_extensions, basestring):
        #logger.warn("code migration: filter_extensions expects a list, not a string.")
        filter_extensions = [filter_extensions]

    for root, dirs, files in DIR_WALK_FN(path):
        for _file in files:
                #filter_extensions = tuple(filter_extensions)
            if _file.endswith(tuple(filter_extensions)):
                yield os.path.join(root, _file).lower()
        if not b_subfolder:
            break #Do not explore subfolders

def get_files(path, filter_extensions, filter, b_subfolder=True):
    """
    :param path: the directory to search
    :param filter_extensions: file extensions to filter when returning
    :param filter: deprecated, do not use!
    :param b_subfolder: recursive search flag
    :return: list of filtered filepaths
    """
    # ret = list(_get_files_iter(path, filter_extensions, b_subfolder=True))
    ret = set(_get_files_iter(path, filter_extensions, b_subfolder=True))
    return ret

def convert_to_path_type(path, type):
    path = path.replace("wd1\\", "")
    path = path.replace("wd2-temp\\", "")
    # path variables
    p4_base_path = r"//wd3-prod"
    p4_data_source_base_path = r"//wd3-data-source"
    data_path = r"\main\data"
    source_data_path = r"/sourcedata_nexus"
    drive = r"w:"

    # clean present path (makes it a relative path)
    path = path.lower()
    path = path.replace(p4_base_path, "")
    path = path.replace(p4_data_source_base_path, "")
    path = path.replace(source_data_path, "")
    path = os.path.normpath(path)
    # path = path.replace(u"file:\\", "")
    path = path.replace(data_path, "")
    path = path.replace(drive, "")
    first_character = path[0]

    if first_character == "\\":
        path = path[1:len(path)]

    if type == 1:  # absolute
        path = os.path.join(drive, data_path, path)
        return path

    if type == 2:  # relative, no need to do anything else
        return path

    if type == 3:  # p4 data
        path = os.path.join(data_path, path)
        path = p4_base_path + path
        path = path.replace("\\", "/")
        return path

    if type == 4:  # sourcedata
        path = os.path.join(drive, source_data_path, path)
        return path

    if type == 5:  # p4 sourcedata
        path = os.path.join(source_data_path, path)
        path = p4_data_source_base_path + path
        path = path.replace("\\", "/")
        return path

def import_gamex(project_root):
    '''
    This function tries to import the GamEx lib by searching for data.py in the project's root.
    This is necessary since users can have that file from different sources (EPA, code branch...).
    If multiple files are found, it will select the most recent one and import that lib.
    '''
    try:
        files = get_files(project_root, ".py", "")
        data_py_files_set = set()
        for file in files:
            if "\\gx\\data.py" in file:
                data_py_files_set.add(file)            
        latest_file = max(data_py_files_set, key=getctime)    
        trim_path = latest_file.replace("\\gx\\data.py","")
        sys.path.append(trim_path)
        import gx.data
        return gx
    except:
        return False

def get_cloID(element):
    cloID = None
    sub_elem = element.find("ActionSettings")
    if sub_elem is not None:
        # The ID is found under one of these three: cloactAction, cloanimalactAction, clorobotactAction.
        cloID = sub_elem.get("cloactAction", cloID)
        cloID = sub_elem.get("cloanimalactAction", cloID)
        cloID = sub_elem.get("clorobotactAction", cloID)
        if cloID is None:
            # If still not found, it can be in one of these two: cloactlistActionList, cloanimalactlistActionList
            cloID = sub_elem.get("cloactlistActionList", cloID)
            cloID = sub_elem.get("cloanimalactlistActionList", cloID)
            
    return cloID

def get_building_properties(new_entity, elem):    
    for building_elem in elem.iter("Building"):
        if building_elem.get("transform") is not None:
            continue
        bool_lod = building_elem.get("bGenerateLowLevelOfDetail")
        if bool_lod == "0":
            new_entity.building_generatelowlod = False
        #NEAR 3 - FAR 2 - FARAWAY 1 >>
        wlu_case_type = "FarAway" #Default
        bool_WLU = building_elem.get('selWluCategory')
        
        if bool_WLU == "2": 
            wlu_case_type = "Far"
        if bool_WLU == "3" : 
            wlu_case_type = "Near"
        
        #Assign current WLU >>
        new_entity.building_current_WLU = wlu_case_type 
            
    for wall_elem in elem.iter("Wall"):
        for floor_elem in wall_elem.iter("Floor"):
            for element_elem in floor_elem.iter("Element"): #Facades >>
                if int(element_elem.get("bHide")):
                    continue

                for socket_elem in element_elem.iter("EditorObjectSocketInstance"):
                    collection_item_id = socket_elem.get("CollectionItemUniqueID", "")
                    new_entity.add_dependency(collection_item_id)

                prefab_guid = element_elem.get("prefabGuid", "").lower()
                new_entity.add_dependency(prefab_guid)
                if element_elem.get("hidHeight"):                                
                    facade_width  = float(element_elem.get("hidWidth"))
                    facade_height = float(element_elem.get("hidHeight"))
                new_entity.building_surface_area += facade_width * facade_height
                new_entity.building_facade_count += 1               
        
    for wall_elem in elem.iter("Floors"):            
        wall_height = 0                            
        for floor_elem in wall_elem.iter("Floor"):                
            for element_elem in floor_elem.iter("Element"):
                if element_elem.get("hidHeight"):                    
                    wall_height += float(element_elem.get("hidHeight"))                        
                    break
        if wall_height >= new_entity.building_height:
            new_entity.building_height = wall_height 

    floor_count = 0
    for i in elem.iter("Floors"):
        floor_count = sum(1 for _ in i.iter("Floor")) # >> Lazy sum
        break
    new_entity.building_floor_count = floor_count                
                        
    for roof_elem in elem.iter("Roof"):
        if roof_elem.get("bGenerate") == "1":
            new_entity.building_roof_material = roof_elem.get("selMaterialBank").lower()
    if new_entity.building_facade_count is not 0:
        new_entity.building_facade_ratio = (new_entity.building_facade_count / new_entity.building_surface_area) * 1000
    else:        
        print "**Corrupted Building** This should not happen: building facade count was 0, please check this building and fix it : " + new_entity.guid
    vertex_list = []
    for sub_corners in elem.iter("Corners"):
        for elem_corner in sub_corners.iter("Corner"):
            values = elem_corner.get("vecCornerPos", "")
            float_values_list = [float(val) for val in values.split(",")]
            vertex_list.append(float_values_list)
    if len(vertex_list) < 3:
        #print elem.get("Id") + " on " + world_layer_file + " is a building with less than 3 corners. DELETE IT!"
        pass
    else:        
        polygon = Polygon(vertex_list)
        new_entity.shape_area = polygon.area                    

        corners_count = len(vertex_list)                    
        edges_distance = []
        for i in range(corners_count):
            if i + 1 < corners_count:
                pointA = Point(vertex_list[i])
                pointB = Point(vertex_list[i+1])
                edges_distance.append(pointA.distance(pointB))
        edges_distance.append(Point(vertex_list[0]).distance(Point(vertex_list[corners_count-1]))) #Manually this one <<
        
        new_entity.building_edges_distance = edges_distance
        #Volume >>
        new_entity.building_volume = new_entity.shape_area * new_entity.building_height
        #Radius
        new_entity.building_radius = distance.euclidean([polygon.centroid.x, polygon.centroid.y, new_entity.building_height/2],[vertex_list[0]])
        #Ideal kill distance >>
        kill_distance = 1        
        project_plane_d = 1.0/0.77 # assume a 75deg fov: tan(75.0/2) Pixels: 16px HardCoded by default **   
        if new_entity.building_radius > 0:
            kill_distance = project_plane_d / (((math.sqrt(((32 * 2) ** 2) / 3.1416)) / 1600) / new_entity.building_radius) 
        #kill Distance falls closely into categories, we apply uncertainty >>
        if kill_distance >= 150 and kill_distance < 150*1.25:
            kill_distance = 149
        if kill_distance >= 256 and kill_distance < 256*1.25:
            kill_distance = 255
        if kill_distance >= 1024 and kill_distance < 1024*1.25:
            kill_distance = 1023 
        new_entity.building_ideal_killdistance = kill_distance
        wlu_case_type = "FarAway" #Default wlu
        
        if kill_distance < 256 :
            wlu_case_type = "Near"
        if kill_distance > 256 and kill_distance < 1024:
            wlu_case_type = "Far"

        new_entity.building_ideal_WLU = wlu_case_type


class d_object(object):                
    EXTENSIONS_DICT = {
                    # All extensions that can be referenced files, associated with the extention that will be used in the identifier. Some of them are the same, some are not.
                    ".xml"   : ".xml",
                    ".glm"   : ".xml",
                    ".lft"   : ".xml",
                    ".xlf"   : ".xml",
                    ".gamex" : ".xml",
                    ".rta"   : ".rta",
                    ".xbg"   : ".xml",
                    ".model" : ".model",
                    ".hkr"   : ".xml",
                    ".hkx"   : ".xml",
                    ".psd"   : ".psd",
                    ".png"   : ".png",
                    ".xbt"   : ".png",
                    ".dds"   : ".png",
                    ".fla"   : ".fla",
                    ".feu"   : ".feu",
                    ".lua"   : ".lua",
                    ".domino": ".domino",
                    ".bik"   : ".bik",
                    ".dat"   : ".dat",
                    ".bin"   : ".xml",
                }

    DEPENDENCY_ATTRIBUTES_SET = set([
                                    # All known attributes that can hold references.
                                    "filemodeldefault",                            
                                    "fileloftshape",
                                    "cloactaction",
                                    "cloanimalactaction",
                                    "fileproxyobject",
                                    "rangedefrangedefinition",
                                    "hidoriginalmaterial",
                                    "roadmatbankroadmaterialbank",
                                    "splineloftloftelement",
                                    "matcornermaterial",
                                    "matoverridematerial",
                                    "matroadmaterial",
                                    "filebink",
                                    "filevideopath",
                                    "filebinkfilepath",
                                    "archarchetype",
                                    "filedistantlightstexture",
                                    "filecolorremapvolumetexture",
                                    "filesplashestexture",
                                    "fileraindroptexture",
                                    "filerainstreaktexture",
                                    "filerainflowtexture",
                                    "filerainheightnoisetexture",
                                    "filefoamtexture",
                                    "filescatteringtexture",
                                    "filecaustictexture",
                                    "filewaveintensitytexture",
                                    "filewaterdetailnormalmap",
                                    "filesunflaretexture",
                                    "filesunflaretimeofdaycolortexture",
                                    "filemoontexture",
                                    "filelightpollutiontexture",
                                    "filefog2dnoisetexture",
                                    "filefog3dnoisetexture",
                                    "filewindglobalnoisetexture",
                                    "filewhitevolume",
                                    "filebandlimitednoise",
                                    "filelut",
                                    "filebasewavetexture",
                                    "mathighlightmaterial",
                                    "psattachparticles",
                                    "psdetachparticles",
                                    "model",
                                    "dissequence",
                                    "hidarchetypename",
                                    "archdronearchetype",
                                    "droneconfigdroneconfig",
                                    "filetexture",
                                    
                                    # references for particle systems:
                                    "psarcfx",
                                    "psarmedparticlefxally",
                                    "psarmedparticlefxenemy",
                                    "psarmedparticlefxnormal",
                                    "psattachparticles",
                                    "psattractfx",
                                    "psbackweaponfx",
                                    "psbasesparkfx",
                                    "psbodybulletimpactparticleid",
                                    "psbollardtakedownfx",
                                    "psbuildupparticles",
                                    "psbulletcaseparticleid",
                                    "psburnparticle",
                                    "pscollisionparticles",
                                    "psdamagedparticlefx",
                                    "psdamagedsparkparticlefx",
                                    "psdamageparticles",
                                    "psdefaulteffectparticles",
                                    "psdestroybyexplosionfx",
                                    "psdestroybyexplosionnohoodfx",
                                    "psdestroyedfx",
                                    "psdestroyedparticles",
                                    "psdestroyparticle",
                                    "psdetachparticle",
                                    "psdetachparticles",
                                    "psdroneeffectparticles",
                                    "psdyingexplosionfx",
                                    "psenginefirefx",
                                    "psenginefirenohoodfx",
                                    "psexplosionfx",
                                    "psexplosionnohoodfx",
                                    "psexplosionparticles",
                                    "psexplosionparticlesarm",
                                    "psexplosionparticlestrigger",
                                    "psflashparticles",
                                    "psfrontweaponfx",
                                    "psfx",
                                    "psfxairbag",
                                    "psfxdeflatetyre",
                                    "psfxexhaust",
                                    "psfxgearshiftexhaust",
                                    "psfxlockedbrake",
                                    "psfxnitroexhaust",
                                    "psfxwatersplash",
                                    "psgasparticles",
                                    "psgroundparticles",
                                    "pshangparticle",
                                    "pshitfx",
                                    "pshitparticlesystem",
                                    "pshumaneffectparticles",
                                    "psimpactparticleemitterparam",
                                    "psjumpattackperkfx",
                                    "pslaunchparticles",
                                    "psleavestrailparticleresid",
                                    "psleftweaponfx",
                                    "psmalfunctionleftengineparticles",
                                    "psmeleeshockwaveparticleid",
                                    "psmotiondetectorparticles",
                                    "psmuzzlebeamparticles",
                                    "psmuzzleflashfx",
                                    "psmuzzleflashparticleid",
                                    "psmuzzleflashparticlenonplayerid",
                                    "psoverchargeparticles",
                                    "psoverheatfx",
                                    "psoverheatparticles",
                                    "psparticle",
                                    "psparticleeffect",
                                    "psparticleemitter",
                                    "psparticles",
                                    "psparticlessystem",
                                    "psparticlessystemid",
                                    "psparticlessystemidnohood",
                                    "psparticlesystem",
                                    "pspartsys",
                                    "pspingbackparticles",
                                    "pspreexplosionfx",
                                    "pspropellerparticlefx",
                                    "psrepair",
                                    "psresource",
                                    "psrightweaponfx",
                                    "pssplashparticleresid",
                                    "pssplashresource",
                                    "psstateparticles",
                                    "pstargetbeamparticles",
                                    "pstimedfizzleparticleemitterparam",
                                    "pstrailparticle",
                                    "pstwowheeledsplashparticleresid",
                                    "pstyredetachparticle",
                                    "psunderwaterresource",
                                    "psvehicledestroyedfx",
                                    "psvehiculeeffectparticles",
                                    "pswaterparticles",
                                    "psweakpointparticles",
                                    "pswipecharge",
                                    "pswipefiring",
                                    "pszapperarcfx",
                                    "pszapperhitfx",
                                    "archarchetypetospawn",
                                    "prefabprefabtospawn",
                                   
                                    
                                    # WARNING list below is dangerous
                                    '''
                                    "accessidrequiredid",
                                    "alonespawnsettinginchasespawn",
                                    "alonespawnsettingoutofchasespawn",
                                    "animalconfiganimalconfig",
                                    "archanimalarchetype",
                                    "archarchetype",
                                    "archarchetypeid",
                                    
                                    "archdefaultarchetype",
                                    "archdefaultspawnpointtype",
                                    "archdestroyedmodelpart",
                                    "archfemalenewarchetype",
                                    "archfocuspointarchetype",
                                    "archgrenadearchetype",
                                    "archimpactexplosionarchetype",
                                    "archintersectionarchetype",
                                    "architemarchetype",
                                    "archmalenewarchetype",
                                    "archmasterarchetype",
                                    "archmultiplayerarchetypeid",
                                    "archplayerarchetype",
                                    "archrobotcombatarchetype",
                                    "archrobotcounterhackerarchetype",
                                    "archrobotgreeterarchetype",
                                    "archrobotgreeterarchetypegalilei",
                                    "archrobotgreeterarchetypenudle",
                                    "archrobotgreeterarchetypetidis",
                                    "archrobotwatcherarchetype",
                                    "archslavearchetype",
                                    "archsniperscope",
                                    "archtaserprojectilearchetype",
                                    "archvehiclearcrtype",
                                    "archvehicleconfig",
                                    "archwreckarchetype",
                                    "availabilityrulegroupavailabilityrulegroup",
                                    "behaviorbehaviorsettings",
                                    "breakableeffecteffect",
                                    "cameracontextcameracontext",
                                    "cameravehiclepresetcamerapreset",
                                    "charattrprogattributeprogression",
                                    "charclass",
                                    "charclassstatuisetstatsuisettings",
                                    "charskillskill",
                                    "civdensityciviliandensitydefoverride",
                                    "clotriggerbhvsettingstriggerbehavior",
                                    "clotriggerbhvsettingstriggerbehaviorpeer",
                                    "cloudlayercloudlayer",
                                    "collectionitemuniqueid",
                                    "collectionresourceid",
                                    "collisiondamagecomponentparametercomponentparameter",
                                    "colorremapset",
                                    "confettisystem",
                                    "confettisystemconfettisystem",
                                    "count",
                                    "crimesettingsarmedrobber",
                                    "current_guid",
                                    "curvelibapproximateaccelcurve",
                                    "curvelibmeleedashcurve",
                                    "curvelibmeleespincurve",
                                    "dbenticercontextkey",
                                    "dbenticercontextkey_1",
                                    "dbenticercontextkey_2",
                                    "dbenticercontextkey_3",
                                    "dbenticercontextkey_4",
                                    "dbenticercontextkey_5",
                                    "dbenticercontextkey_6",
                                    "dbwiretypeid",
                                    "debrisdebrisspawner",
                                    "debugannotationiconicondefinition",
                                    "defaultvalue",
                                    "diffusetexture",
                                    #"disguid",
                                    "dismatid",
                                    #"disnomadobjectid",
                                    "disspline",
                                    "distortiontexture",
                                    "dodgeconfigdodgeconfig",
                                    "driverlightpresetlightpreset",
                                    "drivervehiclemiscsounddbvehicledrivermiscsounddb",
                                    "dynmediapresetmediapreset",
                                    "editorobjectsocketcategorycategory",
                                    "editorobjectsocketcollectioncollection",
                                    "emitterkey",
                                    "entcontcontext",
                                    "envcloudsequencecloudsequence",
                                    "envweatherpresetcinematicoverride",
                                    "envweatherpresetpreset",
                                    "enwctconnectortype",
                                    "exitexitsettings",
                                    "filebink",
                                    "fileimage",
                                    "filematerial",
                                    "fileprojectedvideo",
                                    "fileproxyobject",
                                    "filetextureresource",
                                    "filter",
                                    "frag",
                                    "gridmenuhubtargethubitem",
                                    #"guid",
                                    "guidfirstobject",
                                    "guidlastobject",
                                    "hackingprofilehackingprofile",
                                    "hiddbkey",
                                    "hidguid",
                                    "hidid",
                                    #"hidkey",
                                    "highend",
                                    "hudlayerthreedsettingscameraview",
                                    "hudlayerthreedsettingsdeephacking",
                                    "hudlayerthreedsettingssettings3d",
                                    "hudlayerthreedsettingsvehicle",
                                    "hudlayerthreedsettingsvehiclebumper",
                                    "hudlayerthreedsettingsvehicleclassic",
                                    "hudlayerthreedsettingsvehicleinterior",
                                    "hudlayerthreedsettingsvehicleremote",
                                    "humanconfighumanconfig",
                                    #"id",
                                    "ingamemapservicesettingsentrymap",
                                    "item",
                                    "itemlistsitemlist",
                                    "itemliststartinginventoryitemlist",
                                    "itemsdefaultcarondemand",
                                    "itemsitemdbobject",
                                    "itemsrelateditem",
                                    "jumpconfigairdash",
                                    "jumpconfigairdrop",
                                    "jumpconfigdoublejumpconfig",
                                    "jumpconfigfreefallconfig",
                                    "jumpconfigjumpconfig",
                                    "jumpconfiglocktargetjump",
                                    "jumpconfiglocktargetsidejump",
                                    "jumpconfigwalljump",
                                    "jumpconfigwallrunjump",
                                    "key",
                                    "logmatchestsurfaceidx",
                                    "logmatcurblogicmaterial",
                                    "logmatdefaulteffectmaterial",
                                    "logmatdefaultsurfaceid",
                                    "logmatfacesurfaceidx",
                                    "logmatfleshsurfaceid",
                                    "logmatgrasssurfaceid",
                                    "logmatheadsurfaceidx",
                                    "logmatlogicmaterial",
                                    "logmatlogicmaterialv2",
                                    "logmatroadlogicmaterial",
                                    "logmatsidewalklogicmaterial",
                                    "logmatsurfaceidx",
                                    "logmatwaterraysurfaceidx",
                                    "mapicondescmapicondescription",
                                    "matbasematerial",
                                    "material",
                                    "matimpdropimpact",
                                    "matimpexplosionimpact",
                                    "matmaterial",
                                    "matmaterialid",
                                    "matoverridematerial",
                                    "matsetmaterialset",
                                    "menuselectionoverridemenuselectionoverride",
                                    "minimaproadtypeminimaproadtype",
                                    "musicobjectdatamusicobjectconfig",
                                    "name",
                                    "normal",
                                    "npcoverrideconfigmobsquadconfig",
                                    "npcoverrideconfigpolicesquadconfig",
                                    "npcpersonalitypersonalityoverride",
                                    "occholsoundparams",
                                    "parent",
                                    "parentid",
                                    "parkeddensityparkedcarsdensityoverride",
                                    "patselecttrafficdensity",
                                    "patselecttrafficdensityoverride",
                                    "perkdesclistperklistdbobject",
                                    "pgnpctyperange",
                                    "pgrangetypeenabledrangetypes",
                                    "phasestrategydecoratorsettingsdecoratorsettings",
                                    "phasestrategydecoratorstrategydecoratortype",
                                    "phasestrategydefcombatphasestrategies",
                                    "phasestrategydefdamagephasestrategies",
                                    "phasestrategysetstrategy",
                                    "phasestrategysettingscombatphasestrategies",
                                    "phasestrategysettingsdamagephasestrategies",
                                    "phasestrategysettingssetstrateysettings",
                                    "prefabguid",
                                    
                                    "profilingpathpresetcustompreset",
                                    "progressiontagprogressiontag",
                                    "prototype",
                                    "psarmedparticlefxally",
                                    "psarmedparticlefxenemy",
                                    "psarmedparticlefxnormal",
                                    "psattractfx",
                                    "psbackweaponfx",
                                    "psbasesparkfx",
                                    "psbasesparkfxwithperk",
                                    "psbollardtakedownfx",
                                    "psbulletcaseparticleid",
                                    "pschangephaseelectricfx",
                                    "psconfettiparticlesystem",
                                    "psdamagedparticlefx",
                                    "psdamagedsparkparticlefx",
                                    "psdamageparticles",
                                    "psdestroybyexplosionfx",
                                    "psdestroybyexplosionnohoodfx",
                                    "psdestroyedfx",
                                    "psdestroyparticle",
                                    "psdestructionexplosionfx",
                                    "psdetachparticle",
                                    "psdiscoveryparticles",
                                    "psenginefirefx",
                                    "psenginefirenohoodfx",
                                    "psexplosionfx",
                                    "psexplosionnohoodfx",
                                    "psfrontweaponfx",
                                    "psfxairbag",
                                    "psfxdeflatetyre",
                                    "psfxexhaust",
                                    "psfxgearshiftexhaust",
                                    "psfxlockedbrake",
                                    "psfxnitroexhaust",
                                    "psfxwatersplash",
                                    "psgroundparticles",
                                    "pshangparticle",
                                    "psimpactparticleemitterparam",
                                    "psinvalidhitfx",
                                    "psjammerparticlefx",
                                    "psleavestrailparticleresid",
                                    "psleftweaponfx",
                                    "psmotiondetectorparticles",
                                    "psmuzzleflashparticleid",
                                    "psmuzzleflashparticlenonplayerid",
                                    "psparticle",
                                    "psparticleeffect",
                                    "psparticleemitter",
                                    "psparticlefx",
                                    "psparticles",
                                    "psparticlessystem",
                                    "psparticlessystemid",
                                    "psparticlessystemidnohood",
                                    "psparticlesystem",
                                    "pspartsys",
                                    "pspreexplosionfx",
                                    "psrightweaponfx",
                                    "psshutdownelectricfx",
                                    "pssplashparticleresid",
                                    "pssplashresource",
                                    "pstimedfizzleparticleemitterparam",
                                    "pstwowheeledsplashparticleresid",
                                    "pstyredetachparticle",
                                    "psunderwaterresource",
                                    "psvalidhitfx",
                                    "psvehicledestroyedfx",
                                    "pszapperarcfx",
                                    "pszapperhitfx",
                                    "rangedefrangedefinition",
                                    "ref_shader_id",
                                    "rewarditemlistsitemfromcandidatelist",
                                    "roadinterdefroaddef",
                                    "roadmatbankroadmaterialbank",
                                    "roadtrafficdeftrafficdefoverride",
                                    "root",
                                    "selaccelerationvaluetileid",
                                    "selaimassistsettingtileid",
                                    "selaimmodetileid",
                                    "selaudiolanguageselectiontileid",
                                    "selautocenterdrivingcameratileid",
                                    "selautoplaymusicincarsettingtileid",
                                    "selbackgroundtileid",
                                    "selbasicdetailstileid",
                                    "selbreadcrumbtileid",
                                    "selbrightnesssettingtileid",
                                    "selbuttonmappingonfootsettingtileid",
                                    "selbuttonmappingsettingtileid",
                                    "selbuttonmappingvehiclesettingtileid",
                                    "selbuygametileid",
                                    "selcarondemandapptileid",
                                    "selcashtileid",
                                    "selcontinuetileid",
                                    "selcontrolremindersvisibilitytileid",
                                    "seldedsecapptileid",
                                    "seldedseccommunicationchannelvisibilitytileid",
                                    "seldescriptionpanelonlineethnicitytileid",
                                    "seldescriptionpanelsmartphonewallpapertileid",
                                    "seldescriptionpaneltileid",
                                    "seldescriptiontileid",
                                    "seldifficultysettingtileid",
                                    "seldistrictvisibilitytileid",
                                    "seldrivingcamerasensitivitytileid",
                                    "seldrivingsmoothingtileid",
                                    "selemotiongridmodetileid",
                                    "selepilepsyloadingtileid",
                                    "selequipmenttoolsvisibilitytileid",
                                    "seleventpropositionvisibilitytileid",
                                    "selfilteralltileid",
                                    "selfiltercollectiblestileid",
                                    "selfilterlocationstileid",
                                    "selfilteronlinetileid",
                                    "selfilteroperationstileid",
                                    "selfilterseparatortileid",
                                    "selfiltershopstileid",
                                    "selfriendinvasionsettingtileid",
                                    "selfriendsautojoinsettingtileid",
                                    "selgamepadsettingtileid",
                                    "selhackingaimassisttileid",
                                    "selhackingoptionsvisibilitytileid",
                                    "selheaderslottileid",
                                    "selheadertileid",
                                    "selinfopaneltileid",
                                    "selinventorygridmodetileid",
                                    "selinvertxaxistileid",
                                    "selinvertxsettingtileid",
                                    "selinvertyaxistileid",
                                    "selinvertysettingtileid",
                                    "selloadgametileid",
                                    "selloadingtileid",
                                    "sellooksensativitysettingtileid",
                                    "sellooksensitivitytileid",
                                    "selmediaplayerapptileid",
                                    "selmenupositionsettingtileid",
                                    "selminimapvisibilitytileid",
                                    "selmissionobjectivesfeedbackvisibilitytileid",
                                    "selmouseaccelerationtileid",
                                    "selmultimonitorsettingtileid",
                                    "selmusictileid",
                                    "selnewgametileid",
                                    "selnewsfeedpaneltileid",
                                    "selnewswidgettileid",
                                    "selnotificationtileid",
                                    "selobjectiveindicatorvisibilitytileid",
                                    "selonfootcontrolschemedisplaytileid",
                                    "selonlineethnicitysettingtileid",
                                    "selpageheadertileid",
                                    "selpagewidgettileid",
                                    "selperformancebartileid",
                                    "selpictorialcontenttileid",
                                    "selpressstarttileid",
                                    "selprofilertargetlinevisibilitytileid",
                                    "selprofilervisibilitytileid",
                                    "selquitmainmenutileid",
                                    "selquitmissiontileid",
                                    "selquitonlinesessiontileid",
                                    "selquittodesktoptileid",
                                    "selradialdetectionvisibilitytileid",
                                    "selreloadautosavetileid",
                                    "selrestartmissiontileid",
                                    "selresumetileid",
                                    "selreticlevisibilitytileid",
                                    "selrewardvisibilitytileid",
                                    "selsafeframesettingtileid",
                                    "selsellallvaluablestileid",
                                    "selsfxvolumesettingtileid",
                                    "selshoppaneltileid",
                                    "selsmartphonenotificationvisibilitytileid",
                                    "selsplinefrom",
                                    "selsplineto",
                                    "selsprintmodetileid",
                                    "selstatstileid",
                                    "selsubtitlessettingtileid",
                                    "seltabswitchertileid",
                                    "seltextlanguageselectionsettingtileid",
                                    "seltipsvisibilitytileid",
                                    "seltooltipssettingtileid",
                                    "seltouchpadsettingtileid",
                                    "seltrafficspeedgridmodetileid",
                                    "seltutorialbackgroundtileid",
                                    "seltutorialdescriptiontileid",
                                    "seltutorialheadertileid",
                                    "seltutorialpictorialcontenttileid",
                                    "selubisoftclubtileid",
                                    "selupdatelogvisibilitytileid",
                                    "selvehiclecontrolschemedisplaytileid",
                                    "selvibrationsettingtileid",
                                    "selvoicechatsettingtileid",
                                    "selvoicechatvolumesettingtileid",
                                    "selwalkmodetileid",
                                    "selwallettileid",
                                    "selwallpapersettingtileid",
                                    "selwarningmessagesvisibilitytileid",
                                    "selweatherapptileid",
                                    "sidewalkmatbanksidewalkmaterialbank",
                                    "skycolorsettingssky",
                                    "sndptsoundpoint",
                                    "socketitemiduniqueid",
                                    "spawnspawnsettings",
                                    "splineloftloftelement",
                                    "stims",
                                    "stimtablestimeffecttable",
                                    "subtype",
                                    "tagcategorytagcategory",
                                    "tagcategoryuitagcategory",
                                    "tagtag",
                                    "targetid",
                                    "trnavcfgconfig",
                                    "uniqueid",
                                    "value",
                                    "vclnavcfgvehicleconfig",
                                    "vehiclecarcardb",
                                    "vehicleconfigvehicleconfig",
                                    "vehicledynamiclightpreset",
                                    "vehicleenginesounddbvehicleenginesounddb",
                                    "vehiclefxpresetvehiclefxpreset",
                                    "vehiclegoingstraighttweak",
                                    "vehicleinfovehiclespawninfo",
                                    "vehiclelamppresetlamppreset",
                                    "vehiclemiscsounddbvehiclemiscsounddb",
                                    "vehiclepartdefaultparams",
                                    "vehiclepartoverrideparams",
                                    "vehiclertpcdbvehiclertpcdb",
                                    "vehicletransmissionsounddbvehicletransmissionsounddb",
                                    "vehiclewheeledphyscomponentparamscomponentparams",
                                    "vehiclewheelsounddbvehiclewheelsounddb",
                                    "waterdefwaterdef",
                                    "waterfxpresetwaterfxpreset",
                                    "worldenvsettingssettings",
                                    '''
                                    #"editorobjectsocketcollectioncollection", # comment to break the link between BFPI and socket collection
                                    ])
    
    LEAN_CONTENT = set([
                        "filename",
                        "type",
                        "special_info",
                        "jira_issue",
                        "jira_status",
                        "jira_studio",
                        "jira_loq",
                        "jira_borough",
                        "jira_id",
                        ])
    
    def __init__(self, callback=None):
        super(d_object, self).__init__()
        self._callback = callback
        self.identifier = "DATA MISSING"
        self.type = "Object"
        self.filename = "DATA MISSING"
        self.name = "DATA MISSING"
        self._content = None
        self.file_id = None
        self._entity_instance_count = 0
        self.is_legal = True
        self.special_info = None #"" # this variable is meant to be used to pass special info that can be read in proparazzi
        self.size = None # this is used to show the size of the item, in memory, in drawcalls, whatever
        self.dependencies = set() #[]
        self._dependencies_legacy = []
        self.identifiers = set() # new set to contain all possible identifiers
        self.subitems = set() # contains all the subitems of a library type object, like a world layer or database_view file

        # Lists of d_objects, for fast genealogy research
        self._parents = {}
        self._children = {}

        self.lit = False  # Used by VFX-Ray and the likes to show the light icon in a tree view

    def broadcast_callback(self, my_type, my_value=None):
        if self._callback is not None:
            self._callback(my_type, my_value)

    def get_info(self):
        return "Name:\t\t\t" + self.name + "\n" + "Filename:\t\t" + self.filename + "\n" + "File ID:\t\t" + self.file_id + "\n"

    def get_value_type(self, value):
        if value is '':
            # .. todo:: track down other uses of the get_value_type and avoid passing empty str
            return 3
        value_len = len(value)

        value_starts = value[0]
        if (value_len == 38) and value_starts is "{" and value.endswith("}"):
            # guid
            return 0
        if (value_len == 18) and value_starts is "0x":
            # unique id
            return 1
        _file, ext = os.path.splitext(value)
        if ext in d_object.EXTENSIONS and "," not in value:
            return 2

        # unknown
        return 3

    def get_dependencies(self, xml_file):
    
        print self, ": get_dependencies is DEPRECATED. Use it at your own risk."
    
        #tree = xml_file
        #if type(xml_file).__name__ != "Element":
        tree = ET.ElementTree(file=xml_file)
            
        for elem in tree.iter():
            for key, value in elem.attrib.iteritems():
                if value is '':
                    continue
                value_type = self.get_value_type(value)
                
                # unknown
                if value_type is 3:
                    continue
                # guid
                elif value_type is 0:
                    if value.lower() not in self._dependencies_legacy:
                        self._dependencies_legacy.append(value.lower())
                # file
                elif value_type is 2:
                    relative_value = convert_to_path_type(value.lower(), 2)  # Relative
                    _file, ext = os.path.splitext(relative_value)
                    replacemap  ={
                        ".tree.bin":"",  # special case for speedtree
                        ".bin": ".xml",
                        # (".glm", ".xml")
                        ".xbg": ".glm",
                        # (".xlf",".lft")
                        # (".lft", ".xml")
                        ".xbt": ".png"
                    }
                    if ext in replacemap.keys():
                        relative_value = relative_value.replace(ext, replacemap[ext])
                    if relative_value not in self._dependencies_legacy:
                        self._dependencies_legacy.append(relative_value)
                # unique id
                elif value_type is 1:
                    # Do nothing if key == "UniqueID (for xml file pointing on models)
                    if key != "UniqueID":
                        self._dependencies_legacy.append(value)
                        # filepath = self.resources_id.get_resource_name_form_id(value)
                        # if filepath not in self._dependencies_legacy:
                            # self._dependencies_legacy.append(filepath)
        
        
    def add_dependencies_from_element(self, tree):
        for elem in tree.iter():
            for key, value in elem.attrib.iteritems():
                if key.lower() in d_object.DEPENDENCY_ATTRIBUTES_SET:
                    self.add_dependency(value)

    def get_file_id_from_metadata(self):
        metadata_xml_file = self.filename +".metadata"
        if isfile(metadata_xml_file):
            tree = ET.ElementTree(file=metadata_xml_file)
            
            for elem in tree.iter():
                if elem.tag == "category":
                    self.file_id = elem.text.lower()
            
            
    def add_dependency(self, dependency):
        
        if dependency is None:
            return False
        
        dependency = dependency.lower()
        
        if dependency == "none" :
            return False
            
        if dependency == "" :
            return False
        
        if dependency[0] == ";": # test disabled textures
            return False
            
        _file, ext = os.path.splitext(dependency)
        if ext in d_object.EXTENSIONS_DICT.keys():
            dependency = convert_to_path_type(dependency, 2)  # Relative
            dependency = dependency.replace(ext, d_object.EXTENSIONS_DICT[ext])
            
        self.dependencies.add(dependency)        
        return True
    
    def get_content(self, separator, lean=False):
        od = OrderedDict(sorted(self.__dict__.items()))
        content = ""
        for k, v in od.iteritems():
            if k == "_content": # skip itself to prevent doubling the properties
                continue
            if lean:
                if k not in d_object.LEAN_CONTENT:
                    continue
            v = str(v)
            
            if not v:
                v = str(None)
            
            content += k.upper()+"="+v
            content += separator
        return content
    
class bad_object(d_object):
    def __init__(self, id):
        super(bad_object, self).__init__()
        self.type = "Bad Object" 
        self.identifier = id

class d_missing(d_object):
    def __init__(self, id):
        super(d_missing, self).__init__()
        self.type = "Missing"
        self.identifier = id
        self.name = id

class d_world(d_object):
    def __init__(self, world_path, callback=None, game_map_zones_image=None, zones_dict=None):
        super(d_world, self).__init__(callback)
        self.type = "World"

        self.name = world_path

        self.world_size = 0 #self.WORLD_SIZE # this needs to be fetched in the data

        self.cell_count = 0 #self.CELL_COUNT # needs to be replaced by CELL_COUNT everywhere
                
        self.get_world_size(world_path)
        
        self.cell_size = self.world_size / self.cell_count
        
        self.world_grid = two_d_grid(self.cell_count)
        self.grid_range = self.world_grid.grid_range
        
        self.game_map_zones_image = game_map_zones_image
        self.zones_dict = zones_dict

        self.special_layers = {} #{"Mission": [], "Interior": [], "HMA": [], "LMA": [], "Sas": [], "Progression": []}
        self.layer_files = get_files(world_path + r"\objects", [".xml"], "")#DOES NOT WORK ANYMORE BECAUSE IT'S A SET [:100] #DEBUG slice world layers for quicker world parsing
        # self.layer_files = set([r"w:\main\data\worlds\london\objects\user\10_southwark\10_swk_walworth\swwl_002\swwl_002_la.xml"]) # debug to test only one world layer
        # self.layer_objects = []
        self.layer_objects = set()

        list_file = join(world_path, "objects", "list.xml")
        if os.path.exists(list_file):
            self.list_file = list_file # world_path + r"\objects\list.xml"
            self.filename = self.list_file
            self.get_layer_types(self.list_file)

        # if scan_cells:
            # self.fill_cells()        

        self.dependencies = self.layer_files

        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative
        
    def get_world_size(self, world_path):
        desc_path = join(world_path, r"desc.xml")
        tree = ET.ElementTree(file=desc_path)
        for elem in tree.iter("Grids"):
            size = [int(elem.get("WorldOffsetX")), int(elem.get("WorldOffsetY"))]
            self.world_size = max(size)*2
            self.cell_count = self.world_size/128
            break        
        
    def get_cell(self, x, y):
        return self.world_grid.cells[(x, y)]

    def get_layer_types(self, list_file):
    
        tree = ET.ElementTree(file=list_file)
        for elem in tree.iter("Layer"):
            name = elem.get("aName")
            if name:
                name = name.lower()
                
                if elem.get("bMission") == "1":
                    self.special_layers[name] = "Mission"
                elif elem.get("bInterior") == "1":
                    self.special_layers[name] = "Interior"
                elif elem.get("bHighMemoryArea") == "1":
                    self.special_layers[name] = "HMA"
                elif elem.get("bLowMemoryArea") == "1":
                    self.special_layers[name] = "LMA"
                elif elem.get("bSas") == "1":
                    self.special_layers[name] = "Sas"
                elif elem.get("bProgression") == "1":
                    self.special_layers[name] = "Progression"
                else:
                    self.special_layers[name] = "Normal"

    def get_coord(self, value):
        value = float(value)
        if value == self.world_size/2:  # for some strange reason, Disrupt allows an entity to be at 4096, which is technically out of bound of the loading grid
            value -= 1
        #value += 4097
        value += (self.world_size/2) #+ 1 # offset the positions so that the grid starts at 0 instead of -4096 # no idea why this offset was added back then, but as Ophelie mentionned, it's returning bad positions and commenting this fixes the issue.
        return int((math.ceil((value) / self.cell_size) * self.cell_size) / self.cell_size)
    
    def fill_cells(self):

        self.broadcast_callback(2, "Filling World Cells")  # Max out progress bar

        # This is a slow operation, so update the progress bar and refresh UI once in a while
        progressbar_stride = 35
        counter = progressbar_stride
        self.broadcast_callback(0, len(self.layer_objects) / progressbar_stride)  # Set progressbar max

        for obj_wl in self.layer_objects:

            counter += 1
            if counter > progressbar_stride:
                self.broadcast_callback(1)  # Update progress bar
                counter = 0

            for obj_entity in obj_wl.entities:
                pos_x, pos_y, pos_z = obj_entity.position
                x = self.get_coord(pos_x)
                y = self.get_coord(pos_y)
                if (x, y) in self.world_grid.cells:
                    #obj_entity.region = self.world_grid.cells[(x, y)].region # pass the region var to the entity # now replaced with zone system from bitmap
                    self.world_grid.cells[(x, y)].entities.append(obj_entity)
                
        self.broadcast_callback(1, True)  # Max out progress bar
        
    def fill_cells_with_ranges(self, range_objects): # this method needs to be called after the world has been created and the splines have been reticulated (lolz)
        
        range_set = set()      
        for range in range_objects.values():
            range_set.add(range)
            
        for range in range_set:
            #print range.points[0], range.points[1]
            for pos in range.points:
                pos_x, pos_y, pos_z = pos
                x = self.get_coord(pos_x)
                y = self.get_coord(pos_y)
                if (x, y) in self.world_grid.cells:
                    self.world_grid.cells[(x, y)].entities.append(range)

class two_d_grid(d_object):
    def __init__(self, cell_count):
        super(two_d_grid, self).__init__()
        self.type = "World Grid"
        self.grid_range = range(1, cell_count + 1)
        self.cell_objects = []
        self.cells = self.build_grid()
        self.set_region()   # regions are to be set as follows : 
                            # 0 = default
                            # 1 = mtl 1
                            # 2 = mtl 2 
                            # 3 = tor 1
                            # 4 = tor 2
                            # 5 = par 1
                            # 6 = par 2
                            # 7 = buc 1
                            # 51 = mtl fp

    
    def build_grid(self):
        grid = {}
        for x in self.grid_range:
            for y in self.grid_range:
                new_cell = grid_cell(x, y)
                grid[(x, y)] = new_cell
                self.cell_objects.append(new_cell)
        return grid
        
    def set_region(self):
        for cell in self.cell_objects:
            if cell.x in range(6,31) and cell.y in range(17,30):
                cell.region = 1            
            if cell.x in range(7,15) and cell.y in range(30,38):
                cell.region = 2
            if cell.x in range(31,57) and cell.y in range(17,30):
                cell.region = 3
            if cell.x in range(31,56) and cell.y in range(28,43):
                cell.region = 4
            if cell.x in range(26,34) and cell.y in range(31,43):
                cell.region = 5
            if cell.x in range(25,50) and cell.y in range(42,50):
                cell.region = 6
            if cell.x in range(16,27) and cell.y in range(30,44):
                cell.region = 7
            if cell.x in range(20,24) and cell.y in range(22,26):
                cell.region = 51
                
            if cell.x == 20 and cell.y == 30:
                cell.region = 1
            if cell.x == 19 and cell.y == 30:
                cell.region = 1
            if cell.x == 18 and cell.y == 30:
                cell.region = 1
            if cell.x == 17 and cell.y == 30:
                cell.region = 1
            if cell.x == 31 and cell.y == 17:
                cell.region = 1
                
            if cell.x == 30 and cell.y == 28:
                cell.region = 3
            if cell.x == 30 and cell.y == 27:
                cell.region = 3
            if cell.x == 30 and cell.y == 26:
                cell.region = 3
            if cell.x == 30 and cell.y == 25:
                cell.region = 3
            if cell.x == 30 and cell.y == 24:
                cell.region = 3
            if cell.x == 30 and cell.y == 23:
                cell.region = 3
                
            if cell.x == 33 and cell.y == 31:
                cell.region = 4
            if cell.x == 33 and cell.y == 32:
                cell.region = 4
            if cell.x == 33 and cell.y == 33:
                cell.region = 4
            if cell.x == 33 and cell.y == 34:
                cell.region = 4
            
            if cell.x == 26 and cell.y == 35:
                cell.region = 5
            if cell.x == 26 and cell.y == 36:
                cell.region = 5
            if cell.x == 26 and cell.y == 37:
                cell.region = 5
            if cell.x == 26 and cell.y == 38:
                cell.region = 5
            if cell.x == 26 and cell.y == 39:
                cell.region = 5
            if cell.x == 26 and cell.y == 40:
                cell.region = 5
            if cell.x == 26 and cell.y == 41:
                cell.region = 5
            if cell.x == 26 and cell.y == 42:
                cell.region = 5
            if cell.x == 26 and cell.y == 43:
                cell.region = 5
            if cell.x == 25 and cell.y == 40:
                cell.region = 5
            if cell.x == 25 and cell.y == 41:
                cell.region = 5
            if cell.x == 25 and cell.y == 42:
                cell.region = 5
            if cell.x == 25 and cell.y == 43:
                cell.region = 5
            if cell.x == 26 and cell.y == 23:
                cell.region = 5   
                
            if cell.x == 27 and cell.y == 30:
                cell.region = 7
            if cell.x == 27 and cell.y == 31:
                cell.region = 7
            if cell.x == 27 and cell.y == 32:
                cell.region = 7
        
class grid_cell(d_object):
    def __init__(self, x, y):
        super(grid_cell, self).__init__()
        self.type = "World Cell"
        self.x = x
        self.y = y
        self.region = 0
        self.coordinates = str(self.x) + "," + str(self.y)
        self.name = self.coordinates
        #self.filename = self.coordinates
        self.filename = str(uuid.uuid4())
        self.entities = []
        self.kits = {}
        self.points = 0
        self.points_compensated = 0
        self.facade_instance_count = 0
        self.resources = [] # this is supposed to be a temp var
        self.resources_alt = [] # this is supposed to be a temp var, yes, another one
        self.resources_dict = {}
        
        #self.identifier = self.coordinates
        self.identifier = self.filename
    
class city_block_cell(d_object):
    def __init__(self):
        super(city_block_cell, self).__init__()
        self.type = "City Block"
        self.entity = None
        self.color = None
        self.heatmap_qcolor = None
        self.points = None
        self.jira_issue = None
        self.resources_dict = {}
        self.entities = set()
        self.resources = set()#[]
    
class d_world_layer(d_object):
    def __init__(self, world_layer_file, world_size=None, game_map_zones_image=None, zones_dict=None):
        super(d_world_layer, self).__init__()
        self.type = "World Layer"
        self.filename = world_layer_file
        self.name = (basename(world_layer_file)).replace(".xml", "")
        self.world_layer_type = None
        self.world_size = world_size
        self.entities = []
        self.bbox_min = None
        self.bbox_max = None
        self.area = None
        self.game_map_zones_image = game_map_zones_image
        self.zones_dict = zones_dict
        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative

        self.get_world_layer_references(world_layer_file)
        if self.area > 4700000000: # by default, world layer have a bogus bounding box, which will give an area of 4701022096
            self.area = 0

    def get_world_layer_area(self, x1, y1, x2, y2):
        width = (float(x2) - float(x1))
        length = (float(y2) - float(y1))
        area = math.fabs(width * length)
        return area

    def get_world_layer_references(self, world_layer_file):
        tree = ET.ElementTree(file=world_layer_file)
        for elem in tree.iter('LayerContent'):
            if elem.get("BBoxMin") is not None:
                self.bbox_min = tuple(elem.get("BBoxMin").split(','))
                self.bbox_max = tuple(elem.get("BBoxMax").split(','))
                self.area = self.get_world_layer_area(self.bbox_min[0], self.bbox_min[1], self.bbox_max[0], self.bbox_max[1])
        for elem in tree.iter('Object'):
            type = elem.get("Type", None)
            if type is None:
                continue
            '''
            if elem.get("bUseWorldCategory", "") == "1":
                print "------------"
                print world_layer_file
                print elem.get("Id", "None")
                print elem.get("Name", "I don't have a name")
            '''
            #if elem.get("Name") is not None:
            new_entity = d_entity(self.world_size, self.game_map_zones_image, self.zones_dict)
            
            new_entity.add_dependencies_from_element(elem)
            
            self.entities.append(new_entity)
            self.subitems.add(new_entity) # double list for now to keep concistancy, self.entities might have to become deprecated at some point but it will break many DDV functions
            new_entity.guid = elem.get("Id", "None")
            new_entity.set_identifier()
            new_entity.name = elem.get("Name", "I don't have a name")
            new_entity.world_layer_type = self.world_layer_type
            new_entity.get_position(elem.get("WorldPos", "0,0,0"))
            new_entity.get_rotation(elem.get("Angles", "None"))
            new_entity.set_scale(elem.get("Scale", "None"))

            new_entity.entity_type = type

            if type != 'PrototypeEntity' and type != 'Prefab':
                for components in elem.iter("Components"):
                    for comp in components:
                        new_entity.components.add(comp.tag)

            if type == "BatchedObject":
                old_reference = elem.get("FileName") # wd1 style reference in world layers
                if old_reference is not None:
                    new_entity.resource = old_reference
                for child in elem.iter():
                    class_name = child.get("hid_DTCTH_ClassName", "")
                    if class_name == "CGraphicBatchModel":
                        new_entity.resource = child.get("fileModel", "").lower()
                    elif class_name == "CParticlesBatchModel":
                        new_entity.resource = child.get("psParticleSystem", "").lower()
                    elif class_name == "CArchetypeBatchModel":
                        new_entity.resource = child.get("archArchetype", "").lower()
                    elif class_name == "CSimplePrimitiveBatchModel":
                        new_entity.is_primitive = True
                    elif class_name == "CSoundPointBatchModel":
                        new_entity.is_soundpoint = True
                    elif class_name == "CLocalCubeMapBatchModel":
                        new_entity.is_localcubemap = True
            elif type == "Prefab":
                new_entity.resource = elem.get("PrefabGUID", "None").lower()
                new_entity.prefab_deleted_children = set()
                for sub_elem in elem.iter("DeletedChild"):
                    deleted_child_id = sub_elem.get("PrefabDBChildId")
                    new_entity.prefab_deleted_children.add(deleted_child_id.lower())
            elif type == "Proxy":
                new_entity.resource = elem.get("SubType", "None").lower()
            elif type == "CityLifeObject":
                cloID = get_cloID(elem)
                new_entity.add_dependency(cloID)
            elif type == "Building":
                get_building_properties(new_entity, elem)

            elif type == "Entity" or type == "PrototypeEntity":
                new_entity.entity_class = elem.get("EntityClass", "")
                current_prototype = elem.get("Prototype","")
                new_entity.add_dependency(current_prototype)
                for sub_elem in elem.iter("CGraphicComponent"):
                    new_entity.add_dependency(sub_elem.get("fileModel"))

                for sub_elem in elem.iter("Entity"):
                    if sub_elem.get("wlucatLoadingUnitCategoryV3", "") is not None:
                        new_entity.wlu_category = sub_elem.get("wlucatLoadingUnitCategoryV3", "")

            elif type == "Plaza":
                vertex_list = []
                for sub_elem in elem.iter():
                    if sub_elem.tag == "Corner":
                        values = sub_elem.get("vecCornerPos", "")
                        values_list = values.split(",")
                        float_values_list = [float(val) for val in values_list]
                        vertex_list.append(float_values_list)
                    elif sub_elem.tag == "Roof":
                        new_entity.plaza_roof_material = sub_elem.get("selMaterialBank", "")
                    elif sub_elem.tag == "Footing":
                        new_entity.plaza_footing_material = sub_elem.get("selMaterialBank", "")
                    elif sub_elem.tag == "Shape":
                        spline_loft_element_id = sub_elem.get("splineloftLoftElement", "")
                        new_entity.add_dependency(spline_loft_element_id)

                try:
                    min_x = vertex_list[0][0]
                    max_x = vertex_list[0][0]
                    min_y = vertex_list[0][1]
                    max_y = vertex_list[0][1]
                    
                    for vertex in vertex_list:
                        if vertex[0] < min_x:
                            min_x = vertex[0]
                        if vertex[0] > max_x:
                            max_x = vertex[0]
                        if vertex[1] < min_y:
                            min_y = vertex[1]
                        if vertex[1] > max_y:
                            max_y = vertex[1]

                    width = max_x - min_x
                    height = max_y - min_y
                    area = width * height
                    new_entity.shape_area = area
                except:
                    print elem.get("Id") + " on " + world_layer_file + " is a plaza with no corners. DELETE IT!"
                    
                new_entity.special_info = (str(new_entity.shape_area)+str(new_entity.plaza_roof_material)+str(new_entity.plaza_footing_material))

            elif type == "CityLocation":
                new_entity.points = []
                for sub_elem in elem.iter("Point"):
                    pos = sub_elem.get("Pos")
                    pos_split = pos.split(",")
                    pos_tup = (float(pos_split[0]), float(pos_split[1]))
                    new_entity.points.append(pos_tup)
                    
            elif type == "EnticerVehicle":
                for sub_elem in elem.iter("SpawnSpecification"):
                    new_entity.add_dependency(sub_elem.get("vehicleinfoVehicleSpawnInfo", ""))
                    new_entity.add_dependency(sub_elem.get("vehiclesbankVehiclesBank", ""))
                
            new_entity.add_dependency(new_entity.resource)
            new_entity.filename = self.identifier
            new_entity.set_region()
        

class d_entity(d_object):
    def __init__(self, world_size, game_map_zones_image=None, zones_dict=None):
        super(d_entity, self).__init__()

        self.type = "Entity"
        self.guid = ""
        self.entity_type = ""
        self.entity_class = ""
        self.world_layer_type = ""
        self.world_size = world_size
        self.resource = ""
        self.dependencies_compiled_size = 0
        self.is_primitive = False
        self.is_soundpoint = False
        self.is_localcubemap = False
        self.kits = []
        self.building_elements = []
        self.building_height = 0
        self.building_volume = 0
        self.building_radius = 0
        self.building_ideal_killdistance = 0
        self.building_ideal_WLU = "FarAway"
        self.building_current_WLU = "FarAway"
        self.building_edges_distance = []
        self.building_floor_count = 0
        self.building_surface_area = 0
        self.building_facade_count = 0
        self.building_facade_ratio = 0
        self.building_roof_material = None
        self.building_generatelowlod = True
        self.shape_area = None
        self.plaza_roof_material = None
        self.plaza_footing_material = None
        self.position = None
        self.rotation = None
        self.scale = None
        self.stream_optimizer_remove_gain = 0
        self.game_map_zones_image = game_map_zones_image
        self.zones_dict = zones_dict
        self.region = 0
        self.points = None
        self.prefab_deleted_children = None
        self.identifier = None

        self.wlu_category = "None"
        '''
        WLU categories:
        world   0
        faraway 1
        far     2
        near    3
        quality 4
        interior5
        hma     6
        sas     7
        lma     10
        mis     11
        invalid 15
        '''

        self.components = set()
        self.components_prefab = [] #this needs to be a list as prefabs can have multiple items in them
        self.loading_cost = None

    def get_position(self, position=None):
        if position is not None:
            self.position = tuple(position.split(','))
        else:
            self.position = (0, 0, 0)

    def get_rotation(self, rotation=None):
        if rotation is not None:
            self.rotation = tuple(rotation.split(','))
        else:
            self.rotation = (0, 0, 0)

    def set_scale(self, scale=None):
        if scale is not None:
            self.scale = tuple(scale.split(','))
        else:
            self.scale = (0, 0, 0)

    def set_identifier(self):
        self.identifier = self.guid.lower()

    def set_region(self):
        if self.game_map_zones_image is None or self.zones_dict is None:
            #print "Problem setting region of", self.name
            return
        if self.position is None:
            print self.name, "has no position!?"
            return
        
        height = self.game_map_zones_image.height()
        ratio = float(self.world_size) / height
            
        x = float(self.position[0])
        y = float(self.position[1])
        
        x = x * -1
        
        x = x / ratio + (height/2)
        y = y / ratio + (height/2)
        
        x = int(x)
        y = int(y)
        
        c = self.game_map_zones_image.pixel(x, y)
        rgb = QtGui.QColor(c).red(), QtGui.QColor(c).green(), QtGui.QColor(c).blue()
        
        zone = self.zones_dict.get(rgb)
        if zone is None:
            zone = (0 , "Zone Error")
        self.region = zone[0]
        self.special_info = zone[1]
    
    def get_city_block_color(self, city_blocks_image):
        if city_blocks_image is None:
            #print "Problem setting city block of", self.name
            return
        if self.position is None:
            print self.name, "has no position!?"
            return
        
        height = city_blocks_image.height()
        ratio = float(self.world_size) / height
            
        x = float(self.position[0])
        y = float(self.position[1])
        
        x = x * -1
        
        x = x / ratio + (height/2)
        y = y / ratio + (height/2)
        
        x = int(x)
        y = int(y)
        
        c = city_blocks_image.pixel(x, y)
        id = c & 0x00ffffff # convert from 24 bits to 16 bits
        return id
         
class d_spline_layer(d_object):
    def __init__(self, spline_layer_file):
        super(d_spline_layer, self).__init__()
        self.type = "Spline Layer"
        self.filename = spline_layer_file
        self.name = basename(spline_layer_file)
        self.spline_objects = []
        self.create_spline_objects()
        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative
        
    def create_spline_objects(self):
        tree = ET.ElementTree(file=self.filename)
        for elem in tree.iter("Splines"):
            for sub_elem in elem.iter("Spline"):
                new_spline_obj = d_spline()
                new_spline_obj.guid = sub_elem.get("hidGuid","")
                new_spline_obj.name = sub_elem.get("aName","")
                self.add_dependency(new_spline_obj.guid)
                new_spline_obj.identifier = new_spline_obj.guid.lower()
                new_spline_obj.filename = self.filename
                self.spline_objects.append(new_spline_obj)
                self.subitems.add(new_spline_obj)
                
                points = {}
                for point_elem in sub_elem.iter("hidPoint"):
                    position = point_elem.get("vectorPosition", "")
                    guid = point_elem.get("disGuid", "")
                    pos_split = position.split(",")
                    x = float(pos_split[0])
                    y = float(pos_split[1])
                    z = float(pos_split[2])
                    points[guid] = (x,y,z)
                
                for range_elem in sub_elem.iter("hidRange"):
                    new_range_object = d_range()
                    new_range_object.guid = range_elem.get("disGuid","")
                    new_range_object.name = range_elem.get("aName","")
                    new_spline_obj.add_dependency(new_range_object.guid)
                    new_range_object.identifier = new_range_object.guid.lower()
                    new_range_object.add_dependencies_from_element(range_elem)
                    new_range_object.filename = self.filename
                    
                    start = None
                    for start_elem in range_elem.iter("Start"):
                        start = points.get(start_elem.get("disPointGuid", ""))
                        
                    end = None
                    for end_elem in range_elem.iter("End"):
                        end = points.get(end_elem.get("disPointGuid", ""))
                        
                    new_range_object.points = (start, end)
                    new_range_object.position = start
                    
                    for custom_props_elem in range_elem.iter("CustomProps"):
                        for custom_prop_elem in range_elem.iter("CustomProp"):
                            definition = custom_prop_elem.get("rangedefRangeDefinition", None)
                            if definition:
                                new_range_object.definition = definition
                    
                    new_spline_obj.range_objects.append(new_range_object)
                    new_spline_obj.subitems.add(new_range_object)
        
  
class d_spline(d_object):
    def __init__(self):
        super(d_spline, self).__init__()
        self.type = "Spline"
        self.filename = None
        self.name = None
        self.guid = None
        self.position = None
        self.range_objects = []
        
class d_range(d_object):
    def __init__(self):
        super(d_range, self).__init__()
        self.type = "Range"
        self.filename = None
        self.name = None
        self.guid = None
        self.points = None
        self.position = None
        self.world_layer_type = self.type # need to do this in order to be compatible with entities, since ranges are added to world cells
        self.entity_type = self.type
        self.definition = None
        
    def get_city_block_color(self, city_blocks_image, world_size):
        if city_blocks_image is None:
            #print "Problem setting city block of", self.name
            return
        if self.position is None:
            print self.name, "has no position!?"
            return
        
        height = city_blocks_image.height()
        ratio = float(world_size) / height
            
        x = float(self.position[0])
        y = float(self.position[1])
        
        x = x * -1
        
        x = x / ratio + (height/2)
        y = y / ratio + (height/2)
        
        x = int(x)
        y = int(y)
        
        c = city_blocks_image.pixel(x, y)
        id = c & 0x00ffffff # convert from 24 bits to 16 bits
        return id
        
class d_proxy(d_object):
    def __init__(self, proxy_file):
        super(d_proxy, self).__init__()
        self.type = "Proxy"
        self.filename = proxy_file
        self.name = basename(proxy_file)
        self.jira_issue = None
        self.jira_status = None
        self.jira_studio = None
        self.jira_loq = None
        self.jira_borough = None
        self.proxy_type = "NONE"
        self.proxy_objects = []
        self.get_proxy_objects(proxy_file)

        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative
        self.get_file_id_from_metadata()

    def get_proxy_objects(self, proxy_file):
        tree = ET.ElementTree(file=proxy_file)
        reference = None
        for elem in tree.iter():
            if elem.tag == "Object":
                type = elem.attrib.get("ProxyObjectType")
                if type == "BatchedObject":
                    childs = elem.getchildren()
                    for child in childs:
                        if child.attrib.get("hid_DTCTH_ClassName") == "CGraphicBatchModel":
                            reference = child.attrib.get("fileModel").lower()
                            self.proxy_objects.append(reference)
                            self.proxy_type = "geometry"
                        if child.attrib.get("hid_DTCTH_ClassName") == "CArchetypeBatchModel":
                            reference = child.attrib.get("archArchetype").lower()
                            self.proxy_objects.append(reference)
                            self.proxy_type = "archetype"

                elif type == "Prefab":
                    reference = elem.attrib.get("PrefabGUID").lower()
                    self.proxy_objects.append(reference)
                    self.proxy_type = "prefab"
        self.add_dependency(reference)
        

class d_archetype_lib(d_object):
    def __init__(self, archetype_lib_file):
        super(d_archetype_lib, self).__init__()
        self.type = "Archetype Library"
        self.filename = archetype_lib_file
        self.name = "DATA MISSING"
        self.lib_items = []
        self.lib_items_objects = []
        self.get_lib_items(archetype_lib_file)

        self.archetype_derivations_dict = dict()
        self.get_archetype_derivations()

        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative

    def get_lib_items(self, archetype_lib_file):
        tree = ET.ElementTree(file=archetype_lib_file)

        previous_wlucat = None

        for elem in tree.iter():
        
            if elem.tag == "EntityPrototypeLibrary":
                self.name = elem.attrib.get("Name").lower()
            elif elem.tag == "EntityPrototype":

                current_archetype_id = elem.attrib.get("Id").lower()
                current_archetype_name = elem.attrib.get("Name")
                if current_archetype_name == "":
                    current_archetype_name = "MyNameIsFuckedUp"
                current_archetype_class = elem.attrib.get("Class")
                self.lib_items.append(current_archetype_id)

                item_object = d_archetype_item(current_archetype_id, current_archetype_name, self.filename.lower(), current_archetype_class)
                if "wd3" not in item_object.filename:
                    item_object.is_legal = False
                if "prototype_mtl" in item_object.filename or "metrics" in item_object.filename or "mapicons" in item_object.filename or "lighting_" in item_object.filename or "gameplay.xml" in item_object.filename:
                    item_object.is_legal = True
                self.lib_items_objects.append(item_object)
                self.subitems.add(item_object)
                
                for sub_elem in elem.iter():
                    item_object.add_dependencies_from_element(sub_elem)
                
            elif elem.tag == "Entity":
                wlucat = elem.attrib.get("wlucatLoadingUnitCategoryV3")


                #SKIPS OVER DERIVATIONS!!!!!!!!!!!!!!

                if item_object is not None:
                    if wlucat is None:
                        item_object.wlu_category = previous_wlucat #Sir, you are a derivation, use preious legit wlucat
                    else:
                        item_object.wlu_category = wlucat.lower()
                        previous_wlucat = wlucat.lower()

            elif elem.tag == "Components":
                for comp in elem:
                    item_object.components.add(comp.tag)

            elif "GraphicComponent" in elem.tag:
                filemodel = elem.attrib.get("fileModel")
                if filemodel is not None and item_object is not None:
                    #item_object.models.append(filemodel.lower())
                    item_object.model = filemodel.lower()
                    item_object.add_dependency(filemodel)

            elif elem.tag == "CFileDescriptorComponent" and item_object.file_descriptor == "None":
                item_object.file_descriptor = elem.attrib.get("fileName")
                
            elif elem.tag == "CBreakablePhysComponent":
                navmesh_multistate = elem.attrib.get("bUseNavmeshMultistate")
                if navmesh_multistate is not None and item_object is not None:
                    if navmesh_multistate == "1":
                        item_object.is_multistate = True
                        
            elif elem.tag == "CStaticPhysComponent":
                flag = elem.get("bUsedForFootIK","")
                if flag == "1":
                    item_object.is_used_for_foot_ik = True
                    
            elif elem.tag == "CSimpleAnimationComponent":
                item_object.has_animated_component = True

    def get_archetype_derivations(self):
        for obj in self.lib_items_objects:
            self.archetype_derivations_dict[obj.name] = obj

        for name, obj in self.archetype_derivations_dict.iteritems():
            tokens = name.split('.')
            if len(tokens) <= 2:
                continue
            parent_name = '.'.join(tokens[:-1])
            obj.parent_archetype = self.archetype_derivations_dict.get(parent_name)

        def get_archetype_recursively(current_object, components, dependencies):
            for component in current_object.components:
                components.append(component)
            for dependency in current_object.dependencies:
                dependencies.append(dependency)
            if current_object.parent_archetype is None:
                return
            get_archetype_recursively(current_object.parent_archetype, components, dependencies)

        for obj in self.lib_items_objects:
            component_list = list(obj.components)
            dependencies_list = (list(obj.dependencies))
            get_archetype_recursively(obj, component_list, dependencies_list)
            obj.components = set(component_list)
            dependencies_set = set(dependencies_list)
            obj.dependencies = dependencies_set

        
class d_archetype_item(d_object):
    def __init__(self, archetype_guid, archetype_name, library_file, archetype_class):
        super(d_archetype_item, self).__init__()
        self.type = "Archetype"
        self.guid = archetype_guid
        self.name = archetype_name
        self.filename = library_file
        self.parent_library = library_file
        self.file_descriptor = "None"
        self.model = "None"
        self.is_multistate = False
        self.has_animated_component = False
        self.archetype_class = archetype_class
        self.is_used_for_foot_ik = False

        self.wlu_category = "None"
        '''
        WLU categories:
        world   0
        faraway 1
        far     2
        near    3
        quality 4
        interior5
        hma     6
        sas     7
        lma     10
        mis     11
        invalid 15
        '''

        self.components = set()
        self.loading_cost = None
        self.parent_archetype = None  # This is to support archetype derivations
        self.identifier = self.guid.lower()

class d_prefab_lib(d_object):
    def __init__(self, prefab_lib_file):
        super(d_prefab_lib, self).__init__()
        self.type = "Prefab Library"
        self.filename = prefab_lib_file
        self.name = "DATA MISSING"
        #self.lib_items = {}
        #self.lib_items = []
        self.lib_items_objects = []
        #self.entities = []
        self.get_lib_items(prefab_lib_file)

        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative

    def get_lib_items(self, prefab_lib_file):
        tree = ET.ElementTree(file=prefab_lib_file)
        for prefab_lib in tree.iter("PrefabLibrary"):
            self.name = prefab_lib.attrib.get("Name")
            is_split_library = int(prefab_lib.attrib.get("SplitLibrary","0"))
            
            if is_split_library:
                split_items_path = self.filename.replace(".xml", "")
                lib_item_files = get_files(split_items_path, ".xml", "")
                for item_file in lib_item_files:
                    item_tree = ET.ElementTree(file=item_file)
                    for prefab in item_tree.iter("Prefab"):
                        self.parse_prefab(prefab)
                return
            
            else:
                for prefab in prefab_lib.iter("Prefab"):
                    self.parse_prefab(prefab)
            
    def parse_prefab(self, prefab):
        current_prefab_id = prefab.attrib.get("Id").lower()
        current_prefab_name = prefab.attrib.get("Name")
        #self.lib_items[current_prefab_id, current_prefab_name] = []
        new_lib_item_object = d_prefab_item(current_prefab_id, current_prefab_name, self.filename)
        self.add_dependency(new_lib_item_object.identifier)
        self.lib_items_objects.append(new_lib_item_object)
        self.subitems.add(new_lib_item_object)

        for elem in prefab.iter('Object'):
            type = elem.get("Type", None)
            if type is None:
                continue
            new_entity = d_prefab_entity()
            
            new_entity.add_dependencies_from_element(elem)
            
            new_entity.filename = self.filename
            new_lib_item_object.entities.append(new_entity)
            new_lib_item_object.subitems.add(new_entity)
            new_entity.guid = elem.get("Id", "None")
            new_entity.set_identifier()
            new_lib_item_object.add_dependency(new_entity.identifier)
            new_entity.name = elem.get("Name", "I don't have a name")
            #new_entity.world_layer_type = self.world_layer_type
            new_entity.get_position(elem.get("WorldPos", "0,0,0"))
            new_entity.get_rotation(elem.get("Angles", "None"))
            new_entity.set_scale(elem.get("Scale", "None"))

            new_entity.entity_type = type

            if type != 'PrototypeEntity' and type != 'Prefab':
                for components in elem.iter("Components"):
                    for comp in components:
                        new_entity.components.add(comp.tag)

            if type == "BatchedObject":
                old_reference = elem.get("FileName") # wd1 style reference in world layers
                if old_reference is not None:
                    new_entity.resource = old_reference
                for child in elem.iter():
                    class_name = child.get("hid_DTCTH_ClassName", "")
                    if class_name == "CGraphicBatchModel":
                        new_entity.resource = child.get("fileModel", "").lower()
                    elif class_name == "CParticlesBatchModel":
                        new_entity.resource = child.get("psParticleSystem", "").lower()
                    elif class_name == "CArchetypeBatchModel":
                        new_entity.resource = child.get("archArchetype", "").lower()
                    elif class_name == "CSimplePrimitiveBatchModel":
                        new_entity.is_primitive = True
                    elif class_name == "CSoundPointBatchModel":
                        new_entity.is_soundpoint = True
            elif type == "Prefab":
                new_entity.resource = elem.get("PrefabGUID", "None").lower()
            elif type == "Proxy":
                new_entity.resource = elem.get("SubType", "None").lower()
            elif type == "CityLifeObject":
                cloID = get_cloID(elem)
                new_entity.add_dependency(cloID)
            elif type == "Building":
                get_building_properties(new_entity, elem)
            elif type == "Entity" or type == "PrototypeEntity":
                new_entity.entity_class = elem.get("EntityClass", "")
                current_prototype = elem.get("Prototype","")
                new_entity.add_dependency(current_prototype)
                for sub_elem in elem.iter("CGraphicComponent"):
                    new_entity.add_dependency(sub_elem.get("fileModel", ""))

                for sub_elem in elem.iter("Entity"):
                    if sub_elem.get("wlucatLoadingUnitCategoryV3", "") is not None:
                        new_entity.wlu_category = sub_elem.get("wlucatLoadingUnitCategoryV3", "")

            elif type == "Plaza":
                vertex_list = []
                for sub_elem in elem.iter():
                    if sub_elem.tag == "Corner":
                        values = sub_elem.get("vecCornerPos", "")
                        values_list = values.split(",")
                        float_values_list = [float(val) for val in values_list]
                        vertex_list.append(float_values_list)
                    elif sub_elem.tag == "Roof":
                        new_entity.plaza_roof_material = sub_elem.get("selMaterialBank", "")
                    elif sub_elem.tag == "Footing":
                        new_entity.plaza_footing_material = sub_elem.get("selMaterialBank", "")
                    elif sub_elem.tag == "Shape":
                        spline_loft_element_id = sub_elem.get("splineloftLoftElement", "")
                        new_entity.add_dependency(spline_loft_element_id)

                try:
                    min_x = vertex_list[0][0]
                    max_x = vertex_list[0][0]
                    min_y = vertex_list[0][1]
                    max_y = vertex_list[0][1]
                    
                    for vertex in vertex_list:
                        if vertex[0] < min_x:
                            min_x = vertex[0]
                        if vertex[0] > max_x:
                            max_x = vertex[0]
                        if vertex[1] < min_y:
                            min_y = vertex[1]
                        if vertex[1] > max_y:
                            max_y = vertex[1]

                    width = max_x - min_x
                    height = max_y - min_y
                    area = width * height
                    new_entity.shape_area = area
                except:
                    print elem.get("Id") + " on " + world_layer_file + " is a plaza with no corners. DELETE IT!"
                    
                new_entity.special_info = (str(new_entity.shape_area)+str(new_entity.plaza_roof_material)+str(new_entity.plaza_footing_material))
        
            new_entity.add_dependency(new_entity.resource)
        
        
class d_prefab_item(d_object):
    def __init__(self, prefab_guid, prefab_name, library_file):
        super(d_prefab_item, self).__init__()
        self.type = "Prefab"
        self.guid = prefab_guid
        self.name = prefab_name
        self.filename = library_file
        self.parent_library = library_file
        self.entities = []

        self.identifier = self.guid.lower()

class d_prefab_entity(d_object):
    def __init__(self):
        super(d_prefab_entity, self).__init__()

        self.type = "Prefab Entity"
        self.guid = ""
        self.entity_type = ""
        self.entity_class = ""
        self.world_layer_type = ""
        #self.world_size = world_size
        self.resource = ""
        self.dependencies_compiled_size = 0
        self.is_primitive = False
        self.is_soundpoint = False
        self.is_localcubemap = False
        self.kits = []        
        self.building_elements = []        
        self.building_height = 0
        self.building_volume = 0
        self.building_radius = 0
        self.building_ideal_killdistance = 0
        self.building_ideal_WLU = "FarAway"
        self.building_current_WLU = "FarAway"
        self.building_edges_distance = []
        self.building_floor_count = 0
        self.building_surface_area = 0
        self.building_facade_count = 0
        self.building_facade_ratio = 0
        self.building_roof_material = None
        self.shape_area = None        
        self.plaza_roof_material = None
        self.plaza_footing_material = None        
        self.position = None
        self.rotation = None
        self.scale = None
        self.stream_optimizer_remove_gain = 0
        #self.game_map_zones_image = game_map_zones_image
        #self.zones_dict = zones_dict
        self.region = 0
        self.points = None
        self.identifier = None

        self.wlu_category = "None"
        '''
        WLU categories:
        world   0
        faraway 1
        far     2
        near    3
        quality 4
        interior5
        hma     6
        sas     7
        lma     10
        mis     11
        invalid 15
        '''
      
        self.components = set()
        self.loading_cost = None

    def get_position(self, position=None):
        if position is not None:
            self.position = tuple(position.split(','))
        else:
            self.position = (0, 0, 0)

    def get_rotation(self, rotation=None):
        if rotation is not None:
            self.rotation = tuple(rotation.split(','))
        else:
            self.rotation = (0, 0, 0)

    def set_scale(self, scale=None):
        if scale is not None:
            self.scale = tuple(scale.split(','))
        else:
            self.scale = (0, 0, 0)

    def set_identifier(self):
        self.identifier = self.guid.lower()
        
class d_building_facade_prefab_lib(d_object):
    def __init__(self, building_facade_prefab_lib_file):
        super(d_building_facade_prefab_lib, self).__init__()
        self.type = "Building Facade Prefab Library"
        self.filename = building_facade_prefab_lib_file
        self.name = "DATA MISSING"
        self.points = 100
        self.group = None
        self.lib_items_objects = []    
        self.parse_lib()
        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative
        
    def parse_lib(self):
        tree = ET.ElementTree(file=self.filename)
        for elem in tree.iter():
            if elem.tag == "BuildingFacadeLibrary":
                self.name = elem.attrib.get("Name")
                break
        
        for bf in tree.iter("BuildingFacade"):
            new_bfpi_obj = d_building_facade_prefab_item(bf.attrib.get("Id"), bf.attrib.get("Name"), self.filename)
            new_bfpi_obj.add_dependencies_from_element(bf)
            new_bfpi_obj.parent_object = self
            self.lib_items_objects.append(new_bfpi_obj)
            self.add_dependency(new_bfpi_obj.identifier)
        

class d_building_facade_prefab_item(d_object):
    def __init__(self, prefab_guid, prefab_name, library_file):
        super(d_building_facade_prefab_item, self).__init__()
        self.type = "Building Facade Prefab Item"
        self.guid = prefab_guid
        self.name = prefab_name
        self.filename = library_file
        self.parent_library = library_file
        self.parent_object = None
        
        self.identifier = self.guid.lower()
                
class d_layer_brushes(d_object):
    def __init__(self, layer_brushes_file):
        super(d_layer_brushes, self).__init__()
        self.type = "Layer Brushes"
        self.filename = layer_brushes_file
        self.name = splitext(basename(layer_brushes_file))[0]
        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative
                
class d_brush_lib(d_object):
    def __init__(self, brush_lib_file):
        super(d_brush_lib, self).__init__()
        self.type = "Brush Library"
        self.filename = brush_lib_file
        self.name = splitext(basename(brush_lib_file))[0]
        self.items = []
        self.get_lib_items()

        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative
        
    def get_lib_items(self):
        tree = ET.ElementTree(file=self.filename)
        for elem in tree.iter():
            if elem.tag == "brush":
                new_item_obj = d_brush_item()
                for subelem in elem.iter():
                    if subelem.tag == "Resource":
                        new_item_obj.add_dependency(subelem.attrib.get("collectionResourceId"))
                new_item_obj.parent_library = self.filename
                new_item_obj.filename = self.filename
                new_item_obj.name = elem.attrib.get("name")
                new_item_obj.guid = elem.attrib.get("current_guid").lower()
                new_item_obj.identifier = new_item_obj.guid
                self.items.append(new_item_obj)
        

class d_brush_item(d_object):
    def __init__(self):
        super(d_brush_item, self).__init__()
        self.type = "Brush Item"
        self.guid = ""
        self.name = ""
        self.parent_library = ""
              
class d_collection_resources_lib(d_object):
    def __init__(self, collection_resources_lib_file):
        super(d_collection_resources_lib, self).__init__()
        self.type = "Collection Resources Library"
        self.filename = collection_resources_lib_file
        self.name = splitext(basename(collection_resources_lib_file))[0]
        self.items = []
        self.get_lib_items()

        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative
        
        self.dependencies = self.items
        
    def get_lib_items(self):
        tree = ET.ElementTree(file=self.filename)
        for elem in tree.iter():
            if elem.tag == "ChildItem":
                new_item_obj = d_collection_resources_item()
                new_item_obj.parent_library = self.filename
                new_item_obj.filename = self.filename
                new_item_obj.name = elem.attrib.get("disName")
                new_item_obj.collection_resource_id = elem.attrib.get("hidId")
                new_item_obj.identifier = new_item_obj.collection_resource_id
                
                for subelem in elem.iter():
                    if subelem.tag == "BatchModelProperties":
                        filemodel = subelem.attrib.get("fileModel")
                        new_item_obj.add_dependency(filemodel)
                        filetree = subelem.attrib.get("fileTree")
                        if filetree is not None:
                            filetree = filetree.replace(".tree.bin","")
                            new_item_obj.add_dependency(filetree)
                
                self.items.append(new_item_obj)
        

class d_collection_resources_item(d_object):
    def __init__(self):
        super(d_collection_resources_item, self).__init__()
        self.type = "Collection Resources Item"
        self.collection_resource_id = ""
        self.name = ""
        self.parent_library = ""
 
class d_particle_emi_lib(d_object):
    def __init__(self, particle_emi_lib_file, get_extra_data=True): # Now we use the DB, scan extra data by default (VFX-Ray)
        super(d_particle_emi_lib, self).__init__()
        self.type = "Particle Emitter Library"
        self.filename = particle_emi_lib_file
        self.name = "DATA MISSING"
        self.lib_items = []
        self.lib_items_objects = []
        self.get_lib_items(get_extra_data)
        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative

    def get_lib_items(self, get_extra_data=False):
        tree = ET.ElementTree(file=self.filename)

        for elem in tree.iter("ParticlesEmitterLibrary"):
            self.name = elem.attrib.get("Name")
            break  # There is only one so don't waste time

        for elem in tree.iter("PartEmit"):
            current_particle_emi_id = elem.attrib.get("Id").lower()
            current_particle_emi_name = elem.attrib.get("Name")
            current_particle_emi_key = elem.attrib.get("hidKey")
            current_particle_emi_diffuse = elem.attrib.get("DiffuseTexture")
            current_particle_emi_normal = elem.attrib.get("NormalTexture")
            current_particle_emi_disto = elem.attrib.get("DistortionTexture")
            current_particle_emi_model = elem.attrib.get("Model")
            current_particle_emi_material = elem.attrib.get("Material")
            self.lib_items.append(current_particle_emi_id)

            item_object = d_particle_emi_item(current_particle_emi_id, current_particle_emi_name, current_particle_emi_key, self.filename.lower())
            self.lib_items_objects.append(item_object)
            self.subitems.add(item_object)

            if item_object is not None:
            
                item_object.add_dependency(current_particle_emi_diffuse)
                item_object.add_dependency(current_particle_emi_normal)
                item_object.add_dependency(current_particle_emi_disto)
                item_object.add_dependency(current_particle_emi_model)
                item_object.add_dependency(current_particle_emi_material)
                
                if get_extra_data:
                    params_dict = {}

                    params_dict["Filename"] = self.name, True
                    params_dict["Emittername"] = current_particle_emi_name, True
                    #params_dict["Name"] = current_emit_name

                    params_dict["Active"] = "1", False
                    params_dict["StaticSize"] = "256", False
                    params_dict["AutoStaticSize"] = "0", False

                    params_dict["NbInitPart"] = "1", False
                    params_dict["AutoEmissionRate"] = "0", False
                    params_dict["EmitDuration"] = "1", False
                    params_dict["EmitLoop"] = "1", False
                    params_dict["InterpEmit"] = "0", False

                    params_dict["TweakInitLifeTime"] = "0", False
                    params_dict["MaxEmitDist"] = "100", False
                    params_dict["FadeEmitDist"] = "75", False
                    params_dict["CameraScalingDistance"] = "0", False
                    params_dict["CameraScaling"] = "1", False

                    #EmitFlag
                    params_dict["EmitVolRadius"] = "0", False
                    params_dict["EmitVolHalfSizeX"] = "0", False
                    params_dict["EmitVolHalfSizeY"] = "0", False
                    params_dict["EmitVolHalfSizeZ"] = "0", False

                    params_dict["UniformSize"] = "1", False

                    params_dict["EmitDirAxisAngle"] = "0", False
                    params_dict["EmitDirAxisSpread"] = "0", False
                    params_dict["EmitDirPlaneAngle"] = "0", False
                    params_dict["EmitDirPlaneSpread"] = "0", False
                    params_dict["EmitDirUseEmitterVelocity"] = "0", False
                    params_dict["EmitDirUseEmitterVelocityModifier"] = "0.5", False

                    params_dict["InitGravityDir"] = "0,0,-1", False
                    params_dict["LocalGravity"] = "0", False

                    params_dict["UseWindSimulation"] = "1", False

                    params_dict["AlphaDissolve"] = "0", False
                    params_dict["AlphaTestValue"] = "0", False
                    params_dict["HDRMul"] = "1", False
                    params_dict["RandomColor"] = "0", False
                    params_dict["RandomAlpha"] = "0", False

                    params_dict["MaterialType"] = "0", False
                    params_dict["BlendType"] = "0", False
                    params_dict["DiffuseTexture"] = "graphics\gfx\_common\gfx_default.dds", False
                    params_dict["RandomMirrorU"] = "0", False
                    params_dict["RandomMirrorV"] = "0", False
                    params_dict["ParticlePivotX"] = "0", False
                    params_dict["ParticlePivotY"] = "0", False

                    params_dict["DistortionTexture"] = "graphics\gfx\_common\gfx_default.dds", False
                    params_dict["DistortionSpeedU"] = "0.25", False
                    params_dict["DistortionSpeedV"] = "0.25", False
                    params_dict["DistortionTilingU"] = "1", False
                    params_dict["DistortionTilingV"] = "1", False
                    params_dict["DistortionStrength"] = "0.005", False

                    params_dict["Model"] = "", False
                    params_dict["EnablePhysics"] = "0", False
                    params_dict["CollisionPostponementPeriod"] = "0", False
                    params_dict["PhysicsGeometry"] = "", False

                    params_dict["PartLightAffectsParticles"] = "0", False
                    params_dict["PartLightAffectsEnvironment"] = "1", False
                    params_dict["PartLightQuadraticFalloff"] = "0", False

                    params_dict["FramePerSecondVariant"] = "0", False
                    params_dict["TileCountU"] = "1", False
                    params_dict["TileCountV"] = "1", False
                    params_dict["FramePlayOnce"] = "0", False
                    params_dict["FrameRandomStart"] = "0", False
                    params_dict["BlendFrames"] = "0", False

                    params_dict["Material"] = "", False

                    params_dict["ParticleSorting"] = "0", False
                    params_dict["Soft"] = "0", False
                    params_dict["SoftRange"] = "0.5", False

                    params_dict["AffectedByLights"] = "0", False
                    params_dict["Ambient"] = "1", False
                    params_dict["AffectedByEmitterLights"] = "0", False
                    params_dict["ScreenSpaceTessellation"] = "0", False
                    params_dict["TessellationIntensity"] = "10", False
                    params_dict["OpacityCompensation"] = "0", False

                    params_dict["TextureProjection"] = "0", False
                    params_dict["AffectedBySunlight"] = "1", False
                    params_dict["PixelShadowSampling"] = "0", False
                    params_dict["Translucency"] = "0", False
                    params_dict["LightingExponent"] = "2", False

                    params_dict["TimeOfDay"] = "0", False
                    params_dict["TimeOfDayStartHour"] = "0", False
                    params_dict["TimeOfDayEndHour"] = "24", False

                    params_dict["MinWindSpeed"] = "0", False
                    params_dict["MaxWindSpeed"] = "250", False

                    params_dict["NearFade"] = "0", False
                    params_dict["VolumetricFog"] = "0", False
                    params_dict["WaterDisplacement"] = "0", False
                    params_dict["ZOffset"] = "0", False

                    params_dict["SoundEffectFile"] = "", False
                    params_dict["SoundEffectStopFile"] = "", False
                    params_dict["SoundEffectOnEveryEmit"] = "0", False
                    params_dict["SoundEffectOnEveryDeath"] = "0", False
                    params_dict["SoundUpdatePosition"] = "0", False
                    params_dict["SoundPositionOffset"] = "0,0,0", False
                    params_dict["SoundDelay"] = "0", False

                    params_dict["ConfettiSystem"] = "", False
                    params_dict["ConfettiSystemLooping"] = "0", False
                    params_dict["ConfettiSystemTextureSelection"] = "0", False
                    params_dict["ConfettiSystemParticleSize"] = "1", False
                    params_dict["ConfettiSystemBounceMultiplier"] = "1", False
                    params_dict["ConfettiSystemAirDragMultiplier"] = "1", False

                    attribs = ["Active",
                                "StaticSize",
                                "AutoStaticSize",
                                "NbInitPart",
                                "AutoEmissionRate",
                                "EmitDuration",
                                "EmitLoop",
                                "InterpEmit",
                                "TweakInitLifeTime",
                                "MaxEmitDist",
                                "FadeEmitDist",
                                "CameraScalingDistance",
                                "CameraScaling",
                                "EmitVolRadius",
                                "EmitVolHalfSizeX",
                                "EmitVolHalfSizeY",
                                "EmitVolHalfSizeZ",
                                "UniformSize",
                                "EmitDirAxisAngle",
                                "EmitDirAxisSpread",
                                "EmitDirPlaneAngle",
                                "EmitDirPlaneSpread",
                                "EmitDirUseEmitterVelocity",
                                "EmitDirUseEmitterVelocityModifier",
                                "InitGravityDir",
                                "LocalGravity",
                                "UseWindSimulation",
                                "AlphaDissolve",
                                "AlphaTestValue",
                                "HDRMul",
                                "RandomColor",
                                "RandomAlpha",
                                "MaterialType",
                                "BlendType",
                                "DiffuseTexture",
                                "RandomMirrorU",
                                "RandomMirrorV",
                                "ParticlePivotX",
                                "ParticlePivotY",
                                "DistortionTexture",
                                "DistortionSpeedU",
                                "DistortionSpeedV",
                                "DistortionTilingU",
                                "DistortionTilingV",
                                "DistortionStrength",
                                "Model",
                                "EnablePhysics",
                                "CollisionPostponementPeriod",
                                "PhysicsGeometry",
                                "PartLightAffectsParticles",
                                "PartLightAffectsEnvironment",
                                "PartLightQuadraticFalloff",
                                "FramePerSecondVariant",
                                "TileCountU",
                                "TileCountV",
                                "FramePlayOnce",
                                "FrameRandomStart",
                                "BlendFrames",
                                "Material",
                                "ParticleSorting",
                                "Soft",
                                "SoftRange",
                                "AffectedByLights",
                                "Ambient",
                                "AffectedByEmitterLights",
                                "ScreenSpaceTessellation",
                                "TessellationIntensity",
                                "OpacityCompensation",
                                "TextureProjection",
                                "AffectedBySunlight",
                                "PixelShadowSampling",
                                "Translucency",
                                "LightingExponent",
                                "TimeOfDay",
                                "TimeOfDayStartHour",
                                "TimeOfDayEndHour",
                                "MinWindSpeed",
                                "MaxWindSpeed",
                                "NearFade",
                                "VolumetricFog",
                                "WaterDisplacement",
                                "ZOffset",
                                "SoundEffectFile",
                                "SoundEffectStopFile",
                                "SoundEffectOnEveryEmit",
                                "SoundEffectOnEveryDeath",
                                "SoundUpdatePosition",
                                "SoundPositionOffset",
                                "SoundDelay",
                                "ConfettiSystem",
                                "ConfettiSystemLooping",
                                "ConfettiSystemTextureSelection",
                                "ConfettiSystemParticleSize",
                                "ConfettiSystemBounceMultiplier",
                                "ConfettiSystemAirDragMultiplier"]

                    for i in attribs:
                        self.update_params_dict(elem, params_dict, i, i)

                    attribs_A = ["EmitRateKF", "InitLifeTimeKF", "InitSizeKF", "InitSpeedKF"]
                    attribs_B = ["InitAnglesXKF", "InitAnglesYKF", "InitAnglesZKF", "InitRotSpeedXKF", "InitRotSpeedYKF", "InitRotSpeedZKF"]
                    attribs_C = ["InitGravityIntensityKF", "InitExtSpdRatioKF", "FramePerSecondKF"]

                    for i in attribs_A:
                        for j in elem.iter(i):
                            for k in j.iter("ValueKF"):
                                temp_name = i + "ValueKF"
                                params_dict[temp_name] = "1", False
                                self.update_params_dict(k, params_dict, "Value", temp_name)
                            for k in j.iter("VariantKF"):
                                temp_name = i + "VariantKF"
                                params_dict[temp_name] = "0", False
                                self.update_params_dict(k, params_dict, "Value", temp_name)

                    for i in attribs_B:
                        for j in elem.iter(i):
                            for k in j.iter("ValueKF"):
                                temp_name = i + "ValueKF"
                                params_dict[temp_name] = "0", False
                                self.update_params_dict(k, params_dict, "Value", temp_name)
                            for k in j.iter("VariantKF"):
                                temp_name = i + "VariantKF"
                                params_dict[temp_name] = "0", False
                                self.update_params_dict(k, params_dict, "Value", temp_name)

                    for i in attribs_C:
                        for j in elem.iter(i):
                            for k in j.iter("ValueKF"):
                                temp_name = i + "ValueKF"
                                params_dict[temp_name] = "0", False
                                self.update_params_dict(k, params_dict, "Value", temp_name)
                            for k in j.iter("VariantKF"):
                                temp_name = i + "VariantKF"
                                params_dict[temp_name] = "0", False
                                self.update_params_dict(k, params_dict, "Value", temp_name)

                    attrib_emitflag = ["DirFromVolumeSurface", "Boundary", "Smooth", "Type"]
                    attrib_flag = ["Orientation", "OffsetWorldSpace=", "LocalEmitterSpace", "NoDrawUnderwater", "NoZTest", "Culling", "Censorable", "NoEmitRot"]

                    for i in elem.iter("EmitFlag"):
                        for j in attrib_emitflag:
                            params_dict[j] = "0", False
                            self.update_params_dict(i, params_dict, j, j)

                    for i in elem.iter("Flags"):
                        for j in attrib_flag:
                            params_dict[j] = "0", False
                            self.update_params_dict(i, params_dict, j, j)

                    #Derivated properties
                    params_dict["DerivedProperties"] = [], False

                    for i in elem.iter("DerivedProperties"):
                        for j in i.iter():
                            params_dict["DerivedProperties"][0].append(j.tag)

                    item_object.params_dict = params_dict
        

    def update_params_dict(self, emit, params_dict, attrib, key):
        data = emit.attrib.get(attrib)
        if data is not None:
            if data != params_dict[key][0]:
                params_dict[key] = data, True

                if key == "DiffuseTexture" or key == "DistortionTexture":
                    params_dict[key] = convert_to_path_type(data, 2), True
                    #Hack to remove invalid path "."
                    if params_dict[key][0] == ".":
                        params_dict[key] = "", False

class d_particle_emi_item(d_object):
    def __init__(self, particle_emi_guid, particle_emi_name, particle_emi_key, library_file):
        super(d_particle_emi_item, self).__init__()
        self.type = "Particle Emitter"
        self.guid = particle_emi_guid
        self.name = particle_emi_name
        self.key = particle_emi_key
        ###
        self.filename = library_file
        ###
        self.parent_library = library_file
        self.identifier = self.key  # Particle data is linked together via a "hidKey" instead of guid
        self.params_dict = {}

class d_particle_sys_lib(d_object):
    def __init__(self, particle_sys_lib_file, get_extra_data=True):
        super(d_particle_sys_lib, self).__init__()
        self.type = "Particle System Library"
        self.filename = particle_sys_lib_file
        self.name = "DATA MISSING"
        self.lib_items = []
        self.lib_items_objects = []
        self.get_lib_items(get_extra_data)
        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative

    def get_lib_items(self, get_extra_data=False):
        tree = ET.ElementTree(file=self.filename)

        for elem in tree.iter("ParticlesSystemLibrary"):
            self.name = elem.attrib.get("Name")
            break  # There is only one so don't waste time

        for elem in tree.iter("PartSys"):
            current_particle_sys_id = elem.attrib.get("Id").lower()
            current_particle_sys_name = elem.attrib.get("Name")
            current_particle_sys_key = elem.attrib.get("hidKey")  # Probably not used, even in Disrupt :O

            self.lib_items.append(current_particle_sys_id)

            item_object = d_particle_sys_item(current_particle_sys_id, current_particle_sys_name, current_particle_sys_key, self.filename.lower())
            self.lib_items_objects.append(item_object)
            self.subitems.add(item_object)

            for emit in elem.iter("PartEmit"):
                current_emit_key = emit.attrib.get("EmitterKey")
                item_object.add_dependency(current_emit_key)

                if get_extra_data:
                    current_emit_id = emit.attrib.get("Id").lower()
                    current_emit_name = emit.attrib.get("Name")
                    instance_data = {}

                    instance_data["Filename"] = self.name
                    instance_data["Systemname"] = current_particle_sys_name
                    instance_data["Name"] = current_emit_name

                    instance_data["Active"] = "0"
                    instance_data["PosOffset"] = "0,0,0"
                    instance_data["RotOffset"] = "0,0,0"
                    instance_data["StartupDelay"] = "0"

                    instance_data["ModRangeStartupDelay"] = "0"
                    instance_data["ModRangeNbParticles"] = "0"
                    instance_data["ModRangeStartupParticles"] = "0"
                    instance_data["ModRangeParticleRate"] = "0"
                    instance_data["ModRangeSpawningDuration"] = "0"
                    instance_data["ModRangeParticleLifetime"] = "0"
                    instance_data["ModRangeParticleSize"] = "0"
                    instance_data["ModRangeEmitterSizeX"] = "0"
                    instance_data["ModRangeEmitterSizeY"] = "0"
                    instance_data["ModRangeEmitterSizeZ"] = "0"
                    instance_data["ModRangeEmitterVelocity"] = "0"
                    instance_data["ModRangeParticleSpeed"] = "0"
                    instance_data["ModRangeGravity"] = "0"
                    instance_data["ModRangeExternalForces"] = "0"
                    instance_data["ModRangeParticleColorR"] = "0"
                    instance_data["ModRangeParticleColorG"] = "0"
                    instance_data["ModRangeParticleColorB"] = "0"
                    instance_data["ModRangeParticleAlpha"] = "0"
                    instance_data["ModRangeInitialRotation"] = "0"
                    instance_data["ModRangeRotationSpeed"] = "0"

                    instance_data["ModNbParticles"] = "1"
                    instance_data["ModStartupParticles"] = "1"
                    instance_data["ModParticleRate"] = "1"
                    instance_data["ModSpawningDuration"] = "1"
                    instance_data["ModParticleLifetime"] = "1"
                    instance_data["ModParticleSize"] = "1"
                    instance_data["ModEmitterSizeX"] = "1"
                    instance_data["ModEmitterSizeY"] = "1"
                    instance_data["ModEmitterSizeZ"] = "1"
                    instance_data["ModEmitterVelocity"] = "1"
                    instance_data["ModParticleSpeed"] = "1"
                    instance_data["ModGravity"] = "1"
                    instance_data["ModExternalForces"] = "1"
                    instance_data["ModParticleColorR"] = "1"
                    instance_data["ModParticleColorG"] = "1"
                    instance_data["ModParticleColorB"] = "1"
                    instance_data["ModParticleAlpha"] = "1"
                    instance_data["ModInitialRotation"] = "1"
                    instance_data["ModRotationSpeed"] = "1"

                    attribs = ["Active",
                                "PosOffset",
                                "RotOffset",
                                "StartupDelay",
                                "ModRangeStartupDelay",

                                "ModNbParticles",
                                "ModRangeNbParticles",
                                "ModStartupParticles",
                                "ModRangeStartupParticles",
                                "ModParticleRate",
                                "ModRangeParticleRate",
                                "ModSpawningDuration",
                                "ModRangeSpawningDuration",
                                "ModParticleLifetime",
                                "ModRangeParticleLifetime",
                                "ModParticleSize",
                                "ModRangeParticleSize",
                                "ModEmitterSizeX",
                                "ModRangeEmitterSizeX",
                                "ModEmitterSizeY",
                                "ModRangeEmitterSizeY",
                                "ModEmitterSizeZ",
                                "ModRangeEmitterSizeZ",
                                "ModEmitterVelocity",
                                "ModRangeEmitterVelocity",
                                "ModParticleSpeed",
                                "ModRangeParticleSpeed",
                                "ModGravity",
                                "ModRangeGravity",
                                "ModExternalForces",
                                "ModRangeExternalForces",
                                "ModParticleColorR",
                                "ModRangeParticleColorR",
                                "ModParticleColorG",
                                "ModRangeParticleColorG",
                                "ModParticleColorB",
                                "ModRangeParticleColorB",
                                "ModParticleAlpha",
                                "ModRangeParticleAlpha",
                                "ModInitialRotation",
                                "ModRangeInitialRotation",
                                "ModRotationSpeed",
                                "ModRangeRotationSpeed"]

                    for i in attribs:
                        data = emit.attrib.get(i)
                        if data is not None:
                            instance_data[i] = data

                    item_object.instance_data[current_emit_id] = instance_data
        

class d_particle_sys_item(d_object):
    def __init__(self, particle_sys_guid, particle_sys_name, particle_sys_key, library_file):
        super(d_particle_sys_item, self).__init__()
        self.type = "Particle System"
        self.guid = particle_sys_guid
        self.name = particle_sys_name
        self.key = particle_sys_key
        ###
        self.filename = library_file
        ###
        self.parent_library = library_file
        self.identifier = self.guid.lower()
        self.instance_data = {}

class d_sequence(d_object):
    def __init__(self, file):
        super(d_sequence, self).__init__()
        self.type = "Sequence"
        self.filename = file
        self.name = split(file.lower())[1].replace(".seq", "")
        self.parse_xml()
        id = convert_to_path_type(self.filename.lower(), 2)  # Relative
        self.identifier = id
        self.identifiers.add(id)
        self.identifiers.add(id.replace(".seq", ".cseq")) # references to sequences in entities is using the complied version (.cseq)
        
    def parse_xml(self):
        tree = ET.ElementTree(file=self.filename)        
        for elem in tree.iter():
            self.add_dependencies_from_element(elem)
        
class d_character_par_lib(d_object):
    def __init__(self, lib_file):
        super(d_character_par_lib, self).__init__()
        self.type = "Character Part Library"
        self.filename = lib_file
        self.name = "DATA MISSING"
        self.lib_items = []
        self.lib_items_objects = []
        self.get_lib_items()
        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative

    def get_lib_items(self):
        tree = ET.ElementTree(file=self.filename)

        for elem in tree.iter("GenericLibrary"):
            self.name = elem.attrib.get("Name")
            break  # There is only one so don't waste time

        for elem in tree.iter("Generic"):
            current_id = elem.attrib.get("Id").lower()
            current_name = elem.attrib.get("Name")
            current_key = elem.attrib.get("hidKey")
            self.lib_items.append(current_id)

            item_object = d_character_par_item(current_id, current_name, current_key, self.filename.lower())
            self.lib_items_objects.append(item_object)

            for part in elem.iter("VisualModelOverride"):
                visual_model = part.attrib.get("fileVisualModelOverride")
                item_object.add_dependency(visual_model)
        

class d_character_par_item(d_object):
    def __init__(self, guid, name, key, library_file):
        super(d_character_par_item, self).__init__()
        self.type = "Character Part"
        self.guid = guid
        self.name = name
        self.key = key
        ###
        self.filename = library_file
        ###
        self.parent_library = library_file
        self.identifier = self.key  # Character data is linked together via a "hidKey" instead of guid

class d_character_mod_lib(d_object):
    def __init__(self, lib_file):
        super(d_character_mod_lib, self).__init__()
        self.type = "Character Model Library"
        self.filename = lib_file
        self.name = "DATA MISSING"
        self.lib_items = []
        self.lib_items_objects = []
        self.get_lib_items()
        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative

    def get_lib_items(self):
        tree = ET.ElementTree(file=self.filename)

        for elem in tree.iter("GenericLibrary"):
            self.name = elem.attrib.get("Name")
            break  # There is only one so don't waste time

        for elem in tree.iter("Generic"):
            current_id = elem.attrib.get("Id").lower()
            current_name = elem.attrib.get("Name")
            current_key = elem.attrib.get("hidKey")
            self.lib_items.append(current_id)

            item_object = d_character_mod_item(current_id, current_name, current_key, self.filename.lower())
            self.lib_items_objects.append(item_object)

            for parts in elem.iter("Parts"):
                for part in parts.iter("Part"):
                    model_part = part.attrib.get("graphickitpartPart")
                    item_object.add_dependency(model_part)
        

class d_character_mod_item(d_object):
    def __init__(self, guid, name, key, library_file):
        super(d_character_mod_item, self).__init__()
        self.type = "Character Model"
        self.guid = guid
        self.name = name
        self.key = key
        ###
        self.filename = library_file
        ###
        self.parent_library = library_file
        self.identifier = self.key  # Character data is linked together via a "hidKey" instead of guid

class d_character_col_lib(d_object):
    def __init__(self, lib_file):
        super(d_character_col_lib, self).__init__()
        self.type = "Character Collection Library"
        self.filename = lib_file
        self.name = "DATA MISSING"
        self.lib_items = []
        self.lib_items_objects = []
        self.get_lib_items()
        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative

    def get_lib_items(self):
        tree = ET.ElementTree(file=self.filename)

        for elem in tree.iter("GenericLibrary"):
            self.name = elem.attrib.get("Name")
            break  # There is only one so don't waste time

        for elem in tree.iter("Generic"):
            current_id = elem.attrib.get("Id").lower()
            current_name = elem.attrib.get("Name")
            current_key = elem.attrib.get("hidKey")
            self.lib_items.append(current_id)

            item_object = d_character_col_item(current_id, current_name, current_key, self.filename.lower())
            self.lib_items_objects.append(item_object)

            for model in elem.iter("graphickitmodelModel"):
                colection_model = model.attrib.get("graphickitmodelModel")
                item_object.add_dependency(colection_model)
        

class d_character_col_item(d_object):
    def __init__(self, guid, name, key, library_file):
        super(d_character_col_item, self).__init__()
        self.type = "Character Collection"
        self.guid = guid
        self.name = name
        self.key = key
        ###
        self.filename = library_file
        ###
        self.parent_library = library_file
        self.identifier = self.guid.lower()

class d_generic_lib(d_object):
    def __init__(self, generic_lib_file):
        super(d_generic_lib, self).__init__()
        self.type = "Generic Library"
        self.filename = generic_lib_file
        self.name = "DATA MISSING"
        self.lib_type = "None"
        self.lib_items = []
        self.lib_items_objects = []
        self.get_lib_items()
        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative
        
    def isCLO(self):
        return self.lib_type in ["CLOAction", "CLOActionList", "CLOAnimalAction", "CLOAnimalActionList", "CLORobotAction"]

    def get_lib_items(self):
        tree = ET.ElementTree(file=self.filename)
        
        for elem in tree.iter("GenericLibrary"):
            self.name = elem.get("Name")
            self.lib_type = elem.get("LibType", "None")
            self.add_dependencies_from_element(elem)
        
        for elem in tree.iter("Generic"):
            if elem.get("Name",None):
                new_item = d_generic_lib_item()
                new_item.lib_type = self.lib_type
                new_item.lib_name = self.name
                new_item.nomad_object_id = elem.attrib.get("disNomadObjectId")
                new_item.identifier = new_item.nomad_object_id
                new_item.name = elem.attrib.get("Name")
                new_item.filename = self.filename
                new_item.parent_library = self.filename
                new_item.custom_id = elem.attrib.get("disId", None)
                new_item.add_dependencies_from_element(elem)
                self.lib_items_objects.append(new_item)
                self.subitems.add(new_item)
                
                for sub_elem in elem.iter("CollectionItemNode"):
                    new_collection_item = d_collection_item()
                    new_collection_item.identifier = sub_elem.attrib.get("socketitemidUniqueID")
                    new_collection_item.add_dependency(sub_elem.attrib.get("fileProxyObject"))
                    new_collection_item.name = new_collection_item.identifier
                    new_collection_item.filename = self.filename
                    new_item.add_dependency(new_collection_item.identifier)
                    new_item.collection_items.append(new_collection_item)
                    new_item.subitems.add(new_collection_item)
        

class d_generic_lib_item(d_object):
    def __init__(self):
        super(d_generic_lib_item, self).__init__()
        self.type = "Generic Item"
        self.lib_type = "None"
        self.nomad_object_id = "None"
        self.name = "None"
        self.lib_name = "None"
        self.filename = "None"
        self.parent_library = "None"
        self.resource = "None"
        self.collection_items = []
        self.custom_id = None
        
    def isCLO(self):
        return self.lib_type in ["CLOAction", "CLOActionList", "CLOAnimalAction", "CLOAnimalActionList", "CLORobotAction"]

class d_collection_item(d_object):
    def __init__(self):
        super(d_collection_item, self).__init__()
        self.type = "Collection Item"
        self.name = "None"
        self.filename = "None"

class d_markup(d_object):
    def __init__(self, markup_file):
        super(d_markup, self).__init__()
        self.type = "Markup"
        self.filename = markup_file
        self.name = split(markup_file.lower())[1].replace(".markup", "") #Keep only meat        
        self.parse_xml()        
        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative
        
    def parse_xml(self):
        tree = ET.ElementTree(file=self.filename)        
        for elem in tree.iter():
            self.add_dependencies_from_element(elem)
            

class d_geometry(d_object):
    def __init__(self, geo_xml_file, get_glm_data=False):
        super(d_geometry, self).__init__()

        self.filename = geo_xml_file
        self.name = "DATA MISSING"
        self.type = "Geometry"
        self.compiled_size = None
        self.bbox_min = []
        self.bbox_max = []
        self.lod_distances = []
        self.kill_distance = 0
        self.lod_triangle_count = {}
        self.materials = []
        self.shader_families = []
        self.default_id = "NONE"
        self.default_id_int = None
        self.models = []
        self.models_name = {}  # Maybe update self.models as a tuple instead of that
        self.source_file = "NONE"
        self.is_speedtree = False
        self.is_gamex = False
        self.is_facade = False
        self.is_lod_distances_override = False
        self.jira_issue = None
        self.jira_status = None
        self.jira_studio = None
        self.jira_loq = None
        self.jira_borough = None
        self.jira_id = None
        self.geometry_type = None
        self.interaction_type = None
        self.wlu_category = "None" #Before get_geometry_data
        self.is_pink = False
        self.has_physics = False
        # LoadingRingSizes: World, FarAway, Far, Near, MediumQuality, HighQuality, Interior, Sas, Preload, AlwaysLoaded -->
        # LoadingRingSizes = "Count(10) 0;8192;896;192;352;32;128;128;0;0;"

        self.material_slots = {}  # For drawcalls
        
        try: # try because having .gamex and .glm files at the same time will make get geometry crash because it has
            self.get_geometry_data(geo_xml_file)
        except:
            pass

        self.material_count = len(self.materials)
        self.size = len(self.material_slots)

        self.volume = 0

        if get_glm_data is not False:
            if self.is_gamex is not True:
                self.get_glm_data(geo_xml_file)
            else:
                print "Warning, can't parse .gamex file"

        if self.is_speedtree:
            tree_file = self.filename.replace("_trunk.",".tree.")
            #self.get_dependencies(tree_file)
            speedtree_identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative
            self.identifier = speedtree_identifier.replace("_trunk.xml","")
        else:
            self.identifier = self.default_id.lower()
            if self.identifier == "none":
                self.identifier = self.identifier.replace(".xml", ".glm")
                self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative
                    
    def get_compiled_size(self):
        geometry_binary_low = self.filename.replace("data", "data_win64")
        geometry_binary_low = geometry_binary_low.replace(".xml", ".xbg")
        
        geometry_binary_med = geometry_binary_low.replace(".xbg",".medium.xbgmip")
        geometry_binary_high = geometry_binary_low.replace(".xbg",".high.xbgmip")
        
        size_low = 0.0
        size_med = 0.0
        size_high = 0.0

        if isfile(geometry_binary_low):
            size_low = float(getsize(geometry_binary_low))
        
            if isfile(geometry_binary_med):
                size_med = float(getsize(geometry_binary_med))
            
            if isfile(geometry_binary_high):
                size_high = float(getsize(geometry_binary_high))
                
            self.compiled_size = float(format(float((size_low + size_med + size_high) / 1048576.0), ".3f"))
                
        else:
            # TO do: find a way to calculate the size of a geometry if there is no compiled file. Return 0.0 by default, as calling this method assumes that the size has been calculated. Keeping None would make DDV crash.
            self.compiled_size = 0.0

    def get_glm_data(self, geo_xml_file):
        geo_glm_file = geo_xml_file.replace("xml", "glm")
        if not isfile(geo_glm_file):
            return
        opened_file = open(geo_glm_file, "r")

        counter = 0
        for line in opened_file:
            if "NB_FACE" in line:
                line = line.replace("NB_FACE", "")
                self.lod_triangle_count[counter] = int(line)
                counter += 1

        opened_file.close()

    def get_geometry_data(self, geo_xml_file):
        # min = ""
        # max = ""
        tree = ET.ElementTree(file=geo_xml_file)
        for elem in tree.iter():
            if elem.tag == "primitivelod":
                self.is_lod_distances_override = int(elem.attrib.get("lod_distances_override", "0"))
            
            if elem.tag == "entities":
                self.name = elem.attrib.get("objectName")
                self.source_file = elem.attrib.get("source_file")
                if ".spm" in self.source_file: # hack to determine if mesh is a speedtree by testing the source file extensions
                    self.is_speedtree = True
                if ".gamex" in elem.attrib.get("model_file"): # hack to determine if mesh is a gamex by testing the source file extensions
                    self.is_gamex = True
            elif elem.tag == "trimesh":
                self.bbox_min = elem.attrib.get("bboxMin")
                self.bbox_max = elem.attrib.get("bboxMax")
                is_facade = elem.attrib.get("lod_atlas", None)
                if is_facade is not None:
                    self.is_facade = True
            elif elem.tag == "material":
                try:
                    # if "-m-" in elem.attrib.get("ref_shader_id").lower(): # ugly hack to find materials in gamex files, as their "name" and "ref_shader_id" are reversed
                        # if elem.attrib.get("ref_shader_id") not in self.materials:
                            # self.materials.append(elem.attrib.get("ref_shader_id").lower())
                    # if "-m-" in elem.attrib.get("name").lower(): # other part of ugly as fuck gamex hack
                        # if elem.attrib.get("name") not in self.materials:
                            # self.materials.append(elem.attrib.get("ref_shader_id").lower())
                            
                    # new better gamex hack, because FUUUUUUUUUUUUUUUUU...
                    material_reference = elem.attrib.get("ref_shader_id")#.lower()
                    relative_path = "graphics\\_materials\\"
                    material_extention = ".material.xml"
                    
                    material_reference = material_reference.replace("/","\\")
                    
                    if relative_path not in material_reference:
                        material_reference = relative_path + material_reference
                    if material_extention not in material_reference:
                        material_reference = material_reference + material_extention

                    self.add_dependency(material_reference)
                    self.materials.append(material_reference)
                    
                    if elem.attrib.get("shader_name") not in self.shader_families:
                        self.shader_families.append(elem.attrib.get("shader_name"))
                    self.material_slots[elem.attrib.get("slot_name")] = 1
                except:
                    #print "Bad Gamex? -- " + geo_xml_file
                    # .. todo:: we should track down prints and change them to "logging" statements, then remove this try/except
                    pass #Quick fix for crash when printing

                    '''
                    import smtplib
                    from email.mime.text import MIMEText

                    msg = MIMEText("patate")

                    me = "gilbert.arcand@ubisoft.com"
                    you = "gilbert.arcand@ubisoft.com"

                    msg['Subject'] = 'The contents of s'
                    msg['From'] = me
                    msg['To'] = you

                    s = smtplib.SMTP('smtp.ubisoft.com')
                    s.sendmail(me, [you], msg.as_string())
                    s.quit()
                    '''
            elif elem.tag == "GraphicModel":

                model_name = elem.attrib.get("DisplayName").lower()
                model_id = elem.attrib.get("UniqueID").lower()

                #self.models.append(elem.attrib.get("UniqueID").lower())
                self.models.append(model_id)
                self.identifiers.add(model_id)
                self.models_name[model_id] = model_name

                '''
                childs = elem.getchildren()
                for child in childs:
                    grandchilds = child.getchildren()
                    for grandchild in grandchilds:
                        if grandchild.tag == "Material":
                            self.materials.append(grandchild.attrib.get("matMaterial").replace(".bin", ".xml").lower())
                '''
                for child in elem.iter("Material"):
                    mat = child.attrib.get("matMaterial").replace(".bin", ".xml").lower()
                    self.materials.append(mat)
                    self.add_dependency(mat)

                if elem.attrib.get("IsEditable") == "0":
                    self.default_id = elem.attrib.get("UniqueID").lower()
                    self.default_id_int = int(self.default_id, 0)
            elif elem.tag == "primitivelod":
                self.lod_distances.append(elem.get("lod0", "0"))
                self.lod_distances.append(elem.get("lod1", "0"))
                self.lod_distances.append(elem.get("lod2", "0"))
                self.lod_distances.append(elem.get("lod3", "0"))
                self.lod_distances.append(elem.get("lod4", "0"))
                self.lod_distances.append(elem.get("lod5", "0"))
            elif elem.tag == "GenericInteraction":
                self.interaction_type = elem.attrib.get("GenericInteractionName")
            elif elem.tag == "ArtValidationStatus":
                status = elem.attrib.get("Code")
                if status is not None:
                    if status != "0":
                        self.is_pink = True
            elif elem.tag == "havok_primitive":
                self.has_physics = True

        for dist in self.lod_distances:
            try:
                dist = float(dist)
            except:
                dist = 0
            if dist > self.kill_distance:
                self.kill_distance = dist

            #WLU stuff
            if self.kill_distance > 192:
                self.wlu_category = "Far"
            else:
                self.wlu_category = "Near"

    def get_logic_material_ids(self, gx):
        ids_set = set()
        if self.is_gamex:
            gamex_file = self.filename.replace(".xml", ".gamex")
            if not isfile(gamex_file):
                print self.filename, "says it's a .gamex in the XML, but it's not."
                return
            with open(gamex_file, "rb") as f:
                gamex_buffer = f.read()
            dag = gx.data.DAG.FromBuffer(gamex_buffer)
            for index, dagNode in enumerate(dag):
                nodeAccessor = dagNode.GetData()
                metadata = nodeAccessor.GetSubData("logic_material_id")
                if metadata:
                    for id in metadata.GetData():
                        if id == 4294967295: # check if mesh col is setbyface
                            refID = nodeAccessor.GetSubData(gx.data.Names.Reference)
                            if refID:
                                refID = refID.GetData()
                                meshbuf = dag.GetReferenceBuffer(refID[0])
                                polyMesh = gx.data.PolyMesh.FromBytes(meshbuf)
                                material_ids = "MaterialIDs"
                                for mat_id in set(polyMesh.GetChannel(material_ids).GetElements()):
                                    ids_set.add(mat_id+1)
                        else:
                            ids_set.add(str(id))

        else:
            hki_file = self.filename.replace(".xml", ".hki")
            if not isfile(hki_file):
                print(self.filename, "is supposed to be a .glm, but it doesn't have an .hki file.")
                return
            try:
                tree = ET.ElementTree(file=hki_file)
            except:
                print(hki_file, "is invalid.")
                return
            for elem in tree.iter("logicmatid"): # from materials
                id = str(int(elem.attrib.get("value"))-1)
                ids_set.add(id)

            for elem in tree.iter("logic_mat"): # from user properties
                id = str(elem.attrib.get("value"))
                ids_set.add(id)

        return ids_set


    def get_triangle_count_per_lod_from_gamex(self, gamex_file, gx):
        with open(gamex_file, "rb") as f:
            gamex_buffer = f.read()
        lods_dict = {}
        dag = gx.data.DAG.FromBuffer(gamex_buffer)
        for index, dagNode in enumerate(dag):
            nodeAccessor = dagNode.GetData()
            metadata = nodeAccessor.GetSubData("type")
            if not metadata:
                continue
            for id in metadata.GetData():
                if "LOD" not in id:
                    continue
                refID = nodeAccessor.GetSubData(gx.data.Names.Reference)
                if not refID:
                    continue
                refID = refID.GetData()
                meshbuf = dag.GetReferenceBuffer(refID[0])
                if not meshbuf:
                    continue
                polyMesh = gx.data.PolyMesh.FromBytes(meshbuf)
                triangulation = "Triangulation"
                if id not in lods_dict.keys():
                    lods_dict[id] = 0
                lods_dict[id] += len(polyMesh.GetChannel(triangulation).GetElements())
        return lods_dict
        
    def get_geometry_type(self, gamex_file, gx):

        if not self.is_gamex:
            return
        
        gamex_file = self.filename.replace(".xml", ".gamex")
        
        if not isfile(gamex_file):
            print self.filename, "says it's a .gamex in the XML, but it's not."
            return

        with open(gamex_file, "rb") as f:
            gamex_buffer = f.read()
        dag = gx.data.DAG.FromBuffer(gamex_buffer)
        for index, dagNode in enumerate(dag):
            nodeAccessor = dagNode.GetData()
            
            # test if LODDistances exists, this will determine if we're at the right level to get the node type
            lods = nodeAccessor.GetSubData("LODDistances")       
            if not lods:
                continue
            
            type = nodeAccessor.GetSubData("type")                
            if type:
                self.geometry_type = type.GetData()[0]
                return
        
                
class d_material(d_object):
    REFERENCE_ATTRIBUTES = set([
                                "AbsorptionDistanceTexture",
                                "AbsorptionTexture",
                                "AlphaTexture",
                                "AlphaTexture1",
                                "AnimTexture1",
                                "BaseColorTexture",
                                "BaseParametersTexture1",
                                "BurntDiffuseTexture",
                                "CausticTextureArray",
                                "CeilingTexture",
                                "ClearCoatParametersTexture1",
                                "ColorMask",
                                "ColorizeTexture1",
                                "CurvatureTexture",
                                "DamageNormalMapTexture",
                                "DamageTexture",
                                "DamageTexture1",
                                "DecalTexture",
                                "DetailTexture",
                                "DetailTexture1",
                                "DetailTexture2",
                                "DetailTexture3",
                                "DetailTextureExtra1",
                                "DetailTextureExtra2",
                                "DetailTextureExtra3",
                                "DiffuseTexture",
                                "DiffuseTexture0",
                                "DiffuseTexture1",
                                "DiffuseTexture2",
                                "DiffuseTextureArray1",
                                "DiffuseTextureLayer2",
                                "DiffuseTextureTopRock",
                                "DistortionTexture",
                                "DitheringTexture",
                                "EmissiveMaskTexture",
                                "EmissiveTexture",
                                "FaceBlendDisplaceTextureArray",
                                "FakeInteriorTexture",
                                "FlowTexture",
                                "FurNormalTexture1",
                                "GlitchTexture",
                                "GradientTexture1",
                                "GrungeTexture",
                                "HairAOTexture",
                                "HairDepthTexture",
                                "HairRoughnessVariationTexture",
                                "HairTransmittanceTexture",
                                "HeightTexture1",
                                "HeightTexture2",
                                "HoloAR_NoiseTexture",
                                "HorizonTexture",
                                "LaserNoiseTexture",
                                "LaserVolumeTexture",
                                "LayerMaskNoiseTexture1",
                                "LayerMaskTexture1",
                                "MaskTexture",
                                "MaskTexture1",
                                "MaskTexture2",
                                "MaskTextureArray1",
                                "MaterialPaletteTexture",
                                "NoiseTexture1",
                                "NormalDynamicWrinklesTexture1A",
                                "NormalDynamicWrinklesTexture1B",
                                "NormalDynamicWrinklesTexture2A",
                                "NormalDynamicWrinklesTexture2B",
                                "NormalDynamicWrinklesTexture3A",
                                "NormalDynamicWrinklesTexture3B",
                                "NormalDynamicWrinklesTexture4A",
                                "NormalDynamicWrinklesTexture4B",
                                "NormalMapTexture",
                                "NormalMapTexture1",
                                "NormalTexture",
                                "NormalTexture1",
                                "NormalTexture2",
                                "NormalTextureArray1",
                                "NormalTextureTopRock",
                                "OpacityTexture",
                                "OpacityTexture1",
                                "OverlayTexture",
                                "PaletteTexture1",
                                "PatternTexture",
                                "PatternTexture1",
                                "RaindropSplashesTexture",
                                "ReflectionTexture",
                                "ScreenFX_Texture1",
                                "SpecularNoiseTexture",
                                "SpecularShiftTexture",
                                "SpecularTexture1",
                                "SurfaceParametersTexture",
                                "SurfaceTexture1",
                                "TarnishMaskTexture",
                                "ThicknessTexture",
                                "TypeTexture",
                                "VegetationLeafNoiseTexture",
                                "VegetationTrunkNoiseTexture",
                                "VideoTexture1",
                                "WaveTexture",
                                "WindLeafAnimNoiseTexture",
                                "WindowLightMaskTexture1",
                                "WindowLightVariationTexture",
                                "WorldColorTexture",
                                "WorldLightDensityTexture1",
                            ])
                            
    def __init__(self, material_xml_file):
        super(d_material, self).__init__()
        self.filename = material_xml_file
        self.type = "Material"
        self.parameters = {}
        self.name = "DATA MISSING"
        self.category = "DATA MISSING"
        self.shader = "DATA MISSING"
        self.has_bink = False
        self.subfamily = None
        self.basematerial = None
        self.textures = []
        self.get_xml(material_xml_file)
        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative

    def get_xml(self, material_xml_file):
    
        tree = ET.ElementTree(file=material_xml_file)
        for elem in tree.iter("parameter"):
            name = elem.attrib.get("name")
            value = elem.attrib.get("value")
            
            if name == "SubFamily":
                self.subfamily = value
            
            self.parameters[name] = value
            # if "_LE" in name:
                # continue
            if name not in d_material.REFERENCE_ATTRIBUTES:
                continue
            value = elem.attrib.get("value")
            self.add_dependency(value)
        
        for elem in tree.iter("category"):
            self.category = elem.text
            break
        for elem in tree.iter("name"):
            self.name = elem.text.lower()
            break
        for elem in tree.iter("shader"):
            self.shader = elem.text
            break
        for elem in tree.iter("material"):
            self.basematerial = elem.attrib.get("matBaseMaterial")
            break
        
        

class d_texture_profiles(object):
    # Class to grab all textures profiles from Disrupt TextureProfiles.xml. You need to initialize before using textures.
    def __init__(self):
        super(d_texture_profiles, self).__init__()
        #self.texture_profiles_path = '../../../../../data/engine/shaders/TextureProfiles.xml'
        cur_path = os.path.dirname(os.path.abspath(__file__))
        cur_path = cur_path.replace(r"td_tools\PythonTools\DDV","")
        self.texture_profiles_path = cur_path + r"/data/engine/shaders/TextureProfiles.xml"
        self.texture_profiles_dict = self.get_textureprofiles_dict(self.texture_profiles_path)

    def _get_attrib(self, child, child_to_find, attrib):
        try:
            if child.find(child_to_find) is not None:
                return child.find(child_to_find).attrib[attrib]
            else:
                return None
        except:
            return None

    def get_textureprofiles_dict(self, path):
        texture_profiles = {}
        texture_profiles_path = ET.parse(path)
        root = texture_profiles_path.getroot()
        for child in root:
            # Some time, name or displayname don't exist in the metadata.
            child_id = child.get('id')
            if child.tag == "profile":
                if child.get('displayname') is not None:
                    texture_profiles[child_id] = {'name': child.get('displayname')}
                else:
                    texture_profiles[child_id] = {'name': child.get('name')}  # child.get('name')

                # mipmap
                texture_profiles[child_id]['mipmap'] = self._get_attrib(child, 'mipmap', 'type')
                texture_profiles[child_id]['mip_filtering'] = self._get_attrib(child, 'mipmap', 'filtering')
                texture_profiles[child_id]['mip_sharpening'] = self._get_attrib(child, 'mipmap', 'sharpening')
                texture_profiles[child_id]['mip_disableskipmips'] = self._get_attrib(child, 'mipmap', 'disableskipmips')
                texture_profiles[child_id]['mip_fade_mipstart'] = self._get_attrib(child, 'mipmap/fade', 'mipstart')
                texture_profiles[child_id]['mip_fade_blending'] = self._get_attrib(child, 'mipmap/fade', 'blending')
                # descriptions
                texture_profiles[child_id]['desc_image'] = self._get_attrib(child, 'description/image', 'type')
                texture_profiles[child_id]['desc_color'] = self._get_attrib(child, 'description/color', 'type')
                texture_profiles[child_id]['desc_alpha_type'] = self._get_attrib(child, 'description/alpha', 'type')
                texture_profiles[child_id]['desc_alpha_val'] = self._get_attrib(child, 'description/alpha', 'values')
                texture_profiles[child_id]['desc_colorspace'] = self._get_attrib(child, 'description/colorspace',
                                                                                 'type')
                texture_profiles[child_id]['desc_premultiplyalpha'] = self._get_attrib(child,
                                                                                       'description/premultiplyalpha',
                                                                                       'enabled')
                texture_profiles[child_id]['desc_renormalize'] = self._get_attrib(child, 'description/renormalize',
                                                                                  'enabled')
                texture_profiles[child_id]['desc_bordercolor_enabled'] = self._get_attrib(child,
                                                                                          'description/bordercolor',
                                                                                          'enabled')
                texture_profiles[child_id]['desc_bordercolor_color'] = self._get_attrib(child,
                                                                                        'description/bordercolor',
                                                                                        'color')
                texture_profiles[child_id]['desc_precisionlevel'] = self._get_attrib(child,
                                                                                     'description/precisionlevel',
                                                                                     'type')  # todo add it in d_textures
                texture_profiles[child_id]['desc_normalvariance'] = self._get_attrib(child,
                                                                                     'description/normalvariance',
                                                                                     'enabled')
                texture_profiles[child_id]['desc_normaldatachannel'] = self._get_attrib(child,
                                                                                     'description/normaldatachannel',
                                                                                     'enabled') 
                texture_profiles[child_id]['desc_normalizeaverage'] = self._get_attrib(child,
                                                                                       'description/normalizeaverage',
                                                                                       'enabled')
                texture_profiles[child_id]['desc_gloss_enabled'] = self._get_attrib(child, 'description/gloss',
                                                                                    'enabled')
                texture_profiles[child_id]['desc_gloss_glossiness'] = self._get_attrib(child, 'description/gloss',
                                                                                       'glossiness')
                texture_profiles[child_id]['desc_cubemap_prefilter'] = self._get_attrib(child, 'description/prefilter',
                                                                                        'prefilter')
                texture_profiles[child_id]['desc_cubemap_cosinepower'] = self._get_attrib(child,
                                                                                          'description/cosinePower',
                                                                                          'cosinePower')
                texture_profiles[child_id]['desc_alphaToCoverageScale_enabled'] = self._get_attrib(child,
                                                                                                   'description/alphaToCoverageScale',
                                                                                                   'enabled')
                texture_profiles[child_id]['desc_alphaToCoverageScale_alphaRef'] = self._get_attrib(child,
                                                                                                    'description/alphaToCoverageScale',
                                                                                                    'alphaRef')
                texture_profiles[child_id]['desc_qualityressplittype'] = self._get_attrib(child,
                                                                                          'description/qualityressplittype',
                                                                                          'type')
                # compression
                texture_profiles[child_id]['compression_enabled'] = self._get_attrib(child, 'compression', 'enabled')
                texture_profiles[child_id]['compression_enableBC67'] = self._get_attrib(child, 'compression',
                                                                                        'enableBC67')
                texture_profiles[child_id]['compression_flagDXT35'] = self._get_attrib(child, 'compression',
                                                                                       'flagDXT35')
                texture_profiles[child_id]['compression_ignorePS3Mem'] = self._get_attrib(child, 'compression',
                                                                                          'ignorePS3Mem')
                texture_profiles[child_id]['compression_weighting'] = self._get_attrib(child, 'compression',
                                                                                       'weighting')
        return texture_profiles

    def get_name(self, profile_id):
        if str(profile_id) in self.texture_profiles_dict.keys():
            # return str(profile_id) #self.texture_profiles_dict
            return self.texture_profiles_dict[str(profile_id)]['name']
        else:
            return None

    def get_id(self, name=None):
        try:
            int(name)
            return str(name)
        except ValueError:
            for key in self.texture_profiles_dict:
                if name == self.texture_profiles_dict[str(key)]['name']:
                    return key
        return name

    def get_mipmap(self, id):
        try:
            mip = self.texture_profiles_dict[str(id)]['mipmap']
        except:
            mip = None
        return mip

    # todo for loop in dict automatically adding variables based on keys
    def get_profile_item(self, id, key):
        try:
            value = self.texture_profiles_dict[str(id)][str(key)]
        except:
            value = None
        return value


class d_texture(d_object):
    def __init__(self, png_file):
        super(d_texture, self).__init__()
        self.type = "Texture"
        self.filename = png_file
        self.name = basename(png_file)
        self.compiled_size = None
        self.get_png(png_file)
        # need to run get_texture_info to get value in thoses variables
        self.width = None
        self.height = None
        self.source_file = None
        self.profile = None
        self.profile_id = None
        self.scale_ps4 = "none"
        self.width_ps4 = None
        self.height_ps4 = None
        self.scale_xboxone = "none"
        self.width_xboxone = None
        self.height_xboxone = None
        self.scale_pc = "none"
        self.width_pc = None
        self.height_pc = None
        self.mipmap = None
        self.mip_filtering = None
        self.mip_sharpening = None
        self.mip_disableskipmips = None
        self.mip_fade_mipstart = None
        self.mip_fade_blending = None

        self.desc_image = None
        self.desc_color = None
        self.desc_alpha_type = None
        self.desc_alpha_val = None
        self.desc_colorspace = None
        self.desc_premultiplyalpha = None
        self.desc_renormalize = None
        self.desc_bordercolor_enabled = None
        self.desc_bordercolor_color = None
        self.desc_precisionlevel = None
        self.desc_normalvariance = None
        self.desc_normaldatachannel = None
        self.desc_normalizeaverage = None
        self.desc_gloss_enabled = None
        self.desc_gloss_glossiness = None
        self.desc_cubemap_prefilter = None
        self.desc_cubemap_cosinepower = None
        self.desc_alphaToCoverageScale_enabled = None
        self.desc_alphaToCoverageScale_alphaRef = None
        self.desc_qualityressplittype = None

        self.compression_enabled = None
        self.compression_enableBC67 = None
        self.compression_flagDXT35 = None
        self.compression_ignorePS3Mem = None
        self.compression_weighting = None

        self.debug_metadata = "Use get_texture_info first."

        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative
        self._platforms = {'durango': False, 'orbis': False, 'pc': False}

        self._texture_profiles = None

    def get_compiled_size(self):    
        self.get_texture_info()
        
        if self.scale_ps4 == 'none': # will be none if no metadata was found
            return
            
        # if self.desc_color is None:
            # return

        four_bpp = 0.5   # DXT1 no mips = 0.5 byte per pixel     - AKA 4bpp
        eight_bpp = 1.0   # DXT5 no mips = 1 byte per pixel       - AKA 8bpp
        thirtytwo_bpp = 4.0 # Uncompressed = 4 bytes per pixel  - AKA 32bpp
        mips_factor = 1.33333 # multiply size per pixel with this factor
        
        actual_width = self.width
        
        if self.mipmap == "Manual":
            actual_width /= 2
        
        pixels = int(actual_width / int(self.scale_ps4)) * (int(self.height) / int(self.scale_ps4))
        
        size = 0.0
        
        if self.desc_color == "ColorMap":
            if self.desc_alpha_type == "Blend":
                size = pixels * eight_bpp
            elif self.desc_precisionlevel == "High":
                size = pixels * eight_bpp
            elif self.desc_precisionlevel == "Uncompressed":
                size = pixels * thirtytwo_bpp                
            else:
                size = pixels * four_bpp
        elif self.desc_color == "NormalMap":
            if self.desc_precisionlevel == "Default":
                size = pixels * eight_bpp
            elif self.desc_precisionlevel == "Uncompressed":
                size = pixels * thirtytwo_bpp   
            elif self.desc_normalvariance == "1":
                size = pixels * eight_bpp
            elif self.desc_normaldatachannel == "1":
                size = pixels * eight_bpp
            else:
                size = pixels * four_bpp
        elif self.desc_color == "Grayscale":
            size = pixels * four_bpp
        elif self.desc_color == "RG":
            size = pixels * eight_bpp
            
        elif self.desc_precisionlevel == "Uncompressed":
            size = pixels * thirtytwo_bpp

        # elif "4bpp" in self.profile:
            # size = pixels * four_bpp
            
        # elif "8bpp" in self.profile:
            # size = pixels * eight_bpp
            
        # elif "32bpp" in self.profile:
            # size = pixels * thirtytwo_bpp
        
        else:
            size = pixels * four_bpp

        if self.mipmap != "None":
            size *= mips_factor

        self.compiled_size = float(format(float(size / 1048576.0), ".3f"))
            
    def get_png(self, png_file):
        self.name = splitext(basename(png_file))[0]

    def _get_scaled_size(self, value, operation=""):
        if operation is not None:
            if operation == 'scale':
                if value != "0":
                    width = self.width / int(value)
                    height = self.height / int(value)
                    size = {'width': width, 'height': height};
            elif operation == 'fixed':
                # todo may need to make sure that the height value is scaled to keep ratio
                width = value
                height = value
                size = {'width': width, 'height': height};
            else:  # No operations should be done
                size = {'width': self.width, 'height': self.height};
        else:
            size = {'width': self.width, 'height': self.height};
        return size

    def _get_scaling_property_value(self, property):
        '''

        :param property: Should be in the format 2x resolution
        :return: only the int from your property
        '''
        value = property.replace("x resolution", "")
        return int(value)

    def _set_texture_settings_from_profile(self, profile_id):
        """
        To set variables of the d_textures with the param coming from the file TextureProfiles.xml
        :param profile_id:
        :return:
        """
        # todo place all thoses variables in dictionnary
        self.mipmap = self._texture_profiles.get_profile_item(profile_id, 'mipmap')
        self.mip_filtering = self._texture_profiles.get_profile_item(profile_id, 'mip_filtering')
        self.mip_sharpening = self._texture_profiles.get_profile_item(profile_id, 'mip_sharpening')
        self.mip_disableskipmips = self._texture_profiles.get_profile_item(profile_id, 'mip_disableskipmips')
        self.mip_fade_mipstart = self._texture_profiles.get_profile_item(profile_id, 'mip_fade_mipstart')
        self.mip_fade_blending = self._texture_profiles.get_profile_item(profile_id, 'mip_fade_blending')

        self.desc_image = self._texture_profiles.get_profile_item(profile_id, 'image')
        self.desc_color = self._texture_profiles.get_profile_item(profile_id, 'desc_color')
        self.desc_alpha_type = self._texture_profiles.get_profile_item(profile_id, 'desc_alpha_type')
        self.desc_alpha_val = self._texture_profiles.get_profile_item(profile_id, 'desc_alpha_val')
        self.desc_colorspace = self._texture_profiles.get_profile_item(profile_id, 'desc_colorspace')
        self.desc_premultiplyalpha = self._texture_profiles.get_profile_item(profile_id, 'desc_premultiplyalpha')
        self.desc_renormalize = self._texture_profiles.get_profile_item(profile_id, 'desc_renormalize')
        self.desc_bordercolor_enabled = self._texture_profiles.get_profile_item(profile_id, 'desc_bordercolor_enabled')
        self.desc_bordercolor_color = self._texture_profiles.get_profile_item(profile_id, 'desc_bordercolor_color')
        self.desc_precisionlevel = self._texture_profiles.get_profile_item(profile_id, 'desc_precisionlevel')
        self.desc_normalvariance = self._texture_profiles.get_profile_item(profile_id, 'desc_normalvariance')
        self.desc_normaldatachannel = self._texture_profiles.get_profile_item(profile_id, 'desc_normaldatachannel')
        self.desc_normalizeaverage = self._texture_profiles.get_profile_item(profile_id, 'desc_normalizeaverage')
        self.desc_gloss_enabled = self._texture_profiles.get_profile_item(profile_id, 'desc_gloss_enabled')
        self.desc_gloss_glossiness = self._texture_profiles.get_profile_item(profile_id, 'desc_gloss_glossiness')
        self.desc_cubemap_prefilter = self._texture_profiles.get_profile_item(profile_id, 'desc_cubemap_prefilter')
        self.desc_cubemap_cosinepower = self._texture_profiles.get_profile_item(profile_id, 'desc_cubemap_cosinepower')
        self.desc_alphaToCoverageScale_enabled = self._texture_profiles.get_profile_item(profile_id,
                                                                                         'desc_alphaToCoverageScale_enabled')
        self.desc_alphaToCoverageScale_alphaRef = self._texture_profiles.get_profile_item(profile_id,
                                                                                          'desc_alphaToCoverageScale_alphaRef')
        self.desc_qualityressplittype = self._texture_profiles.get_profile_item(profile_id, 'desc_qualityressplittype')

        self.compression_enabled = self._texture_profiles.get_profile_item(profile_id, 'compression_enabled')
        self.compression_enableBC67 = self._texture_profiles.get_profile_item(profile_id, 'compression_enableBC67')
        self.compression_flagDXT35 = self._texture_profiles.get_profile_item(profile_id, 'compression_flagDXT35')
        self.compression_ignorePS3Mem = self._texture_profiles.get_profile_item(profile_id, 'compression_ignorePS3Mem')
        self.compression_weighting = self._texture_profiles.get_profile_item(profile_id, 'compression_weighting')

    def get_texture_info(self):  # This method will fetch the nomad metadata in the png file.
        # As we can get false textures with no metadata or png from world folder like following file
        #    y:\main\data\worlds\gym-buc-alexandra\terrain\uv\00_00.png
        # just do a try on the file for now until the .png become .uv files
        currpng = Image.open(self.filename)
        currinfo = currpng.info
        self.debug_metadata = currinfo

        self.width = currpng.size[0]
        self.height = currpng.size[1]

        ''' Always starting with nomadPNGMetadata'''
        for key, value in currinfo.items():
            if key == "nomadPNGMetadata":
                pngmetadata = ET.fromstring(value)

                '''
                Getting the profile name based on 2 different way to read it from meta
                    <settings database="TextureProfiles.xml" profile="ColorMap AlphaBlend">
                    <settings profileid="2">
                '''
                for attrib in pngmetadata.attrib.items():
                    if 'profileid' in attrib[0]:
                        self.profile = self._texture_profiles.get_name(attrib[1])
                        self.profile_id = attrib[1]
                        break
                    elif 'profile' in attrib[0]:
                        self.profile = attrib[1]
                        self.profile_id = self._texture_profiles.get_id(self.profile)
                        break
                    else:
                        self.profile = ""
                        self.profile_id = self._texture_profiles.get_id(self.profile)
                '''End of getting the profile'''

                '''Filling all texture variables with informations from texture profiles'''
                self._set_texture_settings_from_profile(self.profile_id)

                '''
                Getting scaling of a texture based on different metadata that we can
                Sadly get in png.
                '''
                myscaling = 1
                property_found = None
                myscaling_operation = None

                # Adding default texture value to the profile
                self.scale_ps4 = 1
                self.width_ps4 = self.width
                self.height_ps4 = self.height
                self.scale_xboxone = 1
                self.width_xboxone = self.width
                self.height_xboxone = self.height
                self.scale_pc = 1
                self.width_pc = self.width
                self.height_pc = self.height

                '''Getting scaling if passed in property'''
                for child in pngmetadata:
                    myscaling = 1
                    myscaling_operation = None
                    property_found = None
                    try:
                        if pngmetadata.find('property').text:
                            myscaling_operation = 'scale'
                            pngproperty = pngmetadata.find('property').text
                            myscaling = self._get_scaling_property_value(pngproperty)
                            property_found = True
                    except:
                        pass
                    if child.tag == 'override':
                        for overr_i in child:
                            if overr_i.tag == "profile":
                                for prof_item in overr_i:
                                    if prof_item.tag == "description":
                                        for desc_item in prof_item:
                                            if desc_item.tag == 'image' and desc_item.get('type') is not None:
                                                self.desc_image = desc_item.get('type')
                                            if desc_item.tag == 'color' and desc_item.get('type') is not None:
                                                self.desc_color = desc_item.get('type')
                                            if desc_item.tag == 'alpha':
                                                if desc_item.get('type') is not None:
                                                    self.desc_alpha_type = desc_item.get('type')
                                                if desc_item.get('values') is not None:
                                                    self.desc_alpha_val = desc_item.get('values')
                                            if desc_item.tag == 'colorspace' and desc_item.get('type') is not None:
                                                self.desc_colorspace = desc_item.get('type')
                                            if desc_item.tag == 'premultiplyalpha' and desc_item.get(
                                                    'enabled') is not None:
                                                self.desc_premultiplyalpha = desc_item.get('enabled')
                                            if desc_item.tag == 'renormalize' and desc_item.get('enabled') is not None:
                                                self.desc_renormalize = desc_item.get('enabled')
                                            if desc_item.tag == 'bordercolor':
                                                if desc_item.get('enabled') is not None:
                                                    self.desc_bordercolor_enabled = desc_item.get('enabled')
                                                if desc_item.get('color') is not None:
                                                    self.desc_bordercolor_color = desc_item.get('color')
                                            if desc_item.tag == 'precisionlevel' and desc_item.get('type') is not None:
                                                self.desc_precisionlevel = desc_item.get('type')
                                            if desc_item.tag == 'normalvariance' and desc_item.get('enabled') is not None:
                                                self.desc_normalvariance = desc_item.get('enabled')
                                            if desc_item.tag == 'normaldatachannel' and desc_item.get('enabled') is not None:
                                                self.desc_normaldatachannel = desc_item.get('enabled')
                                            if desc_item.tag == 'normalizeaverage' and desc_item.get(
                                                    'enabled') is not None:
                                                self.desc_normalizeaverage = desc_item.get('enabled')
                                            if desc_item.tag == 'gloss':
                                                if desc_item.get('enabled') is not None:
                                                    self.desc_gloss_enabled = desc_item.get('enabled')
                                                if desc_item.get('glossiness') is not None:
                                                    self.desc_gloss_glossiness = desc_item.get('glossiness')
                                            if desc_item.tag == 'cubemap':
                                                if desc_item.get('prefilter') is not None:
                                                    self.desc_cubemap_prefilter = desc_item.get('prefilter')
                                                if desc_item.get('cosinePower') is not None:
                                                    self.desc_cubemap_cosinepower = desc_item.get('cosinePower')
                                            if desc_item.tag == 'alphaToCoverageScale':
                                                if desc_item.get('enabled') is not None:
                                                    self.desc_alphaToCoverageScale_enabled = desc_item.get('enabled')
                                                if desc_item.get('alphaRef') is not None:
                                                    self.desc_alphaToCoverageScale_alphaRef = desc_item.get('alphaRef')
                                            if desc_item.tag == 'qualityressplittype' and desc_item.get(
                                                    'type') is not None:
                                                self.desc_qualityressplittype = desc_item.get('type')

                                    if prof_item.tag == "compression":
                                        if prof_item.get('enabled') is not None:
                                            self.compression_enabled = prof_item.get('enabled')
                                        if prof_item.get('enableBC67') is not None:
                                            self.compression_enableBC67 = prof_item.get('enableBC67')
                                        if prof_item.get('flagDXT35') is not None:
                                            self.compression_flagDXT35 = prof_item.get('flagDXT35')
                                        if prof_item.get('ignorePS3Mem') is not None:
                                            self.compression_ignorePS3Mem = prof_item.get('ignorePS3Mem')
                                        if prof_item.get('weighting') is not None:
                                            self.compression_weighting = prof_item.get('weighting')

                                    if prof_item.tag == "mipmap":
                                        if prof_item.get('type') is not None:
                                            self.mipmap = prof_item.get('type')
                                        if prof_item.get('filtering') is not None:
                                            self.mip_filtering = prof_item.get('filtering')
                                        if prof_item.get('sharpening') is not None:
                                            self.mip_sharpening = prof_item.get('sharpening')
                                        if prof_item.get('disableskipmips') is not None:
                                            self.mip_disableskipmips = prof_item.get('disableskipmips')
                                            # for mip in prof_item:
                                            # should be able to get <fade mipstart="0" blending="0" />

                    if child.tag == 'resizeOp':
                        if child.get('platform') == 'durango':
                            try:
                                myscaling_operation = child.get('operation')
                            except:
                                myscaling_operation = None

                            if child.get('value') is None:
                                myscaling = 1
                            else:
                                myscaling = child.get('value')
                            mysize = self._get_scaled_size(myscaling, myscaling_operation)
                            self.scale_xboxone = myscaling
                            self.width_xboxone = mysize['width']
                            self.height_xboxone = mysize['height']
                            self._platforms['durango'] = True

                        if child.get('platform') == 'orbis':
                            try:
                                myscaling_operation = child.get('operation')
                            except:
                                myscaling_operation = None

                            if child.get('value') is None:
                                myscaling = 1
                            else:
                                myscaling = child.get('value')
                            mysize = self._get_scaled_size(myscaling, myscaling_operation)
                            self.scale_ps4 = myscaling
                            self.width_ps4 = mysize['width']
                            self.height_ps4 = mysize['height']
                            self._platforms['orbis'] = True

                        if child.get('platform') == 'pc':
                            try:
                                myscaling_operation = child.get('operation')
                            except:
                                myscaling_operation = None

                            if child.get('value') is None:
                                myscaling = 1
                            else:
                                myscaling = child.get('value')
                            mysize = self._get_scaled_size(myscaling, myscaling_operation)
                            self.scale_pc = myscaling
                            self.width_pc = mysize['width']
                            self.height_pc = mysize['height']
                            self._platforms['pc'] = True

                if property_found:
                    mysize = self._get_scaled_size(myscaling, myscaling_operation)
                    self.scale_xboxone = myscaling
                    self.width_xboxone = mysize['width']
                    self.height_xboxone = mysize['height']

                    self.scale_ps4 = myscaling
                    self.width_ps4 = mysize['width']
                    self.height_ps4 = mysize['height']

                    self.scale_pc = myscaling
                    self.width_pc = mysize['width']
                    self.height_pc = mysize['height']
                '''End of Getting scaling of a texture'''

            if key == "nomadPNGSource":
                self.source_file = value.lower()
            # todo implement better behavior
            if key == "dpi":
                pass
                # print("dpi founded")
            if key == "gamma":
                pass # print("gamma founded")

        ''' Override nomadPNGMetadata info is .png.meta file exists '''
        meta_file = self.filename + '.meta'
        if isfile(meta_file):
            tree = ET.ElementTree(file=meta_file)
            for resize_op in tree.iter('resizeOp'):
                if resize_op.get('platform') == 'orbis':
                    self.scale_ps4 = resize_op.get('value')
                if resize_op.get('platform') == 'durango':
                    self.scale_xboxone = resize_op.get('value')

            for settings in tree.iter('settings'):
                profile_id = settings.get('profileid')
                if profile_id is not None:
                    self.profile = self._texture_profiles.get_name(profile_id)

class d_bink(d_object):
    def __init__(self, bik_file):
        super(d_bink, self).__init__()
        self.type = "Bink"
        self.filename = bik_file
        self.name = basename(bik_file)
        self.identifier = convert_to_path_type(self.filename.lower(), 2)  # Relative

class d_sqlite_db(object):
    def __init__(self):
        super(d_sqlite_db, self).__init__()
        self.version = 17
        self.path = os.path.dirname(os.path.abspath(__file__)) + r"\resources\\"
        self.name = "DDV_Data_v" + str(self.version) + ".db"
        self.db_filename = self.path + self.name
        self.sanitize_old_db_files()
    
    def sanitize_old_db_files(self):
        db_files = get_files(self.path, ".db", "")        
        current_version = str(self.version)
        for file in db_files:
            file_version = self.get_version_from_file(file)
            if file_version != current_version:
                os.remove(file)
                
    def get_version_from_file(self, file):
        return file.replace(self.path.lower(), "").replace("ddv_data_v", "").replace(".db", "")
        
    def connect_to_db(self):
        conn = sqlite3.connect(self.db_filename)
        return conn
        
    def disconnect_from_db(self, conn):
        conn.commit()    
        conn.close()
        
    def create_tables(self, cursor):
        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS file (
                    path TEXT NOT NULL,
                    timestamp FLOAT,
                    pickle BLOB,
                    type TEXT,
                    UNIQUE (path)
                    )
               ''')
               
        cursor.execute(''' PRAGMA main.page_size = 4096 ''')
        cursor.execute(''' PRAGMA main.cache_size=10000 ''')
        cursor.execute(''' PRAGMA main.locking_mode=EXCLUSIVE ''')
        cursor.execute(''' PRAGMA main.synchronous=NORMAL ''')
        cursor.execute(''' PRAGMA main.journal_mode=WAL ''')
        cursor.execute(''' PRAGMA main.cache_size=5000 ''')
        cursor.execute(''' PRAGMA auto_vacuum = FULL ''')
        
    def get_timestamps(self, cursor):
        cursor.execute(''' SELECT path,timestamp FROM file''')
        timestamps = dict((x, y) for x, y in cursor.fetchall())
        return timestamps
        
    def check_timestamp(self, file, timestamps):            
        timestamp_in_db = timestamps.get(file)
        if timestamp_in_db is None:
            return None
        
        timestamp = os.path.getmtime(file)        
        if timestamp != timestamp_in_db:
            return False
            
        return True
        
    def delete_files(self, cursor, files_to_delete, ddv=None):
        if ddv is not None:
            ddv.update_status_bar("Deleting " + str(len(files_to_delete)) + " files")
            ddv.refresh_ui()
        query_delete_file_line = ''' DELETE FROM file WHERE path = ? '''
        cursor.executemany(query_delete_file_line, files_to_delete)
        
    def insert_files(self, cursor, files_to_insert, ddv=None):
        if ddv is not None:
            ddv.update_status_bar("Inserting " + str(len(files_to_insert)) + " files")
            ddv.refresh_ui()
        query_create_file_line = ''' INSERT INTO file(path,timestamp,pickle,type) VALUES(?,?,?,?) '''
        cursor.executemany(query_create_file_line, files_to_insert)
        
    def get_orphaned_files(self, new_files, timestamps, ddv=None):
        files_to_delete = set()
        for file in timestamps.keys():
            if file not in new_files:
                files_to_delete.add((file,))
        if ddv is not None:
            ddv.update_status_bar("Deleting " + str(len(files_to_delete)) + " orphan files")
            ddv.refresh_ui()
        return files_to_delete
    
    def update_files_in_db(self, cursor, files, timestamps, d_class, progressbar_stride, counter, ddv=None):
        files_to_delete = set()
        files_to_insert = set()
        
        for file in files:

            if ddv is not None:
                counter += 1
                if counter > progressbar_stride:
                    ddv.progressbar_update()
                    counter = 0
            
            status = self.check_timestamp(file, timestamps)
            if status == True:
                continue
            if status == False:
                files_to_delete.add((file,))

            object = d_class(file)
            
            for subitem in object.subitems:
                subitem._content = subitem.get_content("|")
                for subsubitem in subitem.subitems:
                    subsubitem._content = subsubitem.get_content("|")
            
            object._content = object.get_content("|")
            p = cPickle.dumps(object, cPickle.HIGHEST_PROTOCOL)
            files_to_insert.add((file,os.path.getmtime(file),sqlite3.Binary(p),object.type))
        
        if files_to_delete:
            self.delete_files(cursor, files_to_delete, ddv)
        if files_to_insert:
            self.insert_files(cursor, files_to_insert, ddv)

    def get_objects_from_db(self, cursor, type, objects, subitem_objects=None, subsubitem_objects=None, ddv=None):
        query = ''' SELECT pickle FROM file WHERE type = ? '''
        cursor.execute(query, (type,))
        rows = cursor.fetchall()
        if ddv is not None:
            ddv.update_status_bar("Getting " + str(len(rows)) + " " + type + " files")
            ddv.refresh_ui()
        
        for row in rows:
            if ddv is not None:
                ddv.refresh_ui()
            mat = str(row[0])
            d = cPickle.loads(mat)
            objects[d.identifier] = d
            objects[d._content] = d
            for identifier in d.identifiers:
                objects[identifier] = d

            if subitem_objects is not None: # oh oh, getting complicated
                for subitem in d.subitems:
                    subitem_objects[subitem.identifier] = subitem
                    subitem_objects[subitem._content] = subitem
                    for identifier in subitem.identifiers:
                        subitem_objects[identifier] = subitem
                        
                    if subsubitem_objects is not None: # nope, not a joke
                        for subsubitem in subitem.subitems:
                            subsubitem_objects[subsubitem.identifier] = subsubitem
                            subsubitem_objects[subsubitem._content] = subsubitem
                            for identifier in subsubitem.identifiers:
                                subsubitem_objects[identifier] = subsubitem
                
            if d.file_id is None:
                continue
            objects[d.file_id] = d