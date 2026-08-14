import json
from os.path import join
import os
import xml.etree.cElementTree as ET
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
    ret = list(_get_files_iter(path, filter_extensions, b_subfolder=True))
    return ret

def get_resource_dict(nfo_files):
    resource_dict = {}
    for nfo_file in nfo_files:
        tree = ET.ElementTree(file=nfo_file)
        for elem in tree.iter("File"):
            resource_dict[elem.attrib.get("Crc")] = elem.attrib.get("Path")
    return resource_dict
            
def classifier(snapshot, nfo_resource_dict):
    with open(snapshot) as json_data:
        snapshot_dict = json.load(json_data)
        
    snapshot_resources = snapshot_dict.get("resources")    
    
    snapshot_wlus = snapshot_dict.get("loading_units")
    wlus_dict = {}
    for snapshot_wlu in snapshot_wlus:
        wlus_dict[snapshot_wlu["id"]] = snapshot_wlu
    
    categories_dict =  {"building_kit":[],
                        "building_low_res_geometry":[],
                        "building_low_res_texture":[],
                        "characters":[],
                        "vehicles":[],
                        "ui":[],
                        #"memory_size_geometry":[],
                        #"memory_size_texture":[],
                        "other":[],
                        }

    for resource in snapshot_resources:
        resource["wlu_types"] = set()
        for parent_resource in resource["parent_resources"]:
            wlu = wlus_dict.get(parent_resource, None)
            if wlu is None:
                resource["wlu_types"].add("systemic")
            else:
                resource["wlu_types"].add(wlu["category"])
                
        print resource["wlu_types"]
        
        id = str(int(resource["id"], 0)).replace("L","")
        name = nfo_resource_dict.get(id, None)
        
        # if resource["class_type"] == "CGeometryResource":
            # categories_dict["memory_size_geometry"].append(resource)
        # if resource["class_type"] == "CTextureResource":
            # categories_dict["memory_size_texture"].append(resource)
        
        if name is None:
            continue
        
        resource["name"] = name
        
        if resource["class_type"] == "CGeometryResource" or resource["class_type"] == "CTextureResource":
        
            if "building_kit" in name:
                categories_dict["building_kit"].append(resource)
                
            elif "building_low.xbg" in name:
                categories_dict["building_low_res_geometry"].append(resource)
                
            elif "generated" in name and "atlas" in name:
                categories_dict["building_low_res_texture"].append(resource)
                
            elif "characters" in name:
                categories_dict["characters"].append(resource)
                
            elif "ui\\" in name:
                categories_dict["ui"].append(resource)
                
            elif "vehicles_nexus" in name:
                categories_dict["vehicles"].append(resource)
                
            else:
                categories_dict["other"].append(resource)

    return categories_dict
    
def write_output(categories_dict):
    output_dict = {}
    
    for category, items in categories_dict.iteritems():
        for item in items:
            category_dict = {"family":category}
            output_dict[item["id"]] = category_dict
    
    dir_path = os.path.dirname(os.path.realpath(__file__))
    output_file = r"classified_data.json"
    output_file = join(dir_path, output_file)
    
    with open(output_file, 'w') as outfile:
        json.dump(output_dict, outfile, indent=4)
        
def main():
    path_to_snapshot = r"W:\main\td_tools\gcassel\snapshot"
    snapshot_files = get_files(path_to_snapshot, "telrs", "")
    snapshot_file = None
    if len(snapshot_files) == 1:
        snapshot_file = snapshot_files[0]
    else:
        print "No snapshot found, or more than one found. There can be only ONE! *KLING*"
        
    if snapshot_file is None:
        return
    print "got snapshot"
    extra = get_files(path_to_snapshot, "nfo", "")
    # print "got nfos"
    # nfo_resource_dict = get_resource_dict(nfo_files)
    # print "parsed nfos"
    extra_resource_dict
    categories_dict = classifier(snapshot_file, extra_resource_dict)
    print "classified stuff"
    write_output(categories_dict)
    print "wrote output"
    
    ###############################################
    grand_total = 0
    for cat, items in categories_dict.it eritems():
        sum = 0
        for item in items:
            sum += int(item["memory_size"])
        
        sum = float(sum) / 1048576.0 
        
        print cat, "%.2f" % sum#, len(items)
        grand_total += sum
    print "TOTAL", grand_total
    ###############################################
if __name__ == "__main__":
    main()