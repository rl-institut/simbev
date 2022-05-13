import json
import pandas as pd
from pathlib import Path
import datetime

from simbev import __version__


def date_string_to_datetime(date_str):
    date_str = date_str.split("-")
    return datetime.date(int(date_str[0]), int(date_str[1]), int(date_str[2]))


def get_column_by_random_number(probability_series, random_number):
    """
    Takes a random number and a pandas.DataFrame with one row
    that contains probabilities,
    returns a column name.
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
    simbev : :obj:`SimBEV`
        SimBEV object with scenario information
    config : cp.ConfigParser
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
