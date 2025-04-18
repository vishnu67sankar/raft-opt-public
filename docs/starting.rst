Getting Started
===============


Required Packages
----------------------

- Python 3
- NumPy
- Matplotlib
- SciPy
- YAML
- `MoorPy <https://github.com/NREL/MoorPy>`_
- `PyHAMS <https://github.com/WISDEM/pyHAMS>`_
- `CCBlade <https://github.com/WISDEM/WISDEM>`_ 
- `RAFT <https://github.com/WISDEM/RAFT>`_
- Streamlit 
- Altair 
- Plotly
- `PyOptSparse <https://github.com/mdolab/pyoptsparse>`_

The installation of `MoorPy`, `PyHAMS`, `CCBlade`, `RAFT` can be found in RAFT's documentation. Make sure you are using the `dev` branch or the `install_readme` branch of RAFT. 

To install ``streamlit`` run ``pip install streamlit`` in the terminal

To install ``altair`` run ``conda install -c conda-forge altair`` in the terminal

To install ``plotly`` run ``pip install plotly`` in the terminal

To install ``pyoptsparse`` run ``conda install -c conda-forge pyoptsparse`` in the terminal

Installation
------------
Once you have downloaded/cloned and installed the RAFT repository, 
you are all set to install RAFT-Opt. 

To install RAFT-Opt for development use:

run ```python setup.py develop``` or ```pip install -e .```
from the command line in the main RAFT-Opt directory.

To install RAFT-Opt for non-development use:

run ```python setup.py``` or ```pip install .``` from the 
command line in the main RAFT-Opt directory.