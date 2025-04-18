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

def _updateMoorings(n_columns, fairlead, lower_column, ms): 
    
    depth     = ms['water_depth']                             # water depth [m]
    start_angle = 60
    angles = np.linspace(start_angle, start_angle+360, n_columns+1)[:-1]
    angles = np.radians(angles)                 # line headings list [rad]
    # angles    = np.radians([0, 120, 240])  
    rAnchor   = 837.6 - 40.868 + fairlead                            # anchor radius/spacing [m]
    zFair     = -14                             # fairlead z elevation [m]
    rFair     = fairlead                              # fairlead radius [m]
    lineLength= 835.5                            # line unstretched length [m]
    typeName  = "drag_embedment"                        # identifier string for the line type
    
    n_points = len(ms['points'])

    for item in ms['points']:
        if (item['name'] == 'line2_vessel'):
            item['location'][0] =-1*(lower_column['rA'][0] + lower_column['d']/2)
        
        elif (item['name'] == 'line1_vessel'):
            item['location'][0] = (lower_column['rA'][0] + lower_column['d']/2)*(np.sin(np.pi/6))
            item['location'][1] = (lower_column['rA'][0] + lower_column['d']/2)*(np.cos(np.pi/6))

        elif (item['name'] == 'line3_vessel'):
            item['location'][0] = (lower_column['rA'][0] + lower_column['d']/2)*(np.sin(np.pi/6))
            item['location'][1] = -1*(lower_column['rA'][0] + lower_column['d']/2)*(np.cos(np.pi/6))
    
    return (ms)

def _updateCrossbrace(main_column, lower_column, upper_column, pontoons, cross_brace):
   
    cross_brace['rA'][0] = main_column['d'][0]/2 # update x coordinate
    cross_brace['rB'][0] = upper_column['rA'][0] - upper_column['d']/2 # update x coordinate

    return(cross_brace)

def _updatePontoons(main_column, lower_column, upper_column, pontoons):
   
    for item in pontoons:
        if item['name'] == 'delta_upper_pontoon':
            item['rA'][0] = upper_column['rA'][0] - upper_column['d']/2*np.sin(np.pi/3) 
            item['rA'][1] = upper_column['d']/2*np.cos(np.pi/3)

            item['rB'][0] = -(upper_column['rA'][0]*np.sin(np.pi/6) - upper_column['d']/2*np.sin(np.pi/3)) 
            item['rB'][1] = upper_column['rA'][0]*np.cos(np.pi/6) - upper_column['d']/2*np.cos(np.pi/3)

        elif item['name'] == 'delta_lower_pontoon':
            item['rA'][0] = lower_column['rA'][0] - lower_column['d']/2*np.sin(np.pi/3) 
            item['rA'][1] = lower_column['d']*np.cos(np.pi/3)

            item['rB'][0] = -(lower_column['rA'][0]*np.sin(np.pi/6) - lower_column['d']/2*np.sin(np.pi/3)) 
            item['rB'][1] = (lower_column['rA'][0])*np.cos(np.pi/6) - lower_column['d']/2*np.cos(np.pi/3)

        elif item['name'] == 'Y_upper_pontoon':
            item['rA'][0] = main_column['d']/2
            item['rB'][0] = upper_column['rA'][0] - upper_column['d']/2
        
        elif item['name'] == 'Y_lower_pontoon':
            item['rA'][0] = main_column['d']/2
            item['rB'][0] = lower_column['rA'][0] - lower_column['d']/2

        return (pontoons)

def _updateColumns(lower_column, upper_column, x_platform):
    
    # lower_column['d'] = x_platform['lower_column_d']

    upper_column['d'] = x_platform['upper_column_d']
    # upper_column['l_fill'] = 0.2988*(12**2)/(x_platform['upper_column_d']**2)
    upper_column['l_fill'] = x_platform['upper_column_l_fill']
    lower_column['l_fill'] = x_platform['lower_column_l_fill']

    return (lower_column, upper_column)

def calcuvate(design, x_platform, x_mooring=None):
    main_column = design['platform']['members'][0]
    lower_column = design['platform']['members'][1]
    upper_column = design['platform']['members'][2]
    pontoons = design['platform']['members'][3:]
    cross_brace = design['platform']['members'][7]
    ms = design['mooring']

    lower_column, upper_column = _updateColumns(lower_column, upper_column, x_platform)
    pontoons = _updatePontoons(main_column, lower_column, upper_column, pontoons)    
    cross_brace = _updateCrossbrace(main_column, lower_column, upper_column, pontoons, cross_brace)
    fairlead = lower_column['rA'][0] + lower_column['d']/2
    ms = _updateMoorings(3, fairlead, lower_column, ms)
    
    design['platform']['members'][1] = lower_column
    design['platform']['members'][2] = upper_column
    design['platform']['members'][3:] = pontoons
    design['platform']['members'][7] = cross_brace
    design['mooring'] = ms

    return (design)