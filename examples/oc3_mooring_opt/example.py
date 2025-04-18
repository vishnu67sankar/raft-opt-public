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

def multi_point_opt():
    output = "output_multi.txt"
    
    with open(design_file) as file:
        design = yaml.load(file, Loader=yaml.FullLoader)

    with open(user_input_file) as file:
        user_input = yaml.load(file, Loader=yaml.FullLoader)
    
    user_input['driver_information']['recorder_file_name'] = 'output_multi.sql'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    calcuvate_path = os.path.join(current_dir, 'calcuvate.py')

    p_values = user_input['p_values']
    cases = user_input['cases']
    optimized_design, user_input = raft_opt.run_weighted_opt(design, user_input, cases, p_values, calcuvate_path, output)
    optimized_design, user_input = raft_opt.run_stability(optimized_design, user_input, calcuvate_path, 'output_multi.txt')

    return optimized_design, user_input

if __name__ == "__main__":
    start = time.time()
    optimized_design, _ = single_point_opt()
    # optimized_design, _ = multi_point_opt()
    print (f'{time.time() - start} seconds elapsed')