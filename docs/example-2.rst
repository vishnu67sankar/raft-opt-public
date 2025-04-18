Example-2
===========

OC3-Hywind Spar Optimization
-----------------------------------
In this example, let's take the same design with which we worked with in the previous example. 
But now let's focus on just decreasing the tension
without decreasing the mass. So let's leave the diameter and the height out of the picture. 
We may not be very sure as to which mooring line design variables are going to impact tension in the cables. 
So for now, let us go ahead and define as many design variables as we can. And let's hope that the optimizer figures out which 
ones to tweak. 


Open a local folder in your machine, and copy the 
``design_file.yaml`` from the ``example>oc3_mooring_opt`` 
folder present in RAFT-Opt repository. This example consists of
the 5MW with OC3-Hywind spar design. The setup file for this problem is shown below:

User Input File
~~~~~~~~~~~~~~~

.. code-block:: yaml

    platform:
        optimize: False
        update_stability: True

        design_variables:
            center_spar_d: 9.4
            center_spar_h: 130

        secondary_design_variables: 
            l_fill_0: 29
            l_fill_1: 29

        bounds_design_variables:
            center_spar_d: [8., 15.]    
            center_spar_h: [85, 150]
        
        bounds_secondary_design_variables:
            l_fill_0: [0.0, 29.0]
            l_fill_1: [0.0, 29.0]

        outputs:
            case_metrics: ['surge_max', 'sway_max', 'heave_max', 'roll_max', 'pitch_max', 'yaw_max', 'Mbase_max', 'AxRNA_max']
            fowtList: ['sway', 'heave', 'roll', 'pitch', 'yaw', 'mass_fowt']
            eigenvalue: ['eigenvalue_surge', 'eigenvalue_heave', 'eigenvalue_pitch']

        inequality_constraints:
            pitch_max: [-10.0, 10.0]
            surge_max: [None, 30]

    mooring:
        optimize: True
        update_stability: False

        design_variables: 
            clump_mass: 5000
            z_fairlead: -70.0          # fairlead height
            r_anchor: 853.87        # anchor radius 
            l_ballast: 254.2             # cable length
            l_anchor: 673.87             # cable length

        bounds_design_variables:
            clump_mass: [5000, 15000]
            z_fairlead: [-90, -50]          # fairlead height
            r_anchor: [550, 920]        # anchor radius 
            l_ballast: [50, 910]             # cable length
            l_anchor: [200, 910]             # cable length

        secondary_design_variables: None

        inequality_constraints: 
            l_cable: [570.0, 930.0]
            
        outputs:
            fowtList: ['tension']
            l_cable: ['l_cable']
            # unstretched_length: ['LBot_0', 'LBot_3', 'LBot_6']

    objective_function: ['tension']  
    objective_weights: [1.0]
    objective_reference: [500000]
    objective_function_alias: {'tension': 'weighted_raft_opt.weighted_multi_obj'}

    driver_information:
        tolerance: 0.01
        algorithm: SLSQP # Currently SLSQP, ALPSO, Diff_GA and COBYLA are supported in the framework
        recorder_file_name: dummy_stability.sql # Feel free to change the name of the file where values of all the design variables, objective functions and constraints are stored

    cases:
        keys : [wind_speed, wind_heading, turbulence, turbine_status, yaw_misalign, wave_spectrum, wave_period, wave_height, wave_heading , current_speed, current_heading ]
        data :  #   m/s        deg    % or e.g. 2B_NTM    string            deg         string          (s)         (m)         (deg)
            -  [   5.75,         0,            0.01,       operating,          0,        JONSWAP,         8.1,        2,           150,    0, 0     ]


Calcuvate
~~~~~~~~~

.. code-block:: python

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

        ms['lines'][1]['length'] = l_ballast # connecting anchor to connection
        ms['lines'][3]['length'] = l_ballast # connecting anchor to connection
        ms['lines'][5]['length'] = l_ballast # connecting anchor to connection

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

The user defined function for ``l_cable`` is given below:

.. code-block:: python
    
    def l_cable(design=None, model=None, x_platform=None, x_mooring=None):
        l_cable = x_mooring['l_ballast'] + x_mooring['l_anchor']
        return (l_cable)


Place the ``calculate.py`` file in the same directory.
And create the optimization setup as shown below:

.. code-block:: python

    from raft_opt import raft_opt
    import yaml
    import os
    import time
    import numpy as np

    design_file = 'oc3_design.yaml'
    user_input_file = 'user_input.yaml'

    with open(design_file) as file:
        design = yaml.load(file, Loader=yaml.FullLoader)

    with open(user_input_file) as file:
        user_input = yaml.load(file, Loader=yaml.FullLoader)

    def clean_numpy(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.generic):
            return obj.item()
        elif isinstance(obj, dict):
            return {key: clean_numpy(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [clean_numpy(element) for element in obj]
        return obj


    def single_point_opt():
        output = "s0.txt"

        with open(design_file) as file:
            design = yaml.load(file, Loader=yaml.FullLoader)

        with open(user_input_file) as file:
            user_input = yaml.load(file, Loader=yaml.FullLoader)

        design['cases']['data'] = [user_input['cases']['data'][0]]
        user_input['driver_information']['recorder_file_name'] = 's0.sql'
        current_dir = os.path.dirname(os.path.abspath(__file__))
        calcuvate_path = os.path.join(current_dir, 'calcuvate.py')
        optimized_design, user_input = raft_opt.run_opt(design, user_input, calcuvate_path, output)
        optimized_design, user_input = raft_opt.run_stability(optimized_design, user_input, calcuvate_path, 's0_stability.txt')

        optimized_design = clean_numpy(optimized_design)

        with open('optimized_design.yaml', 'w') as file:
            yaml.dump(optimized_design, file, default_flow_style=False)

        return (optimized_design, user_input)

    if __name__ == "__main__":
        start = time.time()
        optimized_design, _ = single_point_opt()
        # optimized_design, _ = multi_point_opt()
        print (f'{time.time() - start} seconds elapsed')

Convergence Plots
_________________

.. image:: /images/oc3_mooring_opt/tension.png

.. image:: /images/oc3_mooring_opt/pitch_max.png

.. image:: /images/oc3_mooring_opt/surge_max.png

.. image:: /images/oc3_mooring_opt/r_anchor.png

.. image:: /images/oc3_mooring_opt/z_fairlead.png

.. image:: /images/oc3_mooring_opt/l_anchor.png

.. image:: /images/oc3_mooring_opt/l_ballast.png