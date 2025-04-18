import numpy as np
import raft
import openmdao.api as om
import os
import yaml
import moorpy as mp
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

def _updateMoorings(fairlead, is_post_procesing=False): 
    # Make it generic
    depth     = 200                             # water depth [m]
    start_angle = 0
    angles    = np.radians([0, 120, 240])  
    rAnchor   = 837.6 - 58 + fairlead                            # anchor radius/spacing [m]
    zFair     = -14                             # fairlead z elevation [m]
    rFair     = fairlead                              # fairlead radius [m]
    lineLength= 850                            # line unstretched length [m]
    typeName  = "chain1"                        # identifier string for the line type
    
    ms = mp.System(depth=depth)
    
    # add a line type
    ms.setLineType(dnommm=180, material='chain', name=typeName)  # this would be 120 mm chain

    # For each line heading, set the anchor point, the fairlead point, and the line itself
    for i, angle in enumerate(angles):
    
        # create end Points for the line
        ms.addPoint(1, [rAnchor*np.cos(angle), rAnchor*np.sin(angle), -depth])   # create anchor point (type 0, fixed)
        ms.addPoint(-1, [  rFair*np.cos(angle),   rFair*np.sin(angle),  zFair])   # create fairlead point (type 0, fixed)
        
        # add a Line going between the anchor and fairlead Points
        ms.addLine(lineLength, typeName, pointA=2*i+1, pointB=2*i+2)
        
    ms.solveEquilibrium()                                       # equilibrate

    if is_post_procesing == True:
        ms.unload("moordyn_upd_pp.dat")                         # export to MD input file

    else: 
        ms.unload("moordyn_upd.dat")                         # export to MD input file

    return (ms)


# def _adjustBallast(design):
#     ## Need to make this generic
#     with suppress_stdout():
#         model = raft.Model(deepcopy(design))
#         model.analyzeUnloaded()
#         heave = model.fowtList[0].Xi0[2] 
        
#         #zero heave
#         store = []
#         adj = 0.01
#         while abs(heave) > 0.1:
#             design['platform']['members'][0]['l_fill'] = design['platform']['members'][0]['l_fill'] + adj * np.sign(heave)
#             design['platform']['members'][1]['l_fill'] = design['platform']['members'][1]['l_fill'] + adj * np.sign(heave)
            
#             if design['platform']['members'][0]['l_fill'] < 0:
#                 design['platform']['members'][0]['l_fill']  = 0
#                 design['platform']['members'][1]['l_fill']  = 0
#                 design['platform']['members'][3]['l_fill'] = design['platform']['members'][3]['l_fill'] + adj * np.sign(heave)
#                 design['platform']['members'][4]['l_fill'] = design['platform']['members'][4]['l_fill'] + adj * np.sign(heave)
                
#             model = raft.Model(deepcopy(design))  
#             model.analyzeUnloaded()
#             heave = model.fowtList[0].Xi0[2] 

#             if len(store) > 2:
#                 if heave == store[-2]:
#                     adj = adj/2
#             store.append(heave)
            
#         print('Heave zerod')
        
#         #zero pitch
#         store = []
#         pitch = model.fowtList[0].Xi0[4]
#         adj = 0.01
#         while pitch > 0.2/180*np.pi or pitch < 0:
            
#             if pitch > 0:
#                 design['platform']['members'][0]['l_fill'] = design['platform']['members'][0]['l_fill'] - adj
#                 design['platform']['members'][1]['l_fill'] = design['platform']['members'][1]['l_fill'] + adj/2
#             else:
#                 design['platform']['members'][0]['l_fill'] = design['platform']['members'][0]['l_fill'] + adj
#                 design['platform']['members'][1]['l_fill'] = design['platform']['members'][1]['l_fill'] - adj/2
            
#             model = raft.Model(deepcopy(design)) 
#             model.analyzeUnloaded()
#             pitch = model.fowtList[0].Xi0[4]
            

#             if len(store) > 2:
#                 if pitch == store[-2]:
#                     adj = adj/2
#             store.append(pitch)
#         print('Pitch zerod')

#         return(design)


def calcuvate(design, x_platform, x_mooring=None, is_post_procesing=False):
    draft = 20
    deck_width = 3.91
    deck_height = 3.91
    freeboard = 15 
    
    column_spacing = x_platform['column_spacing']
    column_diameter = x_platform['column_diameter']
    pontoon_width = x_platform['pontoon_width']
    pontoon_height = x_platform['pontoon_height']
    #calculate column centers

    c1x = column_spacing*np.sqrt(3)/2 * 2/3 # from formula for centroid of equilateral triangle
    c1y = 0
    c2x = -column_spacing*np.sqrt(3)/2 * 1/3
    c2y = column_spacing/2
    c3x = -column_spacing*np.sqrt(3)/2 * 1/3
    c3y = -column_spacing/2
    
    #calculate pontoons and deck beams
    pontoon_len = column_spacing - column_diameter
    pontoon_depth = draft - pontoon_height/2
    deck_z = freeboard - deck_height/2
    fairlead_width = c1x + column_diameter/2
    
    #update columns
    design['platform']['members'][0]['d'] = column_diameter
    design['platform']['members'][1]['d'] = column_diameter
    
    # design['platform']['members'][0]['l_fill'] = x_platform['outer_column_A_l_fill']
    # design['platform']['members'][1]['l_fill'] = x_platform['outer_column_BC_l_fill']
    
    design['platform']['members'][0]['rA'] = [c1x, 0, -draft]
    design['platform']['members'][0]['rB'] = [c1x, 0, freeboard]
    
    design['platform']['members'][1]['rA'] = [c1x, 0, -draft]
    design['platform']['members'][1]['rB'] = [c1x, 0, freeboard]
    
    
    #update pontoons
    design['platform']['members'][2]['d'] = [pontoon_width,pontoon_height]
    design['platform']['members'][3]['d'] = [pontoon_width,pontoon_height]
    design['platform']['members'][4]['d'] = [pontoon_width,pontoon_height]


    # design['platform']['members'][2]['l_fill'] = x_platform['pontoon_A_l_fill']
    # design['platform']['members'][3]['l_fill'] = x_platform['pontoon_B_l_fill']
    # design['platform']['members'][4]['l_fill'] = x_platform['pontoon_B_l_fill']
    
    design['platform']['members'][2]['rA'] = [c2x, pontoon_len/2, -pontoon_depth]
    design['platform']['members'][2]['rB'] = [c2x, -pontoon_len/2, -pontoon_depth]
    
    design['platform']['members'][3]['rA'] = [c2x, pontoon_len/2, -pontoon_depth]
    design['platform']['members'][3]['rB'] = [c2x, -pontoon_len/2, -pontoon_depth]

    design['platform']['members'][4]['rA'] = [c2x, -pontoon_len/2, -pontoon_depth]
    design['platform']['members'][4]['rB'] = [c2x, pontoon_len/2, -pontoon_depth]
    
    #update deck beam
    design['platform']['members'][5]['d'] = [deck_width,deck_height]
    
    design['platform']['members'][5]['rA'] = [c2x, pontoon_len/2, deck_z]
    design['platform']['members'][5]['rB'] = [c2x, -pontoon_len/2, deck_z]
    
    design['turbine']['tower']['rA'] = [c1x,0, freeboard]
    design['turbine']['tower']['rB'] = [c1x,0, 144.582]
    
    _updateMoorings(fairlead_width, is_post_procesing)
    design['mooring']['file'] = 'moordyn_upd.dat'

    # design = _adjustBallast(deepcopy(design))
    

    return (design)