'''This modules classifies all the resource in a snapshot'''
import json
import sys
import gzip

def deduce_domain(resource_id, resource, extra):
    '''Using the resource name, deduce the domain of the resource'''
    
    cat = {  
            0:"_unknown_",
            1:"Graphic",
            2:"Amination",
            3:"Sound",
            4:"Engine",
            99:"Domain Other",
          }
    
    try:        
        name = extra['resources'][resource_id]['name']
        class_name = extra['resources'][resource_id]['class_name']
        
        if name is None:
            return cat[0]
            
        if class_name == "CGeometryResource" or class_name == "CTextureResource" or class_name == "CBinkResource" or class_name == "CSplineLoftLowResGfxResource" or class_name == "CSplineLoftHiResGfxResource" or class_name == "CLightProbesResource" or class_name == "CRealtreeResource" or class_name == "CFireTextureResource":
            return cat[1]
            
        elif class_name == "CMoveResource" or class_name == "CPoseAnimationResource" or class_name == "CAnimationTrackCollectionResource" or class_name == "CAnimationResource":
            return cat[2]

        elif class_name == "CSoundResource":
            return cat[3]
            
        return cat[99]
            
    except KeyError:
        pass
    return None
    
def deduce_department(resource_id, resource, extra):
    '''Using the resource name, deduce the department of the resource'''
    
    cat = {  
            0:"_unknown_",
            1:"World",
            2:"Characters",
            3:"Vehicles",
            4:"Mission",
            5:"UI",
            6:"Preloaded",
            7:"Illegal",
            8:"Interior",
            9:"LMA",
            10:"SAS",
            11:"HMA",
            12:"Lighting & Rendering",
            13:"VFX",
            14:"Video",
            99:"Department Other",
          }
     
    illegal_graphics_folders = [
                                "graphics\\_generic_textures\\",
                                "graphics\\_geometries\\",
                                "graphics\\_Textures\\",
                                "graphics\\_Textures_CURRENT_GEN\\",
                                "graphics\\buildings\\",
                                "graphics\\buildings_proto\\",
                                "graphics\\Editor\\",
                                "graphics\\electrical_network\\",
                                "graphics\\Fonts\\",
                                "graphics\\Game_Ingredients\\",
                                "graphics\\ies\\",
                                "graphics\\infrastructures\\",
                                "graphics\\kom\\",
                                "graphics\\landscape\\",
                                "graphics\\leveldesign\\",
                                "graphics\\lofts\\",
                                "graphics\\metrics\\",
                                "graphics\\objects\\",
                                "graphics\\Orwell__generic_textures\\",
                                "graphics\\Orwell__Textures\\",
                                "graphics\\plaza_loft\\",
                                "graphics\\PostFX\\",
                                "graphics\\roads\\",
                                "graphics\\SFX_3DMeshes\\",
                                "graphics\\sidewalk\\",
                                "graphics\\Sky\\",
                                "graphics\\techart\\",
                                "graphics\\terrain\\",
                                "graphics\\test\\",
                                "graphics\\Users\\",
                                "graphics\\vegetation\\",
                                "graphics\\Vehicles\\",
                                "graphics\\water\\",
                            ]
    
    try:        
        name = extra['resources'][resource_id]['name']
        class_name = extra['resources'][resource_id]['class_name']
        
        if name is None:
            return cat[0]
            
        for folder in illegal_graphics_folders:
            if folder.lower() in name:
                return cat[7]

        if "lightprobes\\" in name or "localcubemaps\\" in name:
            return cat[12]
            
        if "graphics\\gfx\\" in name:
            return cat[13]
            
        if ".bik" in name:
            return cat[14]
            
        if "ui\\" in name or "ingamemap\\" in name:
            return cat[5]
        
        if "Near" in resource["loading_unit_categories"] or "Far" in resource["loading_unit_categories"] or "FarAway" in resource["loading_unit_categories"]:
            return cat[1]
            
        if "Interior" in resource["loading_unit_categories"]:
            return cat[8]
            
        if "LMA" in resource["loading_unit_categories"]:
            return cat[9]
        
        if "SAS" in resource["loading_unit_categories"]:
            return cat[10]
            
        if "HMA" in resource["loading_unit_categories"]:
            return cat[11]
            
        if len(resource["loading_unit_categories"]) == 0 or len(resource["loading_unit_categories"]) == 1 and "PreloadCache" in resource["loading_unit_categories"]:
            #if "vehicles" in name or "vehicles_nexus" in name:
            if "vehicles_nexus" in name:
                return cat[3]
            if "characters" in name:
                return cat[2]
                
        # if len(resource["loading_unit_categories"]) == 1 and "StreamingCache" in resource["loading_unit_categories"]:
            # return cat[1]
                
        if "Mission" in resource["loading_unit_categories"]:
            return cat[4]
            
        if "PreloadCache" in resource["loading_unit_categories"] or "AlwaysLoaded" in resource["loading_unit_categories"]:
            return cat[6]
        
        return cat[99]
            
    except KeyError:
        pass
    return None

def deduce_division(resource_id, resource, extra):
    '''Using the resource name, deduce the division of the resource'''
    
    cat = {  
            0:"_unknown_",
            1:"Building Kit",
            2:"Building Low Res Geometry",
            3:"Building Low Res Texture",
            4:"Level Art",
            5:"Tech",
            6:"Animals",
            7:"Terrain",
            8:"Generated",
            9:"Branding",
            99:"Division Other",
          }
    
    legal_level_art_folders = [
                                "graphics\\lights\\",
                                "graphics\\geometry\\",
                                "graphics\\character_props\\",
                                "graphics\\cinematics\\",
                                "graphics\\gameplay_ingredients\\",
                                "graphics\\_texture\\",
                             ]  
    
    try:        
        name = extra['resources'][resource_id]['name']
        class_name = extra['resources'][resource_id]['class_name']

        if name is None:
            return cat[0]
            
        if class_name == "CGeometryResource" or class_name == "CTextureResource" or class_name == "CSplineLoftLowResGfxResource" or class_name == "CSplineLoftHiResGfxResource":
        
            if "graphics\\Characters\\animal\\" in name:
                return cat[6]
                
            if "generated\\sdat" in name:
                return cat[7]
            
            if "building_low.xbg" in name:
                return cat[2]
        
            if "generated\\" in name and "atlas" in name:
                return cat[3]
        
            if "generated\\" in name:
                return cat[8]
        
            if "geometry\\building_kit\\" in name:
                return cat[1]
                
            if "graphics\\tech\\" in name:
                return cat[5]
                
            if "branding\\" in name:
                return cat[9]
                
            for folder in legal_level_art_folders:
                if folder.lower() in name:
                    return cat[4]
                
            return cat[99]
                
    except KeyError:
        pass
    return None

def deduce_debug(resource_id, resource, extra):
    '''Using the resource name, deduce the domain of the resource'''
    
    cat = {  
            0:"_unknown_",
            1:"DEBUG-Graphic-World",
            2:"DEBUG-Graphic-Characters",
            3:"DEBUG-Graphic-Vehicles",
            4:"DEBUG-Graphic-Mission",
            5:"DEBUG-Graphic-UI",
            6:"DEBUG-Graphic-StreamingCache",
            7:"DEBUG-Graphic-Illegal",
            8:"DEBUG-Graphic-Interior",
            9:"DEBUG-Graphic-LMA",
            10:"DEBUG-Graphic-SAS",
            11:"DEBUG-Graphic-HMA",
            12:"DEBUG-Graphic-Lighting & Rendering",
            99:"DEBUG-Graphic-Department_Other",
          }
    try:
        name = extra['resources'][resource_id]['name']
        class_name = extra['resources'][resource_id]['class_name']
        
        if class_name == "CGeometryResource" or class_name == "CTextureResource" or class_name == "CBinkResource" or class_name == "CSplineLoftLowResGfxResource" or class_name == "CSplineLoftHiResGfxResource" or class_name == "CLightProbesResource" or class_name == "CRealtreeResource" or class_name == "CFireTextureResource":
            if "lightprobes\\" in name or "localcubemaps\\" in name:
                return cat[12]
            
            if "Near" in resource["loading_unit_categories"] or "Far" in resource["loading_unit_categories"] or "FarAway" in resource["loading_unit_categories"]:
                return cat[1]
                
            if "Interior" in resource["loading_unit_categories"]:
                return cat[8]
                
            if "LMA" in resource["loading_unit_categories"]:
                return cat[9]
            
            if "SAS" in resource["loading_unit_categories"]:
                return cat[10]
                
            if "HMA" in resource["loading_unit_categories"]:
                return cat[11]
                
            if len(resource["loading_unit_categories"]) == 0 or len(resource["loading_unit_categories"]) == 1 and "PreloadCache" in resource["loading_unit_categories"]:
                #if "vehicles" in name or "vehicles_nexus" in name:
                if "vehicles_nexus" in name:
                    return cat[3]
                if "characters" in name:
                    return cat[2]
                    
            if len(resource["loading_unit_categories"]) == 1 and "StreamingCache" in resource["loading_unit_categories"]:
                return cat[6]
                    
            if "Mission" in resource["loading_unit_categories"]:
                return cat[4]
     
            if "\\ui\\" in name or "\\ingamemap\\" in name:
                return cat[5]
                
            if "PreloadCache" in resource["loading_unit_categories"] or "AlwaysLoaded" in resource["loading_unit_categories"]:
                return cat[1]
                
            return cat[99]
            
    except KeyError:
        pass
    return None
        
def print_results(output_dict, resources_dict):
    '''
    Prints the output by category and the total in MB.
    '''
    dict_to_print = {}
    for key, value_dict in output_dict.iteritems():
        if key == "classification_axes":
            continue
        for id, categories_dict in value_dict.iteritems():
            for category, data in categories_dict.iteritems():
                if data not in dict_to_print.keys():
                    dict_to_print[data] = 0
                dict_to_print[data] += int(resources_dict[id].get("memory_size"))
        
    for category, sum in dict_to_print.iteritems():
        print category, "%.2f" % (float(sum) / 1048576.0)
    
def classify(telrs_path, extra_path, output_path, print_output=False):
    '''
    Classifies the resources in the file identified by 'telrs_path',
    using the data in the 'extra_path', and outputting the result in 'output_path'
    '''
    print "Open Snapshot file."
    with gzip.open(telrs_path) as json_data:
        snapshot = json.load(json_data)

    print "Open Extra File."
    with gzip.open(extra_path) as json_data:
        extra = json.load(json_data)

    resources_dict = snapshot['resources']
    loading_units_dict = snapshot['loading_units']
    instances_dict = snapshot['instances']

    print "Classify Resources."
    classified_resources = {}
    for resource_id, resource in resources_dict.iteritems():
        resource["loading_unit_categories"] = set() 
        for instance in resource.get("instances"):
            for loading_unit in instances_dict.get(instance)["loading_units"]:
                resource["loading_unit_categories"].add(loading_units_dict.get(loading_unit).get("category"))
        
        classified_resources[resource_id] =  {
                                        'Domain': deduce_domain(resource_id, resource, extra),
                                        'Department': deduce_department(resource_id, resource, extra),
                                        'Division': deduce_division(resource_id, resource, extra),
                                        #'Debug': deduce_debug(resource_id, resource, extra),
                                    }
                                    
    output_dict = {'classification_axes': ['Domain', 'Department', 'Division'], 'classified_resources': classified_resources}
        
    # Add an analizer function here, to find weird data like: building texture on a character, or a character texture in world WLUs.

    print "Write output file."
    with gzip.open(output_path, 'w') as outfile:
        json.dump(output_dict, outfile, indent=4)
        
    if print_output:
        print_results(output_dict, resources_dict)

if __name__ == "__main__":
    # classify(*sys.argv[1:])
    
    #telrs_path = r"W:\main\td_tools\gcassel\snapshot\resource_snapshot.telrs"
    telrs_path = r"W:\main\td_tools\gcassel\snapshot\2017.10.17-14.53.39.6b38_vtheriault-2017-10-17- 9-40-43-90_resource_snapshot.telrs"
    extra_path = r"W:\main\td_tools\gcassel\snapshot\resource_snapshot.telrs_extra"
    output_path = r"W:\main\td_tools\gcassel\snapshot\result.telrs_classified"
    classify(telrs_path, extra_path, output_path, True)