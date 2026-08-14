##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##
##
## python shader reader 
##
##  ##  ## ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##  ##

# TODO: move maya bits to their own .py
import maya.cmds as cmds

# globals

class ShaderInfo:
    """A class for storing shader information"""
    name = ''
    transformName = ''
    timeList = []
    valueList = []
    inAngleList = []
    outAngleList = []
    inWeightList = []
    outWeightList = []
    inTangentTypeList = []
    outTangentTypeList = []
    inGlobalTangentTypeList = []
    outGlobalTangentTypeList = []

def ReadXml(shaderFile):
    """Reads shader xml and stores in ShaderInfo"""
    for i, transform in enumerate(transformList):
            #print '\n\n***********'
            #print 'sourceAnim: %s, %s' % (i, transform)
            #print vars(sourceAnim[i])
            if sourceAnim[i].timeList != None:
                for k, timeVal in enumerate(sourceAnim[i].timeList):
                    cmds.setKeyframe( obj, t=timeVal, at=transform, v=sourceAnim[i].valueList[k] )
                    # set the tangents. Set the type separate, otherwise stepped tangents do not apply correctly.
                    cmds.keyTangent( obj, attribute=transform, time=(timeVal,), inAngle=sourceAnim[i].inAngleList[k], outAngle=sourceAnim[i].outAngleList[k], inWeight=sourceAnim[i].inWeightList[k], outWeight=sourceAnim[i].outWeightList[k])
                    cmds.keyTangent( obj, attribute=transform, time=(timeVal,), inTangentType=sourceAnim[i].inTangentTypeList[k], outTangentType=sourceAnim[i].outTangentTypeList[k] )

def BuildMayaShader(shaderInfo):
	"""Reads shaderInfo param and builds equivelant maya shader"""

def ApplyMayaShader(obj, mayaShader):
	"""Applies maya shader to obj"""
	