# Changelog
All notable changes to this project will be documented in this file.

The format is inspired from [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and the versioning aim to respect [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

Here is a template for new release sections

```
## [_._._] - 20XX-MM-DD

### Added

-

### Changed

-

### Removed

-
```

## [_._._] - 2022-MM-DD

### Changed

- Fix implausible driving times #70

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
