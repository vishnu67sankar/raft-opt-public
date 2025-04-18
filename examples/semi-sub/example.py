from raft_opt import raft_opt
import yaml
import raft
import os

def raft_run(design):
    model = raft.Model(design)
    model.analyzeUnloaded()
    model.solveEigen()
    model.analyzeCases(display=1)
    print(1/model.results['eigen']['frequencies'])
    model.fowtList[0].ms.getTensions()
    model.fowtList[0].rotorList[0].aero_power

    print(f"Time priod of Heave = ",  round(1/model.results['eigen']['frequencies'][2], 2))
    print(f"Timperiod of Pitch = ",  round(1/model.results['eigen']['frequencies'][3], 2))

    print("tensions = ", max(model.fowtList[0].ms.getTensions()))
    print("rotor power", model.fowtList[0].rotorList[0].aero_power)
    print(model.fowtList[0].Xi0[0])

if __name__ == "__main__":
    output = "output.txt"
    design_file = 'semi-sub.yaml'
    user_input_file = 'user_input.yaml'

    with open(design_file) as file:
        design = yaml.load(file, Loader=yaml.FullLoader)

    with open(user_input_file) as file:
        user_input = yaml.load(file, Loader=yaml.FullLoader)

    raft_run(design)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    calcuvate_path = os.path.join(current_dir, 'calcuvate.py')
    optimized_design, user_input = raft_opt.run_opt(design, user_input, calcuvate_path, output)
    optimized_design, user_input = raft_opt.run_stability(optimized_design, user_input, calcuvate_path, 'output_stability.txt')

    raft_run(optimized_design)
    