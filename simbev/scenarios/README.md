# Scenarios

## Default scenarios

Available default scenarios:

- [default_single](./default_single/SCENARIO.md)
- [default_multi](./default_multi/SCENARIO.md)
- [default_RS7](./default_RS7/SCENARIO.md)

## Create new scenario

This is the scenario directory. You can create new scenarios in two different
ways:

### (I) Single region

Create a new scenario by adding a new directory `<SCENARIO_NAME>` with the
following files:
    
    charging_point_probability.csv
    fast_charging_probability.csv
    simbev_config.cfg (simbev config file with ramp up and tech data)
    SCENARIO.md (optional)

See example `default_single`.

### (II) Multiple regions

Create a new scenario by adding a new directory `<SCENARIO_NAME>` with the
following files:
    
    charging_point_probability.csv
    fast_charging_probability.csv
    regions.csv
    simbev_config.cfg (simbev config file)
    tech_data.csv
    SCENARIO.md (optional)

See example `default_multi`.
