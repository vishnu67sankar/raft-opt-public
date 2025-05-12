import openmdao.api as om
import matplotlib.pyplot as plt
import os
import time
import yaml
import streamlit as st
import pandas as pd
import altair as alt

def extract_data(driver, design_file):
    """
    Extracts optimization data from an OpenMDAO CaseReader.

    Parses driver cases to retrieve iteration history for objectives,
    constraints, and design variables. It also reads the design and
    user input YAML files to get the names and references for these
    quantities.

    Args:
        driver (om.CaseReader): An OpenMDAO CaseReader object initialized
                                with the optimization recording (e.g., .sql file).
        design_file (str): Path to the design YAML file. This is used
                           to understand the structure if needed, though
                           currently user_input.yaml is more heavily used
                           for naming.

    Returns:
        tuple: A tuple containing:
            - list: Iteration numbers.
            - dict: A dictionary where keys are objective names (aliases)
                    and values are lists of their values at each iteration.
                    Objective values are scaled by their reference values.
            - dict: A dictionary where keys are constraint names and values
                    are lists of their values at each iteration.
            - dict: A dictionary where keys are design variable names and
                    values are lists of their values at each iteration.
    """

    driver_cases = driver.get_cases('driver', recurse=False)
    iter = []
    objectives = []
    constraints = []
    design_variables = []

    with open(design_file) as file:
        design = yaml.load(file, Loader=yaml.FullLoader)

    with open("user_input.yaml") as file:
        user_input = yaml.load(file, Loader=yaml.FullLoader)

    for i, case in enumerate(driver_cases):
        iter.append(i)
        objectives.append(case.get_objectives())
        constraints.append(case.get_constraints())
        design_variables.append(case.get_design_vars())

    

    obj_name = user_input['objective_function_alias']
    objective_reference = user_input['objective_reference']
    const_name = {}
    dv_name = {}
    if (user_input['platform']['inequality_constraints'] != 'None'):
        const_name.update(user_input['platform']['inequality_constraints'])

    if (user_input['mooring']['inequality_constraints'] != 'None'):
        const_name.update(user_input['mooring']['inequality_constraints'])

    if (user_input['platform']['optimize'] == True):
        dv_name.update(user_input['platform']['design_variables'])

    if (user_input['mooring']['optimize'] == True):
        dv_name.update(user_input['mooring']['design_variables'])

    print("objectives = ", objectives)
    
    obj_plots = {}
    for key, value in obj_name.items():
        obj_plots.update({key: [obj[value][0]*objective_reference[0] for obj in objectives]})  
        

    const_plots = {}
    for key in const_name.keys():
        const_plots.update({key: [con[key][0] for con in constraints]}) 

    dv_plots = {}
    for key in dv_name.keys():
        dv_plots.update({key: [dv[key][0] for dv in design_variables]})  

    return iter, obj_plots, const_plots, dv_plots

def main(sql_file, design_file):
    """
    Runs a Streamlit application to visualize optimization convergence.

    Continuously monitors an OpenMDAO SQL recording file for updates and
    plots the history of objectives, constraints, and design variables
    using Altair charts in a Streamlit web interface.

    The application assumes "user_input.yaml" is present in the current
    working directory to fetch names and references for plotting.

    Args:
        sql_file (str): Path to the OpenMDAO SQL recorder file (e.g., "cases.sql").
        design_file (str): Path to the design YAML file, passed to `extract_data`.

    Note:
        This function runs an infinite loop to periodically check the SQL file
        for updates. It's designed to be run as a Streamlit app.
        To stop the app, you typically interrupt the Streamlit process (e.g., Ctrl+C).
    """
    
    plot_width = 250
    plot_height = 500
    last_size = -1

    st.title("Optimization Convergence History")

    while True:
        current_size = os.path.getsize(sql_file)

        if current_size != last_size:
            cr = om.CaseReader(sql_file)
            iterations, obj_values, con_values, dv_values = extract_data(cr, design_file)
            
          
            for obj_name, obj_value in obj_values.items():
                # if obj_name not in objective_charts:
                #     objective_charts[obj_name] = st.line_chart()
                
                data = pd.DataFrame({"Iteration": iterations, obj_name: obj_value})
                print(data)
                chart = alt.Chart(data).mark_line(point=True).encode(
                        x=alt.X("Iteration:Q", title="Iteration"),
                        y=alt.Y(f"{obj_name}:Q", title=obj_name, scale=alt.Scale(zero=False)) 
                    ).properties(title=f"Convergence of {obj_name}", width=plot_width, height=plot_height)
                if not data.empty:
                    st.altair_chart(chart, use_container_width=True)
           
            for con_name, con_value in con_values.items():
                # if con_name not in constraint_charts:
                #     constraint_charts[con_name] = st.line_chart()

                data = pd.DataFrame({"Iteration": iterations, con_name: con_value})
                chart = alt.Chart(data).mark_line(point=True).encode(
                    x=alt.X("Iteration:Q", title="Iteration"),
                    y=alt.Y(f"{con_name}:Q", title=con_name, scale=alt.Scale(zero=False))).properties(width=plot_width, height=plot_height)
                if not data.empty:
                    st.altair_chart(chart, use_container_width=True)

            for dv_name, dv_value in dv_values.items():
                # if dv_name not in design_var_charts:
                #     design_var_charts[dv_name] = st.line_chart()

                data = pd.DataFrame({"Iteration": iterations, dv_name: dv_value})
                chart = alt.Chart(data).mark_line(point=True).encode(
                    x=alt.X("Iteration:Q", title="Iteration"),
                    y=alt.Y(f"{dv_name}:Q", title=dv_name, scale=alt.Scale(zero=False))).properties(width=plot_width, height=plot_height)
                if not data.empty:
                    st.altair_chart(chart, use_container_width=True)

            last_size = current_size
        
        time.sleep(5)  

# if __name__ == "__main__":
#     main()