import json
from pathlib import Path
import datetime

import pandas as pd

from simbev import __version__


def date_string_to_datetime(date_str):
    """ Function that converts string to date-format.

    Parameters
    ----------
    date_str : str
        Date to be converted.

    Returns
    -------
    date
        Converted date.
    """

    date_str = date_str.split("-")
    return datetime.date(int(date_str[0]), int(date_str[1]), int(date_str[2]))


def get_column_by_random_number(probability_series, random_number):
    """
    Takes a random number and a pandas.DataFrame with one row
    that contains probabilities,
    returns a column name.

    Parameters
    ----------
    probability_series : Series
        Contains probabilities for charging power.
    random_number : float
        Random number.

    Returns
    -------
    str
    """
    probability_series = probability_series / probability_series.sum()
    probability_series = probability_series.cumsum()
    probability_series.iloc[-1] = 1

    probability_series = probability_series.loc[probability_series > random_number]
    return probability_series.index[0]


def export_metadata(
        simbev,
        config
):
    """Export metadata of run to JSON file in result's root directory

    Parameters
    ----------
    simbev : SimBEV
        SimBEV object with scenario information.
    config : ConfigParser
        Object for parsing config.
    """
    cars = simbev.region_data[["bev_mini", "bev_medium", "bev_luxury", "phev_mini", "phev_medium", "phev_luxury"]]
    meta_dict = {
        "simBEV_version": __version__,
        "scenario": simbev.name,
        "timestamp_start": simbev.timestamp,
        "timestamp_end": datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S"),
        "config": config._sections,
        "tech_data": simbev.tech_data.to_dict(orient="index"),
        "charge_prob_slow": simbev.charging_probabilities["slow"].to_dict(orient="index"),
        "charge_prob_fast": simbev.charging_probabilities["fast"].to_dict(orient="index"),
        "car_sum": cars.sum().to_dict(),
        "car_amounts": cars.to_dict(orient="index")
    }
    outfile = Path(simbev.save_directory, 'metadata_simbev_run.json')
    with open(outfile, 'w') as f:
        json.dump(meta_dict, f, indent=4)


def export_analysis(analysis_array, directory):
    """
    Saves csv-file for analysis.

    Parameters
    ----------
    analysis_array : ndarray
        Contains summarized analysis-data.
    directory : WindowsPath
        Directory where to save file.
    """
    df = pd.DataFrame(analysis_array, columns=["car_type", "drive_count", "drive_max_length", "drive_min_length",
                                               "drive_mean_length", "drive_max_consumption",
                                               "drive_min_consumption", "drive_mean_consumption",
                                               "charge_count", "hpc_count", "charge_max_length", "charge_min_length",
                                               "charge_mean_length", "charge_max_energy",
                                               "charge_min_energy", "charge_mean_energy", "hpc_mean_energy",
                                               "home_mean_energy", "work_mean_energy", "public_mean_energy"
                                               ])
    df.to_csv(Path(directory, "analysis.csv"))
