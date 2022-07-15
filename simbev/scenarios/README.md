# Scenarios

## Default scenarios

Available default scenarios:

* [default](default/SCENARIO.md), a small scenario for testing purposes
* [default_RS7](default_RS7/SCENARIO.md), scenario with realistic example numbers per region type

## Create new scenario

This is the scenario directory. You can create new scenarios here:

Create a new scenario by adding a new directory `<SCENARIO_NAME>` with the
following files:
    
    charging_point_probability.csv
    fast_charging_probability.csv
    regions.csv
    simbev_config.cfg (simbev config file)
    tech_data.csv
    SCENARIO.md (optional)

See example `default`.
