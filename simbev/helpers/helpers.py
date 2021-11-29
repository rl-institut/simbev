import pandas as pd
from pathlib import Path


def single_to_multi_scenario(region_type,
                             rampup,
                             max_charging_capacity_slow,
                             max_charging_capacity_fast,
                             battery_capacity,
                             energy_consumption):
    """Convert params from single region scenario to multi scenario DFs

    Parameters
    ----------
    region_type : :obj:`str`
        MiD region type
    rampup : :obj:`dict`
        Ramp up data for EVs as given in the config
    max_charging_capacity_slow : :obj:`dict`
        Max. slow (AC) charging capacity for EVs as given in the config
    max_charging_capacity_fast : :obj:`dict`
        Max. fast (DC) charging capacity for EVs as given in the config
    battery_capacity : :obj:`dict`
        Battery capacity data for EVs as given in the config
    energy_consumption : :obj:`dict`
        Energy consumption data for EVs as given in the config

    Returns
    -------
    :pandas.DataFrame:
        Regions
    :pandas.DataFrame:
        Technology data
    """

    if rampup is None:
        rampup = dict()
    regions = pd.DataFrame({
        'region_id': 'single_region',
        'RegioStaR7': region_type,
        **{k: int(v) for k, v in rampup.items()}
    }, index=[0]).set_index('region_id')

    tech_data = pd.DataFrame({
        'max_charging_capacity_slow': max_charging_capacity_slow,
        'max_charging_capacity_fast': max_charging_capacity_fast,
        'battery_capacity': battery_capacity,
        'energy_consumption': energy_consumption
    }).astype('float')
    tech_data.index.name = 'type'

    return regions, tech_data


def compile_output(dir: Path, start, end, timestep=15, file_name="output.csv"):  # maybe convert dir into Path
    # create Dataframe, take start and end date + timestep as parameter, build timeseries as index
    # fill rest with zeroes
    # columns:
    # sum CS power;sum UC work;sum UC business;sum UC school;sum UC shopping;
    # sum UC private/ridesharing;sum UC leisure;sum UC home;sum UC hub
    # run through all csv result files of this run that include "standing_times" in the title
    for file in dir.rglob("*.csv"):
        file_df = pd.read_csv(file)
        # go through all events, if charging then add power at that time step to the use case
    # at the end combine all sums in column sum CS power

    return
