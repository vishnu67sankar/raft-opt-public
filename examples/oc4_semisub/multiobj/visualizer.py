from raft_opt import visualizer

if __name__ == "__main__":
    sql_file = 'multi_pt_final_1.sql'
    design_file = 'oc4_semisub.yaml'
    visualizer.main(sql_file, design_file)