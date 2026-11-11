# Changelog
All notable changes to this project will be documented in this file.

The format is inspired from [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and the versioning aim to respect [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
-
### Changed
-
### Removed
-

## [2.1.0] - 2026-11-xx

### Added

- optional simulation of commercial vehicle groups (commercial cars, light and heavy duty vehicles) based on KiD2010
via a new `vehicle_group` column in tech_data.csv and a `[commercial_vehicles]` config section, disabled if not set #148
- new charging use case depot (private charging at a commercial vehicle's company depot),
with availability drawn the same way as home/work private charging #148
- new MCS methodology for en-route charging of heavy duty vehicles #148
- new consumption model based on season and speed of a vehicle #147
- driving_profile_seed parameter in the config file to set the seed for the driving profile generation step #139
- battery energy output in driving profiles
- new input data set on Zenodo (MiD 2023 for private cars, KiD 2010 for commercial vehicles): https://doi.org/10.5281/zenodo.24108280

### Changed

- moved optional config parameters from [basic] to the new section [extended settings], configs with these parameters in [basic] still work #147
- hpc parameters moved from hpc_config.csv to the config section [hpc] #148
- trip purposes of commercial vehicles renamed to English, German names in older probability data are translated automatically #148
- updated tech data of the default scenario: higher fast charging capacities of private BEVs (150/250/350 kW) and realistic values for commercial vehicles, heavy duty vehicles use MCS (1000 kW) #148
- scenario default_RS7 uses the same settings and input files as the default scenario, including all commercial vehicle types (numbers set to 0) #148
- results are the same for the same seed specified in the config file #139
- fix charging time bug #141
- fix charging logics bug, eta_cp is now included correctly #145
- datatype conversion and removal of NaN values in the grid time series #143
- fix SoC dropping below zero in the hpc methodology #148
- license classifier in setup.py corrected to MIT, matching the LICENSE file
- default input_directory changed to data/probability_private, matching the new data set on Zenodo
- fix simulation crash if driving_profile_seed is not set in the config

### Removed

- hpc_config.csv, replaced by the config section [hpc] #148

## [1.0.0] - 2022-07-15

### Added

- Complete revamp of the code base #71
- New HPC methodology
- Optional plots
- Minimum charging energy and SoC threshold
- Charging curve calculation

### Changed

- Fix implausible driving times #70
- Optional time series outputs have more data
- Vehicle csv outputs are now optional
- All instances of DataFrame.append() have been changed to pandas.concat() #71
- Performance for time series outputs has been improved drastically #71

### Removed

- Old code
- Single regions

## [0.1.3] - 2022-05-12

### Added

- Add documentation for simBEV
- Add total car amounts to metadata output #62
- Distinguish between private and public charging at use cases home and work #33

## Changed

- Fix last event in event list when time range is exceeded #66
- Fix first event in event list: set `park_start` to 0 when `park_start`>0 #66

## [0.1.2] - 2022-01-10

### Added

- Export metadata of run to JSON #27

## Changed

- Fix package config in setup.py
- Fix conda install instructions

## [0.1.1] - 2022-01-04

### Changed

- Fix missing EVs (CSVs) in output #54

## [0.1.0] - 2021-12-21

First version of simBEV to run simulations of electric vehicle charging demands.
