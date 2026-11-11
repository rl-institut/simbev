# Scenario: default_RS7

This scenario uses the same settings and input files as the default scenario,
but with realistic vehicle numbers for all seven RegioStaR7 regions.
Commercial vehicles are enabled, but their numbers are set to 0 in `regions.csv`.
To simulate commercial vehicles, set the columns `bev_commercial`, `phev_commercial`,
`bev_light_duty_vehicle` and `bev_heavy_duty_vehicle` to the desired numbers.
You may edit `default.cfg` and the CSV files to adjust parameters.

Start the simulation using

    python -m simbev scenarios/default_RS7/configs/default.cfg
