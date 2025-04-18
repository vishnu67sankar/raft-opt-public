.. RAFT-OPT documentation master file, created by
   sphinx-quickstart on Mon Dec 16 14:51:20 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

RAFT-Opt Documentation
======================
RAFT-opt is an OpenMDAO wrapper for the RAFT tool (https://github.com/WISDEM/RAFT), specifically 
designed to facilitate the optimization of platform and mooring lines for Floating Offshore Wind 
Turbines (FOWT). The core focus of RAFT-opt is on leveraging gradient-based algorithms to ensure faster computation
times, making it an ideal solution for complex design optimization tasks. This optimization framework 
enables one to explore the feasible design space and perform Multidisciplinary Design Analysis and 
Optimization (MDAO) of both conventional and unconventional FOWT designs, hence delivering an optimal set of design choices.

RAFT-opt is agnostic to the type of system design, mirroring RAFT's design-agnostic approach to 
FOWT analysis. This flexibility allows RAFT-opt to optimize various FOWT designs, including:

- Spar-based platforms
- Semi-submersibles
- Tension Leg Platforms (TLP)
- Marine Hydrokinetic (MHK) Turbines

Key features of RAFT-opt include the ability to optimize subcomponents independently or 
optimize the entire system with all subcomponents together. This ensures a thorough exploration 
of design alternatives and the identification of the most efficient and effective configurations. 
RAFT-opt provides a robust and versatile optimization framework, empowering engineers to achieve 
optimal designs for a wide range of FOWT systems.


.. toctree::
   :maxdepth: 7
   :hidden:
   
   Home <self>
   starting
   tutorial
   example-1
   example-2
   example-3
   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`