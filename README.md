# raft-opt-public-version
RAFT-OPT is a Python-based optimization framework for floating offshore wind turbines. It's an OpenMDAO wrapper for RAFT, which is a frequency-domain analysis solver of floating wind turbines. The source code was primarily developed by me, with invaluable guidance from research engineers at NREL. A special thanks to Stein Housner, who mentored me throughout the process and collaborated with me closely during a tidal turbine optimization project, and helped shape and validate RAFT-OPT.

Kindly install raft and its dependencies from https://github.com/WISDEM/RAFT before installing RAFT-OPT

[![image](https://img.shields.io/pypi/v/raft-opt.svg)](https://pypi.python.org/pypi/raft-opt)
[![image](https://img.shields.io/conda/vn/conda-forge/raft-opt.svg)](https://anaconda.org/conda-forge/raft-opt)



**Optimization wrapper for RAFT**
-   Free software: Apache Software License 2.0
-   Sphinx Documentation: Kindly clone this repo locally, and open ``docs\_build\html\index.html`` in your web browser for installation steps, and examples to get started. 

**Brief Overview of the RAFT-OPT's Features**
- Supports multi-point, multi-objective optimization using a weighted sum formulation
- Design variables typically include mooring line parameters and floating substructure geometry, while objectives are often total mass, tension, or a combination of both, constraints can include stability limits, structural loads
    - Or custom-defined objective functions and constraints are also supported by incorporating them within `calcuvate.py`
- Compatible with optimization algorithms such as SLSQP, ALPSO, Diff_GA, and COBYLA (via SciPy and pyOptSparse)
- Outputs a text log file recording all optimization progress and updates
- Live progress tracking is available by running `streamlit run visualizer.py` in a separate terminal which opens a web-browser

More details can be found in the Sphinx Documentation. It will be hosted online soon, meanwhile for now you can clone this repo locally, and open ``docs\_build\html\index.html`` in your web browser. 