
import raft
import yaml
import openmdao.api as om
import numpy as np
import moorpy as mp
import random
import copy
import argparse
from raft_opt import adjustStability
import ast
import importlib.util
import sys
import os
from copy import deepcopy 


def import_calcuvate(module_name, file_path):
    """
    Dynamically imports the 'calcuvate' module from a specified file path.

    This allows the optimization script to use custom calculation functions
    defined externally.

    Args:
        module_name (str): The name to assign to the imported module (e.g., 'calcuvate').
        file_path (str): The absolute or relative path to the Python file
                         containing the module's code.

    Returns:
        module: The imported module object.
    """
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

class Turbine(om.ExplicitComponent):
    """
    Represents the turbine component within the OpenMDAO model.

    Placeholder class. Currently does not implement specific turbine logic
    within this component, but acts as a structural element in the model
    hierarchy inherited by OWT.
    """
    pass

class Platform(om.ExplicitComponent):
    """
    Represents the floating platform component in the OpenMDAO model.

    Handles the definition of platform-related inputs based on the design
    and user input YAML files. This includes primary design variables,
    secondary design variables (if any), and fixed parameters. It also
    declares platform-related outputs specified by the user.

    Options:
        design (dict): Dictionary loaded from the design input YAML file.
        user_input (dict): Dictionary loaded from the user input YAML file.
    """

    def initialize(self):
        """Declares options for the Platform component."""
        self.options.declare('design', desc='design input yaml file name')
        self.options.declare('user_input', desc = 'user input yaml file name')

    def setup(self):
        """
        Defines inputs and outputs for the Platform component.

        Reads the 'design' and 'user_input' dictionaries to determine
        which platform parameters are design variables (inputs) and which
        quantities should be computed as outputs.
        """
        design = self.options['design']
        user_input = self.options['user_input']
      
        design_variables = {}
        secondary_design_variables = {}
        platform_outputs = {}

        platform_members = design['platform']['members']
        
        if (user_input['platform']['design_variables'] != 'None'):
            design_variables = user_input['platform']['design_variables']
            for key, value in design_variables.items():
                self.add_input(key, val=value)
        
        if (user_input['platform']['outputs'] != 'None'):
            platform_outputs = user_input['platform']['outputs']

        n_members = len(platform_members)

        for n in range(0, n_members):
            name = platform_members[n]['name']
            for key, value in platform_members[n].items():
                
                if (key == 'name'):
                    continue

                if (type(value) == list):
                        if (((name + '_' + key) not in design_variables.keys()) and ((name + '_' + key) not in secondary_design_variables.keys())):
                            self.add_input(name + '_' + key, val=np.array(value))

                elif (type(value) == (float or int or bool)):
                        if (((name + '_' + key) not in design_variables.keys()) and ((name + '_' + key) not in secondary_design_variables.keys())):
                            self.add_input(name + '_' + key, val=value) 

                elif (type(value) == str):
                    continue
        
        if (user_input['platform']['outputs'] != 'None'):
            for key, value in platform_outputs.items():
                for _output in value:
                    self.add_output(_output)

class MooringSystem(om.ExplicitComponent):
    """
    Represents the mooring system component in the OpenMDAO model.

    Handles the definition of mooring system inputs based on the design
    and user input YAML files. This includes primary design variables,
    secondary design variables (if any), and fixed parameters (like point
    locations if not varied). It also declares mooring-related outputs
    specified by the user.

    Options:
        design (dict): Dictionary loaded from the design input YAML file.
        user_input (dict): Dictionary loaded from the user input YAML file.
    """

    def initialize(self):
        """Declares options for the MooringSystem component."""
        self.options.declare('design', desc='design input yaml file name')
        self.options.declare('user_input', desc = 'user input yaml file name')
       
    def setup(self):
        """
        Defines inputs and outputs for the MooringSystem component.

        Reads the 'design' and 'user_input' dictionaries to determine
        which mooring parameters are design variables (inputs) and which
        quantities should be computed as outputs.
        """
        design = self.options['design']
        user_input = self.options['user_input']
       
        design_variables = {}
        secondary_design_variables = {}
        mooring_outputs = {}
        mooring_points = {}
        mooring_lines = {}

        try:
            mooring_points = design['mooring']['points']
            mooring_lines = design['mooring']['lines']

        except:
            print('Mooring points and lines not present in design files, probably designed passed as moorpy file')

        if (user_input['mooring']['design_variables'] != 'None'):
            design_variables = user_input['mooring']['design_variables']
            for key, value in design_variables.items():
                self.add_input(key, val=value)

        if (user_input['mooring']['outputs'] != 'None'):
            mooring_outputs = user_input['mooring']['outputs']

        n_points = len(mooring_points)
        n_lines = len(mooring_lines)

        for n in range(0, n_points):
            name = mooring_points[n]['name']
            for key, value in mooring_points[n].items():
                if (key == 'location'):
                    if (((name + '_' + key) not in design_variables.keys()) and ((name + '_' + key) not in secondary_design_variables.keys())):
                        self.add_input(name + '_' + key, val=np.array(value))

        for n in range(0, n_lines):
            name = mooring_lines[n]['name']
            for key, value in mooring_lines[n].items():
                if (key == 'location'):
                    if (((name + '_' + key) not in design_variables.keys()) and ((name + '_' + key) not in secondary_design_variables.keys())):
                        self.add_input(name + '_' + key, val=np.array(value))

        if (user_input['mooring']['outputs'] != 'None'):
            for key, value in mooring_outputs.items():
                for _output in value:
                    self.add_output(_output)


class OWT(Platform, MooringSystem, Turbine):
    """
    OpenMDAO ExplicitComponent representing the Offshore Wind Turbine system.

    Integrates Platform, MooringSystem, and Turbine characteristics.
    It takes design variables as inputs, runs the RAFT analysis using the
    'calcuvate' module to update the design dictionary, and computes
    specified outputs (objectives and constraints).

    Inherits setup methods from Platform and MooringSystem to define inputs
    and outputs related to those subsystems.

    Options:
        design (dict): Dictionary loaded from the design input YAML file.
        user_input (dict): Dictionary loaded from the user input YAML file.

    Attributes:
        is_solver_divergence (bool): Flag indicating if the RAFT solver
                                     encountered an error during computation.
        surge, sway, heave, roll, pitch, yaw (float | None): Static offsets
                                    calculated by RAFT's analyzeUnloaded.
    """
     
    def setup(self):
        """
        Declares partial derivatives for optimization.

        Uses finite differencing ('fd') to approximate partial derivatives
        of outputs (objectives and constraints) with respect to inputs
        (design variables). Step sizes are adjusted based on the magnitude
        of the design variable bounds.
        """
        self.design = self.options['design']
        self.user_input = self.options['user_input']
        self.is_solver_divergence = False

        Platform.setup(self)
        MooringSystem.setup(self)
        # Turbine.setup(self)

        self.surge = None
        self.sway = None
        self.heave = None
        self.roll = None
        self.pitch = None
        self.yaw = None
        self.AxRNA_max = None
        self.Mbase = None

    def setup_partials(self):
        """
        Declares partial derivatives for optimization.

        Uses finite differencing ('fd') to approximate partial derivatives
        of outputs (objectives and constraints) with respect to inputs
        (design variables). Step sizes are adjusted based on the magnitude
        of the design variable bounds.
        """
        objective_function = self.user_input['objective_function']

        if (self.user_input['platform']['inequality_constraints'] != 'None'):

            ineq_cons_platform = self.user_input['platform']['inequality_constraints']
            
            if (self.user_input['platform']['optimize'] == True):
                dv_platform = self.user_input['platform']['bounds_design_variables']

                for cons_key in ineq_cons_platform.keys():
                    for dv_key, bnd in dv_platform.items():
                        if(bnd[-1] < 1):
                            self.declare_partials(cons_key, dv_key, method='fd', step=10e-5)

                        elif (bnd[-1]/100 < 1):
                            self.declare_partials(cons_key, dv_key, method='fd', step=10e-2)

                        elif (bnd[-1]/100 >= 1):
                            self.declare_partials(cons_key, dv_key, method='fd', step=10e-1)

            if (self.user_input['mooring']['optimize'] == True):
                dv_mooring = self.user_input['mooring']['bounds_design_variables']

                for cons_key in ineq_cons_platform.keys():
                    for dv_key, bnd in dv_mooring.items():
                        if(bnd[-1] < 1):
                            self.declare_partials(cons_key, dv_key, method='fd', step=10e-5)

                        elif (bnd[-1]/100 < 1):
                            self.declare_partials(cons_key, dv_key, method='fd', step=10e-2)

                        elif (bnd[-1]/100 >= 1):
                            self.declare_partials(cons_key, dv_key, method='fd', step=10e-1)

        if (self.user_input['mooring']['inequality_constraints'] != 'None'):
            ineq_cons_mooring = self.user_input['mooring']['inequality_constraints']

            if (self.user_input['mooring']['optimize'] == True):
                dv_mooring = self.user_input['mooring']['bounds_design_variables']
                for cons_key in ineq_cons_mooring.keys():
                    for dv_key, bnd in dv_mooring.items():
                        if(bnd[-1] < 1):
                            self.declare_partials(cons_key, dv_key, method='fd', step=10e-5)

                        elif (bnd[-1]/100 < 1):
                            self.declare_partials(cons_key, dv_key, method='fd', step=10e-2)

                        elif (bnd[-1]/100 >= 1):
                            self.declare_partials(cons_key, dv_key, method='fd', step=10e-1)

            if (self.user_input['platform']['optimize'] == True):
                dv_platform = self.user_input['platform']['bounds_design_variables']
                for cons_key in ineq_cons_mooring.keys():
                    for dv_key, bnd in dv_platform.items():
                        if(bnd[-1] < 1):
                            self.declare_partials(cons_key, dv_key, method='fd', step=10e-5)

                        elif (bnd[-1]/100 < 1):
                            self.declare_partials(cons_key, dv_key, method='fd', step=10e-2)

                        elif (bnd[-1]/100 >= 1):
                            self.declare_partials(cons_key, dv_key, method='fd', step=10e-1)

        for _output in objective_function:

            if (self.user_input['mooring']['optimize'] == True):
                dv_mooring = self.user_input['mooring']['bounds_design_variables']
                for dv_key, bnd in dv_mooring.items():
                    if(bnd[-1] < 1):
                            self.declare_partials(cons_key, dv_key, method='fd', step=10e-5)

                    elif (bnd[-1]/100 < 1):
                        self.declare_partials(_output, dv_key, method='fd', step=10e-2)

                    elif (bnd[-1]/100 >= 1):
                        self.declare_partials(_output, dv_key, method='fd', step=10e-1)
            
            if (self.user_input['platform']['optimize'] == True):
                dv_platform = self.user_input['platform']['bounds_design_variables']
                for dv_key, bnd in dv_platform.items():
                    if(bnd[-1] < 1):
                            self.declare_partials(cons_key, dv_key, method='fd', step=10e-5)

                    elif (bnd[-1]/100 < 1):
                        self.declare_partials(_output, dv_key, method='fd', step=10e-2)

                    elif (bnd[-1]/100 >= 1):
                        self.declare_partials(_output, dv_key, method='fd', step=10e-1)

    def compute (self, inputs, outputs):
        """
        Performs the RAFT analysis for the current set of inputs.

        Args:
            inputs (om.Vector): Input vector containing current design variable values.
            outputs (om.Vector): Output vector to store computed objective and constraint values.
        """
        x_platform = {}
        x_primary_platform = {}
        x_secondary_platform = {}
        x_bnd_secondary_platform = {}
        platform_outputs = {}

        x_mooring = {}
        x_primary_mooring = {}
        x_secondary_mooring = {}
        mooring_outputs = {}
        x_bnd_secondary_mooring = {}

        try:
            x_primary_platform = self.user_input['platform']['design_variables']
        except:
            print('Primary platform design variables not provided for the platform. User wants to proceed with the design in the desigl_file.yaml as the baseline design')
            
        try:
            x_secondary_platform = self.user_input['platform']['secondary_design_variables']
        except:
            print('Secondary platform design variables not provided for the platform. User wants to proceed with the design in the desigl_file.yaml as the baseline design')
        
        
        try:
            x_primary_mooring = self.user_input['mooring']['design_variables']
        except:
            print('Primary mooring design variables not provided for the mooring lines. User wants to proceed with the design in the desigl_file.yaml as the baseline design')
            
        try:
            x_secondary_mooring = self.user_input['mooring']['secondary_design_variables']
        except:
            print('Secondary mooring design variables not provided for the mooring lines. User wants to proceed with the design in the desigl_file.yaml as the baseline design')
        
        try:
            platform_outputs = self.user_input['platform']['outputs']
        except:
            print('Platform outputs not given')

        if (self.user_input['platform']['optimize'] == True) or (self.user_input['platform']['design_variables'] != None):
            platform_outputs = self.user_input['platform']['outputs']

            try:
                x_bnd_platform = self.user_input['platform']['bounds_design_variables']
                
                for key in x_primary_platform.keys(): ## platform DVs
                    if (inputs[key][0] < x_bnd_platform[key][0]):
                        inputs[key][0] = x_bnd_platform[key][0]

                    elif(inputs[key][0] > x_bnd_platform[key][1]):
                        inputs[key][0] = x_bnd_platform[key][1]
                
                    x_primary_platform[key] = inputs[key][0]
                    print(f'{key} = {x_primary_platform[key]}')

                x_platform.update(x_primary_platform)
                self.user_input['platform']['design_variables'] = x_primary_platform

            
            except:
                x_bnd_platform = None

            
        if (self.user_input['mooring']['optimize'] == True) or (self.user_input['mooring']['design_variables'] != None):
            x_primary_mooring = self.user_input['mooring']['design_variables']
            mooring_outputs = self.user_input['mooring']['outputs']
            try:
                x_bnd_mooring = self.user_input['mooring']['bounds_design_variables']
                
                for key in x_primary_mooring.keys(): ## Mooring DVs
                    if (inputs[key][0] < x_bnd_mooring[key][0]):
                        inputs[key][0] = x_bnd_mooring[key][0]

                    elif(inputs[key][0] > x_bnd_mooring[key][1]):
                        inputs[key][0] = x_bnd_mooring[key][1]

                    x_primary_mooring[key] = inputs[key][0]
                    print(f'{key} = {x_primary_mooring[key]}')

                x_mooring.update(x_primary_mooring)
                self.user_input['mooring']['design_variables'] = x_primary_mooring

            
            except:
                x_bnd_mooring = None

            
        objective_function = self.user_input['objective_function']

        if (self.user_input['platform']['update_stability'] == True):
            # x_secondary_platform  = adjustStability.main(self.design, self.user_input, calcuvate)
            self.user_input['platform']['secondary_design_variables'] = x_secondary_platform
            x_platform.update(x_secondary_platform)

            for key in x_secondary_platform.keys():
                print(f'{key} = {x_secondary_platform[key]}')

        if (self.user_input['mooring']['update_stability'] == True):
            # x_secondary_mooring = adjustStability.main(self.design, self.user_input, calcuvate)
            self.user_input['mooring']['secondary_design_variables'] = x_secondary_mooring
            x_mooring.update(x_secondary_mooring)

            for key in x_secondary_mooring.keys():
                print(f'{key} = {x_secondary_mooring[key]}')

        print('x_mooring = ', x_mooring)
        print('x_platform = ', x_platform)

        self.design = calcuvate.calcuvate(self.design, x_platform, x_mooring)
        design = deepcopy(self.design)
        model = raft.Model(design)

        try:
            model.analyzeUnloaded()
            self.surge = model.fowtList[0].Xi0[0] 
            self.sway = model.fowtList[0].Xi0[1] 
            self.heave = model.fowtList[0].Xi0[2]
            self.roll = model.fowtList[0].Xi0[3]
            self.pitch = model.fowtList[0].Xi0[4] 
            self.yaw = model.fowtList[0].Xi0[5]
            model.solveEigen()
            model.analyzeCases(display=0)

        except:
            print ('Runtime error in RAFT Solver')
            self.is_solver_divergence = True
            # raise om.AnalysisError('Runtime error in RAFT Solver')

        if (self.user_input['mooring']['outputs'] != 'None'):
            for key, value in mooring_outputs.items():
                if (key == 'fowtList'):
                    for _output in value:
                        
                        if (self.is_solver_divergence == True):
                            outputs[_output] = 10**20 #float('inf') 
                            
                        else: 
                            if(_output == 'tension'):
                                outputs[_output] = max(model.fowtList[0].ms.getTensions())
                            
                            elif(_output == 'max_tension'):
                                outputs[_output] = max(model.results['case_metrics'][0][0]['Tmoor_max'])
                        
                        print(f'{_output} = {outputs[_output]}')

                elif (key == 'unstretched_length'):
                    for _output in value:
                        if (self.is_solver_divergence == True):
                            outputs[_output] = 10**20 #float('inf') 
                            
                        else: 
                            _index = _output.split('_')[-1]
                            outputs[_output] = model.fowtList[0].ms.lineList[int(_index)].LBot/(x_mooring['l_cable'])
                        
                        print(f'{_output} = {outputs[_output]}')

                elif (key == value[0]):
                    if (self.is_solver_divergence == True):
                        outputs[key] = 10**20 #float('inf') 
                    
                    else:
                        args = (deepcopy(design), deepcopy(model), x_platform, x_mooring)
                        outputs[key] = getattr(calcuvate, key)(*args)
                    
                    print(f'{key} = {outputs[key]}')


        if (self.user_input['platform']['outputs'] != 'None'):
            for key, value in platform_outputs.items():
                if (key == 'case_metrics'):
                    for _output in value:
                            if (self.is_solver_divergence == True):
                                outputs[_output] = 10**20 # float('inf') 
                            
                            else:
                                outputs[_output] = model.results['case_metrics'][0][0][_output]
                            
                            print(f'{_output} = {outputs[_output]}')
                
                elif (key == 'fowtList'):
                    for _output in value:
                        if (self.is_solver_divergence == True):
                            outputs[_output] = 10**20 #float('inf')
                            print(f'{_output} = {outputs[_output]}')

                        else: 
                            if(_output == 'sway'):
                                outputs[_output] = self.sway 
                                print(f'{_output} = {outputs[_output]}')
                            
                            elif(_output == 'heave'):
                                outputs[_output] = self.heave
                                print(f'{_output} = {outputs[_output]}')
                            
                            elif(_output == 'roll'):
                                outputs[_output] = self.roll 
                                print(f'{_output} = {outputs[_output]}')
                            
                            elif(_output == 'pitch'):
                                outputs[_output] = self.pitch 
                                print(f'{_output} = {outputs[_output]}')
                            
                            elif(_output == 'yaw'):
                                outputs[_output] = self.yaw 
                                print(f'{_output} = {outputs[_output]}')
                            
                            elif(_output == 'mass_fowt'):
                                outputs[_output] = model.fowtList[0].m_shell/1000
                                print(f'{_output} = {outputs[_output]}')
                            
            
                elif (key == 'eigen_frequencies'):
                    for _key, _val in value.items():
                        if (self.is_solver_divergence == True):
                            outputs[_key] = 10**20 #float('inf') 
                        else:
                            outputs[_key] = 1/model.results['eigen']['frequencies'][_val]
                        print(f'{_key} = {outputs[_key]}')
                
                elif (key == 'mass_fowt'):
                    outputs['mass_fowt'] =  model.fowtList[0].m_shell/1000
                    print(outputs['mass_fowt'])
                
                elif (key == value[0]):
                    args = (deepcopy(design), deepcopy(model), x_platform, x_mooring)
                    outputs[key] = getattr(calcuvate, key)(*args)
        
        self.is_solver_divergence = False
    
    def get_optimized_data(self):
        """
        Returns the final design and user_input dictionaries.

        Note: This currently returns the self.design and self.user_input
        attributes. Be aware that self.design might have been modified
        in the last compute call if not handled carefully (e.g., using deepcopy).

        Returns:
            tuple: A tuple containing:
                - dict: The potentially modified design dictionary.
                - dict: The potentially modified user_input dictionary.
        """
        return (self.design, self.user_input)


class WeightedObjectives(om.ExplicitComponent):
    """
    Combines multiple objective functions into a single weighted sum.

    Takes individual objective values as inputs and computes a single
    output 'weighted_multi_obj' using specified weights and reference values.
    The formula is: sum(obj_i * weight_i / ref_value_i).

    Options:
        w_values (list[float]): List of weights for each objective.
        r_values (list[float]): List of reference values for normalization.
    """

    def initialize(self):
        self.options.declare('w_values', types=list, desc="List of weights associated with each objective function")
        self.options.declare('r_values', types=list, desc="List of references associated with each objective function")
    
    def setup(self):
        """
        Declares options for the WeightedObjectives component.
        """
        num_objs = len(self.options['w_values'])
        
        for i in range(num_objs):
            self.add_input(f'obj_{i}', val=0.0)
        
        self.add_output('weighted_multi_obj', val=0.0)
    
    def setup_partials(self):
        """Declares analytical partial derivatives."""
        num_objs = len(self.options['w_values'])
        for i in range(num_objs):
            self.declare_partials('weighted_multi_obj', f'obj_{i}')

    def compute(self, inputs, outputs):
        """
        Computes the weighted sum of objectives.

        Args:
            inputs (om.Vector): Input vector containing individual objective values (obj_0, obj_1, ...).
            outputs (om.Vector): Output vector where 'weighted_multi_obj' is stored.
        """
        w_values = self.options['w_values']
        r_values = self.options['r_values']
        num_objs = len(self.options['w_values'])
        
        objs = [inputs[f'obj_{i}'] for i in range (num_objs)]

        for i, obj in enumerate(objs):
            print(f"Obj_{i} = {obj}")

        outputs['weighted_multi_obj'] =  sum(f * w / r for f, w, r in zip(objs, w_values, r_values))
        print(f"weighted_multi_obj = {outputs['weighted_multi_obj']}")

    def compute_partials(self, inputs, partials):
        """
        Computes analytical partial derivatives.

        Args:
            inputs (om.Vector): Input vector (not directly used, derivatives are constant).
            partials (om.Jacobian): Jacobian object to store derivative values.
        """
        w_values = self.options['w_values']
        r_values = self.options['r_values']
        num_objs = len(self.options['w_values'])

        for i in range(num_objs):
            partials['weighted_multi_obj', f'obj_{i}'] = w_values[i]/r_values[i]

class WeightedOWT(om.ExplicitComponent):
    """
    Combines objective function values from multiple probabilistic cases.

    Takes objective values from different analysis cases (e.g., different
    environmental conditions) as inputs and computes a single weighted
    average based on the probability of each case. The formula is:
    sum(obj_i * probability_i).

    Options:
        p_values (list[float]): List of probabilities for each input objective/case.
                                Should sum to 1.0 ideally.
    """
    def initialize(self):
        """Declares options for the WeightedOWT component."""
        self.options.declare('p_values', types=list, desc="List of probabilities associated with each k value")
    
    def setup(self):
        """Defines inputs for case objectives and the combined output."""
        num_p = len(self.options['p_values'])
        
        for i in range(num_p):
            self.add_input(f'obj_{i}', val=0.0)
        
        self.add_output('weighted_multi_obj', val=0.0)
    
    def setup_partials(self):
        """Declares analytical partial derivatives."""
        num_p = len(self.options['p_values'])
        for i in range(num_p):
            self.declare_partials('weighted_multi_obj', f'obj_{i}')
    
    def compute(self, inputs, outputs):
        """Computes the probability-weighted sum of case objectives.

        Args:
            inputs (om.Vector): Input vector containing objective values from each case (obj_0, obj_1, ...).
            outputs (om.Vector): Output vector where 'weighted_multi_obj' is stored.
        """
        p_values = self.options['p_values']
        num_p = len(p_values)
        objs = [inputs[f'obj_{i}'] for i in range (num_p)]

        for obj in objs:
            print(f"Obj = {obj}")

        outputs['weighted_multi_obj'] = sum(p * obj for p, obj in zip (p_values, objs))
        print(f"weighted_multi_obj = {outputs['weighted_multi_obj']}")

    def compute_partials(self, inputs, partials):
        """Computes analytical partial derivatives.

        Args:
            inputs (om.Vector): Input vector (not directly used).
            partials (om.Jacobian): Jacobian object to store derivative values.
        """
        p_values = self.options['p_values']
        num_p = len(p_values)
        for i in range(num_p):
            partials['weighted_multi_obj', f'obj_{i}'] = p_values[i]

def run_weighted_opt(design, user_input, cases, p_values, calcuvate_path, output):
    """Runs a RAFT optimization considering multiple probabilistic cases.

    Sets up and executes an OpenMDAO problem where multiple OWT instances
    (one for each case) are evaluated. Their individual weighted objectives
    are then combined using probabilities in the WeightedOWT component.

    Args:
        design (dict): Base design dictionary.
        user_input (dict): User input dictionary specifying optimization settings.
        cases (dict): Dictionary containing case-specific data (e.g., environmental conditions).
                      Expected format: {'data': [case_data_0, case_data_1, ...]}.
        p_values (list[float]): List of probabilities corresponding to each case in `cases['data']`.
        calcuvate_path (str): Path to the 'calcuvate.py' file.
        output_log_file (str): Path to the file where stdout/stderr will be redirected.

    Returns:
        tuple: A tuple containing:
            - dict: The final optimized design dictionary (potentially modified).
            - dict: The user_input dictionary (potentially modified).
    """
    current_directory = os.path.dirname(os.path.abspath(__file__))
    
    with open(output, "w") as output_file:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        sys.stdout = output_file
        sys.stderr = output_file

        try:
            optimized_design, user_input = raft_weighted_opt(design, user_input, cases, p_values, calcuvate_path)
            return (optimized_design, user_input)
        
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

def raft_weighted_opt(design, user_input, cases, p_values, calcuvate_path):
    """Core logic for setting up and running the weighted (probabilistic) optimization.

    Internal function called by `run_weighted_opt`.

    Args:
        design (dict): Base design dictionary.
        user_input (dict): User input dictionary.
        cases (dict): Case-specific data.
        p_values (list[float]): Case probabilities.
        calcuvate_path (str): Path to 'calcuvate.py'.

    Returns:
        tuple: A tuple containing:
            - dict: The final optimized design dictionary.
            - dict: The user_input dictionary.
    """

    global calcuvate
    calcuvate = import_calcuvate('calcuvate', calcuvate_path)
    
    algorithm = user_input['driver_information']['algorithm']
    tolerance = user_input['driver_information']['tolerance']
    objective_function = user_input['objective_function']
    w_values = user_input['objective_weights']
    r_values = user_input['objective_reference']

    model = om.Group()
    n_cases = len(p_values)

    for i in range(0, n_cases):
        print(f"case {i} = {cases['data'][i]}")
        design['cases']['data'] = [deepcopy(cases['data'][i])]
        print(f"design['cases']['data'] = {design['cases']['data']}")
        model.add_subsystem(f'run_raft_opt_{i}', OWT(design=deepcopy(design), user_input=deepcopy(user_input)), promotes_inputs=['*'])
        model.add_subsystem(f'weighted_raft_opt_{i}', WeightedObjectives(w_values=w_values, r_values=r_values))
        for j, obj in enumerate(objective_function):
            model.connect(f'run_raft_opt_{i}.{obj}', f'weighted_raft_opt_{i}.obj_{j}')
        
    model.add_subsystem('rdo', WeightedOWT(p_values=p_values))

    for i in range(n_cases):
        model.connect(f'weighted_raft_opt_{i}.weighted_multi_obj', f'rdo.obj_{i}')

    prob = om.Problem(model)

    if algorithm == 'Differential_GA':
        prob.driver = om.DifferentialEvolutionDriver()

    elif algorithm == 'COBYLA':
        prob.driver = om.ScipyOptimizeDriver()
        prob.driver.options['optimizer'] = 'COBYLA'
        prob.driver.options['tol'] = tolerance
        prob.driver.options['disp'] = True  

    elif algorithm == 'ALPSO':
        prob.driver = om.pyOptSparseDriver(optimizer='ALPSO')

    elif ((algorithm == 'SLSQP') or (algorithm == 'SLSQP_PYOPT')):        
        if (algorithm == 'SLSQP_PYOPT'):
            prob.driver = om.pyOptSparseDriver(optimizer='SLSQP')
        
        elif(algorithm == 'SLSQP'):
            prob.driver = om.ScipyOptimizeDriver()
            prob.driver.options['optimizer'] = 'SLSQP'
            prob.driver.options['tol'] = tolerance
            prob.driver.options['disp'] = True  

    if (user_input['platform']['optimize'] == True):
        x_platform = user_input['platform']['design_variables']
        x_bnd_platform = user_input['platform']['bounds_design_variables']

        for key, default_value in x_platform.items():    
            model.set_input_defaults(key, default_value)

        for key, bounds in x_bnd_platform.items():
            print(key)
            model.add_design_var(key, lower=bounds[0], upper=bounds[1])

##----------------------------------------TRADITIONAL----------------------------------------##
    try:
        x_platform_ineq_cons = user_input['platform']['inequality_constraints']
        for i in range(n_cases):
                
            for key, bnd in x_platform_ineq_cons.items():
                print(key)
                if (bnd[0] == 'None'):
                    prob.model.add_constraint(f'run_raft_opt_{i}.{key}', upper=bnd[1])
                
                elif (bnd[1] == 'None'):
                    prob.model.add_constraint(f'run_raft_opt_{i}.{key}', lower=bnd[0])
            
                else:
                    for i in range(n_cases):
                        prob.model.add_constraint(f'run_raft_opt_{i}.{key}', lower=bnd[0], upper=bnd[1])

    except:
        print('Platform inequality constraint not provided by the user')


    if (user_input['mooring']['optimize'] == True):
        x_mooring = user_input['mooring']['design_variables']
        x_bnd_mooring = user_input['mooring']['bounds_design_variables']
        
        for key, default_value in x_mooring.items():    
            print(key)
            prob.model.set_input_defaults(key, default_value)

        for key, bounds in x_bnd_mooring.items():  
            prob.model.add_design_var(key, lower=bounds[0], upper=bounds[1])

    try:
        x_mooring_ineq_cons = user_input['mooring']['inequality_constraints']
        
        
        for i in range(n_cases):
            for key, bnd in x_mooring_ineq_cons.items():
                print(key)
                if (bnd[0] == 'None'):
                    prob.model.add_constraint(f'run_raft_opt_{i}.{key}', upper=bnd[1])
                    
                
                elif (bnd[1] == 'None'):
                    prob.model.add_constraint(f'run_raft_opt_{i}.{key}', lower=bnd[0])
            
                else:
                    for i in range(n_cases):
                        prob.model.add_constraint(f'run_raft_opt_{i}.{key}', lower=bnd[0], upper=bnd[1])

    except:
        print('Mooring line inequality constraint not provided by the user')
        
    
    prob.model.add_objective('rdo.weighted_multi_obj')
    
    recorder = om.SqliteRecorder(user_input['driver_information']['recorder_file_name'])
    prob.driver.add_recorder(recorder)
    prob.driver.recording_options['includes'] = ['*']
    prob.driver.recording_options['record_objectives'] = True
    prob.driver.recording_options['record_constraints'] = True
    prob.driver.recording_options['record_inputs'] = True
    prob.driver.recording_options['record_outputs'] = True
    prob.driver.recording_options['record_residuals'] = True
    prob.setup()
    prob.run_driver()

    # rdo = prob.model.rdo
    # optimized_design, user_input = rdo.get_optimized_data()
    opt_design = deepcopy(design)
    x_platform_opt = None
    x_mooring_opt = None

    if (user_input['platform']['optimize'] == True):
        x_platform = user_input['platform']['design_variables']
        x_bnd_platform = user_input['platform']['bounds_design_variables']
        x_platform_opt = deepcopy(x_platform)

        for key, _ in x_platform.items():    
            x_platform_opt[key] = prob[key]
            print(f'{key} = {prob[key]}')

    if (user_input['mooring']['optimize'] == True):
        x_mooring = user_input['mooring']['design_variables']
        x_bnd_mooring = user_input['mooring']['bounds_design_variables']
        x_mooring_opt = deepcopy(x_mooring)

        for key, _ in x_mooring.items():    
            x_mooring_opt[key] = prob[key]
            print(f'{key} = {prob[key]}')

    # opt_design = calcuvate.calcuvate(opt_design, x_platform_opt, x_mooring_opt)

    return (opt_design, user_input)

def run_opt(design, user_input, calcuvate_path, output):
    current_directory = os.path.dirname(os.path.abspath(__file__))
    
    with open(output, "w") as output_file:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        sys.stdout = output_file
        sys.stderr = output_file

        try:
            optimized_design, user_input = raft_opt(design, user_input, calcuvate_path)
            # print(f"optimized_design = {optimized_design}")
            # print('\n')
            # print(f"user_input = {user_input}")
            return (optimized_design, user_input)
        
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

def raft_opt(design, user_input, calcuvate_path):
    """
    Core logic for setting up and running a standard (deterministic) optimization.

    Internal function called by `run_opt`.

    Args:
        design (dict): Design dictionary.
        user_input (dict): User input dictionary.
        calcuvate_path (str): Path to 'calcuvate.py'.

    Returns:
        tuple: A tuple containing:
            - dict: The final optimized design dictionary.
            - dict: The user_input dictionary with updated design variable values.
    """

    global calcuvate
    calcuvate = import_calcuvate('calcuvate', calcuvate_path)
    
    algorithm = user_input['driver_information']['algorithm']
    tolerance = user_input['driver_information']['tolerance']
    objective_function = user_input['objective_function']
    w_values = user_input['objective_weights']
    r_values = user_input['objective_reference']

    model = om.Group()
    model.add_subsystem('run_raft_opt', OWT(design=design, user_input=user_input), promotes=['*'])

    model.add_subsystem('weighted_raft_opt', WeightedObjectives(w_values=w_values, r_values=r_values))
    
    for i, obj in enumerate(objective_function):
        model.connect(f'{obj}', f'weighted_raft_opt.obj_{i}')
    
    model.add_objective('weighted_raft_opt.weighted_multi_obj')


    if (user_input['platform']['optimize'] == True):
        x_platform = user_input['platform']['design_variables']
        x_bnd_platform = user_input['platform']['bounds_design_variables']
        
        for key, default_value in x_platform.items():    
            model.set_input_defaults(key, default_value)

        for key, bounds in x_bnd_platform.items():
            print(key)
            model.add_design_var(key, lower=bounds[0], upper=bounds[1])

    try:
        x_platform_ineq_cons = user_input['platform']['inequality_constraints']
        for key, bnd in x_platform_ineq_cons.items():
            print(key)
            if (bnd[0] == 'None'):
                model.add_constraint(key, upper=bnd[1])
            
            elif (bnd[1] == 'None'):
                model.add_constraint(key, lower=bnd[0])
            
            else:
                model.add_constraint(key, lower=bnd[0], upper=bnd[1])

    except:
        print('Platform inequality constraint not provided by the user')


    if (user_input['mooring']['optimize'] == True):
        x_mooring = user_input['mooring']['design_variables']
        x_bnd_mooring = user_input['mooring']['bounds_design_variables']
        
        for key, default_value in x_mooring.items():    
            print(key)
            model.set_input_defaults(key, default_value)

        for key, bounds in x_bnd_mooring.items():  
            model.add_design_var(key, lower=bounds[0], upper=bounds[1])

    try:
        x_mooring_ineq_cons = user_input['mooring']['inequality_constraints']


        for key, bnd in x_mooring_ineq_cons.items():
            print(key)
            if (bnd[0] == 'None'):
                model.add_constraint(key, upper=bnd[1])
            
            elif (bnd[1] == 'None'):
                model.add_constraint(key, lower=bnd[0])
            
            else:
                model.add_constraint(key, lower=bnd[0], upper=bnd[1])

    except:
        print('Mooring line inequality constraint not provided by the user')
        
    prob = om.Problem(model)

    if algorithm == 'Differential_GA':
        prob.driver = om.DifferentialEvolutionDriver()

    elif algorithm == 'COBYLA':
        prob.driver = om.ScipyOptimizeDriver()
        prob.driver.options['optimizer'] = 'COBYLA'
        prob.driver.options['tol'] = tolerance
        prob.driver.options['disp'] = True  

    elif algorithm == 'ALPSO':
        prob.driver = om.pyOptSparseDriver(optimizer='ALPSO')

    elif ((algorithm == 'SLSQP') or (algorithm == 'SLSQP_PYOPT')):        
        if (algorithm == 'SLSQP_PYOPT'):
            prob.driver = om.pyOptSparseDriver(optimizer='SLSQP')
        
        elif(algorithm == 'SLSQP'):
            prob.driver = om.ScipyOptimizeDriver()
            prob.driver.options['optimizer'] = 'SLSQP'
            prob.driver.options['tol'] = tolerance
            prob.driver.options['disp'] = True  


    recorder = om.SqliteRecorder(user_input['driver_information']['recorder_file_name'])
    prob.driver.add_recorder(recorder)
    prob.driver.recording_options['includes'] = ['*']
    prob.driver.recording_options['record_objectives'] = True
    prob.driver.recording_options['record_constraints'] = True
    prob.driver.recording_options['record_inputs'] = True
    prob.driver.recording_options['record_outputs'] = True
    prob.driver.recording_options['record_residuals'] = True
    prob.setup()
    prob.run_driver()

    owt_instance = prob.model.run_raft_opt
    optimized_design, user_input = owt_instance.get_optimized_data()
    return (optimized_design, user_input)

def run_stability(design, user_input, calcuvate_path, output):
    """
    Runs only the stability adjustment step without full optimization.

    This function is intended to adjust secondary design variables (e.g., ballast)
    to meet stability requirements (e.g., zero pitch/roll offsets) for a
    *given* set of primary design variables. It calls the `raft_stability`
    function which performs this adjustment.

    Args:
        design (dict): Design dictionary with primary variables set.
        user_input (dict): User input dictionary specifying stability settings
                           (secondary variables, bounds, targets).
        calcuvate_path (str): Path to the 'calcuvate.py' file.
        output_log_file (str): Path to the file where stdout/stderr will be redirected.

    Returns:
        tuple: A tuple containing:
            - dict: The design dictionary updated by calcuvate using the
                    adjusted secondary variables.
            - dict: The user_input dictionary, potentially with updated
                    secondary variable values.
    """
    with open(output, "w") as output_file:
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        sys.stdout = output_file
        sys.stderr = output_file

        try:
            optimized_design, user_input = raft_stability(design, user_input, calcuvate_path)
            return (optimized_design, user_input)
        
        finally:
            sys.stdout = original_stdout
            sys.stderr = original_stderr

def raft_stability(design, user_input, calcuvate_path):
    """
    Core logic for performing stability adjustment.

    Reads primary and secondary design variables from input dictionaries.
    If `update_stability` is True in `user_input` for platform or mooring,
    it calls `adjustStability.main` (which runs a sub-optimization) to find
    the secondary variable values that minimize static offsets.
    Finally, it uses `calcuvate` to update the design dictionary with both
    primary and the (potentially adjusted) secondary variables.

    Args:
        design (dict): Input design dictionary.
        user_input (dict): User input dictionary.
        calcuvate_path (str): Path to 'calcuvate.py'.

    Returns:
        tuple: A tuple containing:
            - dict: The updated design dictionary.
            - dict: The user_input dictionary with potentially updated secondary variables.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-df', '--design', default = design, help='Name of the design yaml file to run RAFT', type = str)
    parser.add_argument('-ui', '--user_input', default = user_input, help='Name of the User Input yaml file to run RAFT', type = str)
    parser.add_argument('-calc', '--calcuvate-path', type = str, help ='Path to calcuvate.py')
    global args, calcuvate
    args = parser.parse_args()
    calcuvate = import_calcuvate('calcuvate', calcuvate_path)

    x_platform = {}
    x_primary_platform = {}
    x_secondary_platform = {}
    x_bnd_secondary_platform = {}
    platform_outputs = {}

    x_mooring = {}
    x_primary_mooring = {}
    x_secondary_mooring = {}
    mooring_outputs = {}
    x_bnd_secondary_mooring = {}

    try:
        x_primary_platform = user_input['platform']['design_variables']
        x_platform.update(x_primary_platform)

    except:
        print('Primary platform design variables not provided for the platform. User wants to proceed with the design in the desigl_file.yaml as the baseline design')
        
    try:
        x_secondary_platform = user_input['platform']['secondary_design_variables']
    except:
        print('Secondary platform design variables not provided for the platform. User wants to proceed with the design in the desigl_file.yaml as the baseline design')
    
    
    try:
        x_primary_mooring = user_input['mooring']['design_variables']
        x_mooring.update(x_primary_mooring)

    except:
        print('Primary mooring design variables not provided for the mooring lines. User wants to proceed with the design in the desigl_file.yaml as the baseline design')
        
    try:
        x_secondary_mooring = user_input['mooring']['secondary_design_variables']
        

    except:
        print('Secondary mooring design variables not provided for the mooring lines. User wants to proceed with the design in the desigl_file.yaml as the baseline design')
    
    try:
        platform_outputs = user_input['platform']['outputs']
    except:
        print('Platform outputs not given')


    if (user_input['platform']['update_stability'] == True):
        x_secondary_platform  = adjustStability.main(design, user_input, calcuvate)
        user_input['platform']['secondary_design_variables'] = x_secondary_platform
        x_platform.update(x_secondary_platform)

        for key in x_secondary_platform.keys():
            print(f'{key} = {x_secondary_platform[key]}')

    if (user_input['mooring']['update_stability'] == True):
        x_secondary_mooring = adjustStability.main(design, user_input, calcuvate)
        user_input['mooring']['secondary_design_variables'] = x_secondary_mooring
        x_mooring.update(x_secondary_mooring)

        for key in x_secondary_mooring.keys():
            print(f'{key} = {x_secondary_mooring[key]}')

    design = calcuvate.calcuvate(design, x_platform, x_mooring)

    print('x_mooring = ', x_mooring)
    print('x_platform = ', x_platform)

    return (design, user_input)