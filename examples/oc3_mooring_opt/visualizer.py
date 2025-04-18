from raft_opt import visualizer

if __name__ == "__main__":
    sql_file = 's0.sql'
    design_file = 'oc3_design.yaml'
    visualizer.main(sql_file, design_file)