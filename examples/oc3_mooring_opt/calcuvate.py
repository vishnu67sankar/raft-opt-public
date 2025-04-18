import numpy as np
import raft
import openmdao.api as om
import os
import yaml
from copy import deepcopy
from contextlib import contextmanager
import sys

@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout

def _updateMoorings(x_mooring, center_spar, ms): 
    water_depth = ms['water_depth']
    z_fair_fraction = 70/120      
    clump_mass = x_mooring['clump_mass']
    r_anchor = x_mooring['r_anchor']
    z_fairlead = x_mooring['z_fairlead']
    l_ballast = x_mooring['l_ballast'] ## cable joining fairlead position to ballast
    l_anchor = x_mooring['l_anchor'] ## cable joining fairlead position to ballast
    spar_d = center_spar['d'][0]

    xFair = center_spar['d'][0]/2 + 0.5   
    zFair = z_fair_fraction*center_spar['rA'][2]

    for lines in ms['points']:
        if lines['name'] == 'line1_vessel':
            lines['location'] = [xFair, 0.0, zFair]

        elif lines['name'] == 'line2_vessel':
            lines['location'] = [-xFair*np.sin(np.radians(30)), xFair*np.cos(np.radians(30)), zFair]
        
        elif lines['name'] == 'line3_vessel':
            lines['location'] = [-xFair*np.sin(np.radians(30)), -xFair*np.cos(np.radians(30)), zFair]
    
    ### line-i_anchor
    ms['points'][0]['location'] = [r_anchor, 0.0, -water_depth]
    ms['points'][1]['location'] = [-r_anchor*np.cos(np.pi/3), r_anchor*np.sin(np.pi/3), -water_depth]
    ms['points'][2]['location'] = [-r_anchor*np.cos(np.pi/3), -r_anchor*np.sin(np.pi/3), -water_depth]

    ### line-i_vessel_right
    ms['points'][3]['location'] = [(spar_d/2 + 0.5), 0.0, -z_fairlead]
    ms['points'][4]['location'] = [-np.cos(np.pi/3)*(spar_d/2), np.sin(np.pi/3)*(spar_d/2) , -z_fairlead]
    ms['points'][5]['location'] = [-np.cos(np.pi/3)*(spar_d/2), -np.sin(np.pi/3)*(spar_d/2) , -z_fairlead]

    ### line-i_connection
    z_ballast = ((l_ballast/l_anchor)*water_depth + z_fairlead)/(1 + l_ballast/l_anchor)
    r_ballast = (l_ballast**2 - (z_ballast-z_fairlead)**2)**0.5

    ms['points'][6]['location'] = [r_ballast, 0.0, -z_ballast]
    ms['points'][6]['mass'] = clump_mass
    ms['points'][7]['location'] = [-r_ballast*np.cos(np.pi/3), r_ballast*np.sin(np.pi/3) , -z_ballast]
    ms['points'][7]['mass'] = clump_mass
    ms['points'][8]['location'] = [-r_ballast*np.cos(np.pi/3), -r_ballast*np.sin(np.pi/3) , -z_ballast]
    ms['points'][8]['mass'] = clump_mass

    # l_ballast = (z_ballast**2 + r_ballast**2)**0.5 + 20.0

    ms['lines'][1]['length'] = l_ballast # connecting anchor to connection
    ms['lines'][3]['length'] = l_ballast # connecting anchor to connection
    ms['lines'][5]['length'] = l_ballast # connecting anchor to connection

    # l_anchor = l_cable - l_ballast ## but what if l_cable is shorter than l_ballast?
    ms['lines'][0]['length'] = l_anchor
    ms['lines'][2]['length'] = l_anchor
    ms['lines'][4]['length'] = l_anchor

    return (ms)

def _updateColumns(center_spar, x_platform):
    freeboard = 10
    center_spar['d'][0] = x_platform['center_spar_d']
    center_spar['d'][1] = x_platform['center_spar_d']
    center_spar['d'][2] = x_platform['center_spar_d']
    center_spar['d'][3] = x_platform['center_spar_d']
    center_spar['rA'][2] = -x_platform['center_spar_h'] + freeboard
    center_spar['stations'][0] = -x_platform['center_spar_h'] + freeboard
    center_spar['stations'][1] = center_spar['stations'][0] + 30.
    center_spar['stations'][2] = center_spar['stations'][1] + 30.
    center_spar['l_fill'][0] = x_platform['l_fill_0']
    center_spar['l_fill'][1] = x_platform['l_fill_1']
    
    center_spar['cap_stations'] = [center_spar['stations'][0]]
    return (center_spar)

def calcuvate(design, x_platform, x_mooring):
    center_spar = design['platform']['members'][0]
    ms = design['mooring']

    center_spar = _updateColumns(center_spar, x_platform)
    ms = _updateMoorings(x_mooring, center_spar, ms)
    
    design['platform']['members'][0] = center_spar
    design['mooring'] = ms
    return (design)

def l_cable(design=None, model=None, x_platform=None, x_mooring=None):
    l_cable = x_mooring['l_ballast'] + x_mooring['l_anchor']
    return (l_cable)
