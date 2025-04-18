import openmdao.api as om
import matplotlib.pyplot as plt
import os
import time
import yaml
import streamlit as st
import pandas as pd
import altair as alt

def extract_data(driver, design_file):
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
        obj_plots.update({key: [obj[value][0]*objective_reference[0] for obj in objectives]})  # Replace 'objective_name' with your objective's name
        # obj_plots.update({key: [obj[key][0] for obj in objectives]})  # Replace 'objective_name' with your objective's name

    const_plots = {}
    for key in const_name.keys():
        const_plots.update({key: [con[key][0] for con in constraints]})  # Replace 'constraint_name' with your constraint's name

    dv_plots = {}
    for key in dv_name.keys():
        dv_plots.update({key: [dv[key][0] for dv in design_variables]})  # Replace 'design_var_name' with your design variable's name

    return iter, obj_plots, const_plots, dv_plots

def main(sql_file, design_file):
    plot_width = 250
    plot_height = 500
    last_size = -1

    st.title("Optimization Convergence History")

    while True:
        current_size = os.path.getsize(sql_file)

        if current_size != last_size:
            cr = om.CaseReader(sql_file)
            iterations, obj_values, con_values, dv_values = extract_data(cr, design_file)
            
            # Update Streamlit charts for objectives
            for obj_name, obj_value in obj_values.items():
                # if obj_name not in objective_charts:
                #     objective_charts[obj_name] = st.line_chart()
                
                data = pd.DataFrame({"Iteration": iterations, obj_name: obj_value})
                print(data)
                chart = alt.Chart(data).mark_line(point=True).encode(
                        x=alt.X("Iteration:Q", title="Iteration"),
                        y=alt.Y(f"{obj_name}:Q", title=obj_name, scale=alt.Scale(zero=False))  # zero=False avoids starting at 0
                    ).properties(title=f"Convergence of {obj_name}", width=plot_width, height=plot_height)
                if not data.empty:
                    st.altair_chart(chart, use_container_width=True)
            
            # Update Streamlit charts for constraints
            for con_name, con_value in con_values.items():
                # if con_name not in constraint_charts:
                #     constraint_charts[con_name] = st.line_chart()

                data = pd.DataFrame({"Iteration": iterations, con_name: con_value})
                chart = alt.Chart(data).mark_line(point=True).encode(
                    x=alt.X("Iteration:Q", title="Iteration"),
                    y=alt.Y(f"{con_name}:Q", title=con_name, scale=alt.Scale(zero=False))).properties(width=plot_width, height=plot_height)
                if not data.empty:
                    st.altair_chart(chart, use_container_width=True)

            
            # Update Streamlit charts for design variables
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
        
        time.sleep(5)  # Adjust the sleep time as needed

# if __name__ == "__main__":
#     main()