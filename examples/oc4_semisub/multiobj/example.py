from raft_opt import raft_opt
import yaml
import os
import raft
import matplotlib.pyplot as plt
import time 

def single_point_opt():
    output = "single_sea_1_pt_2.txt"
    design_file = 'oc4_semisub.yaml'
    user_input_file = 'user_input.yaml'

    with open(design_file) as file:
        design = yaml.load(file, Loader=yaml.FullLoader)

    with open(user_input_file) as file:
        user_input = yaml.load(file, Loader=yaml.FullLoader)
    
    user_input['driver_information']['recorder_file_name'] = 'single_sea_1_pt_2.sql'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    calcuvate_path = os.path.join(current_dir, 'calcuvate.py')
    optimized_design, user_input = raft_opt.run_opt(design, user_input, calcuvate_path, output)
    # optimized_design, user_input = raft_opt_modular.run_stability(optimized_design, user_input, calcuvate_path, 'single_pt_0_stability.txt')
    # print(f"optimized_design = {optimized_design}")

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
    # optimized_design, user_input = raft_opt_modular.run_stability(optimized_design, user_input, calcuvate_path, 'output_stability.txt')

# if __name__ == "__main__":

#    with open('oc4_semisub.yaml') as file:
#         design = yaml.load(file, Loader=yaml.FullLoader)

#    model = raft.Model(design)
#    model.plot(hideGrid=False)
#    plt.show()
