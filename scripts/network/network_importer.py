import inro.emme.desktop.app as app
import inro.modeller as _m
import inro.emme.matrix as ematrix
import inro.emme.database.matrix
import inro.emme.database.emmebank as _eb
import os
import re 
import multiprocessing as mp
import subprocess
from multiprocessing import Pool, pool


project = 'Projects/LoadTripTables/LoadTripTables.emp'
tod_networks = ['am', 'md', 'pm', 'ev', 'ni']
sound_cast_net_dict = {'5to6' : 'am', '6to7' : 'am', '7to8' : 'am', '8to9' : 'am', '9to10' : 'md', '10to14' : 'md', '14to15' : 'md', '15to16' : 'pm', '16to17' : 'pm', '17to18' : 'pm', '18to20' : 'ev', '20to5' : 'ni'}
load_transit_tod = ['6to7', '7to8', '8to9', '9to10']

mode_crosswalk_dict = {'b': 'bp', 'bwl' : 'bpwl', 'aijb' : 'aimjbp', 'ahijb' : 'ahdimjbp', 'ashijtuvb': 'asehdimjvutbp', 'r' : 'rc', 'br' : 'bprc', 'ashijtuvbwl' : 'asehdimjvutbpwl', 'ashijtuvbfl' : 'asehdimjvutbpfl', 'asbw' : 'asehdimjvutbpwl', 'ashijtuvbxl' : 'asehdimjvutbpxl', 'ahijstuvbw' : 'asehdimjvutbpw'}
mode_file = 'modes.txt'
transit_vehicle_file = 'vehicles.txt'
base_net_name = '_roadway.in'
turns_name = '_turns.in'
transit_name = '_transit.in'
shape_name = '_link_shape_1002.txt'

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
    def network_counts_by_element(self, element):
        network = self.current_scenario.get_network()
        d = network.element_totals
        count = d[element]
        return count
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
    def process_modes(self, mode_file):
        NAMESPACE = "inro.emme.data.network.mode.mode_transaction"
        process_modes = self.m.tool(NAMESPACE)
        process_modes(transaction_file = mode_file,
              revert_on_error = True,
              scenario = self.current_scenario)
                
    def create_scenario(self, scenario_number, scenario_title = 'test'):
        NAMESPACE = "inro.emme.data.scenario.create_scenario"
        create_scenario = self.m.tool(NAMESPACE)
        create_scenario(scenario_id=scenario_number,
                        scenario_title= scenario_title)


   
    def delete_links(self):
        if self.network_counts_by_element('links') > 0:
            NAMESPACE = "inro.emme.data.network.base.delete_links"
            delete_links = self.m.tool(NAMESPACE)
            #delete_links(selection="@dist=9", condition="cascade")
            delete_links(condition="cascade")

    def delete_nodes(self):
        if self.network_counts_by_element('regular_nodes') > 0:
            NAMESPACE = "inro.emme.data.network.base.delete_nodes"
            delete_nodes = self.m.tool(NAMESPACE)
            delete_nodes(condition="cascade")
    def process_vehicles(self,vehicle_file):
          NAMESPACE = "inro.emme.data.network.transit.vehicle_transaction"
          process = self.m.tool(NAMESPACE)
          process(transaction_file = vehicle_file,
            revert_on_error = True,
            scenario = self.current_scenario)

    def process_base_network(self, basenet_file):
        NAMESPACE = "inro.emme.data.network.base.base_network_transaction"
        process = self.m.tool(NAMESPACE)
        process(transaction_file = basenet_file,
              revert_on_error = True,
              scenario = self.current_scenario)
    def process_turn(self, turn_file):
        NAMESPACE = "inro.emme.data.network.turn.turn_transaction"
        process = self.m.tool(NAMESPACE)
        process(transaction_file = turn_file,
            revert_on_error = False,
            scenario = self.current_scenario)

    def process_transit(self, transit_file):
        NAMESPACE = "inro.emme.data.network.transit.transit_line_transaction"
        process = self.m.tool(NAMESPACE)
        process(transaction_file = transit_file,
            revert_on_error = True,
            scenario = self.current_scenario)
    def process_shape(self, linkshape_file):
        NAMESPACE = "inro.emme.data.network.base.link_shape_transaction"
        process = self.m.tool(NAMESPACE)
        process(transaction_file = linkshape_file,
            revert_on_error = True,
            scenario = self.current_scenario)
    def change_scenario(self):
        self.current_scenario = list(self.bank.scenarios())[0]


def multiwordReplace(text, replace_dict):
    rc = re.compile(r"[A-Za-z_]\w*")
    def translate(match):
        word = match.group(0)
        return replace_dict.get(word, word)
    return rc.sub(translate, text)




def run_importer(project_name):
    my_project = EmmeProject(project_name)
    for key, value in sound_cast_net_dict.iteritems():
        my_project.change_active_database(key)
        for scenario in list(my_project.bank.scenarios()):
            my_project.bank.delete_scenario(scenario)
        #create scenario
        my_project.bank.create_scenario(1002)
        my_project.change_scenario()
        #print key
        my_project.delete_links()
        my_project.delete_nodes()
      
        my_project.process_modes('inputs/networks/' + mode_file)
        
        my_project.process_base_network('inputs/networks/' + value + base_net_name)
        my_project.process_turn('inputs/networks/' + value + turns_name)
    #my_project.process_shape('/inputs/network' + tod_network + shape_name)

        if my_project.tod in load_transit_tod:
           my_project.process_vehicles('inputs/networks/' + transit_vehicle_file)
           my_project.process_transit('inputs/networks/' + value + transit_name)
    
    


#change network modes from 4k to AB

def main():
    for tod in tod_networks:
        filepath = os.path.join('inputs/networks/', tod + base_net_name )
        filepath = filepath.replace('\\','/')
        f = open(filepath, "r")
        lines = f.readlines()
        f.close()
        f = open(filepath, "w")
        for line in lines:
            line = str(line)
            line = multiwordReplace(line, mode_crosswalk_dict)
            f.write(line)
        f.close()
        print 'done'
   
    
    run_importer(project)
    print 'done'
if __name__ == "__main__":
    main()





