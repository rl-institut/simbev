SimBEV usage
=========================

This section gives a quick overview, what you can do with SimBEV and how to use it.

General Concept
---------------

SimBEV forecast charging demand for different e-cars for a pre-given time period. It does so by analysing the mobility in Germany
data. This data is split into different region types:

Rural regions:
    * Kleinstädtischer, dörflicher Raum - LR_Klein
    * Mittelstädte, städtischer Raum - LR_Mitte
    * Zentrale Stadt - LR_Zentr
Urban regions:
    * Kleinstädtischer, städtischer Raum - SR_Klein
    * Mittelstädte, städtischer Raum - SR_Mitte
    * Regiopolen, Großstädte - SR_Gross
    * Metropole - SR_Metro

The system is parameterized with the help of different input parameters such as battery capacity and charging power (slow and fast)
as well as the consumption of each car.

- It reads the data and creates SimBEV object(s) (depends on the specified iterations).

- Every SimBEV object gets setup.

- For every region a new process is created and it iterates through all vehicles and generate their events and outputs.

Example run
-----------

To determine the charging demand for a single defined region, you first need to collect the relevant data:

- Region type of the region
- Vehicle types and their amount for the relevant year
- Vehicle tech data (if unsure, use the default values)

For your first scenario, you can simply copy the directory "default" in the scenarios folder, rename the copy to your scenario name, and then change the relevant files (regions.csv, tech_data.csv). In this example, we will name it "test".

After you have collected the necessary data and input it into the scenario files, we can look at the config settings next. Open the "minimal.cfg" and set the start and end dates (ISO-format). If you have many vehicles in your region, you might also want to increase the scaling (section sim_params at the bottom of the config). If you have multiple regions set in your regions.csv (either due to different region types or to split your regions for multiprocessing), you can also adjust the parameter num_threads. Now you can run your simulation with the following command:

.. code-block:: shell

    python -m simbev scenarios/test/configs/minimal.cfg

You can check the simulation results in your scenario directory under "results".

For more in-depth settings, check out the section :doc:`simulation_settings` and the "default.cfg".

Usage overview
--------------------
With SimBEV, you can:

#. Create driving profiles for electric cars including:

    * times of driving, parking and charging
    * distance of driving
    * current location of the car
    * charging information - power, energy, time, type of charging station
    * battery state of the car for each timestep

#. Aggregated energy time series of charging events

#. Allocation of charging events and stations in combination with TracBEV

#. Application of different charging strategies with SpiceEV

Get the data
------------

If you want to run SimBEV in the mode using probabilities, a data set is available `here <https://zenodo.org/record/7609683>`_.

If you have access to the MiD 2017 data set and want to create your own driving profiles, you can use the script examples/driving_profiles_from_mid. At the bottom of the file you can set the number of driving profiles and the regions and car types.

Create a scenario
-----------------

- You can use a default scenario or define a custom one in the directory `scenarios`
- Run SimBEV with the desired scenario:

.. code:: bash

    python -m simbev path/to/config

defaults to:

.. code:: bash

    python -m simbev scenarios/default/configs/default.cfg

- Results are created in the subdirectory `results` in the scenario directory

Set parameters for your scenario
--------------------------------

Select regio-type for the mobility characteristics:

Rural regions:
    * Kleinstädtischer, dörflicher Raum - LR_Klein
    * Mittelstädte, städtischer Raum - LR_Mitte
    * Zentrale Stadt - LR_Zentr
Urban regions:
    * Kleinstädtischer, städtischer Raum - SR_Klein
    * Mittelstädte, städtischer Raum - SR_Mitte
    * Regiopolen, Großstädte - SR_Gross
    * Metropole - SR_Metro

Change vehicle configuration
 * battery capacity
 * charging power (slow and fast)
 * consumption

Decide how many vehicles should be simulated:

- note: more than 5000 vehicles of one type in one region is not necessary, if you want to analyze more, scale it accordingly

Iterations
----------

The default value of simulation iterations is 1.
By using the argument ``-r`` or ``--repeat`` a certain number of simulations can be specified:

.. code:: bash

    python -m simbev -r <number of iterations>

or

.. code:: bash

    python -m simbev --repeat <number of iterations>
