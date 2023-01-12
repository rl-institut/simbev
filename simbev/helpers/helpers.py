import json
from pathlib import Path
import datetime

import pandas as pd

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


def export_analysis(analysis_array, directory, start_date, end_date):
    analysis_mid_dict = {
        "average_drive_time": float,
        "average_distance": float,
        "average_trip_count": int,
        "by_car_type": {
            "average_trip_count": {
                    "mini": float,
                    "medium": float,
                    "luxury": float
                },
            "average_drive_time": {
                    "mini": float,
                    "medium": float,
                    "luxury": float
                },
            "average_distance": {
                    "mini": float,
                    "medium": float,
                    "luxury": float
                }

        }
    }
    df = pd.DataFrame(analysis_array, columns=["car_type", "drive_count", "drive_max_length", "drive_min_length",
                                               "drive_mean_length", "drive_max_consumption",
                                               "drive_min_consumption", "drive_mean_consumption",
                                               "average_driving_time", "average_distance",
                                               "charge_count", "hpc_count", "charge_max_length", "charge_min_length",
                                               "charge_mean_length", "charge_max_energy",
                                               "charge_min_energy", "charge_mean_energy", "hpc_mean_energy",
                                               "home_mean_energy", "work_mean_energy", "public_mean_energy"
                                               ])

    df.to_csv(Path(directory, "analysis.csv"))
    df["drive_count"] = pd.to_numeric(df["drive_count"])
    df["average_driving_time"] = pd.to_numeric(df["average_driving_time"])
    df["average_distance"] = pd.to_numeric(df["average_distance"])

    start_date = start_date.date()
    number_of_days = end_date-start_date
    number_of_days = number_of_days.days + 1

    # general
    analysis_mid_dict["average_trip_count"] = round(df["drive_count"].mean()/number_of_days, 4)
    analysis_mid_dict["average_drive_time"] = round(df["average_driving_time"].mean(), 4)
    analysis_mid_dict["average_distance"] = round(df["average_distance"].mean(), 4)

    # by car-type
    # trip count by day
    analysis_mid_dict["by_car_type"]["average_trip_count"]["mini"] = round(df["drive_count"].loc[
                                                                               df["car_type"] == "bev_mini"
                                                                           ].mean()/number_of_days, 4)
    analysis_mid_dict["by_car_type"]["average_trip_count"]["medium"] = round(df["drive_count"].loc[
                                                                                 df["car_type"] == "bev_medium"
                                                                             ].mean()/number_of_days, 4)
    analysis_mid_dict["by_car_type"]["average_trip_count"]["luxury"] = round(df["drive_count"].loc[
                                                                                 df["car_type"] == "bev_luxury"
                                                                             ].mean()/number_of_days, 4)
    # average drive time by trip
    analysis_mid_dict["by_car_type"]["average_drive_time"]["mini"] = round(df["average_driving_time"].loc[
                                                                               df["car_type"] == "bev_mini"
                                                                           ].mean(), 4)
    analysis_mid_dict["by_car_type"]["average_drive_time"]["medium"] = round(df["average_driving_time"].loc[
                                                                                 df["car_type"] == "bev_medium"
                                                                             ].mean(), 4)
    analysis_mid_dict["by_car_type"]["average_drive_time"]["luxury"] = round(df["average_driving_time"].loc[
                                                                                 df["car_type"] == "bev_luxury"
                                                                             ].mean(), 4)
    # average distance by trip
    analysis_mid_dict["by_car_type"]["average_distance"]["mini"] = round(df["average_distance"].loc[
                                                                               df["car_type"] == "bev_mini"
                                                                           ].mean(), 4)
    analysis_mid_dict["by_car_type"]["average_distance"]["medium"] = round(df["average_distance"].loc[
                                                                                 df["car_type"] == "bev_medium"
                                                                             ].mean(), 4)
    analysis_mid_dict["by_car_type"]["average_distance"]["luxury"] = round(df["average_distance"].loc[
                                                                                 df["car_type"] == "bev_luxury"
                                                                             ].mean(), 4)

    with open(Path(directory, "analysis_mid.json"), "w") as outfile:
        json.dump(analysis_mid_dict, outfile)
