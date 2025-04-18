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

def _updateMoorings(x_mooring, x_platform, ms): 
    water_depth = ms['water_depth']
    x_anchor_trailing = x_mooring['x_anchor_trailing']
    y_anchor_trailing = x_mooring['y_anchor_trailing']

    x_anchor_leading = x_mooring['x_anchor_leading']
    y_anchor_leading = x_mooring['y_anchor_leading']
    
    x_fairlead = x_mooring['x_fairlead']
    l_cable = x_mooring['l_cable']
    
    ms['points'][4]['location'][0] = x_fairlead
    ms['points'][6]['location'][0] = x_fairlead

    ms['lines'][0]['length'] = l_cable
    ms['lines'][1]['length'] = l_cable
    ms['lines'][2]['length'] = l_cable
    ms['lines'][3]['length'] = l_cable

    ms['points'][0]['location'] = [-x_anchor_trailing, y_anchor_trailing, -water_depth]
    ms['points'][1]['location'] = [x_anchor_leading, y_anchor_leading, -water_depth]
    ms['points'][2]['location'] = [-x_anchor_trailing, -y_anchor_trailing, -water_depth]
    ms['points'][3]['location'] = [x_anchor_leading, -y_anchor_leading, -water_depth]
    
    # ms['points'][4]['location'][0] = x_fairlead
    # ms['points'][6]['location'][0] = x_fairlead

    ms['points'][4]['location'][1] = x_platform['d_lower_pod']/2 + 0.2475
    ms['points'][5]['location'][1] = x_platform['d_lower_pod']/2 + 0.2475
    ms['points'][6]['location'][1] = -(x_platform['d_lower_pod']/2 + 0.2475)
    ms['points'][7]['location'][1] = -(x_platform['d_lower_pod']/2 + 0.2475)

    ms['lines'][0]['length'] = l_cable
    ms['lines'][1]['length'] = l_cable
    ms['lines'][2]['length'] = l_cable
    ms['lines'][3]['length'] = l_cable


    return (ms)

def _updateColumns(upper_pod, lower_pod, x_platform):
    d_upper_pod = x_platform['d_upper_pod']
    
    upper_pod['d'][1] = d_upper_pod
    upper_pod['d'][2] = d_upper_pod
    upper_pod['d'][3] = d_upper_pod

    d_lower_pod = x_platform['d_lower_pod']
    
    for i in range(1, 11):
        lower_pod['d'][i] = d_lower_pod

    return (upper_pod, lower_pod)

def calcuvate(design, x_platform, x_mooring):
    upper_pod = design['platform']['members'][0]
    lower_pod = design['platform']['members'][1]
    ms = design['mooring']

    upper_pod, lower_pod = _updateColumns(upper_pod, lower_pod, x_platform)

    ms = _updateMoorings(x_mooring, x_platform, ms)
    
    design['platform']['members'][0] = upper_pod
    design['platform']['members'][1] = lower_pod
    design['mooring'] = ms

    return (design)

def power_mass_ratio(design=None, model=None, x_platform=None, x_mooring=None):
    power_mass_ratio = -1*(model.fowtList[0].rotorList[0].aero_power/model.fowtList[0].m_shell)


    return power_mass_ratio

def intersect_dist_1(design=None, model=None, x_platform=None, x_mooring=None):
    x_rotor = design['turbine']['rotorCoords'][0][0]
    y_rotor = design['turbine']['rotorCoords'][0][1]
    z_rotor = design['turbine']['Zhub']

    x_fairlead = design['mooring']['points'][4]['location'][0]
    y_fairlead = design['mooring']['points'][4]['location'][1]
    z_fairlead = design['mooring']['points'][4]['location'][2]

    x_anchor = design['mooring']['points'][0]['location'][0]
    y_anchor = design['mooring']['points'][0]['location'][1]
    z_anchor = design['mooring']['points'][0]['location'][2]

    lamda = (x_rotor-x_fairlead)/(x_anchor-x_fairlead)

    x_intersect = (x_anchor - x_fairlead)*lamda + x_fairlead
    y_intersect = (y_anchor - y_fairlead)*lamda + y_fairlead
    z_intersect = (z_anchor - z_fairlead)*lamda + z_fairlead

    intersect_dist_1 = ((x_intersect - x_rotor)**2 + (y_intersect - y_rotor)**2 + (z_intersect - z_rotor)**2)**0.5
    print("intersect_dist_1 = ", intersect_dist_1)
    return (intersect_dist_1)

def intersect_dist_2(design=None, model=None, x_platform=None, x_mooring=None):
    x_rotor = design['turbine']['rotorCoords'][0][0]
    y_rotor = design['turbine']['rotorCoords'][0][1]
    z_rotor = design['turbine']['Zhub']

    x_fairlead = design['mooring']['points'][5]['location'][0]
    y_fairlead = design['mooring']['points'][5]['location'][1]
    z_fairlead = design['mooring']['points'][5]['location'][2]

    x_anchor = design['mooring']['points'][1]['location'][0]
    y_anchor = design['mooring']['points'][1]['location'][1]
    z_anchor = design['mooring']['points'][1]['location'][2]

    lamda = (x_rotor-x_fairlead)/(x_anchor-x_fairlead)
    
    x_intersect = (x_anchor - x_fairlead)*lamda + x_fairlead
    y_intersect = (y_anchor - y_fairlead)*lamda + y_fairlead
    z_intersect = (z_anchor - z_fairlead)*lamda + z_fairlead

    intersect_dist_2 = ((x_intersect - x_rotor)**2 + (y_intersect - y_rotor)**2 + (z_intersect - z_rotor)**2)**0.5
    print("intersect_dist_2 = ", intersect_dist_2)
    return (intersect_dist_2)


def intersect_dist_3(design=None, model=None, x_platform=None, x_mooring=None):
    x_rotor = design['turbine']['rotorCoords'][0][0]
    y_rotor = design['turbine']['rotorCoords'][0][1]
    z_rotor = design['turbine']['Zhub']

    x_fairlead = design['mooring']['points'][6]['location'][0]
    y_fairlead = design['mooring']['points'][6]['location'][1]
    z_fairlead = design['mooring']['points'][6]['location'][2]

    x_anchor = design['mooring']['points'][2]['location'][0]
    y_anchor = design['mooring']['points'][2]['location'][1]
    z_anchor = design['mooring']['points'][2]['location'][2]

    lamda = (x_rotor-x_fairlead)/(x_anchor-x_fairlead)
    
    x_intersect = (x_anchor - x_fairlead)*lamda + x_fairlead
    y_intersect = (y_anchor - y_fairlead)*lamda + y_fairlead
    z_intersect = (z_anchor - z_fairlead)*lamda + z_fairlead

    intersect_dist_3 = ((x_intersect - x_rotor)**2 + (y_intersect - y_rotor)**2 + (z_intersect - z_rotor)**2)**0.5
    print("intersect_dist_3 = ", intersect_dist_3)
    return (intersect_dist_3)


def intersect_dist_4(design=None, model=None, x_platform=None, x_mooring=None):
    x_rotor = design['turbine']['rotorCoords'][0][0]
    y_rotor = design['turbine']['rotorCoords'][0][1]
    z_rotor = design['turbine']['Zhub']

    x_fairlead = design['mooring']['points'][7]['location'][0]
    y_fairlead = design['mooring']['points'][7]['location'][1]
    z_fairlead = design['mooring']['points'][7]['location'][2]

    x_anchor = design['mooring']['points'][3]['location'][0]
    y_anchor = design['mooring']['points'][3]['location'][1]
    z_anchor = design['mooring']['points'][3]['location'][2]

    lamda = (x_rotor-x_fairlead)/(x_anchor-x_fairlead)

    x_intersect = (x_anchor - x_fairlead)*lamda + x_fairlead
    y_intersect = (y_anchor - y_fairlead)*lamda + y_fairlead
    z_intersect = (z_anchor - z_fairlead)*lamda + z_fairlead

    intersect_dist_4 = ((x_intersect - x_rotor)**2 + (y_intersect - y_rotor)**2 + (z_intersect - z_rotor)**2)**0.5
    print("intersect_dist_4 = ", intersect_dist_4)
    return (intersect_dist_4)