#!/usr/bin/env python3
from lxml import etree
from lxml.etree import iterparse
from attribute_getters import *
from event_processing import event_type_dispatcher
import os
import codecs
import time

PROFILE_MEMORY = False
PROFILE_TIME = False

try:
    from pympler.asizeof import asizeof
except ImportError:
    PROFILE_MEMORY = False
    PROFILE_TIME = False

'''
Process an XML file with invalid characters and replace them with 
question marks.
'''
def handle_invalid_file(filename):
    print("Attempting to fix invalid file: " + filename)
    BLOCKSIZE = 1048576 # one megabyte
    
    tempfile = filename.replace(".xml", "-fixed.xml")

    statinfo = os.stat(filename)
    print("File size: " + str(statinfo.st_size) + " bytes")

    counter = 0

    with codecs.open(filename, "r", 'us-ascii', errors='replace') as sourceFile:
        with open(tempfile, "w") as targetFile:
            while True:
                counter += BLOCKSIZE
                percent_done = counter / statinfo.st_size
                if counter % (10 * BLOCKSIZE) < BLOCKSIZE:
                    print("\r" + str(percent_done))
                contents = sourceFile.read(BLOCKSIZE)
                
                if "�" in contents:
                    contents = contents.replace("�", "?")
                    
                if not contents:
                    break
                    
                targetFile.write(contents)

    print("Fixed file")
    return tempfile

'''
Parse the entire XML file 
'''
def load_dict(filename):
    print("Loading file: " + filename)
    parser = etree.iterparse(filename)
        
    everything = {}
    
    tag_mapping = {'region': 'regions', \
                   'underground_region': 'underground_regions', \
                   'site': 'sites', \
                   'world_construction': 'world_constructions', \
                   'artifact':'artifacts', \
                   'historical_figure': 'historical_figures', \
                   'entity_population': 'entity_populations',\
                   'entity': 'entities',\
                   'historical_event': 'historical_events',\
                   'historical_event_collection': 'historical_event_collections',\
                   'historical_era':'historical_eras'}

    lower_level_tags = tag_mapping.keys()
    upper_level_tags = tag_mapping.values()
    
    #save names for fast lookup
    #TODO: not all tags will be needed
    for tag in lower_level_tags:
        everything[tag + '_names'] = {}
    
    #PROFILING
    if PROFILE_TIME:
        time_array = []
        start_time = time.clock()
    
    if PROFILE_MEMORY:
        memory_array = []
        memory_array.append(("At beginning : ", asizeof(everything)))
    
    temp_element_array = []
    for _, element in parser:
        if element.tag in lower_level_tags:
            
            if element.tag == 'historical_figure':
                element_data = load_hist_figure_data(element, everything)
            else: 
                element_data = load_generic_element_data(element, everything)
                                       
            temp_element_array.append(element_data)
            close_element(element)
            
        elif element.tag in upper_level_tags:
            print("Finishing: " + element.tag)
            
            #This "offset" is for indexing purposes. So, for example, perhaps the first historical figure in the
            #'historical_figures' section has id=5764. From there, the indexes progress one-by-one. So we can
            #set 'historical_figures_offset' to 5764. So then, accessing an element is easy and efficient; we just need to do
            #everything[element_type][id - offset]
            try:
                everything[element.tag + "_offset"] = temp_element_array[0]['id']
            except KeyError:
                print("Exception in creation of offset for " + element.tag + ", ignoring...")
                
            everything[element.tag] = temp_element_array
            temp_element_array = []
            
            if PROFILE_TIME:
                time_array.append([element.tag, time.clock() - start_time])
                start_time = time.clock() #measure time until next high-level tag is finished
                
            if PROFILE_MEMORY:
                memory_array.append(("Finishing " + element.tag + ": ", asizeof(everything)))
                
            close_element(element)
        
    if PROFILE_TIME:
        start_time = time.clock()
        
    parse_historical_events(everything)
    
    if PROFILE_TIME:
        time_array.append(['parsing historical events', time.clock() - start_time])
    
    if PROFILE_MEMORY:
        memory_array.append(("After parsing historical events: ", asizeof(everything)))
    
    #PRINT PROFILING INFO
    if PROFILE_TIME:
        total_time = 0
        print("\n\nTIMING INFO:")
        for e, t in time_array:
            print("Time taken for " + e + ": " + str(t) + "s")
            total_time += t
        print("Total time: " + str(total_time) + "s")
        
    if PROFILE_MEMORY:
        print("\n\nMEMORY INFO:")
        for i in range(0, len(memory_array)):
            difference = 0
            if (i >= 1):
                difference = memory_array[i][1] - memory_array[i-1][1]
            print(memory_array[i][0] + " : " + str(memory_array[i][1]/1024) + " KB || Difference: " + str(difference/1024) + " KB")
            
    return everything

'''
Makes the following changes to the master dictionary:
    -Adds a name to the historical_figure_names array

Returns an element data dictionary with the following structure:
    { 'events': [12521, 3462, 123, 733, 1324...],
      'hf_links': [ {'type':'mother', 'id':12415}, {'type':'father', 'id':1235}...],
      'entity_links' : [ {'type':'something', 'id':12415}, {'type':'somethingelse', 'id':1235}...],
    }
'''
def load_hist_figure_data(element, everything):
    element_data = {}
    element_data['events'] = []
    element_data['hf_links'] = []
    element_data['entity_links'] = []
    
    for attribute in element:
        #not loaded
        if attribute.tag in ['hf_skill', 'entity_former_position_link']:
            continue
        
        #save names in separate array for searching
        if attribute.tag in ["name", "animated_string"]:
            for attrib in element:
                if attrib.tag == "id":
                    hf_id = attrib.text
                    break
            everything['historical_figure_names'][hf_id] = attribute.text
            
        #These tags have tags nested within them, and there are multiple for each historical figure,
        #Here, we parse them separately and store their information in subdictionaries within lists.
        if attribute.tag in ['hf_link', 'entity_link']:
            children = attribute.getchildren()
            
            attribute_dict = {}
            attribute_dict['type'] = children[0].text
            attribute_dict['id'] = int(children[1].text)
            
            if attribute.tag == 'entity_link' and len(children) > 2:
                attribute_dict['strength'] = int(children[2].text)
                
            element_data[attribute.tag + 's'].append(attribute_dict)
        else: #other hf_fig attribute
        
            #attributes such as death year for hf_figs still alive
            #or some site coords
            if attribute.text == "-1" or attribute.text == "-1,-1":
                continue
                
            try:
                element_data[attribute.tag] = int(attribute.text)
            except (ValueError, TypeError):
                element_data[attribute.tag] = attribute.text

    return element_data
     
'''
Makes the following changes to the master dictionary:
    -Adds a single name to the <element_type>_names array
'''
def load_generic_element_data(element, everything):
    element_data = {}
    attributes = element.getchildren()
    #generic element
    #Add the element attributes to a dictionary representing the element
    for attribute in attributes:
        if attribute.text == "-1":
            continue
        
        if element.tag == "historical_event":
            #unimplemented events
            if attribute.tag == 'type' and attribute.text in ['add hf entity link', 'add hf site link', 'create entity position', 'creature devoured', 'hf new pet', 'item stolen', 'remove hf site link', 'remove hf entity link']:
                continue

        #save names in separate array for searching
        #TODO figure out what's happening here
        if attribute.tag == "name":
            element_id = None
            for attrib in element:
                if attrib.tag == "id":
                    element_id = attrib.text
                    break
            if element_id is not None:
                everything[element.tag + '_names'][element_id] = attribute.text
            else:
                everything[element.tag + '_names']['id'] = attribute.text
            
        try:
            element_data[attribute.tag] = int(attribute.text)
        except Exception:
            element_data[attribute.tag] = attribute.text

    return element_data
    
def close_element(element):
    element.clear()                 # clean up children
    while element.getprevious() is not None:
        del element.getparent()[0]  # clean up preceding siblings
    
def add_event_link_to_hf(hfid, event_id, everything):
    get_element(hfid, 'historical_figures', everything)['events'].append(event_id)

def parse_historical_events(everything):
    if not 'historical_events' in everything:
        return
    
    hfid_set = ['hfid', 'slayer_hfid', 'group_hfid', 'group_1_hfid', 'group_2_hfid', 'woundee_hfid',
                           'wounder_hfid', 'trickster_hfid', 'cover_hfid', 'hist_fig_id', 'target_hfid', 
                           'snatcher_hfid', 'changee_hfid', 'changer_hfid', 'hist_figure_id', 'hfid_target']
                           
    for event_data in everything['historical_events']:
        for key in event_data.keys():
            if key in hfid_set:
                add_event_link_to_hf(event_data[key], event_data['id'], everything)
