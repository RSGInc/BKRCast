import array as _array
import inro.emme.desktop.app as app
import inro.modeller as _m
import inro.emme.matrix as ematrix
import inro.emme.database.matrix
import inro.emme.database.emmebank as _eb
import json
import numpy as np
import time
import os,sys
import h5py
import Tkinter, tkFileDialog
import multiprocessing as mp
import subprocess
import csv 
from multiprocessing import Pool
import pandas as pd

project = 'Projects/LoadTripTables/LoadTripTables.emp'
fac_type_dict = {'highway' : 'ul3 = 1 or ul3 = 2', 'arterial' : 'ul3 = 3 or ul3 = 4 or ul3 = 6', 'connectors' : 'ul3 = 5'}
extra_attributes_dict = {'@tveh' : 'total vehicles', '@mveh' : 'medium trucks', '@hveh' : 'heavy trucks', '@vmt' : 'vmt',\
                         '@vht' : 'vht'}
sound_cast_net_dict = {'5to6' : 'ni', '6to7' : 'am', '7to8' : 'am', '8to9' : 'am', '9to10' : 'md',\
                     '10to14' : 'md', '14to15' : 'md', '15to16' : 'pm', '16to17' : 'pm',\
                      '17to18' : 'pm', '18to20' : 'ev', '20to5' : 'ni'}
transit_tod = ['6to7', '7to8', '8to9', '9to10']
#input files:
counts_file = 'TrafficCounts_Mid.txt'
#output_files: 
net_summary_file = 'network_summary.csv'
counts_output_file = 'counts_output.csv'
screenlines_file = 'screenline_volumes.csv'

class EmmeProject:
    def __init__(self, filepath):
        self.desktop = app.start_dedicated(True, "cth", filepath)
        self.m = _m.Modeller(self.desktop)
        pathlist = filepath.split("/")
        self.fullpath = filepath
        self.filename = pathlist.pop()
        self.dir = "/".join(pathlist) + "/"
        self.bank = self.m.emmebank
        self.tod = self.bank.title
        self.current_scenario = list(self.bank.scenarios())[0]
        self.data_explorer = self.desktop.data_explorer()
    def change_active_database(self, database_name):
        for database in self.data_explorer.databases():
            #print database.title()
            if database.title() == database_name:
                
                database.open()
                print 'changed'
                self.bank = self.m.emmebank
                self.tod = self.bank.title
                print self.tod
                self.current_scenario = list(self.bank.scenarios())[0]
    def create_extras(self, type, name, description):
        NAMESPACE = "inro.emme.data.extra_attribute.create_extra_attribute"
        create_extras = self.m.tool(NAMESPACE)
        create_extras(extra_attribute_type=type, extra_attribute_name = name, extra_attribute_description = description, overwrite=True)
    def link_calculator(self):
        spec = {u'type': u'NETWORK_CALCULATION', u'selections': {u'link': u'all'}, u'expression': u'1', u'result': u'@tmpl1', u'aggregation': None}
        NAMESPACE = "inro.emme.network_calculation.network_calculator"
        network_calc = self.m.tool(NAMESPACE)
        network_calc(spec)
def json_to_dictionary(dict_name):

    #Determine the Path to the input files and load them
    input_filename = os.path.join('D:/soundcast/soundcat/inputs/skim_params/',dict_name+'.txt').replace("\\","/")
    my_dictionary = json.load(open(input_filename))

    return(my_dictionary)
 
def calc_vmt_vht_delay_by_ft(modeler):
    ###calculates vmt, vht, and delay for all links and returns a nested dictionary with key=metric(e.g. 'vmt') 
    #and value = dictionary where dictionary has key = facility type(e.g. 'highway') and value = sum of metric 
    #for that facility type
  
     network_calc = modeler.tool("inro.emme.network_calculation.network_calculator")
     
     #convert truck-auto equivalents back to trucks:
     #medium trucks
     network_calc_spec = json_to_dictionary("link_calculation")
     mod_spec = network_calc_spec
     mod_spec["result"] = "@mveh"
     mod_spec["expression"] = '@metrk/1.5'
     network_calc(mod_spec)
    
     #heavy trucks:
     mod_spec = network_calc_spec
     mod_spec["result"] = "@hveh"
     mod_spec["expression"] = '@hvtrk/2'        
     network_calc(mod_spec)
     
     ####################still need to do*****************************
     #hdw- number of buses:
     #mod_spec = network_calc_spec
     #mod_spec["result"] = "@hdw"
     #mod_spec["expression"] = 'hdw'
     #network_calc(mod_spec)
     
     #calc total vehicles, store in @tveh 
     str_expression = '@svtl1 + @svtl2 + @svtl3 + @svnt1 + @h2tl1 + @h2tl2 + @h2tl3 + @h2nt1 + @h3tl1\
                       + @h3tl2 + @h3tl3 + @h3nt1 + @lttrk + @mveh + @hveh'
     mod_spec = network_calc_spec
     mod_spec["result"] = "@tveh"
     mod_spec["expression"] = str_expression
     #mod_spec["selections"]["link"] = 'ALL'
     network_calc(mod_spec)
     
     #a dictionary to hold vmt/vht/delay values:
     results_dict = {}
     #dictionary to hold vmts:
     vmt_dict = {}
     #calc vmt for all links by factilty type and get sum by ft. 
     for key, value in fac_type_dict.iteritems():    
        mod_spec = network_calc_spec
        mod_spec["result"] = "@vmt"
        mod_spec["selections"]["link"] = value
        mod_spec["expression"] = "@tveh * length"
        #x stores a dictionary of the results, including sum of links
        x = network_calc(mod_spec)
        #total vmt by ft:
        vmt_dict[key] = x['sum']
     #add to results dictionary
     results_dict['vmt'] = vmt_dict
    
     #Now do the same for VHT:
     vht_dict = {}
     for key, value in fac_type_dict.iteritems():    
        mod_spec = network_calc_spec
        mod_spec["result"] = "@vht"
        mod_spec["selections"]["link"] = value
        mod_spec["expression"] = "@tveh * timau / 60"
        x = network_calc(mod_spec)
        vht_dict[key] = x['sum']
     results_dict['vht'] = vht_dict

     #Delay:
     delay_dict = {}
     for key, value in fac_type_dict.iteritems():    
        mod_spec = network_calc_spec
        mod_spec["result"] = None
        mod_spec["selections"]["link"] = value
        mod_spec["expression"] = "@tveh*(timau-(length*60/ul2))/60"
        x = network_calc(mod_spec)
        delay_dict[key] = x['sum']
     
     results_dict['delay'] = delay_dict
     return results_dict

def get_link_counts(EmmeProject, df_counts, tod):
    #get the network for the active scenario
     network = EmmeProject.current_scenario.get_network()
     list_model_vols = []
     for item in df_counts.index:
         i = list(item)[0]
         j = list(item)[1]
         link = network.link(i, j)
         x = {}
         x['loop_INode'] = i
         x['loop_JNode'] = j
         if link <> None:
            x['vol' + tod] = link['@tveh']   
         else:
            x['vol' + tod] = None
         list_model_vols.append(x)
     print len(list_model_vols)
     df =  pd.DataFrame(list_model_vols)
     df = df.set_index(['loop_INode', 'loop_JNode'])
     return df
def get_unique_screenlines(EmmeProject):
    network = EmmeProject.current_scenario.get_network()
    unique_screenlines = []
    for link in network.links():
        if link.type <> 90 and link.type not in unique_screenlines:
            unique_screenlines.append(str(link.type))
    return unique_screenlines
def get_screenline_volumes(screenline_dict, modeler):

    network_calc = modeler.tool("inro.emme.network_calculation.network_calculator")
    network_calc_spec = json_to_dictionary("link_calculation")
    for screen_line in screenline_dict.iterkeys():
        mod_spec = network_calc_spec
        mod_spec["result"] = None
        mod_spec["selections"]["link"] = screen_line
        mod_spec["expression"] = "@tveh"
        #mod_spec["aggregation"] = "+"
        x = network_calc(mod_spec)
        screenline_dict[screen_line] = screenline_dict[screen_line] + x['sum']

#def get_transit_boardings(EmmeProject):
#    network = EmmeProject.current_scenario.get_network()
#    transit_attributes_list = []
#    for transit_line in network.transit_lines():
#        x = {}
#        x[lineID] = transit_line.id
#        x[time] = transit_line.

        
def writeCSV(fileNamePath, listOfTuples):
    myWriter = csv.writer(open(fileNamePath, 'wb'))
    for l in listOfTuples:
        myWriter.writerow(l)


def main():
    ft_summary_dict = {}
    my_project = EmmeProject(project)
    
    #create extra attributes:
    for name, desc in extra_attributes_dict.iteritems():
        my_project.create_extras('LINK', name, desc)
    
    
    #pandas dataframe to hold count table:
    df_counts = pd.read_csv('inputs/network_summary/' + counts_file, index_col=['loop_INode', 'loop_JNode'])
    counts_dict = {}
    #get a list of screenlines from the bank/scenario
    screenline_list = get_unique_screenlines(my_project) 
    screenline_dict = {}
    
    for item in screenline_list:
        #dict where key is screen line id and value is 0
        screenline_dict[item] = 0

    #loop through all tod banks and get network summaries
    for key, value in sound_cast_net_dict.iteritems():
        my_project.change_active_database(key)
        net_stats = calc_vmt_vht_delay_by_ft(my_project.m)
        #store tod network summaries in dictionary where key is tod:
        ft_summary_dict[key] = net_stats
        #counts:
        df_tod_vol = get_link_counts(my_project, df_counts, key)
        counts_dict[key] = df_tod_vol
        
        get_screenline_volumes(screenline_dict, my_project.m) 

    #*******write out counts:
    for value in counts_dict.itervalues():
        df_counts = df_counts.merge(value, right_index = True, left_index = True)
        df_counts = df_counts.drop_duplicates()
    
    #write counts out to csv:
    with open('outputs/' + counts_output_file, 'wb') as f:
        df_counts.to_csv(f)
    f.close


    #*******write out network summaries
    #will rewrite using pandas
    soundcast_tods = sound_cast_net_dict.keys
    list_of_measures = ['vmt', 'vht', 'delay']
    list_of_FTs = fac_type_dict.keys()
    row_list = []
    list_of_rows = []
    header = ['tod', 'TP_4k']
    
    #create the header
    for measure in list_of_measures:
        for factype in list_of_FTs:
            header.append(factype + '_' + measure)
    list_of_rows.append(header)
    
    #write out the rows and columns
    for key, value in ft_summary_dict.iteritems():
        #tod
        row_list.append(key)
        #4k time period:
        row_list.append(sound_cast_net_dict[key])
        for measure in list_of_measures:
            for factype in list_of_FTs:
                print measure, factype
                row_list.append(value[measure][factype])
        list_of_rows.append(row_list)
        row_list = []
    
    writeCSV('outputs/' + net_summary_file, list_of_rows)

    #*******write out screenlines
    with open('outputs/' + screenlines_file, 'wb') as f:
        writer = csv.writer(f)
        for key, value in screenline_dict.iteritems():
           print key, value
           writer.writerow([key, value])
    f.close
    
    #writer = csv.writer(open('outputs/' + screenlines_file, 'ab'))
    #for key, value in screenline_dict.iteritems():
    #    print key, value
    #    writer.writerow([key, value])
    #writer = None

if __name__ == "__main__":
    main()



 





               