#!/usr/bin/env python3
from lxml import etree
from lxml.etree import iterparse
from attribute_getters import *
from event_processing import event_type_dispatcher

def load_dict(filename):
    parser = etree.iterparse(filename)
    everything = {}
 
    #There are a handful of "upper-level" tags. This includes historical_figures, sites, entities, etc.
    #Loop through these. Inefficiency... the lower-level tags are looped through, but just ignored.
    for item in parser:
        if item[1].tag == 'df_world':
            for element in item[1].getchildren():
                if element.tag == 'historical_figures':
                    element_data = load_historical_figures(element)
                else:
                    #A lot of these tag types are just single-level, so we can just do this.
                    element_data = load_generic_element(element)
                everything[element.tag] = element_data[0]
                #This "offset" is for indexing purposes. So, for example, perhaps the first historical figure in the
                #'historical_figures' section has id=5764. From there, the indexes progress one-by-one. So we can
                #set 'historical_figures_offset' to 5764. So then, accessing an element is easy and efficient; we just need to do
                #everything[element_type][id - offset]
                everything[element.tag + '_offset'] = element_data[1]
            break
    #parse_historical_events(everything)
    return everything

'''
Given an "upper-level" tag, load the gigantic dictionary with every piece of data in that category.
This basically goes two levels down, so we have historical_figures -> historical_figure -> data for that historical_figure
At the end, the dictionary looks like this:
everything = {'historical_figures' : [ {'id' : '57', 'race': 'amphibian man', 'name': 'Urist McAmphibianMan'}, { another historical figure, etc.} ], 'historical_figures_offset' : '57'}

So basically, it's a dictionary that maps strings to lists, where each list is a list of 
dictionaries that map strings to strings. 
'''
def load_generic_element(element_category):
    elements_xml = element_category.getchildren()
    elements_list = []
    offset = None
    
    #For each element,
    for element in elements_xml:
        element_dict = {}
        attributes = element.getchildren()

        #Add the element attributes to a dictionary representing the element
        for attribute in attributes:
            if((offset is None) and (attribute.tag == 'id')):
                offset = int(attribute.text)
                
            element_dict[attribute.tag] = attribute.text
            
        element_dict['events'] = []
        elements_list.append(element_dict)
        
    return (elements_list, offset)

def load_historical_figures(element_category):
    elements_xml = element_category.getchildren()
    elements_list = []
    offset = None

    #For each element,
    for element in elements_xml:
        element_dict = {}

        element_dict['events'] = []
        element_dict['hf_links'] = []
        element_dict['entity_links'] = []

        attributes = element.getchildren()

        #Add the element attributes to a dictionary representing the element
        for attribute in attributes:
            if((offset is None) and (attribute.tag == 'id')):
                offset = int(attribute.text)


            #These tags have tags nested within them, and there are multiple for each historical figure,
            #Here, we parse them separately and store their information in subdictionaries within lists.
            if attribute.tag not in ['hf_link', 'entity_link', 'hf_skill', 'entity_former_position_link']:
                element_dict[attribute.tag] = attribute.text

            elif attribute.tag == 'hf_link':
                hf_link_dict = {}
                for link_info in attribute.getchildren():
                    hf_link_dict[link_info.tag] = link_info.text 
                element_dict['hf_links'].append(hf_link_dict)

            elif attribute.tag == 'entity_link':
                entity_link_dict = {}
                for link_info in attribute.getchildren():
                    entity_link_dict[link_info.tag] = link_info.text
                element_dict['entity_links'].append(entity_link_dict)

        elements_list.append(element_dict)

    return (elements_list, offset)
    
def add_event_link_to_hf(hfid, event_id, everything):
    get_element(hfid, 'historical_figures', everything)['events'].append(event_id)

def parse_historical_events(everything):
    for event_data in everything['historical_events']:
        for key in event_data.keys():
            if key in set(['hfid', 'slayer_hfid', 'group_hfid', 'group_1_hfid', 'group_2_hfid', 'woundee_hfid',
                           'wounder_hfid', 'trickster_hfid', 'cover_hfid', 'hist_fig_id', 'target_hfid', 
                           'snatcher_hfid', 'changee_hfid', 'changer_hfid', 'hist_figure_id', 'hfid_target',]):
                if event_data[key] != '-1':
                    add_event_link_to_hf(event_data[key], event_data['id'], everything)
        event_type_dispatcher(event_data['id'], everything)
            
    '''
    for var in range(5500, 6100):
        print(get_name(var, 'historical_figures', everything) + ' events:')
        for i in get_element(var, 'historical_figures', everything)['events']:
            print_event_info(i, everything)
    '''