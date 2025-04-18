from raft_opt import visualizer

if __name__ == "__main__":
    sql_file = 'output.sql'
    design_file = 'spar-buoy.yaml'
    visualizer.main(sql_file, design_file)