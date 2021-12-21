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

Full documentation can be found `here <https://simbev.readthedocs.io/en/latest/>`_

Installing simBEV
=================

Install using pip
-----------------

First, clone via SSH using

.. code:: bash

    git clone git@github.com:rl-institut/simbev.git /local/path/to/simbev/

Make sure you have Python >= 3.8 installed, let's create a virtual env:

.. code:: bash

    virtualenv --python=python3.8 simbev
    source simbev/bin/activate

Install package with

.. code:: bash

    pip install -e /local/path/to/simbev/

Install using conda
-------------------

Make sure you have conda installed, e.g. miniconda. Then create the env:

    conda create -n simbev /local/path/to/simbev/environment.yml
    conda activate simbev

General concept
===============

Simbev forecast charging demand for different e-cars for a pregiven time period. It does so by analysing the mobility in Germany
data. This data is splitted into different regiontypes ( Ländliche Regionen LR_Klein - Kleinstädtischer, dörflicher Raum LR_Mitte
- Mittelstädte, städtischer Raum LR_Zentr - Zentrale Stadt Stadtregionen SR_Klein - Kleinstädtischer, dörflicher Raum SR_Mitte
- Mittelstädte, städtischer Raum SR_Gross - Regiopolen, Großstädte SR_Metro - Metropole).
The system is parameterized with the help of different input parameters such as battery capacity and charging power (slow and fast)
as well as the consumption of each car.

Structure of the Simbev module
==============================

TODO

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

TODO

Scenarios
=========

See directory `scenarios`.

License
=======

GNU Affero General Public License v3.0

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
