~~~~~~~~~~~~~~~
Getting started
~~~~~~~~~~~~~~~

Simbev stands for "". Simbev take the mobility in Germany data and uses it to forecast e-car drivers
daily routes and for that is able to forecast charging demand. The key features
of Simbev are:

* Reduce the mobility in Germany data to just probabilities
* Detailed modelling of
* Stepwise simulation without using perfect foresight
* Parameter optimization possible in combination with a genetic algorithm


.. contents::
    :depth: 1
    :local:
    :backlinks: top


Documentation
=============

Full documentation can be found `here <https://smooth.readthedocs.io/en/latest/>`_

Installing simbev
=================

In order to use Simbev, the simbev package and its requirements need to be installed. There
is the option to clone the current repository of SMOOTH to your local machine using:

.. code:: bash

	git clone https://github.com/rl-institut/smooth

The necessary requirements (found in requirements.txt in repository) are installed into a
working Python3 environment by:

.. code:: bash

    pip install -r requirements.txt

Simbev is then installed by:

.. code:: bash

    python setup.py install


You also need to install the solver for oemof. This can be done according to
`this <https://oemof-solph.readthedocs.io/en/latest/readme.html#installing-a-solver>`_
documentation page.

General concept
===============
Simbev forecast charging demand for different e-cars for a pregiven time period. It does so by analysing the mobility in Germany
data. This data is splitted into different regiontypes ( Ländliche Regionen LR_Klein - Kleinstädtischer, dörflicher Raum LR_Mitte
- Mittelstädte, städtischer Raum LR_Zentr - Zentrale Stadt Stadtregionen SR_Klein - Kleinstädtischer, dörflicher Raum SR_Mitte
- Mittelstädte, städtischer Raum SR_Gross - Regiopolen, Großstädte SR_Metro - Metropole).
The system is parameterized with the help of different input parameters such as battery capacity and charging power (slow and fast)
as well as the consumption of each car. While the components and the algorithm executing the simulation are part of
SMOOTH, each component creates a valid oemof model for each time step and the system is solved using
`oemof-solph <https://oemof.readthedocs.io/en/release-v0.1/oemof_solph.html>`_. The financial costs/revenues and emissions, where
the costs are divided into variable costs, CAPEX and OPEX, are tracked for each component individually. After the simulation, all
costs/revenues and emissions are transferred to annuities (kg/a and EUR/a, respectively) based on the component lifetimes, and the
total system financial and emissions annuities are recorded. The notable states of the components and the energy and mass flows of
the system are also recorded and all results can be saved for later use.

An additional functionality of SMOOTH is the optimization (MOEA) which optimizes the topology and operational management of an
energy system with regards to ecological and economic target criteria. Key parameters of components are chosen, such as the
maximum power output or capacity, and varied in numerous versions of the energy system until the optimal solution/s is/are
reached. The specification of the final system/s is/are finally returned as SMOOTH results.

Structure of the Simbev module
==============================



Functions
==========

 run_simbev(region_ctr, region_id, region_data, cfg_dict, charge_prob,regions, tech_data, main_path)

    :

        components (object) – List containing each component object
        index (int, optional) – Index of the foreign state (should be None if there is only one foreign state) [-]

    Returns:

    Foreign state value

availability(cardata,probdata,stepsize,batcap,con,chargepower_slow,chargepower_fast,soc_start,car_type,charge_prob_slow,charge_prob_fast,idx_home,idx_work,home_charging_capacity,work_charging_capacity,last_charging_capacity,rng,eta,soc_min,tseries_purpose,carstatus)

   The function avaiability is used to get the dataframes for each car showing the movements. It also calculates the consumption, batterie status, charging demand and
    :

        components (object) – List containing each component object
        index (int, optional) – Index of the foreign state (should be None if there is only one foreign state) [-]

    Returns:

    Foreign state value

Examples
========
In order to get a better, applied understanding of how to define a model, and either run a simulation
or an optimization, see the `examples directory <https://github.com/rl-institut/smooth/tree/dev/smooth/examples>`_
for examples, and the :doc:`smooth.examples` for corresponding explanations.

Framework
=========
The :doc:`smooth.framework` consists of the main function that runs the SMOOTH simulation
framework (the :func:`run_smooth` function) as well as other functions that are necessary for
updating and evaluating the simulation results (in the :doc:`smooth.framework.functions`).
An outline and brief description of the available functions in the framework is presented below:

* :func:`~smooth.framework.run_smooth`: the main function which enables the simulation in SMOOTH,
  and must be called by the user.
* :func:`~smooth.framework.functions.calculate_external_costs`: calculates costs for components
  in the system which are not part of the optimization but their costs should be taken into
  consideration. This function can be called in the same file as the run_smooth function.
* :func:`~smooth.framework.functions.debug`: generates debugging information from
  the results, and prints, plots and saves them. It is called in the run_smooth function if the
  user sets the *show_debug_flag* parameter as True in the simulation parameters.
* :func:`~smooth.framework.functions.load_results`: loads the saved results of either a
  simulation or optimization. Can be called by the user in a file where the results are
  evaluated.
* :func:`~smooth.framework.functions.plot_results`: plots results of a SMOOTH run, which can
  be called after the simulation/optimization results are obtained.
* :func:`~smooth.framework.functions.print_results`: prints the financial results of a
  SMOOTH run, which can be called after the simulation/optimization results are obtained.
* :func:`~smooth.framework.functions.save_results`: saves the results of either a SMOOTH
  run or an optimization, which can be called after the results are obtained.
* :func:`~smooth.framework.functions.update_annuities`: calculates and updates the financial
  and emission annuities for the components used in the system. It is called in the
  generic Component class, which is used to define each component.
* :func:`~smooth.framework.functions.update_fitted_costs`: calculates the fixed costs and fixed emissions of a component. The user can define the dependencies on certain values using a set of specific fitting methods. This function is also called in the generic Component class, which is used to define each component.

Optimization
============
The genetic algorithm used for the optimization in SMOOTH is defined in the
:doc:`smooth.optimization`, along with instructions on how to use it.

Got further questions on using SMOOTH?
======================================

Contact ...


License
=======

SMOOTH is licensed under the Apache License, Version 2.0 or the MIT license, at your option.
See the `COPYRIGHT file <https://github.com/rl-institut/smooth/blob/dev/COPYRIGHT>`_ for details.

