import openmdao.api as om
import streamlit as st
import pandas as pd
import os
import time
import plotly.express as px

def extract_data(cr):
    driver_cases = cr.get_cases('driver', recurse=False)
    iterations = []
    objectives = {}
    constraints = {}
    design_vars = {}

    for i, case in enumerate(driver_cases):
        iterations.append(i)
        for obj_name, obj_value in case.get_objectives().items():
            if obj_name not in objectives:
                objectives[obj_name] = []
            objectives[obj_name].append(obj_value[0])
        
        for con_name, con_value in case.get_constraints().items():
            if con_name not in constraints:
                constraints[con_name] = []
            constraints[con_name].append(con_value[0])
        
        for dv_name, dv_value in case.get_design_vars().items():
            if dv_name not in design_vars:
                design_vars[dv_name] = []
            design_vars[dv_name].append(dv_value[0])
    
    return iterations, objectives, constraints, design_vars

def create_plot(df, y_label):
    fig = px.line(df, x=df.index, y=df.columns[0], markers=True)
    fig.update_layout(
        xaxis_title="Iteration",
        yaxis_title=y_label
    )
    return fig

def main():
    sql_file = 'dummy.sql'
    last_size = -1

    st.title("Optimization Convergence History")
    objective_charts = {}
    constraint_charts = {}
    design_var_charts = {}

    while True:
        current_size = os.path.getsize(sql_file)

        if current_size != last_size:
            cr = om.CaseReader(sql_file)
            iterations, obj_values, con_values, dv_values = extract_data(cr)
            
            iterations = list(range(len(iterations)))
            
            for obj_name, obj_value in obj_values.items():
                df = pd.DataFrame({obj_name: obj_value}, index=iterations)
                df.index.name = "Iteration"
                if obj_name not in objective_charts:
                    st.subheader(f"Objective: {obj_name}")
                    objective_charts[obj_name] = st.plotly_chart(create_plot(df, obj_name))
                else:
                    objective_charts[obj_name].plotly_chart(create_plot(df, obj_name))
            
            for con_name, con_value in con_values.items():
                df = pd.DataFrame({con_name: con_value}, index=iterations)
                df.index.name = "Iteration"
                if con_name not in constraint_charts:
                    st.subheader(f"Constraint: {con_name}")
                    constraint_charts[con_name] = st.plotly_chart(create_plot(df, con_name))
                else:
                    constraint_charts[con_name].plotly_chart(create_plot(df, con_name))
            
            for dv_name, dv_value in dv_values.items():
                df = pd.DataFrame({dv_name: dv_value}, index=iterations)
                df.index.name = "Iteration"
                if dv_name not in design_var_charts:
                    st.subheader(f"Design Variable: {dv_name}")
                    design_var_charts[dv_name] = st.plotly_chart(create_plot(df, dv_name))
                else:
                    design_var_charts[dv_name].plotly_chart(create_plot(df, dv_name))

            last_size = current_size
        
        time.sleep(5)  # Adjust the sleep time as needed

if __name__ == "__main__":
    main()
