from raft_opt import raft_opt
import yaml
import raft
import os
import time 
import numpy as np


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

if __name__ == "__main__":
    output = "output.txt"
    design_file = 'spar-buoy.yaml'
    user_input_file = 'user_input.yaml'

    with open(design_file) as file:
        design = yaml.load(file, Loader=yaml.FullLoader)

    with open(user_input_file) as file:
        user_input = yaml.load(file, Loader=yaml.FullLoader)

    user_input['driver_information']['recorder_file_name'] = 'output.sql'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    calcuvate_path = os.path.join(current_dir, 'calcuvate.py')
    start_t = time.time()
    optimized_design, user_input = raft_opt.run_opt(design, user_input, calcuvate_path, output)
    optimized_design, user_input = raft_opt.run_stability(optimized_design, user_input, calcuvate_path, 'output_stability.txt')

    end_t = time.time()
    print(f'Time taken for the simulation = {end_t-start_t}')

    optimized_design = clean_numpy(optimized_design)

    with open('optimized_design.yaml', 'w') as file:
        yaml.dump(optimized_design, file, default_flow_style=False)

