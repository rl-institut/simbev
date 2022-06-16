## Output metadata

### Vehicle outputs
| Column                    | Unit       | Description                                                                 |
|---------------------------|------------|-----------------------------------------------------------------------------|
| timestamp                 | ISO date   | start of event                                                              |
| event_start               | time steps | start of event                                                              |
| event_time                | time steps | duration of event                                                           |
| location                  | -          | event location                                                              |
| use_case                  | -          | Use Case used to determine charging types                                   |
| soc_start                 | -, 0 to 1  | share of total SoC that's available at event start                          |
| soc_end                   | -, 0 to 1  | share of total SoC that's available at event end                            |
| energy                    | kWh        | energy change in the battery. positive is charging, negative is consumption |
| station_charging_capacity | kW         | nominal charging capacity of the charging point                             |
| average_charging_power    | kW         | average charging power being used during the event                          |

### Grid time series
| Column                    | Unit      | Description                                                                 |
|---------------------------|-----------|-----------------------------------------------------------------------------|
| timestamp                 | ISO date  | timestamp of step                                                           |
| total_power               | kW        | sum of charging power in the region                                         |
| (use_case)_total_power    | kW        | sum of charging power in (use_case)                                         |
| cars_(use_case)_(power)   | -         | number of cars using a station with (power) in (use_case)                   |