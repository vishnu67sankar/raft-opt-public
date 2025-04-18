import raft
import openmdao.api as om
import numpy as np
import copy
# from calcuvate import calcuvate
import argparse
import yaml
import copy

class AdjustBallast(om.ExplicitComponent):

    def __init__(self, design, user_input, calcuvate):
        super().__init__()
        self.design = design
        self.user_input = user_input
        self.calcuvate = calcuvate

    def setup(self):
        self.heave = None
        self.pitch = None
        self.sway = None
        self.roll = None
        self.surge = None
        self.yaw = None

        design_variables = self.user_input['platform']['secondary_design_variables']


        if (self.user_input['platform']['update_stability'] == True):
            design_variables = self.user_input['platform']['secondary_design_variables']
            for key, value in design_variables.items():
                print(key)
                self.add_input(key, val=value)

        self.add_output("heave")
        self.add_output("pitch")
        self.add_output("surge")
        self.add_output("sway")
        self.add_output("roll")
        self.add_output("yaw")
        self.add_output("unloaded_stability")

    def setup_partials(self):
        self.declare_partials('*', '*', method='fd')
    
    def compute (self, inputs, outputs):
        x_primary_platform = {}
        try:
            x_primary_platform = self.user_input['platform']['design_variables']

        except:
            print('None given')

        x_secondary_platform = self.user_input['platform']['secondary_design_variables']

        for key in x_secondary_platform.keys(): ## platform DVs
            x_secondary_platform[key] = inputs[key][0]
            print(f'{key} = {x_secondary_platform[key]}')
        
        x_platform = {}
        x_platform.update(x_primary_platform)
        x_platform.update(x_secondary_platform)

        if (self.user_input['mooring']['optimize'] == True):
            x_mooring = self.user_input['mooring']['design_variables']
        
        else:
            x_mooring = {}

        self.design = self.calcuvate.calcuvate(self.design, x_platform, x_mooring)

        model = raft.Model(copy.deepcopy(self.design))

        try:
            model.analyzeUnloaded()
            self.surge = model.fowtList[0].Xi0[0] 
            self.sway = model.fowtList[0].Xi0[1] 
            self.heave = model.fowtList[0].Xi0[2]
            self.roll = model.fowtList[0].Xi0[3]
            self.pitch = model.fowtList[0].Xi0[4] 
            self.yaw = model.fowtList[0].Xi0[5]

        except:
            print ("Runtime error in RAFT Solver within test_adjustMooring")
            self.is_solver_divergence = True

        outputs['heave'] = (self.heave)
        outputs['pitch'] = (self.pitch)
        outputs['surge'] = (self.surge)
        outputs['sway'] = (self.sway)
        outputs['roll'] = (self.roll)
        outputs['yaw'] = (self.yaw)

        if ((self.heave != None) and ((self.pitch != None)) and (self.surge != None) and (self.sway != None) and (self.roll != None) and (self.yaw != None)):
            outputs['unloaded_stability'] = (self.heave/0.5)**2 + (self.pitch/0.01)**2 + (self.surge/0.5)**2 + (self.sway/0.5)**2 + (self.roll/0.5)**2 + (self.yaw/0.5)**2
        
        else:
            outputs['unloaded_stability'] = 10**20

def main_ballast(design, user_input, calcuvate, algorithm = 'SLSQP', tolerance = 10**-6):

    test_ballast = AdjustBallast(design, user_input, calcuvate)
    model = om.Group()
    model.add_subsystem('test_ballast', test_ballast, promotes=['*'])

    prob_adjust = om.Problem(model)

    if algorithm == 'Differential_GA':
        prob_adjust.driver = om.DifferentialEvolutionDriver()

    elif algorithm == 'COBYLA':
        prob_adjust.driver = om.ScipyOptimizeDriver()
        prob_adjust.driver.options['optimizer'] = 'COBYLA'
        prob_adjust.driver.options['tol'] = tolerance
        prob_adjust.driver.options['disp'] = True  

    elif algorithm == 'ALPSO':
        prob_adjust.driver = om.pyOptSparseDriver(optimizer='ALPSO')
        # prob_adjust.driver.options['tol'] = tolerance
        # prob_adjust.driver.options['disp'] = True  

    elif algorithm == 'SLSQP':
        # prob_adjust.driver = om.pyOptSparseDriver(optimizer='SLSQP')
        prob_adjust.driver = om.ScipyOptimizeDriver()
        prob_adjust.driver.options['optimizer'] = 'SLSQP'
        prob_adjust.driver.options['tol'] = tolerance
        prob_adjust.driver.options['disp'] = True  

    design_variables = user_input['platform']['secondary_design_variables']
    bounds_design_variables = user_input['platform']['bounds_secondary_design_variables']

    for key, value in design_variables.items():
        prob_adjust.model.set_input_defaults(key, value)

    for key, bounds in bounds_design_variables.items(): 
        prob_adjust.model.add_design_var(key, lower=bounds[0], upper=bounds[1])

    prob_adjust.model.add_objective("unloaded_stability")

    # recorder = om.SqliteRecorder('test_adjustBallast.sql')
    # prob_adjust.driver.add_recorder(recorder)
    # prob_adjust.driver.recording_options['includes'] = ['*']
    # prob_adjust.driver.recording_options['record_objectives'] = True
    # prob_adjust.driver.recording_options['record_constraints'] = True
    # prob_adjust.driver.recording_options['record_inputs'] = True
    # prob_adjust.driver.recording_options['record_outputs'] = True
    # prob_adjust.driver.recording_options['record_residuals'] = True
    prob_adjust.setup()
    prob_adjust.run_driver()
    
    for key in design_variables.keys():
        design_variables[key] = prob_adjust.get_val(key)[0]
        
    return (design_variables)

class AdjustMooring(om.ExplicitComponent):

    def __init__(self, design, user_input, calcuvate):
        super().__init__()
        self.design = design
        self.user_input = user_input
        self.calcuvate = calcuvate

    def setup(self):
        self.heave = None
        self.pitch = None
        self.sway = None
        self.roll = None
        self.surge = None
        self.yaw = None

        # Automate it with a for loop
        if (self.user_input['mooring']['update_stability'] == True):
            design_variables = self.user_input['mooring']['secondary_design_variables']
            for key, value in design_variables.items():
                self.add_input(key, val=value)

        try:
            secondary_inequality_constraints = self.user_input['mooring']['secondary_inequality_constraints']
            for key in secondary_inequality_constraints.keys():
                self.add_output(key)
        
        except:
            print("Secondary Inequality Constraint not provided")

        self.add_output("heave")
        self.add_output("pitch")
        self.add_output("surge")
        self.add_output("sway")
        self.add_output("roll")
        self.add_output("yaw")
        self.add_output("unloaded_stability")

    def setup_partials(self):
        self.declare_partials('*', '*', method='fd')
    
    def compute (self, inputs, outputs):
        x_primary_mooring = self.user_input['mooring']['design_variables']
        x_secondary_mooring = self.user_input['mooring']['secondary_design_variables']
        
        for key in x_secondary_mooring.keys(): ## Mooring DVs
            x_secondary_mooring[key] = inputs[key][0]
            print(f'{key} = {x_secondary_mooring[key]}')

        x_mooring = {}
        
        if (x_primary_mooring != 'None'):
            x_mooring.update(x_primary_mooring)

        x_mooring.update(x_secondary_mooring)
        x_platform = self.user_input['platform']['design_variables']

        self.design = self.calcuvate.calcuvate(self.design, x_platform, x_mooring)

        model = raft.Model(copy.deepcopy(self.design))

        try:
            model.analyzeUnloaded()
            self.surge = model.fowtList[0].Xi0[0] 
            self.sway = model.fowtList[0].Xi0[1] 
            self.heave = model.fowtList[0].Xi0[2]
            self.roll = model.fowtList[0].Xi0[3]
            self.pitch = model.fowtList[0].Xi0[4] 
            self.yaw = model.fowtList[0].Xi0[5]

        except:
            print ("Runtime error in RAFT Solver within test_adjustMooring")
            self.is_solver_divergence = True
            # raise om.AnalysisError("Runtime error in RAFT Solver within adjustStability")

        outputs['heave'] = (self.heave)
        outputs['pitch'] = (self.pitch)
        outputs['surge'] = (self.surge)
        outputs['sway'] = (self.sway)
        outputs['roll'] = (self.roll)
        outputs['yaw'] = (self.yaw)
        
        if ((self.heave != None) and ((self.pitch != None)) and (self.surge != None) and (self.sway != None) and (self.roll != None) and (self.yaw != None)):
            outputs['unloaded_stability'] = (self.heave/0.5)**2 + (self.pitch/0.01)**2 + (self.surge/0.5)**2 + (self.sway/0.5)**2 + (self.roll/0.5)**2 + (self.yaw/0.5)**2
        
        else:
            outputs['unloaded_stability'] = 10**20
            
        if (self.user_input['mooring']['secondary_outputs'] != 'None'):
            secondary_outputs = self.user_input['mooring']['secondary_outputs']
            for key, value in secondary_outputs.items():
                if (key == value[0]):
                    design = copy.deepcopy(self.design)
                    args = (design, model, x_platform, x_mooring)
                    outputs[key] = getattr(self.calcuvate, key)(*args)
                # print(f"{key} = {outputs[key]}")
                

def main_mooring(design, user_input, calcuvate, algorithm = 'SLSQP', tolerance = 10**-3):
    
    adjust_stability = AdjustMooring(design, user_input, calcuvate)
    model = om.Group()
    model.add_subsystem('adjust_stability', adjust_stability, promotes=['*'])

    prob_adjust = om.Problem(model)

    if algorithm == 'Differential_GA':
        prob_adjust.driver = om.DifferentialEvolutionDriver()

    elif algorithm == 'COBYLA':
        prob_adjust.driver = om.ScipyOptimizeDriver()
        prob_adjust.driver.options['optimizer'] = 'COBYLA'
        prob_adjust.driver.options['tol'] = tolerance
        prob_adjust.driver.options['disp'] = True  

    elif algorithm == 'ALPSO':
        prob_adjust.driver = om.pyOptSparseDriver(optimizer='ALPSO')

    elif algorithm == 'SLSQP':
        prob_adjust.driver = om.ScipyOptimizeDriver()
        prob_adjust.driver.options['optimizer'] = 'SLSQP'
        prob_adjust.driver.options['tol'] = tolerance
        prob_adjust.driver.options['disp'] = True  

    design_variables = user_input['mooring']['secondary_design_variables']
    bounds_design_variables = user_input['mooring']['bounds_secondary_design_variables']

    for key, value in design_variables.items():
        prob_adjust.model.set_input_defaults(key, value)

    for key, bounds in bounds_design_variables.items():   
        prob_adjust.model.add_design_var(key, lower=bounds[0], upper=bounds[1])

    try:
        x_mooring_ineq_cons = user_input['mooring']['secondary_inequality_constraints']

        for key, bnd in x_mooring_ineq_cons.items():
            print(key)
            if (bnd[0] == 'None'):
                prob_adjust.model.add_constraint(key, upper=bnd[1])
            
            elif (bnd[1] == 'None'):
                prob_adjust.model.add_constraint(key, lower=bnd[0])
            
            else:
                prob_adjust.model.add_constraint(key, lower=bnd[0], upper=bnd[1])

    except:
        print("Secondary Mooring line inequality constraint not provided by the user")

    prob_adjust.model.add_objective("unloaded_stability")

    
    # recorder = om.SqliteRecorder('test_adjustBallast.sql')
    # prob_adjust.driver.add_recorder(recorder)
    # prob_adjust.driver.recording_options['includes'] = ['*']
    # prob_adjust.driver.recording_options['record_objectives'] = True
    # prob_adjust.driver.recording_options['record_constraints'] = True
    # prob_adjust.driver.recording_options['record_inputs'] = True
    # prob_adjust.driver.recording_options['record_outputs'] = True
    # prob_adjust.driver.recording_options['record_residuals'] = True

    prob_adjust.setup()
    prob_adjust.run_driver()

    for key in design_variables.keys():
        design_variables[key] = prob_adjust.get_val(key)[0]

    return (design_variables)

def main(design, user_input, calcuvate, algorithm = 'SLSQP', tolerance = 10**-3):
    if (user_input['platform']['update_stability'] == True):
        design_variables = main_ballast(design, user_input, calcuvate)
        return (design_variables)

    if (user_input['mooring']['update_stability'] == True):
        design_variables = main_mooring(design, user_input, calcuvate)
        return (design_variables)