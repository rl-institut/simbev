Simulation Settings
===================

The simulation settings are organized in a configuration file where different parameters are set and
the input data. In a directory scenarios/ there is following folder structure:

.. code-block::

    ├── scenarios
           └── default
                ├── configs
                │   ├──default.cfg
                │   └──minimal.cfg
                ├── results (outputs)
                ├── charging_curve.csv
                ├── charging_probability.csv
                ├── charging_probability_by_usecase.csv
                ├── energy_min.csv
                ├── fast_charging_probability.csv
                ├── home_work_private.csv
                ├── hpc_config.csv
                ├── regions.csv
                ├── tech_data.csv
                ├── tech_data_by_probability.csv
                └── user_groups.csv

The default scenario can be seen `here <https://github.com/rl-institut/simbev/tree/dev/scenarios/default>`_.

Required Parameters for a minimal simulation
--------------------------------------------

As an introductory example there is a minimal configuration that offers the least amount of parameter settings.

The configuration file consists of sections. Every section has parameters or keys that have a value.
Here for example the [basic] section has only two parameters: start_date and end_date.
Both have values with dates that have the format YYYY-MM-DD. In the [output] section we got only booleans that signal if
a certain output file should be generated.

.. csv-table:: [basic]
   :header: **Keyword**, **Example**, **Description**
   :widths: 33, 33, 33

   start_date, 2021-09-17, Starting date of the simulation
   end_date, 2021-09-30, Ending date of the simulation

.. csv-table:: [output]
   :header: **Keyword**, **Default**, **Description**
   :widths: 33, 33, 33

   vehicle_csv, true, Saves the vehicle events with socs and energy use as csv
   grid_time_series_csv, true, Saves energy use of the grid by time step as csv
   plot_grid_time_series_split, false, Saves grid plots for each region
   plot_grid_time_series_collective, false, Saves aggregated grid plot for the scenario
   analyze, false, Saves an additional analysis csv with multiple computed values

.. csv-table:: [rampup_ev]
   :header: **Keyword**, **Default**, **Description**
   :widths: 33, 33, 33

   rampup, regions.csv, Link to input file for region definitions and vehicle amounts

.. csv-table:: [tech_data]
   :header: **Keyword**, **Default**, **Description**
   :widths: 33, 33, 33

   tech_data, tech_data.csv, Link to input file for technical vehicle data (for example battery capacity)
   charging_curve, charging_curve.csv, Link to input file for charging curve definition
   hpc_data, hpc_config.csv, Link to input file for High Power Charging parameters

.. csv-table:: [user_data]
   :header: **Keyword**, **Default**, **Description**
   :widths: 33, 33, 33

   user_groups, user_groups.csv, Link to input file for user group definitions for different charging behaviour

.. csv-table:: [charging_probabilities]
   :header: **Keyword**, **Default**, **Description**
   :widths: 33, 33, 33

   slow, charging_probability.csv, Link to input file for charging probabilites outside of HPC charging
   fast, fast_charging_probability.csv, Link to input file for HPC charging
   home_work_private, home_work_private.csv, Link to input file for availability of private charging infrastructure
   energy_min, energy_min.csv, Link to input file for minimal charging requirements

.. csv-table:: [sim_params]
   :header: **Keyword**, **Default/Example**, **Description**
   :widths: 33, 33, 33

   scaling, 1, Simulation scaling. Example: With a scaling of 10 SimBEV would simulate only 1/10th of the given vehicles and extrapolate results
   num_threads, 4, Number of regions to be calculated at the same time (limited by processor cores)




All Settings
------------

.. csv-table:: [basic]
   :header: **Keyword**, **Default/Example**, **Description**
   :widths: 33, 33, 33

   start_date, 2021-09-17, Starting date of the simulation
   end_date, 2021-09-30, Ending date of the simulation
   input_type, probability, Choose what kind of input is used for driving profiles (Options: probability or profile)
   input_directory, data\probability, specify where the input data is located
   eta_cp, 1, Efficiency of charging points
   stepsize, 15, Step size of simulation (should stay at 15 min for best results)
   soc_min, 0.2, Minimum SoC left over at all times (not usable). Value can be between 0 and 1
   charging_threshold, 0.8, SoC threshold. Vehicles with higher SoC will not attempt to charge
   distance_threshold_extra_urban, 50, Determines if a trip is urban or extra urban by distance in kilometers
   consumption_factor_highway, 1.2, Extra consumption on highway trips
   dc_power_threshold, 50, Threshold power in kW. Anything higher is considered DC charging
   threshold_retail_limitation, 21, Time of day in hours until when retail charging is allowed
   threshold_street_night_limitation, 21, Time of day in hours where night charging methods are used (different allowed standing times)
   maximum_park_time_flag, false, Toggle a maximum standing time. Higher standing times will not be allowed to charge (have to park elsewhere)
   maximum_park_time, 10, Time in hours. Any parking events that are shorter than this are considered for charging
   street_night_charging_flag, true, Enables night charging option for street use case. This overrides the maximum park time for night events
   home_night_charging_flag, false, Enables night charging option for public home use case. This overrides the maximum park time for night events
   night_departure_standard_deviation, 1, Standard deviation for departure. Normal distribution
   night_departure_time, 9, Standard departure time after night charging event. Normal distribution


.. csv-table:: [output]
   :header: **Keyword**, **Default**, **Description**
   :widths: 33, 33, 33

   vehicle_csv, true, Saves the vehicle events with socs and energy use as csv
   grid_time_series_csv, true, Saves energy use of the grid by time step as csv
   plot_grid_time_series_split, false, Saves grid plots for each region
   plot_grid_time_series_collective, false, Saves aggregated grid plot for the scenario
   analyze, false, Saves an additional analysis csv with multiple computed values
   timing, false, Debug option to time simulation

.. csv-table:: [rampup_ev]
   :header: **Keyword**, **Default**, **Description**
   :widths: 33, 33, 33

   rampup, regions.csv, Number of every vehicle type per region

.. csv-table:: [tech_data]
   :header: **Keyword**, **Default**, **Description**
   :widths: 33, 33, 33

   tech_data, tech_data.csv, Link to input file for technical vehicle data (for example battery capacity)
   charging_curve, charging_curve.csv, Link to input file for charging curve definition
   hpc_data, hpc_config.csv, Link to input file for High Power Charging parameters

.. csv-table:: [user_data]
   :header: **Keyword**, **Default**, **Description**
   :widths: 33, 33, 33

   user_groups, user_groups.csv, Link to input file for user group definitions for different charging behaviour

.. csv-table:: [charging_probabilities]
   :header: **Keyword**, **Default**, **Description**
   :widths: 33, 33, 33

   slow, charging_probability.csv, Link to input file for charging probabilites outside of HPC charging
   fast, fast_charging_probability.csv, Link to input file for HPC charging
   home_work_private, home_work_private.csv, Link to input file for availability of private charging infrastructure
   energy_min, energy_min.csv, Link to input file for minimal charging requirements
   use_case, charging_probability_by_usecase.csv, Variant to determine charging probabilities

.. csv-table:: [sim_params]
   :header: **Keyword**, **Default**, **Description**
   :widths: 33, 33, 33

   scaling, 1, Simulation scaling. Example: With a scaling of 10 SimBEV would simulate only 1/10th of the given vehicles and extrapolate results
   num_threads, 4, Number of regions to be calculated at the same time (limited by processor cores)
   seed, 3, RNG seed. Same seed with same input data will produce the same results
   private_run_only, false, Attempts to charge all vehicles with private charging infrastructure if they have access

Input Files
-----------

charging_curve.csv
~~~~~~~~~~~~~~~~~~

The charging intensity is described from 0.1 to 0.9 in 0.2 steps over all vehicles.

**columns:** key, vehicle0, vehicle1, ...

**example:**

.. csv-table:: charging_curve.csv
   :header: key,bev_mini,bev_medium,bev_luxury,phev_mini,phev_medium,phev_luxury
   :widths: 10,10,10,10,10,10,10

   0.1,0.9,0.9,0.9,0.9,0.9,0.9
   0.3,0.915,0.915,0.915,0.915,0.915,0.915
   0.5,0.81,0.81,0.81,0.81,0.81,0.81
   0.7,0.64,0.64,0.64,0.64,0.64,0.64
   0.9,0.35,0.35,0.35,0.35,0.35,0.3

charging_probability.csv
~~~~~~~~~~~~~~~~~~~~~~~~

The probability of charging in the given destination by kW.

**columns:** destination,0,3.7,11.0,22.0,50.0

**example:**

.. csv-table:: charging_probability.csv
   :header: destination,0,3.7,11.0,22.0,50.0
   :widths: 10,10,10,10,10,10

   work,0.5887,0.0411,0.1645,0.1645,0.0411
   business,0.64,0.033,0.135,0.15,0.042
   school,0.5887,0.0411,0.1645,0.1645,0.0411
   shopping,0.5588,0.0059,0.0618,0.253,0.1206
   private/ridesharing,0.655,0.0155,0.081,0.176,0.0725
   leisure,0.6538,0.0154,0.0808,0.177,0.0731
   home,0.4894,0.0911,0.3402,0.0715,0.0079

charging_probability_by_usecase.csv
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The probability of charging by usecase in the given destination.

**columns:** destination,22.0,50.0,150.0,250.0,350.0

**example:**

.. csv-table:: charging_probability_by_usecase.csv
   :header: destination,22.0,50.0,150.0,250.0,350.0
   :widths: 10,10,10,10,10,10

   home,1,0,0,0,0
   work,1,0,0,0,0
   retail,0.75,0.15,0.1,0,0
   street,0.9,0.075,0.025,0,0
   urban_fast,0,0.05,0.45,0.45,0.05
   highway_fast,0,0,0.2,0.7

energy_min.csv
~~~~~~~~~~~~~~

The minimum charged energy by vehicle type.

**columns:** uc,bev,phev

**example:**

.. csv-table:: energy_min.csv
   :header: uc,bev,phev
   :widths: 10,10,10

   home,4,3
   work,4,3
   public,7,5
   hpc,20,10

fast_charging_probability.csv
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The fast charging probability for urban or ex-urban destinations.

**columns:** destination,150.0,350.0

**example:**

.. csv-table:: fast_charging_probability.csv
   :header: destination,150.0,350.0
   :widths: 10,10,10

   urban,0.8,0.2
   ex-urban,0.2,0.8

home_work_private.csv
~~~~~~~~~~~~~~~~~~~~~

Different values for home and work.

**columns:** region,LR_Klein,LR_Mitte,LR_Zentr,SR_Klein,SR_Mitte,SR_Gross,SR_Metro

**example:**

.. csv-table:: home_work_private.csv
   :header: region,LR_Klein,LR_Mitte,LR_Zentr,SR_Klein,SR_Mitte,SR_Gross,SR_Metro
   :widths: 10,10,10,10,10,10,10,10

   home, 0.9,0.85,0.7,0.85,0.8,0.6,0.4
   work,0.7,0.7,0.7,0.7,0.7,0.7,0.7
   probability_detached_home,0.9,0.8,0.7,0.6,0.5,0.4,0.3

hpc_config.csv
~~~~~~~~~~~~~~

Configuration for high power charging.

**columns:** key,values

**example:**

.. csv-table:: hpc_config.csv
   :header: key,values
   :widths: 10,10

   soc_end_min,0.8
   soc_end_max,0.95
   soc_start_threshold,0.6
   park_time_max,90
   distance_min,0.6
   distance_max,1

regions.csv
~~~~~~~~~~~

Amount of vehicles per region and vehicle type.

**columns:** region_id,RegioStaR7,bev_mini,bev_medium,bev_luxury,phev_mini,phev_medium,phev_luxury

**example:**

.. csv-table:: regions.csv
   :header: region_id,RegioStaR7,bev_mini,bev_medium,bev_luxury,phev_mini,phev_medium,phev_luxury
   :widths: 10,10,10,10,10,10,10,10

   LR_Klein,LR_Klein,10,5,5,5,10,1
   LR_Mitte,LR_Mitte,20,30,10,2,20,10
   LR_Zentr,LR_Zentr,5,5,5,5,5,5
   SR_Gross,SR_Gross,5,5,5,10,5,2
   SR_Klein,SR_Klein,1,1,5,10,0,10
   SR_Metro,SR_Metro,10,30,20,30,20,20
   SR_Mitte,SR_Mitte,20,5,30,10,20,15

tech_data.csv
~~~~~~~~~~~~~

Technical data for every vehicle type in terms charging, capacity and consumption.

**columns:** type,max_charging_capacity_slow,max_charging_capacity_fast,battery_capacity,energy_consumption

**example:**

.. csv-table:: tech_data.csv
   :header: type,max_charging_capacity_slow,max_charging_capacity_fast,battery_capacity,energy_consumption
   :widths: 10,10,10,10,10

   bev_mini,11,50,60,0.1397
   bev_medium,22,50,90,0.1746
   bev_luxury,50,150,110,0.2096
   phev_mini,3.7,0,14,0.1425
   phev_medium,11,0,20,0.1782
   phev_luxury,11,0,30,0.2138

tech_data_by_probability.csv
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Technical probability data for every vehicle type in terms charging, capacity and consumption.

**columns:** type,slow_3.7,slow_11,slow_22,fast_50,fast_150,fast_350,battery_capacity,energy_consumption

**example:**

.. csv-table:: tech_data_by_probability.csv
   :header: type,slow_3.7,slow_11,slow_22,fast_50,fast_150,fast_350,battery_capacity,energy_consumption
   :widths: 10,10,10,10,10,10,10,10,10

   bev_mini,0.05,0.80,0.15,0.30,0.65,0.05,60,0.1397
   bev_medium,0,0.7,0.3,0.3,0.6,0.1,90,0.1746
   bev_luxury,0,0.8,0.2,0,0.85,0.15,110,0.2096
   phev_mini,0.9,0.1,0,1,0,0,14,0.1425
   phev_medium,0.5,0.2,0.3,1,0,0,20,0.1782
   phev_luxury,0.75,0.25,0,1,0,0,30,0.2138


user_groups.csv
~~~~~~~~~~~~~~~

Data on user groups in different areas.

**columns:** user_group,home_detached,home_apartment,work,urban_fast,highway_fast,retail,street

**example:**

.. csv-table:: user_groups.csv
   :header: user_group,home_detached,home_apartment,work,urban_fast,highway_fast,retail,street
   :widths: 10,10,10,10,10,10,10,10

   0,0.85,0.85,0.6,0.2,0.25,0.2,0.1
   1,0.95,0.95,0,0.2,0.3,0.2,0.1
   2,0,0,0.95,0.3,0.55,0.4,0.4
   3,0,0,0,0.4,0.6,0.55,0.7
