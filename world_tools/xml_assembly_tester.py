import xml.etree.cElementTree as ET
from xml.dom import minidom

world_layer = '''<LayerContent BBoxMin="16.8542,13.3328" BBoxMax="22.1717,17.6633">
</LayerContent>'''

object = '''<Object Type="DebugAnnotationShape" Id="{E9D8D137-C19B-4220-BE96-46F3D71370A0}" Name="DebugAnnotationShape_2" Pos="19.5701,15.4334,0.1" WorldPos="19.5701,15.4334,0.1" ColorRGB="16763904" EntityClass="DebugAnnotationShape" Height="10">
    <Entity disNomadObjectId="9223372086276922673" hidName="DebugAnnotationShape_2" hidEntityClass="CEntity" hidResourceCount="1" hidPos="19.5701,15.4334,0.1" hidAngles="0,0,0" hidPos_precise="1100779412,1098313506,1036831951" hidConstEntity="0" hidFakeArchetypeId="debugannotationshape" wlucatLoadingUnitCategoryV3="3" bPoolable="0" bEnableLocalProperties="0" bPoolClearOnUnused="1">
        <hidGroupIds />
        <hidBBox vectorBBoxMin="0,0,0" vectorBBoxMax="0,0,0" />
        <Components>
            <CDebugAnnotationShapeComponent hidHasAliasName="0">
                <DebugAnnotationObject bEnabled="1" bEnableVisibilityDistanceTest="1" fVisibilityDistance="30" Points="Count(5) 1.60157,-1.10054,-0.0000000149012;1.50915,0.79204,-0.0000000149012;-1.36888,1.22993,-0.0000000223517;-1.71595,0.150137,-0.00000000745058;-0.0258923,-1.07157,-0.00000000745058;" fHeight="10" clrColor="0,1,0" fAlpha="0.2" />
            </CDebugAnnotationShapeComponent>
            <CEditableComponent hidHasAliasName="0" gigGIGroup="4294967295">
                <TerrainModifier bEnabled="0" fFlatRadius="1" fFalloff="0" fHeightModifier="0" />
                <Atlas bExportToAtlas="0" atlastypeElementType="" />
                <AdjustToCurvedRoad bAdjustToCurvedRoad="0" />
            </CEditableComponent>
            <CEventComponent hidHasAliasName="0">
                <hidLinks />
                <hidBatchedLinks />
            </CEventComponent>
        </Components>
    </Entity>
    <Points>
        <Point Pos="1.60157,-1.10054,-0.0000000149012" />
        <Point Pos="1.50915,0.79204,-0.0000000149012" />
        <Point Pos="-1.36888,1.22993,-0.0000000223517" />
        <Point Pos="-1.71595,0.150137,-0.00000000745058" />
        <Point Pos="-0.0258923,-1.07157,-0.00000000745058" />
    </Points>
</Object>'''

def construct_xml(base_element, new_element):
    ET.fromstring(base_element)
    tree = ET.ElementTree(ET.fromstring(base_element))
    root = tree.getroot()    
    
    for i in range(10):
        new_element = ET.fromstring(object)
        new_element.set("Name", str(i))
        root.append(new_element)
        
    return root

def write_xml(root, file_to_write):
        for elem in root.iter('*'):
            if elem.text is not None:
                elem.text = elem.text.strip()
            if elem.tail is not None:
                elem.tail = elem.tail.strip()
        rough_string = ET.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="\t")
        
        file = open(file_to_write,"w")
        file.write(pretty_xml.replace('<?xml version="1.0" ?>\n',""))
        file.close()
    
def main():
    xml = construct_xml(world_layer, object)
    write_xml(xml, r"W:\main\td_tools\gcassel\xml_assembly_test.xml")
    
main()
    
    