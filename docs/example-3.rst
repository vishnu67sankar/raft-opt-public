Example-3
===========

Muliobjective Optimization
-----------------------------------
So far we have looked at single point optimization, however, oceanic and wind variability 
cannot be overlooked in a design optimization process. In this example, the OC4 design is being 
optimized for multiple oceanic and wind states. Based on the data from Humboldt bay three oceanic and wind states
with the highest variability. This example optimizes both the mass and tension across the three states. 

Open a local folder in your machine, and copy the 
``oc4_semisub.yaml`` from the ``example>oc4_semisub`` 
folder present in RAFT-Opt repository. This example consists of
OC4 5 MW turbine designed by NREL. The setup file for this problem is shown below:

User Input File
~~~~~~~~~~~~~~~

.. code-block:: yaml

    cases:
        keys : [wind_speed, wind_heading, turbulence, turbine_status, yaw_misalign, wave_spectrum, wave_period, wave_height, wave_heading , current_speed, current_heading  ]
        data :  #   m/s        deg    % or e.g. 2B_NTM    string            deg         string          (s)         (m)         (deg)
            -  [   10.5,         350,            0.01,       operating,          0,        JONSWAP,         8.1,        2.0,           325,    0.2,  0     ] ## state-1
            -  [   9.5,         335,            0.01,       operating,          0,        JONSWAP,         10.5,        2.1,           300,    0.22, 0     ] ## state-2
            -  [   15.0,         325,            0.01,       operating,          0,        JONSWAP,         11.7,        3.2,           300,    0.4,  0     ] ## state-3

    p_values: [0.675, 0.25, 0.075] ## probability of each state above

    platform:
        optimize: True
        update_stability: False
        design_variables: 
            lower_column_d: 24
            upper_column_d: 12
        
        secondary_design_variables:
            lower_column_l_fill: 0.84
            upper_column_l_fill: 0.2988

        bounds_design_variables:
            lower_column_d: [20., 28.]
            upper_column_d: [5., 20.]

        bounds_secondary_design_variables:
            lower_column_l_fill: [0.0, 1.0]
            upper_column_l_fill: [0.0, 1.0]

        outputs:
            case_metrics: ['surge_max', 'sway_max', 'heave_max', 'roll_max', 'pitch_max', 'yaw_max', 'Mbase_max']
            fowtList: ['heave', 'pitch', 'mass_fowt']
            eigen_frequencies: {'f_heave': 2, 'f_pitch': 3}

        secondary_outputs: None

        inequality_constraints: 
            f_heave: [18.5, None]
            f_pitch: [30.0, None]
            pitch_max: [-10.0, 10.0]
            surge_max: [-20.0, 20.0]
            
        secondary_inequality_constraints: None
        secondary_outputs: None

    mooring:
        optimize: True
        update_stability: False
        design_variables: 
            line_length: 800
            line_dia: 0.0766

        bounds_design_variables:
            line_length: [500.0, 1200.0]
            line_dia: [0.002, 0.2]

        secondary_design_variables: None
        outputs: 
            fowtList: ['tension']
            MBL: ['MBL']

        inequality_constraints: 
            MBL: [2.0, None]
            
        secondary_inequality_constraints: None
        secondary_outputs: None

    objective_function: ['mass_fowt', 'tension']
    objective_weights: [0.75, 0.25]
    objective_reference: [2750, 300000.0]

    driver_information:
        tolerance: 0.01
        algorithm: SLSQP # Currently SLSQP, SLSQP_PYOPT, ALPSO, Diff_GA and COBYLA are supported in the framework
        recorder_file_name: dummy.sql # Feel free to change the name of the file where values of all the design variables, objective functions and constraints are stored


Calcuvate
~~~~~~~~~

.. code-block:: python

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

    def _updateMoorings(n_columns, fairlead, lower_column, ms, line_length=None, line_dia=None): 
        
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

            elif(item['name'] == 'line1_anchor'):
                item['location'][0] = (line_length*np.cos(np.pi/3) + 1)
                item['location'][1] = (line_length*np.sin(np.pi/3) + 1.75)

            elif(item['name'] == 'line2_anchor'):
                item['location'][0] = -1*(line_length + 1)
            
            elif(item['name'] == 'line3_anchor'):
                item['location'][0] = (line_length*np.cos(np.pi/3) + 1)
                item['location'][1] = -1*(line_length*np.sin(np.pi/3) + 1.75)


        for item in ms['lines']:
            item['length'] = line_length

        ms['line_types'][0]['diameter'] = line_dia
        ms['line_types'][0]['mass_density'] = 20.0e3 * line_dia**2
        ms['line_types'][0]['stiffness'] = 85.6e9*(line_dia)**2 - 3.93e7*(line_dia)**3
        ms['line_types'][0]['breaking_load'] = 9.11e2*(line_dia) + 1.21e9*(line_dia)**2 - 2.19e9*(line_dia)**3

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
        
        lower_column['d'] = x_platform['lower_column_d']
        upper_column['d'] = x_platform['upper_column_d']
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

        line_length = x_mooring['line_length']
        line_dia = x_mooring['line_dia']

        ms = _updateMoorings(3, fairlead, lower_column, ms, line_length, line_dia)
        
        design['platform']['members'][1] = lower_column
        design['platform']['members'][2] = upper_column
        design['platform']['members'][3:] = pontoons
        design['platform']['members'][7] = cross_brace
        design['mooring'] = ms

        return (design)


    def MBL(design=None, model=None, x_platform=None, x_mooring=None):
        breaking_load = design['mooring']['line_types'][0]['breaking_load']
        MBL = breaking_load/max(model.fowtList[0].ms.getTensions())
        return (MBL)


Place the ``calculate.py`` file in the same directory.
And create the optimization setup as shown below:

.. code-block:: python

    from raft_opt import raft_opt
    import yaml
    import os
    import raft
    import matplotlib.pyplot as plt
    import time 

    def multi_point_opt():
        output = "multi_pt_final_1.txt"
        design_file = 'oc4_semisub.yaml'
        user_input_file = 'user_input.yaml'

        with open(design_file) as file:
            design = yaml.load(file, Loader=yaml.FullLoader)

        with open(user_input_file) as file:
            user_input = yaml.load(file, Loader=yaml.FullLoader)

        user_input['driver_information']['recorder_file_name'] = 'multi_pt_final_1.sql'
        current_dir = os.path.dirname(os.path.abspath(__file__))
        calcuvate_path = os.path.join(current_dir, 'calcuvate.py')

        p_values = user_input['p_values']
        cases = user_input['cases']
        optimized_design, user_input = raft_opt.run_weighted_opt(design, user_input, cases, p_values, calcuvate_path, output)

    if __name__ == "__main__":
        start = time.time()
        single_point_opt()
        # multi_point_opt()
        print(f"{time.time()-start} seconds elapsed")

Convergence Plots
_________________

.. image:: /images/oc4_multiobjective/tension.png

.. image:: /images/oc4_multiobjective/mass.png

.. image:: /images/oc4_multiobjective/lower_column_d.png

.. image:: /images/oc4_multiobjective/upper_column_d.png

.. image:: /images/oc4_multiobjective/line_length.png

.. image:: /images/oc4_multiobjective/line_dia.png