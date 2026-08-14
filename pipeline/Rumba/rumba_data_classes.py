from xml.etree.cElementTree import ElementTree, fromstring, ParseError
from Common.file_helpers import convert_to_path_type
from os.path import splitext, basename, isfile, join
from PIL import Image


class DObject:

    TYPE = 'DObject'
    MAIN_PATH = r'W:\main\data'
    DEPENDENCY_ATTRIBUTES_SET = {
        # All known attributes that can hold references.
        'filemodel',
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
        "ref_shader_id",
        "prefabguid",
        "matmaterial",
        "prototype",
        #"editorobjectsocketcollectioncollection",
        "collectionitemuniqueid",
        'hidintersection',
        "prefabprefabtospawn",
        "archarchetypetospawn",


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
        "subtype",
        "archarchetypeid",
        "matsetmaterialset",

        # WARNING list below is dangerous
        '''
        "accessidrequiredid",
        "alonespawnsettinginchasespawn",
        "alonespawnsettingoutofchasespawn",
        "animalconfiganimalconfig",
        "archanimalarchetype",
        "archarchetype",
        
        
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
        
        "matmaterialid",
        "matoverridematerial",
        
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
        
        "profilingpathpresetcustompreset",
        "progressiontagprogressiontag",
        
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
        # "editorobjectsocketcollectioncollection", # comment to break the link between BFPI and socket collection
    }

    EXPOSED_VALUES = {'name', 'type'}

    EXTENSIONS_DICT = {
        # All extensions that can be referenced files, associated with the extension that will be used in the identifier. Some of them are the same, some are not.
        ".xml": ".xml",
        ".glm": ".xml",
        ".lft": ".xml",
        ".xlf": ".xml",
        ".gamex": ".xml",
        ".rta": ".rta",
        ".xbg": ".xml",
        ".model": ".model",
        ".hkr": ".xml",
        ".hkx": ".xml",
        ".psd": ".psd",
        ".png": ".png",
        ".xbt": ".png",
        ".dds": ".png",
        ".fla": ".fla",
        ".feu": ".feu",
        ".lua": ".lua",
        ".domino": ".domino",
        ".bik": ".bik",
        ".dat": ".dat",
        ".bin": ".xml",
    }

    def __init__(self):
        super(DObject, self).__init__()
        self.type = self.TYPE
        self.name = None
        self.relatives = set()
        self.dependencies = set()
        self.identifiers = set()
        self._parents = set()
        self._children = set()
        self._search_data = tuple()

    def add_parent(self, d_object):
        self._parents.add(d_object)

    def add_child(self, d_object):
        self._children.add(d_object)

    def get_parents(self):
        return self._parents

    def get_children(self):
        return self._children

    def add_dependency(self, dependency, isRelative=False):

        if dependency is None:
            return False

        dependency = dependency.lower()

        if dependency == "none":
            return False

        if dependency == "":
            return False

        if dependency[0] == ";":  # test disabled textures
            return False

        _file, ext = splitext(dependency)
        if ext in DObject.EXTENSIONS_DICT.keys():
            dependency = convert_to_path_type(dependency, 2)  # Relative
            dependency = dependency.replace(ext, DObject.EXTENSIONS_DICT[ext])
        if isRelative: self.relatives.add(self.format_dependency(dependency))
        else: self.dependencies.add(self.format_dependency(dependency))
        return True

    def add_dependencies_from_element(self, tree):
        for elem in tree.iter():
            for key, value in elem.attrib.items():
                if key.lower() in DObject.DEPENDENCY_ATTRIBUTES_SET:
                    self.add_dependency(self.format_dependency(value))

    @staticmethod
    def format_dependency(value):
        value = value.lower()
        value = value.replace('/', '\\')
        value = value.replace('graphics\_materials\\', '')
        value = value.replace('.material.xml', '')
        value = value.replace('graphics\models\\', '')
        value = value.replace('.model', '')
        return value

    def compute_search_data(self):
        values_list = list()
        for name, value in self.__dict__.items():
            if name.startswith('_'):
                continue
            if type(value) is set:
                continue
            data = name.lower() + '=' + str(value).lower()
            values_list.append(data)
        self._search_data = tuple(values_list)


class DWorld:
    LIST_XML = join(DObject.MAIN_PATH, r'Worlds\London\Objects\list.xml')
    @staticmethod
    def get_wlu_type():
        layer_wlu_type_dict = dict()
        tree = ElementTree(file=DWorld.LIST_XML)
        for layer in tree.iter('Layer'):
            name = layer.get('aName').lower()
            if int(layer.get('bMission')):
                layer_wlu_type_dict[name] = 'Mission'
            elif int(layer.get('bInterior')):
                layer_wlu_type_dict[name] = 'Interior'
            elif int(layer.get('bHighMemoryArea')):
                layer_wlu_type_dict[name] = 'HMA'
            elif int(layer.get('bLowMemoryArea')):
                layer_wlu_type_dict[name] = 'LMA'
            else:
                layer_wlu_type_dict[name] = 'World'
        return layer_wlu_type_dict


class DWorldLayer(DObject):
    VERSION = 2
    TYPE = "World_Layer"
    IS_CONTAINER = True
    PATH_TO_FILES = join(DObject.MAIN_PATH, r'Worlds\London\Objects\User')
    EXTENSIONS = {'.xml'}
    LAYER_TYPES = DWorld.get_wlu_type()

    def __init__(self, world_layer_file):
        super().__init__()
        self.filename = world_layer_file.lower()
        self.name = convert_to_path_type(self.filename.lower(), 2)
        self.layer_type = DWorldLayer.LAYER_TYPES.get(basename(splitext(self.filename)[0]))
        self.library_objects = set()
        self.parse_xml_file(world_layer_file)
        self.identifier = convert_to_path_type(self.filename.lower(), 2)
        self.identifiers.add(self.identifier)
        self.identifiers.add(self.name)
        self.identifiers.add(self.filename)

    def parse_xml_file(self, xml_file):
        if xml_file is None:
            return
        tree = ElementTree(file=xml_file)
        for world_object in tree.iter('Object'):
            d_object = DWorldLayer.WorldObject()
            element_id = world_object.get('Id')
            if element_id is None:
                continue
            self.identifier = element_id.lower()
            self.library_objects.add(d_object)
            d_object.name = world_object.get('Name')
            if d_object.name is not None:
                d_object.name = d_object.name.lower()
            d_object.position = world_object.get('WorldPos')
            d_object.angles = world_object.get('Angles')
            d_object.entity_class = world_object.get('EntityClass')
            d_object.object_type = world_object.get('Type')
            d_object.filename = self.filename
            d_object.layer_type = self.layer_type
            d_object.identifier = world_object.get('Id').lower()
            d_object.identifiers.add(d_object.identifier)
            d_object.identifiers.add(d_object.name)
            d_object.identifiers.add(d_object.filename)
            d_object.add_dependencies_from_element(world_object)
            d_object.compute_search_data()

    class WorldObject(DObject):
        TYPE = 'World_Object'
        IS_WORLD_INSTANCE = True
        IS_CONTAINER_ELEMENT = True

        def __init__(self):
            super().__init__()


class DSplineLayer(DObject):
    VERSION = 2
    TYPE = "Spline_Layer"
    IS_CONTAINER = True
    PATH_TO_FILES = join(DObject.MAIN_PATH, r'Worlds\London\Road\Roads')
    EXTENSIONS = {'.xml'}

    def __init__(self, spline_layer_file):
        super().__init__()
        self.filename = spline_layer_file.lower()
        self.name = convert_to_path_type(self.filename.lower(), 2)
        self.library_objects = set()
        self.positions_dict = dict()
        self.parse_xml_file(spline_layer_file)
        self.identifier = convert_to_path_type(self.filename.lower(), 2)
        self.identifiers.add(self.identifier)
        self.identifiers.add(self.name)
        self.identifiers.add(self.filename)

    def parse_xml_file(self, xml_file):
        if xml_file is None:
            return
        tree = ElementTree(file=xml_file)

        for splines in tree.iter("Splines"):
            for spline in splines.iter('Spline'):
                d_object_spline = DSplineLayer.DSpline()
                self.library_objects.add(d_object_spline)
                d_object_spline.identifier = spline.attrib.get('hidGuid').lower()
                d_object_spline.name = spline.attrib.get('aName').lower()
                d_object_spline.filename = self.filename
                d_object_spline.identifiers.add(d_object_spline.identifier)
                d_object_spline.identifiers.add(d_object_spline.name)
                d_object_spline.identifiers.add(self.filename)
                d_object_spline.compute_search_data()

                points = {}
                for point_elem in spline.iter('hidPoint'):
                    position = point_elem.attrib.get('vectorPosition')
                    guid = point_elem.attrib.get('disGuid').lower()
                    points[guid] = position
                    d_object_spline.add_dependencies_from_element(point_elem)
                    self.positions_dict[guid] = position

                for range_elem in spline.iter('hidRange'):
                    d_object_range = DSplineLayer.DRange()
                    self.library_objects.add(d_object_range)
                    d_object_range.identifier = d_object_spline.identifier + ':' + range_elem.attrib.get('disGuid').lower()
                    d_object_range.name = range_elem.attrib.get('aName')
                    d_object_range.filename = self.filename
                    d_object_spline.add_dependency(d_object_range.identifier)
                    d_object_range.add_dependencies_from_element(range_elem)
                    d_object_range.filename = self.filename
                    d_object_range.identifiers.add(d_object_range.identifier)
                    d_object_range.identifiers.add(d_object_range.name)
                    d_object_range.identifiers.add(self.filename)
                    d_object_range.compute_search_data()

                    start = None
                    for start_elem in range_elem.iter('Start'):
                        start = points.get(start_elem.attrib.get('disPointGuid').lower())

                    end = None
                    for end_elem in range_elem.iter('End'):
                        end = points.get(end_elem.attrib.get('disPointGuid').lower())

                    d_object_range.points = (start, end)
                    d_object_range.position = start


                    for custom_props in range_elem.iter('CustomProps'):
                        for custom_prop in custom_props.iter('CustomProp'):
                            definition = custom_prop.attrib.get('rangedefRangeDefinition')
                            if definition:
                                d_object_range.definition = definition

        for intersection in tree.iter('Intersection'):
            d_object_intersection = DSplineLayer.DIntersection()
            self.library_objects.add(d_object_intersection)
            d_object_intersection.identifier = intersection.attrib.get('hidGuid').lower()
            d_object_intersection.name = d_object_intersection.identifier
            d_object_intersection.filename = self.filename
            for point_elem in intersection.iter('hidPoint'):
                point_guid = point_elem.attrib.get('disPointGuid')
                if point_guid is not None:
                    d_object_intersection.position = self.positions_dict.get(point_guid.lower())
                    break  # just need to get one point
            d_object_intersection.add_dependencies_from_element(intersection)
            d_object_intersection.identifiers.add(d_object_intersection.identifier)
            d_object_intersection.identifiers.add(d_object_intersection.name)
            d_object_intersection.identifiers.add(self.filename)
            d_object_intersection.compute_search_data()

    class DSpline(DObject):
        TYPE = 'Spline'
        IS_CONTAINER_ELEMENT = True

        def __init__(self):
            super().__init__()

    class DIntersection(DObject):
        TYPE = 'Intersection'
        IS_WORLD_INSTANCE = True
        IS_CONTAINER_ELEMENT = True

        def __init__(self):
            super().__init__()
            self.layer_type = 'World'

    class DRange(DObject):
        TYPE = 'Range'
        IS_WORLD_INSTANCE = True
        IS_CONTAINER_ELEMENT = True

        def __init__(self):
            super().__init__()
            self.layer_type = 'World'


class DProxy(DObject):
    VERSION = 2
    TYPE = "Proxy"
    PATH_TO_FILES = join(DObject.MAIN_PATH, r'editor\proxy')
    EXTENSIONS = {'.proxy.xml'}

    def __init__(self, proxy_file):
        super().__init__()
        self.filename = proxy_file.lower()
        self.name = basename(self.filename)
        self.identifier = convert_to_path_type(self.filename.lower(), 2)
        self.parse_xml_file(proxy_file)
        self.identifiers.add(self.identifier)
        self.identifiers.add(self.name)
        self.identifiers.add(self.filename)
        self.compute_search_data()

    def parse_xml_file(self, xml_file):
        tree = ElementTree(file=xml_file)
        for elem_object in tree.iter('Object'):
            self.add_dependencies_from_element(elem_object)

        metadata_file = xml_file + '.metadata'
        if not isfile(metadata_file):
            return

        tree = ElementTree(file=metadata_file)
        for elem_object in tree.iter('object'):
            object_id = elem_object.get('id')
            object_id_hex = elem_object.get('id_hex')
            if object_id_hex is not None:
                self.identifier = object_id_hex.lower()
                return
            self.identifier = object_id.lower()


class DPrefabLibrary(DObject):
    VERSION = 2
    TYPE = "Prefab_Library"
    IS_CONTAINER = True
    PATH_TO_FILES = join(DObject.MAIN_PATH, r'Databases\Prefabs')
    EXTENSIONS = {'.xml'}

    def __init__(self, library_file):
        super().__init__()
        self.filename = library_file.lower()
        self.name = convert_to_path_type(self.filename.lower(), 2)
        self.library_objects = set()
        self.parse_xml_file(library_file)
        self.identifier = convert_to_path_type(self.filename.lower(), 2)
        self.identifiers.add(self.identifier)
        self.identifiers.add(self.name)
        self.identifiers.add(self.filename)

    def parse_xml_file(self, xml_file):
        if xml_file is None:
            return
        tree = ElementTree(file=xml_file)
        for prefab in tree.iter('Prefab'):
            prefab_d_object = DPrefabLibrary.DPrefab()
            self.library_objects.add(prefab_d_object)
            prefab_d_object.name = prefab.get('Name').lower()
            prefab_d_object.filename = self.filename
            prefab_d_object.identifier = prefab.get('Id').lower()
            prefab_d_object.identifiers.add(prefab_d_object.identifier)
            prefab_d_object.identifiers.add(prefab_d_object.name)
            prefab_d_object.identifiers.add(prefab_d_object.filename)
            prefab_d_object.compute_search_data()
            for element in prefab.iter('Object'):
                element_d_object = DPrefabLibrary.DPrefabObject()
                element_id = element.get('Id')
                if element_id is None:
                    continue
                element_d_object.identifier = element_id.lower()
                prefab_d_object.elements.add(element_d_object)
                element_d_object.name = element.get('Name')
                element_d_object.position = element.get('WorldPos')
                element_d_object.angles = element.get('Angles')
                element_d_object.entity_class = element.get('EntityClass')
                element_d_object.object_type = element.get('Type')
                element_d_object.filename = self.filename
                element_d_object.identifiers.add(element_d_object.identifier)
                element_d_object.identifiers.add(element_d_object.name)
                element_d_object.identifiers.add(element_d_object.filename)
                element_d_object.add_dependencies_from_element(element)
                prefab_d_object.add_child(element_d_object)
                element_d_object.add_parent(prefab_d_object)
                element_d_object.compute_search_data()

    class DPrefab(DObject):
        TYPE = 'Prefab'
        IS_CONTAINER_ELEMENT = True

        def __init__(self):
            super().__init__()
            self.elements = set()

    class DPrefabObject(DObject):
        TYPE = 'Prefab_Object'
        IS_CONTAINER_ELEMENT = True

        def __init__(self):
            super().__init__()


class DArchetypeLibrary(DObject):
    VERSION = 2
    TYPE = "Archetype_Library"
    IS_CONTAINER = True
    PATH_TO_FILES = join(DObject.MAIN_PATH, r'editor\EntityLibrary')
    EXTENSIONS = {'.xml'}

    def __init__(self, library_file):
        super().__init__()
        self.filename = library_file.lower()
        self.name = convert_to_path_type(self.filename.lower(), 2)
        self.library_objects = set()
        self.parse_xml_file(library_file)
        self.get_archetype_derivations()
        self.identifier = convert_to_path_type(self.filename.lower(), 2)
        self.identifiers.add(self.identifier)
        self.identifiers.add(self.name)
        self.identifiers.add(self.filename)

    def parse_xml_file(self, xml_file):
        if xml_file is None:
            return
        tree = ElementTree(file=xml_file)
        for entity_prototype in tree.iter('EntityPrototype'):
            d_object = DArchetypeLibrary.DArchetype()
            self.library_objects.add(d_object)
            d_object.name = entity_prototype.get('Name').lower()
            d_object.filename = self.filename
            d_object.use_navmesh_multistate = False
            d_object.projection_decal_box_offset = None
            d_object.projection_decal_box_depth = None
            d_object.parent_archetype = None

            d_object.components = set()
            for components in entity_prototype.iter('Components'):
                for component in components.iter():
                    if component.tag == 'Components':
                        continue
                    if 'component' in component.tag.lower():
                        d_object.components.add(component.tag)

                    if component.tag == "CBreakablePhysComponent":
                        d_object.use_navmesh_multistate = True

                    if component.tag == "CDecalComponent":
                        offset = component.attrib.get('fProjDecalBoxOffset')
                        if offset is None:
                            continue
                        depth = component.attrib.get('fProjDecalBoxDepth')
                        d_object.projection_decal_box_offset = float(offset)
                        d_object.projection_decal_box_depth = float(depth)

            d_object.archetype_class = entity_prototype.get('Class')

            d_object.identifier = entity_prototype.get('Id').lower()
            d_object.identifiers.add(d_object.identifier)
            d_object.identifiers.add(d_object.name)
            d_object.identifiers.add(d_object.filename)
            d_object.add_dependencies_from_element(entity_prototype)
            d_object.compute_search_data()

    def get_archetype_derivations(self):
        archetype_derivations_dict = dict()

        for obj in self.library_objects:
            archetype_derivations_dict[obj.name] = obj

        for name, obj in archetype_derivations_dict.items():
            tokens = name.split('.')
            if len(tokens) <= 2:
                continue
            parent_name = '.'.join(tokens[:-1])
            obj.parent_archetype = archetype_derivations_dict.get(parent_name)

        def get_archetype_recursively(current_object, components, dependencies):
            for component in current_object.components:
                components.append(component)
            for dependency in current_object.dependencies:
                dependencies.append(dependency)
            if current_object.parent_archetype is None:
                return
            get_archetype_recursively(current_object.parent_archetype, components, dependencies)

        for obj in self.library_objects:
            component_list = list(obj.components)
            dependencies_list = (list(obj.dependencies))
            get_archetype_recursively(obj, component_list, dependencies_list)
            obj.components = set(component_list)
            dependencies_set = set(dependencies_list)
            obj.dependencies = dependencies_set

    class DArchetype(DObject):
        TYPE = 'Archetype'
        IS_CONTAINER_ELEMENT = True

        def __init__(self):
            super().__init__()


class DGenericLibrary(DObject):
    VERSION = 2
    TYPE = "Generic_Library"
    IS_CONTAINER = True
    PATH_TO_FILES = join(DObject.MAIN_PATH, r'Databases\Generic')
    EXTENSIONS = {'.xml'}

    def __init__(self, library_file):
        super().__init__()
        self.filename = library_file.lower()
        self.name = convert_to_path_type(self.filename.lower(), 2)
        self.library_objects = set()
        self.parse_xml_file(library_file)
        self.identifier = convert_to_path_type(self.filename.lower(), 2)
        self.identifiers.add(self.identifier)
        self.identifiers.add(self.name)
        self.identifiers.add(self.filename)

    def parse_xml_file(self, xml_file):
        if xml_file is None:
            return
        tree = ElementTree(file=xml_file)
        for generic in tree.iter('Generic'):
            d_object_generic = DGenericLibrary.DGeneric()
            self.library_objects.add(d_object_generic)
            name = generic.get('Name')
            if name is not None:
                d_object_generic.name = name.lower()
            d_object_generic.filename = self.filename
            current_id = generic.get('disNomadObjectId')
            if current_id is not None:
                d_object_generic.identifier = current_id.lower()
                d_object_generic.identifiers.add(d_object_generic.identifier)
            d_object_generic.identifiers.add(d_object_generic.name)
            d_object_generic.identifiers.add(d_object_generic.filename)
            d_object_generic.add_dependencies_from_element(generic)
            d_object_generic.compute_search_data()

            for collection_item_node in generic.iter("CollectionItemNode"):
                new_collection_item = DGenericLibrary.DCollectionItem()
                new_collection_item.identifier = collection_item_node.attrib.get("socketitemidUniqueID")
                # new_collection_item.add_dependency(collection_item_node.attrib.get("fileProxyObject"))
                new_collection_item.add_dependencies_from_element(collection_item_node)
                new_collection_item.name = new_collection_item.identifier
                new_collection_item.filename = self.filename
                d_object_generic.add_dependency(new_collection_item.identifier)
                new_collection_item.identifiers.add(new_collection_item.identifier)
                new_collection_item.identifiers.add(self.filename)
                self.library_objects.add(new_collection_item)

    class DGeneric(DObject):
        TYPE = 'Generic'
        IS_CONTAINER_ELEMENT = True
        def __init__(self):
            super().__init__()

    class DCollectionItem(DObject):
        TYPE = 'Collection_Item'
        IS_CONTAINER_ELEMENT = True

        def __init__(self):
            super().__init__()


class DBuildingFacadePrefabLibrary(DObject):
    VERSION = 2
    TYPE = "Building_Facade_Prefab_Library"
    IS_CONTAINER = True
    PATH_TO_FILES = join(DObject.MAIN_PATH, r'Databases\Building')
    EXTENSIONS = {'.xml'}
    def __init__(self, library_file):
        super().__init__()
        self.filename = library_file.lower()
        self.name = convert_to_path_type(self.filename.lower(), 2)
        self.library_objects = set()
        self.parse_xml_file(library_file)
        self.identifier = convert_to_path_type(self.filename.lower(), 2)
        self.identifiers.add(self.identifier)
        self.identifiers.add(self.name)
        self.identifiers.add(self.filename)

    def parse_xml_file(self, xml_file):
        if xml_file is None:
            return
        tree = ElementTree(file=xml_file)
        for building_facade in tree.iter('BuildingFacade'):
            d_object = DBuildingFacadePrefabLibrary.DBuildingPrefab()
            self.library_objects.add(d_object)
            d_object.name = building_facade.get('Name').lower()
            d_object.filename = self.filename
            d_object.identifier = building_facade.get('Id').lower()
            d_object.identifiers.add(d_object.identifier)
            d_object.identifiers.add(d_object.name)
            d_object.identifiers.add(d_object.filename)
            d_object.add_dependencies_from_element(building_facade)
            d_object.compute_search_data()

    class DBuildingPrefab(DObject):
        TYPE = 'Building_Facade_Prefab'
        IS_CONTAINER_ELEMENT = True
        def __init__(self):
            super().__init__()


class DGeometryLibrary(DObject):
    VERSION = 3
    TYPE = "Geometry_Library"
    IS_CONTAINER = True
    PATH_TO_FILES = join(DObject.MAIN_PATH, r'graphics')
    EXTENSIONS = {'.gamex', '.lft', '.glm'}

    def __init__(self, geometry_file):
        super().__init__()
        self.filename = geometry_file.lower().replace('.gamex', '.xml').replace('.glm', '.xml').replace('.lft', '.xml')
        self.file_descriptor = self.set_file_descriptor(self.filename)
        self.name = convert_to_path_type(self.filename.lower(), 2)
        self.is_projected_decal = 0
        self.bbox_min = None
        self.bbox_max = None
        self.size_x = None
        self.size_y = None
        self.size_z = None
        self.library_objects = set()
        self.identifier = convert_to_path_type(self.filename.lower(), 2)
        self.parse_xml_file(self.file_descriptor)
        self.identifiers.add(self.identifier)
        self.identifiers.add(self.name)
        self.identifiers.add(self.filename)
        # self.compute_search_data()

    @staticmethod
    def set_file_descriptor(filename):
        for extension in DGeometryLibrary.EXTENSIONS:
            filename = filename.replace(extension, '.xml')
        if isfile(filename):
            return filename
        return None

    def parse_xml_file(self, xml_file):
        if xml_file is None:
            return
        tree = ElementTree(file=xml_file)

        for elem in tree.iter('entities'):
            self.name = elem.attrib.get("objectName").lower()

        for elem in tree.iter('material_reference_list'):
            self.add_dependencies_from_element(elem)

        for elem in tree.iter('ProjectedDecal'):
            if elem.attrib.get('bIsProjectedDecal') == "1":
                self.is_projected_decal = 1

        for elem in tree.iter('object'):
            bbox_min = elem.attrib.get('bboxMin')
            bbox_max = elem.attrib.get('bboxMax')
            if not bbox_min:
                continue
            self.bbox_min = [float(i) for i in bbox_min.split(',')]
            self.bbox_max = [float(i) for i in bbox_max.split(',')]

            self.size_x = self.bbox_max[0] - self.bbox_min[0]
            self.size_y = self.bbox_max[1] - self.bbox_min[1]
            self.size_z = self.bbox_max[2] - self.bbox_min[2]

        for elem in tree.iter('GraphicModel'):
            d_object = DGeometryLibrary.DGeometry()
            name = elem.attrib.get('DisplayName').lower()
            if name == 'default':
                d_object.name = self.name
            else:
                d_object.name = name
            d_object.filename = self.filename
            d_object.is_projected_decal = self.is_projected_decal
            d_object.bbox_min = self.bbox_min
            d_object.bbox_max = self.bbox_max
            d_object.size_x = self.size_x
            d_object.size_y = self.size_y
            d_object.size_z = self.size_z
            d_object.identifier = elem.attrib.get('UniqueID').lower()
            d_object.identifiers.add(d_object.identifier)
            d_object.identifiers.add(d_object.name)
            d_object.identifiers.add(d_object.filename)
            d_object.add_dependencies_from_element(elem)
            d_object.dependencies = d_object.dependencies.union(self.dependencies)
            d_object.compute_search_data()

            self.library_objects.add(d_object)

    class DGeometry(DObject):
        TYPE = 'Geometry'
        IS_CONTAINER_ELEMENT = True

        def __init__(self):
            super().__init__()


class DMaterial(DObject):
    VERSION = 3
    TYPE = "Material"
    PATH_TO_FILES = join(DObject.MAIN_PATH, r'graphics')
    EXTENSIONS = {'.material.xml'}
    REFERENCE_ATTRIBUTES = {
        "absorptiondistancetexture",
        "absorptiontexture",
        "alphatexture",
        "alphatexture1",
        "animtexture1",
        "basecolortexture",
        "baseparameterstexture1",
        "burntdiffusetexture",
        "caustictexturearray",
        "ceilingtexture",
        "clearcoatparameterstexture1",
        "colormask",
        "colorizetexture1",
        "curvaturetexture",
        "damagenormalmaptexture",
        "damagetexture",
        "damagetexture1",
        "decaltexture",
        "detailtexture",
        "detailtexture1",
        "detailtexture2",
        "detailtexture3",
        "detailtextureextra1",
        "detailtextureextra2",
        "detailtextureextra3",
        "diffusetexture",
        "diffusetexture0",
        "diffusetexture1",
        "diffusetexture2",
        "diffusetexturearray1",
        "diffusetexturelayer2",
        "diffusetexturetoprock",
        "distortiontexture",
        "ditheringtexture",
        "emissivemasktexture",
        "emissivetexture",
        "faceblenddisplacetexturearray",
        "fakeinteriortexture",
        "flowtexture",
        "furnormaltexture1",
        "glitchtexture",
        "gradienttexture1",
        "grungetexture",
        "hairaotexture",
        "hairdepthtexture",
        "hairroughnessvariationtexture",
        "hairtransmittancetexture",
        "heighttexture1",
        "heighttexture2",
        "holoar_noisetexture",
        "horizontexture",
        "lasernoisetexture",
        "laservolumetexture",
        "layermasknoisetexture1",
        "layermasktexture1",
        "masktexture",
        "masktexture1",
        "masktexture2",
        "masktexturearray1",
        "materialpalettetexture",
        "noisetexture1",
        "normaldynamicwrinklestexture1a",
        "normaldynamicwrinklestexture1b",
        "normaldynamicwrinklestexture2a",
        "normaldynamicwrinklestexture2b",
        "normaldynamicwrinklestexture3a",
        "normaldynamicwrinklestexture3b",
        "normaldynamicwrinklestexture4a",
        "normaldynamicwrinklestexture4b",
        "normalmaptexture",
        "normalmaptexture1",
        "normaltexture",
        "normaltexture1",
        "normaltexture2",
        "normaltexturearray1",
        "normaltexturetoprock",
        "opacitytexture",
        "opacitytexture1",
        "overlaytexture",
        "palettetexture1",
        "patterntexture",
        "patterntexture1",
        "raindropsplashestexture",
        "reflectiontexture",
        "screenfx_texture1",
        "specularnoisetexture",
        "specularshifttexture",
        "speculartexture1",
        "surfaceparameterstexture",
        "surfacetexture1",
        "tarnishmasktexture",
        "thicknesstexture",
        "typetexture",
        "vegetationleafnoisetexture",
        "vegetationtrunknoisetexture",
        "videotexture1",
        "wavetexture",
        "windleafanimnoisetexture",
        "windowlightmasktexture1",
        "windowlightvariationtexture",
        "worldcolortexture",
        "worldlightdensitytexture1",
    }

    def __init__(self, material_file):
        super().__init__()
        self.filename = material_file.lower()
        self.name = None
        self.category = None
        self.shader = None
        self.subfamily = None
        self.base_material = None
        self.get_xml()
        self.identifier = self.format_dependency(convert_to_path_type(self.filename.lower(), 2))
        self.identifiers.add(self.identifier)
        self.identifiers.add(self.name)
        self.identifiers.add(self.filename)
        self.compute_search_data()


    def get_xml(self):
        tree = ElementTree(file=self.filename)
        root = tree.getroot()
        parent = root.get('matBaseMaterial')
        if parent is not None:
            self.base_material = parent.lower()
            self.add_dependency(self.base_material, True)
        for elem in tree.iter("parameter"):
            name = elem.attrib.get("name").lower()
            value = elem.attrib.get("value")
            if value != None:
                value = value.lower()
            setattr(self, name, value)
            if name == "SubFamily":
                self.subfamily = value
            if name not in DMaterial.REFERENCE_ATTRIBUTES:
                continue
            self.add_dependency(value)
        for elem in tree.iter("category"):
            category = elem.text
            if category is not None:
                self.category = category.lower()
            break
        for elem in tree.iter("name"):
            self.name = elem.text.lower().lower()
            break
        for elem in tree.iter("shader"):
            self.shader = elem.text.lower()
            break


class DTexture(DObject):

    class TextureProfiles:

        PATH_TO_FILE = join(DObject.MAIN_PATH, r'engine\shaders\TextureProfiles.xml')
        def __init__(self):
            self.profiles = dict()
            self.get_xml()

        def get_xml(self):
            tree = ElementTree(file=self.PATH_TO_FILE)
            for profile in tree.iter('profile'):
                new_profile = self.TextureProfile()
                new_profile.id = profile.attrib.get('id')
                new_profile.displayname = profile.attrib.get('displayname')

                for description in profile.iter('description'):
                    for color in description.iter('color'):
                        new_profile.color = color.attrib.get('type')
                    for precisionlevel in description.iter('precisionlevel'):
                        new_profile.precisionlevel = precisionlevel.attrib.get('type')

                self.profiles[new_profile.id] = new_profile

            # for compression in tree.iter('compression'):
            # for mipmap in tree.iter('mipmap'):

        class TextureProfile:
            def __init__(self):
                self.id = None
                self.displayname = None
                self.color = None
                self.precisionlevel = None

    VERSION = 3
    TYPE = "Texture"
    PATH_TO_FILES = join(DObject.MAIN_PATH, r'graphics')
    # PATH_TO_FILES = join(DObject.MAIN_PATH, r'UI')
    EXTENSIONS = {'.png'}
    TEXTURE_PROFILES = TextureProfiles()

    def __init__(self, png_file):
        super().__init__()

        self.filename = png_file.lower()
        self.meta_file = None
        self.name = basename(self.filename)
        self.height = None
        self.width = None
        self.height_ps4 = None
        self.width_ps4 = None
        self.profile = None
        self.scale_ps4 = None
        self.scale_xbox_one = None
        self.get_xml()

        self.identifier = convert_to_path_type(self.filename.lower(), 2)
        self.identifiers.add(self.identifier)
        self.identifiers.add(self.name)
        self.identifiers.add(self.filename)
        self.compute_search_data()

    def get_xml(self):
        png = Image.open(self.filename)
        self.height = png.size[0]
        self.width = png.size[1]

        for k, v in png.info.items():
            if k != 'nomadPNGMetadata':
                continue
           
            try:
                tree =fromstring(v)
            except ParseError:
                print ("This File contains corrupted meta .xml structure", self.filename)
                continue


            for resize_op in tree.iter('resizeOp'):
                if resize_op.attrib.get('platform') == 'orbis':
                    self.scale_ps4 = resize_op.get('value')

        if isfile(self.filename + '.meta'):
            self.meta_file = self.filename + '.meta'
            tree = ElementTree(file=self.meta_file)
            for resize_op in tree.iter('resizeOp'):
                if resize_op.get('platform') == 'orbis':
                    self.scale_ps4 = resize_op.get('value')
                if resize_op.get('platform') == 'durango':
                    self.scale_xbox_one = resize_op.get('value')
            for settings in tree.iter('settings'):
                profile_id = settings.get('profileid')
                if profile_id is not None:
                    self.profile = self.TEXTURE_PROFILES.profiles.get(profile_id)

        if not self.scale_ps4:
            self.scale_ps4 = 1

        self.height_ps4 = int(int(self.height) / int(self.scale_ps4))
        self.width_ps4 = int(int(self.width) / int(self.scale_ps4))


def main():
    texture = DTexture(r'W:\main\data\graphics\_Texture\Branding\Borough\Brixton\decal_lam_brixton_windrush_chalkart_01_c.png')
    for id, profile in texture.TEXTURE_PROFILES.profiles.items():
        print(id, profile.displayname, profile.color, profile.precisionlevel)


if __name__ == "__main__":
    main()
