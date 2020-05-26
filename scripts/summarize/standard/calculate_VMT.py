import pandas as pd
import os, sys
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(),"scripts"))
from EmmeProject import *
from input_configuration import *
from emme_configuration import *

# link selectors. only one selection one link selector can be used for now
# it may have multiple selections. For example, we can select by jurisdiction boundary 
# and subarea boundary. They are two seperate and independent selections. That's OK.
# but you cannot have a selection of ul1=1000 and ul2=60. This kind of selection is not allowed
link_selectors = {'@bkrlink': 1}

# file will be exported to default output folder.
outputfilename = 'system_metrics.txt'

def main():
    print network_summary_project
    my_project = EmmeProject(network_summary_project)

    metrics = {}
    for flag, val in link_selectors.iteritems():    
        temp = {}
        for key, value in sound_cast_net_dict.iteritems():
            my_project.change_active_database(key)
            ret = my_project.calculate_VHT_subarea(flag, val, 1002)
            temp.update({value:ret})
        metrics.update({flag:temp})
    my_project.CloseDesktop()
    print metrics    

    outputfile = os.path.join(project_folder, report_output_location, outputfilename)

    # export to file also calculate daily VMT/VHT/VDT
    with open(outputfile, 'w')  as f:
        for flag, val in metrics.iteritems():
            daily_vmt = 0
            daily_vht = 0
            daily_vdt = 0
            f.write('Selection: %s\n' % flag)
            for tod, value in val.iteritems():
                f.write('  ')
                f.write('Time of Day: %s\n' % tod)
                for variable, var_val in value.iteritems():
                    f.write('    ')
                    f.write('%s: %.2f\n' % (variable, var_val))
                    if variable == 'VMT':
                        daily_vmt = daily_vmt + var_val
                    elif variable == 'VHT':
                        daily_vht = daily_vht + var_val
                    elif variable == 'VDT':
                        daily_vdt = daily_vdt + var_val
            f.write('  Time of Day: Daily\n')
            f.write('    VMT: %.2f\n' % daily_vmt)
            f.write('    VHT: %.2f\n' % daily_vht)
            f.write('    VDT: %.2f\n' % daily_vdt)
            f.write('\n')
    print 'Done'
if __name__ == '__main__':
    main()
