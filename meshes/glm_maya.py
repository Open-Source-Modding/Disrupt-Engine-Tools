#GLM operations

# Useful
# https://stackoverflow.com/questions/26845134/autodesk-maya-api-import-geometry
# http://forums.cgsociety.org/archive/index.php?t-795493.html
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya # as om

def test():
    verts = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)]
    faces = [(0, 1, 2), (1, 2, 3)]
    create(verts, faces, False)
    create_geometry(verts, faces)

def create(verts, faces, merge=True):
    '''
    Given a list of vertices (iterables of floats) and a list of faces (iterable of integer vert indices),
    creates and returns a maya Mesh
    '''

    cmds.select(cl=True)
    outputMesh = OpenMaya.MObject()

    numFaces = len(faces)
    numVertices = len(verts)

    # point array of plane vertex local positions
    points = OpenMaya.MFloatPointArray()
    for eachVt in verts:
        p = OpenMaya.MFloatPoint(eachVt[0], eachVt[1], eachVt[2])
        points.append(p)

    # vertex connections per poly face in one array of indexs into point array given above
    faceConnects = OpenMaya.MIntArray()
    for eachFace in faces:
        for eachCorner in eachFace:
            faceConnects.append(eachCorner)

    # an array to hold the total number of vertices that each face has
    faceCounts = OpenMaya.MIntArray()
    for c in range(0, numFaces, 1):
        faceCounts.append(3)

    # create mesh object using arrays above and get name of new mesh
    meshFS = OpenMaya.MFnMesh()
    newMesh = meshFS.create(numVertices, numFaces, points, faceCounts, faceConnects, outputMesh)
    nodeName = meshFS.name()
    cmds.sets(nodeName, add='initialShadingGroup')
    cmds.select(nodeName)
    meshFS.updateSurface()
    # this is useful because it deletes stray vertices (ie, those not used in any faces)
    if merge:
        cmds.polyMergeVertex(nodeName, ch=0)
    meshFS.updateSurface()
    return nodeName

def create_geometry(verts, faces):
   cmds.constructionHistory(tgl = 'off')
   results = []
   for f in faces:
       points = [verts[i] for i in f]
       results += cmds.polyCreateFacet( p = points, ch = 0)
   cmds.polyUnite(results, ch=0)
   cmds.polyMergeVertex(d=0, ch=0)
   cmds.constructionHistory(tgl = 'on')

def readGlm(path):
    print "load here"

def writeGlm(path, glmData):
    print "save here"