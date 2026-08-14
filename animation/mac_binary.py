from struct import unpack, pack
from utility import lPartTypes,lDataTypes,CurvesToXFormsFromDictionary
from os.path import basename, dirname
from binascii import a2b_base64
from array import array
from contextlib import contextmanager
from crc import CrcForString
from math import isnan
from mxml import WriteJson
import traceback
from os import makedirs
import json
import math

CURRENT_VERSION=11.0
ORWELL_VERSION=9.0
MOMENTUM_BINARY="/////29NbkH+/////v///w==" # momentum objects do not appear to be used on farcry, why are they included? It is a mystery for the ages.
WEIRD_BUFFER_THING ="sWjeOg==" # this is probably the hash of something? it shows up all over the place. It might just be an artifact of the serialization system
PART_EVENT_PREFIX="ePartEvent"

@contextmanager
def OutMovingFile(f): # for debugging purposes, lets you read ahead without effecting the current offset
    hold=f.tell()
    yield
    f.seek(hold)


def FileName(sFileName):
    return basename(sFileName).split(".")[0]
    

def OpenFile(sFileName,bRead=True):
    if bRead:
        return open(sFileName,mode="rb")
    return open(sFileName,mode="wb")


def ReadCString(f):
    _,size=unpack("<II",f.read(8))
    return f.read(size)
    
    
def WriteCString(sValue):
    if sValue is None:
        return WriteCString("")
    if isinstance(sValue,unicode):
        sValue=sValue.encode("utf8")
    if not isinstance(sValue,str):
        raise Exception("You cannot store %s of type %s in a CString"%(str(sValue),str(type(sValue))))
    return pack("<II",CrcForString(sValue),len(sValue))+sValue
    
    
def RemoveVerySmallNumbers(i):
    if abs(i)<0.00001:
        return 0
    return i
    
    
def ReadCAnimDiscreteCurve(f):
    valuesCount,curveType,byteCount=unpack("<III",f.read(12))
    values=unpack("<%df"%valuesCount,f.read(byteCount))
    return lDataTypes[curveType],map(RemoveVerySmallNumbers,values)
    
    
def WriteCAnimDiscreteCurve(curveType,lValues):
    result=pack("<III",len(lValues),lDataTypes.index(curveType),len(lValues)*4)
    return result + array("f",lValues).tostring()


def XFormsToCurveBinary(xforms):
    return "".join([WriteCAnimDiscreteCurve("eCurveDataTransX",[k["translation"]["x"] for k in xforms]),
                    WriteCAnimDiscreteCurve("eCurveDataTransY",[k["translation"]["y"] for k in xforms]),
                    WriteCAnimDiscreteCurve("eCurveDataTransZ",[k["translation"]["z"] for k in xforms]),
                    WriteCAnimDiscreteCurve("eCurveDataQuatX",[k["rotation"]["x"] for k in xforms]),
                    WriteCAnimDiscreteCurve("eCurveDataQuatY",[k["rotation"]["y"] for k in xforms]),
                    WriteCAnimDiscreteCurve("eCurveDataQuatZ",[k["rotation"]["z"] for k in xforms]),
                    WriteCAnimDiscreteCurve("eCurveDataQuatW",[k["rotation"]["w"] for k in xforms])])
    
    
def SkipComplexTransfer(f):
    ReadComplexTransfer(f)
    
    
DONT_KEEP_READING_COMPLEX_TRANSFER=-2
THE_ONLY_VALUE_FOR_COMPLEX_TRANSFERS_THAT_WORK=-1
    
    
def ReadComplexTransfer(f):
    transferType,=unpack("<i",f.read(4))
    name=None
    if transferType!=DONT_KEEP_READING_COMPLEX_TRANSFER:
        name=f.read(4)
        name="".join(reversed(name)) if any([k!="\x00" for k in name]) else None
    return transferType,name
    

def WriteComplexTransfer(name=None):
    if name:
        return pack("<i",THE_ONLY_VALUE_FOR_COMPLEX_TRANSFERS_THAT_WORK) + "".join(reversed(name)) # for mac files, the transfer type is always -1 if we're actually storing it
    return pack("<i",DONT_KEEP_READING_COMPLEX_TRANSFER)


def ReadDisplacementKeys(f,num):
    result=[]
    for _ in range(num):
        rx,ry,rz,rw,tx,ty,tz,t=map(RemoveVerySmallNumbers,unpack("<ffffffff",f.read(32)))
        result.append({"time":t,
                       "translation":{"x":tx,"y":ty,"z":tz},
                       "rotation":{"x":rx,"y":ry,"z":rz,"w":rw}})
    return result 

def ReadCAnimDirNode(f):
    SkipComplexTransfer(f) # skip transfer complex
    weirdBuffer,=unpack("<I",f.read(4)) # skip the weird
    if not weirdBuffer:
        return None,None
    numberOfDisplacementKeys=0
    if weirdBuffer!=7:
        version,numberOfCurves,numberOfDisplacementKeys=unpack("<III",f.read(12)) # the second one in this case is the curve count
        if version!=1:
            raise Exception("We only handle dirNodes of version 1 not %d. Problem at %d"%(version,f.tell()))
        if not numberOfCurves:
            return None, None
    curves=list(CurvesToXFormsFromDictionary(dict(ReadCAnimDiscreteCurve(f) for _ in range(7))))
    displacement_keys=ReadDisplacementKeys(f, numberOfDisplacementKeys)
    return curves, displacement_keys


def WeirdBufferBinary():
    return a2b_base64(WEIRD_BUFFER_THING)


def WriteCAnimDirNode(displacement):
    numberOfDisplacementKeys=0 if not displacement["keys"] else len(displacement["keys"]) 
    res=WriteComplexTransfer("AnDi")
    res+=WeirdBufferBinary()
    res+=pack("<III",1, 7 if displacement["curves"] else 0,numberOfDisplacementKeys)
    if len(displacement["curves"]):
        res+=XFormsToCurveBinary(displacement["curves"])
    if numberOfDisplacementKeys:
        for key in displacement["keys"]:
            res+=pack("<ffff",key["rotation"]["x"],key["rotation"]["y"],key["rotation"]["z"],key["rotation"]["w"])
            res+=pack("<fff",key["translation"]["x"],key["translation"]["y"],key["translation"]["z"])
            res+=pack("<f",key["time"])
    return res


def ReadCAnimBone(f):
    name=ReadCString(f)
    _,_,curveCount=unpack("<3I",f.read(12))
    if curveCount!=7:
        f.read(12) # old versions that are not flagged properly
    return name, list(CurvesToXFormsFromDictionary(dict(ReadCAnimDiscreteCurve(f) for _ in range(7))))

    
def WriteCAnimBone(name,xforms):
    res=WriteCString(name)
    res+=pack("<II",0,0) # adding the id and parent id
    res+=WeirdBufferBinary() # this thing again
    res+=pack("<III",1,7,0) # adding the version, number of curves, and number of displacement keys (which is always zero)
    res+=XFormsToCurveBinary(xforms)
    return res
    
    
def ReadString(f):
    length,=unpack("<I",f.read(4))
    location = f.tell()
    if not length:
        return
    return f.read(length)

def WriteString(sValue):
    if sValue is None:
        return WriteString("")
    return pack("<I",len(sValue)) + sValue
    
    
def ReadCAnimPart(f):
    _,version,=unpack("<II",f.read(8)) # skip the unused buffer hash thing
    if version != 2:
        raise Exception("We can only handle parts of version 2, not version %d. Problem found at %d"%(version,f.tell()))
    name=ReadCString(f)
    time,partType=unpack("<dI",f.read(12))
    parent=ReadCString(f)
    handle=ReadCString(f)
    SkipComplexTransfer(f)
    animation=ReadMac("part",f)


    # TODO: Figure out why we get 8 bytes ahead here. Probably something I modified somewhere
    if animation['version'] == 9.0:
        f.seek(f.tell()-8)


    _=ReadString(f)
    ikBoneName=ReadString(f)
    return {"frames":animation["frames"],
            "type":lPartTypes[partType].replace(PART_EVENT_PREFIX,""),
            "handle":handle if handle else None,
            "parent":parent if parent else None,
            "ikBone":ikBoneName,
            "name":name,
            "offset":int(time*animation["framerate"]) if time else 0,
            "skeleton":animation["skeleton"],
            "animation":animation["animation"]["skeleton"]}
    
    
def WritePart(macFile,part,framerate,version):
    macFile.write(WeirdBufferBinary())
    macFile.write(pack("<I",2)) # write the version
    macFile.write(WriteCString(part["name"]))
    macFile.write(pack("<d",float(part["offset"]) / framerate)) # offset is weird, it is stored in seconds unlike _everything else_
    macFile.write(pack("<I",lPartTypes.index(PART_EVENT_PREFIX+part["type"]))) # the part events are an enum
    macFile.write(WriteCString(part["parent"]))
    macFile.write(WriteCString(part["handle"]))
    macFile.write(WriteComplexTransfer("AnFi"))
    WriteMac(macFile, skeleton=part["skeleton"], framerate=framerate, animation={"skeleton":part["animation"]},version=version)
    macFile.write(WriteString("")) # write the unused handlename field
    macFile.write(WriteString(part["ikBone"]))
    
    
def WriteCAnimSkeleton(macFile,dSkeleton):
    macFile.write(WriteComplexTransfer("AnSk"))
    macFile.write(pack("<I",len(dSkeleton)))
    for name,xforms in sorted(dSkeleton.items(),key=lambda x : x[0]):
        macFile.write(WriteCAnimBone(name,xforms))


def ReadCAnimSkeleton(f):
    SkipComplexTransfer(f)
    numberOfBones,=unpack("<I",f.read(4))
    return dict(ReadCAnimBone(f) for _ in range(numberOfBones))

#region Writing
def WriteMacMainSegment(macFile,skeleton,parts,framerate,animation,version):

    if version == ORWELL_VERSION:
        macFile.write(WriteString(skeleton))
    else:
        macFile.write(WriteCString(skeleton))

    macFile.write(pack("<fIII",framerate,0,0,len(parts))) # the two values in the middle are flag count and event count, they're both apparently unused.
    for part in parts:
        WritePart(macFile,part,framerate,version)
    macFile.write(WriteCAnimDirNode(animation["displacement"] if animation.has_key("displacement") else {"curves":[],"keys":[]}))
    macFile.write(a2b_base64(MOMENTUM_BINARY)) # write the unused momentum node
    WriteCAnimSkeleton(macFile,animation["skeleton"] if animation.has_key("skeleton") else []) # anim skeleton


def WriteMacSubtraction(macFile,skeleton,framerate,subtraction,version):
    if subtraction:
        macFile.write(WriteComplexTransfer("AnFi"))
        WriteMac(macFile, skeleton, framerate, subtraction["parts"], subtraction["animation"], subtraction=None, version=version)
    else:
        macFile.write(WriteComplexTransfer())


def WriteMacVersionTen(macFile=None,skeleton=None,framerate=None,parts=[],animation={},subtraction=None):
    macFile.write(pack("<fI",10.0,1)) # add the version and type numbers (type number is the number of skeletons. It's always 1.)
    WriteMacMainSegment(macFile, skeleton, parts, framerate, animation, 10.0)
    WriteMacSubtraction(macFile, skeleton, framerate, subtraction, 10.0)
    macFile.write(pack("<I",0)) # this is actually a zero length string for no reason, hurray for macs!
    

def WriteMacVersionSeven(macFile=None,skeleton=None,framerate=None,parts=[],animation={},subtraction=None):
    macFile.write(pack("<f",7.0))
    WriteMacMainSegment(macFile, skeleton, parts, framerate, animation, 7.0)
    macFile.write(pack("<I",0)) # this is actually a zero length string for no reason, hurray for macs!


def WriteMacVersionNine(macFile=None,skeleton=None,framerate=None,parts=[],animation={},subtraction=None):
    macFile.write(pack("<f",9.0)) # add the version and type numbers (type number is the number of skeletons)
    macFile.write(pack("<ff", 9.0, 6.0)) # "Exporter" major and minor version numbers. No idea what this does right now
    WriteMacMainSegment(macFile, skeleton, parts, framerate, animation, 9.0)
    WriteMacSubtraction(macFile, skeleton, framerate, subtraction, 9.0)
    macFile.write(pack("<I",0)) # this is actually a zero length string for no reason, hurray for macs!


def WriteMacVersionEleven(macFile=None,skeleton=None,framerate=None,parts=[],animation={},subtraction=None):
    macFile.write(pack("<f",11.0)) # add the version and type numbers (type number is the number of skeletons)
    WriteMacMainSegment(macFile, skeleton, parts, framerate, animation, 11.0)
    WriteMacSubtraction(macFile, skeleton, framerate, subtraction, 11.0)
    macFile.write(pack("<I",0)) # this is actually a zero length string for no reason, hurray for macs!
#endregion


MAC_WRITING_FUNCTIONS={7.0:WriteMacVersionSeven,
                       9.0:WriteMacVersionNine,
                       10.0:WriteMacVersionTen,
                       11.0:WriteMacVersionEleven}


def WriteMac(macFile=None,skeleton=None,framerate=None,parts=[],animation={},subtraction=None,version=ORWELL_VERSION):
    if not version in MAC_WRITING_FUNCTIONS:
        raise Exception ("Cannot write a mac file of version %f"%version)
    MAC_WRITING_FUNCTIONS[version](macFile,skeleton,framerate,parts,animation,subtraction)
        
        
def EnsureDirectoryExists(path):
    try:
        makedirs(dirname(path))
    except:
        pass
        
        
def WriteMacFile(path,dMac):
    EnsureDirectoryExists(path)
    with open(path,"wb") as macFile:
        WriteMac(macFile, skeleton=dMac["skeleton"], framerate=dMac["framerate"], parts=dMac["parts"], animation=dMac["animation"], subtraction=dMac["subtraction"],version=dMac["version"])


def SkipMomentumGarbage(macFile):
    testString=""
    while not "kSnA" in testString: 
        """This reads forward until it finds the skeleton, there is a _bunch_ of weird junk after the parts and
        I haven't been able to figure out what any of it is used for. None of it appears relevant, and there are
        no version number changes to detect it. Very frustrating."""
        testString+=macFile.read(1)
    macFile.seek(macFile.tell()-8) # skip back so the skeleton can read it's own tag
    

def ReadMacMainSegment(macFile, version=None):

    # TODO: Changed to ReadString rather than ReadCString. Make sure this only happens if mac v9
    if version == 9.0:
        skeleton=ReadString(macFile)
    else:
        skeleton=ReadCString(macFile)

    framerate, = unpack('f', macFile.read(4))

    # TODO: This is different from FarCry, doesn't look like they include source files in the mac. only in mac v9 and 8
    sourceFile = None
    if version == 9.0:
        sourceFile = ReadString(macFile)
    if version == 8.0:
        sourceFile = ReadCString(macFile)

    # TODO: This is slightly different in v9 as well, because the source path comes before the flag/event/part count
    if version == 9.0 or version == 8.0:
        flagCount, eventCount, partCount = unpack('III', macFile.read(12))
    elif version == 7.0:
        _, _, partCount = unpack("<III", macFile.read(12))
    else:
        framerate,_,_,partCount=unpack("<fIII",macFile.read(16))

    parts=[ReadCAnimPart(macFile) for _ in range(partCount)]
    displacementAnimation,displacementKeys=ReadCAnimDirNode(macFile)
    SkipMomentumGarbage(macFile)
    dSkeleton=ReadCAnimSkeleton(macFile)

    if version == 9.0 or version == 8.0:
        return skeleton,sourceFile,framerate,parts,displacementAnimation,displacementKeys,dSkeleton
    else:
        return skeleton,framerate,parts,displacementAnimation,displacementKeys,dSkeleton

def ReadSubtraction(macFile):
    _,subtractionClassType=ReadComplexTransfer(macFile)
    return ReadMac("subtraction",macFile) if subtractionClassType else None


def MacDictionary(name,skeleton,framerate,dSkeleton,parts,displacementAnimation,displacementKeys,subtraction,version, sourceFile=None):
    return {"version":version,
            "name":name,
            "sourceFile":sourceFile,
            "skeleton":skeleton,
            "framerate":framerate,
            "frames":len(dSkeleton.values()[0]),
            "parts":parts,
            "animation":{"displacement":{"curves":displacementAnimation,"keys":displacementKeys},"skeleton":dSkeleton},
            "subtraction":subtraction}


def ReadMacVersionSeven(name,macFile):
    skeleton,framerate,parts,displacementAnimation,displacementKeys,dSkeleton=ReadMacMainSegment(macFile, version=7.0)
    macFile.read(4)
    return MacDictionary(name, skeleton, framerate, dSkeleton, parts, displacementAnimation, displacementKeys, None, 7.0)

def ReadMacVersionNine(name,macFile):
    # TODO: This is different from Far Cry. It's "major" and "minor" exporter version? Only in mac v9
    _,_ = unpack("ff", macFile.read(8))

    skeleton,sourceFile,framerate,parts,displacementAnimation,displacementKeys,dSkeleton=ReadMacMainSegment(macFile, version=9.0)
    subtraction=ReadSubtraction(macFile)
    macFile.read(4)


    return MacDictionary(name, skeleton, framerate, dSkeleton, parts, displacementAnimation, displacementKeys, subtraction, 9.0, sourceFile)

def ReadMacVersionEight(name,macFile):
    skeleton,sourceFile,framerate,parts,displacementAnimation,displacementKeys,dSkeleton=ReadMacMainSegment(macFile, version=8.0)
    subtraction=ReadSubtraction(macFile)
    macFile.read(4)
    return MacDictionary(name, skeleton, framerate, dSkeleton, parts, displacementAnimation, displacementKeys, subtraction, 8.0, sourceFile)
    

def ReadMacVersionTen(name,macFile):
    typeNumber,=unpack("<I",macFile.read(4))
    if typeNumber!=1:
        raise Exception("We only support files with a single skeleton.")
    skeleton,framerate,parts,displacementAnimation,displacementKeys,dSkeleton=ReadMacMainSegment(macFile)
    subtraction=ReadSubtraction(macFile)
    macFile.read(4)
    return MacDictionary(name, skeleton, framerate, dSkeleton, parts, displacementAnimation, displacementKeys, subtraction, 10.0)


def ReadMacVersionEleven(name,macFile):
    skeleton,sourceFile,framerate,parts,displacementAnimation,displacementKeys,dSkeleton=ReadMacMainSegment(macFile)
    subtraction=ReadSubtraction(macFile)
    macFile.read(4)
    return MacDictionary(name, skeleton, framerate, dSkeleton, parts, displacementAnimation, displacementKeys, subtraction, 11.0)


MAC_VERSION_READING_FUNCTIONS={11.0:ReadMacVersionEleven,
                               10.0:ReadMacVersionEleven,
                               7.0:ReadMacVersionSeven,
                               9.0:ReadMacVersionNine,
                               8.0:ReadMacVersionEight
                               }
A_REASONABLE_VALUE=50

def GetVersionNumber(macFile):
    version,=unpack("<f",macFile.read(4))
    version = math.floor(version)
    if isnan(version) or version > A_REASONABLE_VALUE or version == 0.0:
        #TODO: Added this instead of throwing an error because I'm a mad man
        return 7
    return version
        

def ReadMac(name,macFile):
    try:
        version=GetVersionNumber(macFile)
        if not version in MAC_VERSION_READING_FUNCTIONS.keys():
            raise Exception("We can only handle macs of the following versions %s not of version %s. Problem at %d."%(str(MAC_VERSION_READING_FUNCTIONS.keys()),version,macFile.tell()))
        return MAC_VERSION_READING_FUNCTIONS[version](name,macFile)
    except Exception as e:
        print "ERROR OCCURED AT %d"%macFile.tell()
        print macFile
        print traceback.format_exc()
        raise e
    
    
def ReadMacFile(sMacFile):
    with OpenFile(sMacFile) as f:
        mac = ReadMac(FileName(sMacFile),f)

        mac["export_path"]=sMacFile
        return mac


def ReadMacSource(sMacFile):
    with OpenFile(sMacFile) as f:
        version = GetVersionNumber(f)

        if version == 9.0:
            _, _ = unpack("ff", f.read(8))
            skeleton = ReadString(f)
            framerate, = unpack('f', f.read(4))
            sourceFile = ReadString(f)
            return sourceFile

        if version == 8.0:
            skeleton = ReadCString(f)
            framerate, = unpack('f', f.read(4))
            sourceFile = ReadCString(f)
            return sourceFile

        else:
            return False


def ReadMacSourceAndFrames(sMacFile):
    with OpenFile(sMacFile) as f:
        version = GetVersionNumber(f)

        sourceFile = None
        if version == 9.0:
            _, _ = unpack("ff", f.read(8))
            skeleton = ReadString(f)
            framerate, = unpack('f', f.read(4))
            sourceFile = ReadString(f)


        if version == 8.0:
            skeleton = ReadCString(f)
            framerate, = unpack('f', f.read(4))
            sourceFile = ReadCString(f)

        flagCount, eventCount, partCount = unpack('III', f.read(12))
        parts = [ReadCAnimPart(f) for _ in range(partCount)]
        displacementAnimation, displacementKeys = ReadCAnimDirNode(f)
        # SkipMomentumGarbage(f)
        # dSkeleton = ReadCAnimSkeleton(f)


        return {'sourceFile':sourceFile, 'frames':len(displacementAnimation)}




def WriteDebug(sMacFile):
    WriteJson(ReadMacFile(sMacFile),sMacFile.replace(".mac",".debug"))

def PrintLog(x):
    print x
    
def SeekToAnFi(macFile):
    next_value=macFile.read(1)
    while next_value:
        if next_value=="i":
            current=macFile.tell()
            res=macFile.read(3)
            if "FnA" in res:
                return
            macFile.seek(current)
        next_value=macFile.read(1)
    
def ReplaceVersionNumberAtPoint(macFile,old_val,new_val,log):
    current=macFile.tell()
    version,=unpack("<f",macFile.read(4))
    if version!=old_val:
        log("    >>> Found %f at %d. Skipping..."%(version,macFile.tell()-4))
        return
    macFile.seek(current)
    macFile.write(pack("<f",new_val))
    macFile.flush()
    log("    >>> Replaced %f with %f at %d"%(old_val,new_val,current))

def EditVersionNumber(sFile,old_val,new_val,log=lambda x : None):
    try:
        with open(sFile,"r+b") as macFile:
            log(">>> Processing %s..."%sFile)
            ReplaceVersionNumberAtPoint(macFile, old_val, new_val, log)
            try:
                while macFile.read(1):
                    SeekToAnFi(macFile)
                    ReplaceVersionNumberAtPoint(macFile, old_val, new_val, log)
            except:
                pass
    except:
        print traceback.format_exc()
        log(">>> Could not open %s"%sFile)




mac_file = ReadMacFile(r"W:\main\data\animations\civilians\umbrella\f00-000-00_layer-umbrella_mcivi.mac")

# mac_source_and_frames = ReadMacSourceAndFrames(r"W:\main\data\animations\civilians\stand\f00-000-00_stand-ar-smartdevice-talking_fcivi.mac")
# print mac_source_and_frames

# print ReadMacSource(r"W:\main\data\animations\civilians\layeredprops\a00-000-00_layered-glasses_fciv_000l.mac")
# #
# print mac_file['version']
# print mac_file['sourceFile']
# print mac_file['frames']

#
JSONFile = r"E:\_ORWELL\blahblabhlabh.json"
#
with open(JSONFile, 'w') as outfile:
    json.dump(mac_file, outfile, indent=4, sort_keys=True)

