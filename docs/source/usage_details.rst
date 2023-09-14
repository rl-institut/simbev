SimBEV usage
=========================

This section gives a quick overview, what you can do with SimBEV and how to use it.

General Concept:

Simbev forecast charging demand for different e-cars for a pregiven time period. It does so by analysing the mobility in Germany
data. This data is split into different region types ( Ländliche Regionen LR_Klein - Kleinstädtischer, dörflicher Raum LR_Mitte
- Mittelstädte, städtischer Raum LR_Zentr - Zentrale Stadt Stadtregionen SR_Klein - Kleinstädtischer, dörflicher Raum SR_Mitte
- Mittelstädte, städtischer Raum SR_Gross - Regiopolen, Großstädte SR_Metro - Metropole).
The system is parameterized with the help of different input parameters such as battery capacity and charging power (slow and fast)
as well as the consumption of each car.


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

Set parameters for your scenario
--------------------------------

Select regio-type for the mobility characteristics:
- regiotypes:
Ländliche Regionen
LR_Klein - Kleinstädtischer, dörflicher Raum
LR_Mitte - Mittelstädte, städtischer Raum
LR_Zentr - Zentrale Stadt
Stadtregionen
SR_Klein - Kleinstädtischer, dörflicher Raum
SR_Mitte - Mittelstädte, städtischer Raum
SR_Gross - Regiopolen, Großstädte
SR_Metro - Metropole

Change vehicle configuration
- battery capacity
- charging power (slow and fast)
- consumption

Decide how many vehicles should be simulated
- note: more than 5000 vehicles of one type in one region is not necessary, if you want to analyze more, scale it accordingly
