#!/usr/bin/env python3

def capitalize(string):
    words = string.split(' ')
    for i in range(len(words)):
        if words[i] not in ['the', 'a', 'of'] or i == 0:
            words[i] = words[i].capitalize()
    
    return ' '.join(words)

###################################
#----GENERIC ATTRIBUTE GETTERS----#
###################################

'''
an_id = a string, the id to get
everything = the main dictionary containing everything
a_type = The category, e.g. 'historical_figures'

Given these, will return an element from the database, accounting for the possible offset.
'''
def get_element(an_id, a_type, everything):  
    return everything[a_type][an_id - everything[a_type + '_offset']]

def get_name(an_id, a_type, everything):
    try:
        return capitalize(get_element(an_id, a_type, everything)['name'])
    except Exception:
            return capitalize(get_element(an_id, a_type, everything)['animated_string'])

#get an id from the name
def get_id(name, everything):
    name = name.lower()
    for tag in everything.keys():
        if not tag.endswith("_names"):
            continue
        for element_id in everything[tag]:
            if everything[tag][element_id] == name:
                return tag.replace("_names", ""), element_id
    print("Could not find name: " + name)
    return "", 0000

####################################
#----SPECIFIC ATTRIBUTE GETTERS----#
####################################

# (In alphabetical order...)

def get_event(event_id, everything):
    return everything['historical_events'][int(event_id) - everything['historical_events_offset']]
        
def get_ent(an_id, everything):
    return get_element(an_id, 'entities', everything)

def get_ent_name(an_id, everything):
    return get_name(an_id, 'entities', everything)

def get_hf(an_id, everything):
    return get_element(an_id, 'historical_figures', everything)

def get_hf_gender(an_id, everything):
    try:
        return capitalize(get_element(an_id, 'historical_figures', everything)['caste'])
    except KeyError:
        #Has no gender... Happens for deities.
        return ""

def get_hf_name(an_id, everything):
    return get_name(an_id, 'historical_figures', everything)

def get_hf_race(an_id, everything):
    try:
        return capitalize(get_element(an_id, 'historical_figures', everything)['race'])
    except KeyError:
        #Has no race... so it's a deity.
        return "Deity"
    
def get_site_name(site_id, everything):
    return capitalize(get_name(site_id, 'sites', everything))
    
def get_site_data(site_coords, everything):
    for site in everything['sites']:
        if site['coords'] == site_coords:
            return (site['id'], capitalize(site['name']))
    return (-1, "")
