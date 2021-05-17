import pandas as pd


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
