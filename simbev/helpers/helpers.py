import pandas as pd
from pathlib import Path
import datetime as dt


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


def compile_output(result_dir: Path, start, end, region_mode, timestep=15):
    """

    Parameters
    ----------
    result_dir : :obj:`Path`
        Path to scenario results
    start : :obj:`datetime`
        starting time of simulation
    end : :obj:`datetime`
        ending time of simulation
    region_mode : :obj:`string`
        single or multi region simulation
    timestep : :obj:`int`
        time step of simulation in minutes

    Returns
    -------

    """
    # create Dataframe, take start and end date + timestep as parameter, build timeseries as index
    dt_range = pd.date_range(start, end + dt.timedelta(days=1), freq=str(timestep)+'min')
    pd_result = pd.DataFrame(0.0, index=range(len(dt_range)),
                             columns=["time", "sum CS power", "sum UC work", "sum UC business", "sum UC school",
                                      "sum UC shopping", "sum UC private/ridesharing", "sum UC leisure",
                                      "sum UC home", "sum UC hub"])
    # fill rest with zeroes
    pd_result["time"] = dt_range
    pd_result_sum = pd_result.copy()
    power_columns = ["sum CS power", "sum UC work", "sum UC business", "sum UC school",
                     "sum UC shopping", "sum UC private/ridesharing", "sum UC leisure",
                     "sum UC home", "sum UC hub"]
    # columns:
    # sum CS power;sum UC work;sum UC business;sum UC school;sum UC shopping;
    # sum UC private/ridesharing;sum UC leisure;sum UC home;sum UC hub

    # run through all csv result files of this run that include "standing_times" in the title
    sub_dirs = [f for f in result_dir.iterdir() if f.is_dir()]
    for sub_dir in sub_dirs:
        for file in sub_dir.rglob("*standing_times.csv"):
            file_df = pd.read_csv(file, sep=',', decimal='.')
            # file_df relevant columns: location,netto_charging_capacity,chargingdemand,charge_time,park_start,park_end
            for i in file_df.index:
                demand = file_df.loc[i, "chargingdemand"]
                if demand > 0:
                    # extract parameters for the charging event
                    uc = file_df.loc[i, "location"].split('_')
                    col = "sum UC " + uc[-1]
                    charge_time = file_df.loc[i, "charge_time"]
                    park_start = file_df.loc[i, "park_start"]
                    cap = file_df.loc[i, "netto_charging_capacity"]
                    max_charge = cap * timestep / 60
                    # average power in each time step
                    power = []
                    for k in range(charge_time):
                        # if possible charge with max power, greedy strat
                        if demand >= max_charge:
                            power.append(cap)
                            demand -= max_charge
                        else:
                            power.append(demand / timestep * 60)
                            demand = 0
                    # add charging series to result pandas
                    for count, p in enumerate(power):
                        if park_start + count < len(pd_result.index):
                            pd_result.loc[park_start + count, col] += p
                        else:
                            # print("There is " + str(p) + " kW to charge in timestep " + str(park_start + count))
                            break

        pd_result["sum CS power"] = (pd_result["sum UC work"] + pd_result["sum UC business"] + pd_result["sum UC school"] +
                                     pd_result["sum UC shopping"] + pd_result["sum UC private/ridesharing"] +
                                     pd_result["sum UC leisure"] + pd_result["sum UC hub"] + pd_result["sum UC home"])

        pd_result.to_csv(Path(result_dir, sub_dir.name + ".csv"), sep=',', decimal='.')
        if region_mode == "multi":
            pd_result_sum[power_columns] += pd_result[power_columns]
        pd_result[power_columns] = 0.0

    if region_mode == "multi":
        pd_result_sum.to_csv(Path(result_dir, "0_results_all_regions.csv"), sep=',', decimal='.')


if __name__ == '__main__':
    s = dt.datetime(2021, 9, 17)
    e = dt.datetime(2021, 9, 30)
    compile_output(Path('..', 'res', 'default_single_2021-11-22_133348_simbev_run'), s, e)
