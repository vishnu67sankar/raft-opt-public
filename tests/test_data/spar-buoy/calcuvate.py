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

def _updateMoorings(center_spar, ms): 
    z_fair_fraction = 70/120                    # ratio of z_fairlead and z_keel is kept constant
    depth = ms['water_depth']                   # water depth [m]
    xAnchor = 853.87                            # anchor radius/spacing [m]
    zAnchor = -1*depth                           # fairlead z elevation [m]
    xFair = center_spar['d'][0]/2 + 0.5                              # fairlead radius [m]
    zFair = z_fair_fraction*center_spar['rA'][2]

    lineLength= 902.2                            # line unstretched length [m]
    typeName  = "drag_embedment"                        # identifier string for the line type
    
    for lines in ms['points']:
        if lines['name'] == 'line1_vessel':
            lines['location'] = [xFair, 0.0, zFair]

        elif lines['name'] == 'line2_vessel':
            lines['location'] = [-xFair*np.sin(np.radians(30)), xFair*np.cos(np.radians(30)), zFair]
        
        elif lines['name'] == 'line3_vessel':
            lines['location'] = [-xFair*np.sin(np.radians(30)), -xFair*np.cos(np.radians(30)), zFair]
    
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


def calcuvate(design, x_platform, x_mooring=None):
    center_spar = design['platform']['members'][0]
    ms = design['mooring']

    center_spar = _updateColumns(center_spar, x_platform)
    
    ms = _updateMoorings(center_spar, ms)
    
    design['platform']['members'][0] = center_spar
    design['mooring'] = ms

    return (design)