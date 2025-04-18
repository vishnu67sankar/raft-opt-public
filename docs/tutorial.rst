Tutorial
=========

In this tutorial, we will guide you through all the necessary 
steps to run a Floating Offshore Wind Turbine (FOWT) 
optimization problem. There are three key files required 
to run any optimization using RAFT-Opt:

- ``design_file.yaml``
- ``user_input.yaml``
- ``calcuvate.py``

User Input File
----------------------
The user input file is where the optimization problem needs 
to be set up. This YAML file consists of the following components:

.. code-block:: yaml

    cases: # Only one environmental state
        keys : [wind_speed, wind_heading, turbulence, turbine_status, yaw_misalign, wave_spectrum, wave_period, wave_height, wave_heading , current_speed, current_heading ]
        data :  #   m/s        deg    % or e.g. 2B_NTM    string            deg         string          (s)         (m)         (deg)
            -  [   10.5,         350,            0.01,       operating,          0,        JONSWAP,         8.1,        2.0,           325,    0.2,  0     ] ## case-1

    objective_function: ['mass_fowt', 'tension'] 
    objective_weights: [0.85, 0.15]
    objective_reference: [10e4, 10e6] 
    p_values: [1.0]

    platform:
        optimize: True or False
        update_stability: True or False
        design_variables: 
            dv_1: Float
            dv_2: Float
            .
            .

        secondary_design_variables: None or similar to design variables

        bounds_design_variables:
            dv_1: [Float, Float]
            dv_2: [Float, Float]
            .
            .

        outputs: # Can be any variable from within RAFT or any user defined function
            case_metrics: ['surge_max', 'sway_max', 'heave_max', 'roll_max', 'pitch_max', 'yaw_max', 'Mbase_max', 'AxRNA_max']
            fowtList: ['sway', 'heave', 'roll', 'pitch', 'yaw', 'mass_fowt']
            .
            .

        inequality_constraints: # Any constraint must be listed in the outputs
            pitch_max: [Float, Float]
            .
            .

    mooring:
        optimize: True or False
        update_stability: True or False
        design_variables: 
        # None 'OR'
            dv_3: Float
            dv_4: Float
            .
            .
            
        secondary_design_variables:
        # None 'OR'
            dv_5: Float
            dv_6: Float
            .
            .
            .

        bounds_design_variables:
        # None 'OR'
            dv_3: [Float, Float]
            dv_4: [Float, Float]
            .
            .

        inequality_constraints:
        # None 'OR'
            dv_3: [Float, Float]
            dv_4: [Float, Float]
            .
            .

        bounds_secondary_design_variables:
        # None 'OR'
            dv_5: Float
            dv_6: Float
            .
            .

        secondary_inequality_constraints:
        # None 'OR'
            dv_5: [Float, Float]
            dv_6: [Float, Float]
            .
            .

        secondary_outputs: 
        # None 'OR'
        # Example of user defined function is given here. 
        # Note that for the user defined functions the 
        # strings in the list should have the same value as the key
            intersect_dist_2 : ['intersect_dist_2']
            intersect_dist_4 : ['intersect_dist_4']

        outputs: 
            fowtList: ['tension']

    driver_information:
        tolerance: Float #Value less then 0.01 is recommended
        algorithm: Algorithm Name 
        # Currently SLSQP, SLSQP_PYOPT, ALPSO, Diff_GA and COBYLA are supported
        # We recommend using SLSQP first, if it does not work try using SLSQP_PYOPT
        recorder_file_name: name_of_recorder.sql 


Now, let's break this script down and understand each section

Objective Functions 
~~~~~~~~~~~~~~~~~~~

The ``objective_function`` is always minimized. If you want to
maximize the objective function, add a user defined function 
inside ``calcuvate.py``. 

.. code-block:: yaml

    cases: # Only one environmental state
        keys : [wind_speed, wind_heading, turbulence, turbine_status, yaw_misalign, wave_spectrum, wave_period, wave_height, wave_heading , current_speed, current_heading ]
        data :  #   m/s        deg    % or e.g. 2B_NTM    string            deg         string          (s)         (m)         (deg)
            -  [   10.5,         350,            0.01,       operating,          0,        JONSWAP,         8.1,        2.0,           325,    0.2,  0     ] ## case-1

    objective_function: ['mass_fowt', 'tension']  # First let's set the objective function (s) for the problem
    objective_weights: [0.85, 0.15]               # Objective weights in a multiobjective function
    objective_reference: [10e4, 10e6]             # Refernce value that non-dimensionalizes objective function
    # Both objective_weights and objective_reference should match the size of objective_function

For now let's consider only one environmental state. The objective function in each of the environmental states is a weighted sum that considers the normalized FOWT mass and the normalized maximum tension in the mooring lines. This is mathematically represented in the equations below:

.. math::
    f_i = \alpha_i \tilde{m} + \beta_i \tilde{T} \quad \text{where} \quad \alpha_i + \beta_i = 1

.. math::
    F = \sum_i w_i f_i

Each of the :math:`f_i` s represents the objective function for each of the environmental states. :math:`\tilde{m}` and :math:`\tilde{T}` are the normalized FOWT mass and mooring line tension, respectively. :math:`\alpha` and :math:`\beta` are their corresponding weights.

We use mass as a proxy for the levelized cost of energy (LCOE), since a lower mass implies a lower cost of construction. The primary goal is to reduce the overall FOWT mass; therefore, :math:`\alpha` is assigned a value of 0.85, prioritizing it three times more than the tension in the mooring lines.


Platform
~~~~~~~~

.. code-block:: yaml

    platform:
        optimize: True or False
        update_stability: True or False
        design_variables: 
        # None 'OR'
            dv_1: Float
            dv_2: Float
            .
            .
            .

        secondary_design_variables: None or similar to design variables

        bounds_design_variables:
        # None 'OR'
            dv_1: [Float, Float]
            dv_2: [Float, Float]
            .
            .
            .

        outputs: # Can be any variable from within RAFT or any user defined function
            case_metrics: ['surge_max', 'sway_max', 'heave_max', 'roll_max', 'pitch_max', 'yaw_max', 'Mbase_max', 'AxRNA_max']
            fowtList: ['sway', 'heave', 'roll', 'pitch', 'yaw', 'mass_fowt']
            .
            .
            .

        inequality_constraints: # Any constraint must be listed in the outputs
            pitch_max: [Float, Float]
            .
            .
            .

Setting optimize to True implies that the user intends to 
optimize the platform geometry. Consequently, the user is 
expected to provide design variables. Failing to do so will 
result in an error.

**Note:** The user can choose to provide design variables even
if optimize is set to False. This situation may arise when 
the user wants to use a baseline design that is geometrically 
different from the design specified in the design_file.yaml file.

**Note:** Any constraint or objective function must be first "listed" in the outputs. 
If ``mass_fowt`` needs to be added as an objective function then mention it in ``outputs[fowt_list]``. 

Setting ``update_stability`` to true informs the optimizer to define a optimization problem that solves for the
converged ``secondary_design_variables`` to ensure stability under unloaded condition of the FOWT.
The objective function of this optimizer is predefined as:

.. math:: 
    \text{Unloaded Stability} = \frac{heave}{0.5}^2 + \frac{surge}{0.5}^2 + \frac{sway}{0.5}^2 + \frac{pitch}{0.5}^2 + \frac{yaw}{0.5}^2 + \frac{roll}{0.5}^2

In addition to unloaded stability no other objective function can be added to the optimizer. However, additional constraints can be 
included in the optimizer using the key ``secondary_inequality_constraints``,
as demonstrated in the mooring section of the user_input.yaml file. The stability optimization take place after 
the geometric optimization for lowering the mass and tension.

Mooring
~~~~~~~~

The mooring section of the script is very similar to the 
platform section. 

.. code-block:: yaml

    mooring:
        optimize: True or False
        update_stability: True or False
        design_variables: 
        # None 'OR'
            dv_3: Float
            dv_4: Float
            .
            .

        secondary_design_variables:
        # None 'OR'
            dv_5: Float
            dv_6: Float
            .
            .

        bounds_design_variables:
        # None 'OR'
            dv_3: [Float, Float]
            dv_4: [Float, Float]
            .
            .

        inequality_constraints:
        # None 'OR'
            dv_3: [Float, Float]
            dv_4: [Float, Float]
            .
            .

        bounds_secondary_design_variables:
        # None 'OR'
            dv_5: Float
            dv_6: Float
            .
            .

        secondary_inequality_constraints:
        # None 'OR'
            dv_5: [Float, Float]
            dv_6: [Float, Float]
            .
            .

        secondary_outputs: 
        # None 'OR'
        # Example of user defined function is given here. 
        # Note that for the user defined functions the 
        # strings in the list should have the same string as the key
            intersect_dist_2 : ['intersect_dist_2']
            intersect_dist_4 : ['intersect_dist_4']

        outputs: 
            fowtList: ['tension']


**Note:** Notice that the output of the keys ``intersect_dist_2`` and ``intersect_dist_4``
are defined as strings with the identifier of the key itself, which indicates that they are not 
direct outputs from RAFT. Instead, these are custom user defined (defined within 
``calcuvate.py`` details of which will be discussed in the next subsection)
constraints used to inform the optimizer that they are not available within RAFT. 

Optimization Settings
~~~~~~~~~~~~~~~~~~~~~

The ``driver_information`` section specifies the parameters and settings for the optimization driver used in RAFT-opt. This section includes the tolerance for convergence, the optimization algorithm to be used, and the name of the file where the results will be recorded.

.. code-block:: yaml

    driver_information:
        tolerance: Float # Value less than 0.01 is recommended
        algorithm: Algorithm Name 
        # Currently SLSQP, SLSQP_PYOPT, ALPSO, Diff_GA and COBYLA are supported
        # We recommend using SLSQP first, if it does not work try using SLSQP_PYOPT
        recorder_file_name: name_of_recorder.sql

The parameters are

**tolerance**:
    - **Type**: ``Float``
    - **Description**: This parameter defines the convergence tolerance for the optimization algorithm. A smaller value indicates a stricter convergence criterion.
    - **Recommendation**: A value less than ``0.01`` is recommended for achieving precise optimization results.

**algorithm**:
    - **Type**: ``String``
    - **Description**: This parameter specifies the optimization algorithm to be used. Several algorithms are supported, each with its strengths and weaknesses. The choice of algorithm can affect the speed and success of the optimization.
    - **Supported Algorithms**: 
      
      - ``SLSQP``: Sequential Least Squares Quadratic Programming
      
      - ``SLSQP_PYOPT``: SLSQP implementation from PYOPT
      - ``ALPSO``: Augmented Lagrangian Particle Swarm Optimization
      - ``Diff_GA``: Differential Evolution Genetic Algorithm
      - ``COBYLA``: Constrained Optimization BY Linear Approximations
    - **Recommendation**: It is recommended to use ``SLSQP`` first. If it does not work, try using ``SLSQP_PYOPT``.
   
**recorder_file_name**:
    - **Type**: ``String``
    - **Description**: This parameter defines the name of the file where the results of the optimization process, including the values of all design variables, objective functions, and constraints, will be recorded.
    - **Example**: ``recorder_file_name: optimization_results.sql``


Calcuvate.py
-------------
The ``calcuvate.py`` consists of the following functions

- ``calcuvate()``
- ``_updateColumns()``
- ``_updateMoorings()``
- ``user_defined_functions()``

The function ``_updateColumns()`` defines the mathematical relation between the platform ``design_variables``, 
``secondary_design_variables`` and the platform geometry. Similarly, the function ``_updateMoorings()`` 
defines the mathematical relation between the mooring ``design_variables``, ``secondary_design_variables`` and the 
mooring line configuration. Calcuvate function returns the next iterative design based on all the design variables 
obtained from the optimizer in the current iteration. 

Let's illustrate the use of the input file and calcuvate file using some examples. 
