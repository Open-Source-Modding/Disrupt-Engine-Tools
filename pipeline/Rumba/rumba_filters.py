from Common.file_helpers import get_files
from xml.etree.cElementTree import ElementTree, fromstring, ParseError
from Rumba.rumba_progress_bar import RumbaProgressWindow
from math import sqrt

def _get_attrib(child, child_to_find, attrib):
    try:
        if child.find(child_to_find) is not None:
            return child.find(child_to_find).attrib[attrib]
        else:
            return None
    except:
        return None

def filter_find_GI_only_shadow_caster(d_objects_by_types, find_parents, find_children):
    result_data_set = set()
    progress_window = RumbaProgressWindow()
    progress_window.ui.show()
    progress_window.ui.bar_1.setMaximum(len(d_objects_by_types.get('World_Object')))
    progress_window.ui.label_1.setText('Checking GI only shadow casters offenders in all World Layers')

    for world_object in d_objects_by_types.get('World_Object'):
        progress_window.update_bar_1()
        if world_object.entity_class == 'OmniLight' or world_object.entity_class == 'SpotLight' or world_object.entity_class == 'CapsuleLight': pass
        else : continue
        tree = ElementTree(file=world_object.filename)
        for object in tree.iter('Object'):
            element_id = object.get('Id')
            if element_id is None:
                continue
            if element_id.lower() != world_object.identifier:
                continue
            cs  = _get_attrib(object, 'Entity/Components/CDynamicLightComponent', 'bCastShadow')
            geo = _get_attrib(object, 'Entity/Components/CDynamicLightComponent/Affects', 'bGeometry')
            gi  = _get_attrib(object, 'Entity/Components/CDynamicLightComponent/Affects', 'bGlobalIllumination')
            if cs == "1" and geo == "0" and gi == "1":
                result_data_set.add(world_object)
    progress_window.ui.close()
    return result_data_set, 'GI_Offenders'

def lights_with_greater_radius_filter_extra(d_objects_by_types, find_parents, find_children, extra_value):
    result_data_set = set()
    progress_window = RumbaProgressWindow()
    progress_window.ui.show()
    progress_window.ui.bar_1.setMaximum(len(d_objects_by_types.get('World_Object')))
    progress_window.ui.label_1.setText('Checking GI only shadow casters offenders in all World Layers')

    for world_object in d_objects_by_types.get('World_Object'):
        progress_window.update_bar_1()
        if world_object.entity_class == 'OmniLight' or world_object.entity_class == 'SpotLight' or world_object.entity_class == 'CapsuleLight': pass
        else : continue
        tree = ElementTree(file=world_object.filename)
        for object in tree.iter('Object'):
            element_id = object.get('Id')
            if element_id is None:
                continue
            if element_id.lower() != world_object.identifier:
                continue
            radius  = _get_attrib(object, 'Entity/Components/CDynamicLightComponent', 'fLightCutOffRadius')
            if radius is None:
                continue
            if float(radius) > float(extra_value):
                result_data_set.add(world_object)
    progress_window.ui.close()
    return result_data_set, 'GI_Offenders'

def filter_non_updated_MSAA_materials(d_objects_by_types, find_parents, find_children):
    result_data_set = set()
    shaders_with_msaa =  set()
    files = get_files(r'W:\Main\data\engine\shaders\materialdescriptors', '.xml') 
    for f in files:
        tree = ElementTree (file=f)
        root = tree.getroot()
        shader_name = root.get('name')
        for elem in tree.iter('parameterprovider'):
            for parameter in elem.iter('parameter'):
                parameter_name = parameter.get('name')
                if parameter_name == "MSAAOptimizationHighQuality":
                    shaders_with_msaa.add(shader_name.lower())

    for material in d_objects_by_types.get('Material'):
        if material.shader in shaders_with_msaa and material.base_material == None:
            has_property = False
            for val in material.search_values:
                if "msaaoptimizationhighquality" in val: has_property = True
            
            if has_property == False : result_data_set.add(material)

    return result_data_set, 'MSAAOptimizationHighQuality_non_updated_materials'

def filter_projected_decals_by_box_size(d_objects_by_types, find_parents, find_children):
    result_data_set = set()
    for archetype in d_objects_by_types.get('Archetype'):
        if archetype.archetype_class == 'CollidableDecal':
            if archetype.projection_decal_box_offset is None:
                continue
            archetype.projection_box_size = str(archetype.projection_decal_box_offset + archetype.projection_decal_box_depth)
            result_data_set.add(archetype)
    return result_data_set, 'projection_box_size'


def filter_projected_decals_branding_texel_ratio(d_objects_by_types, find_parents, find_children):
    result_data_set = set()
    for geometry in d_objects_by_types.get('Geometry'):
        if not geometry.is_projected_decal:
            continue
        if 'branding' not in geometry.filename:
            continue
        geometry.texel_ratio = 0
        textures = find_children(geometry, 'Texture')
        color_texture = None
        for texture in textures:
            if 'basic_4x4' in texture.name:
                continue
            if 'color_swatch' in texture.name:
                continue
            if 'placeholder' in texture.name:
                continue
            # if 'branding' not in texture.filename:
            #     continue
            if '_c.' in texture.filename or '_albedo.' in texture.filename:
                color_texture = texture
        if color_texture is None:
            continue
        if geometry.size_x is None:
            continue
        print(geometry.name, color_texture.name)
        texels = color_texture.height_ps4 * color_texture.width_ps4
        surface = geometry.size_x * geometry.size_y
        geometry.texel_ratio = sqrt(texels / surface)
        result_data_set.add(geometry)
    print('patate')
    return result_data_set, 'texel_ratio'
