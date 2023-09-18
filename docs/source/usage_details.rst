SimBEV usage
=========================

This section gives a quick overview, what you can do with SimBEV and how to use it.

General Concept
---------------

Simbev forecast charging demand for different e-cars for a pregiven time period. It does so by analysing the mobility in Germany
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

- It reads the data and creates simBEV object(s) (depends on the specified iterations).

- Every simBEV object gets setup.

- For every region a new process is created and it iterates through all vehicles and generate their events and outputs.

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

Configuration possibilities
---------------------------
Each simulation must include the following parameters:

#. param1
#. param2



Get the data
------------

If you want to run SimBEV in the mode using probabilities, a data set is available `here <https://zenodo.org/record/7609683>`_.

Create a scenario
-----------------

- You can use a default scenario or define a custom one in the directory `scenarios`
- Run simbev with the desired scenario:

.. code:: bash

    python -m simbev path/to/config

defaults to:

.. code:: bash

    python -m simbev scenarios/default/configs/default.cfg

- Results are created in the subdirectory `results` in the scenario directory

Iterations
----------

The default value of simulation iterations is 1.
By using the argument ``-r`` or ``--repeat`` a certain number of simulations can be specified:

.. code:: bash

    python -m simbev -r <number of iterations>

or

.. code:: bash

    python -m simbev --repeat <number of iterations>

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
