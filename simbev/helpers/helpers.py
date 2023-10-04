import json
from pathlib import Path
import datetime
from functools import wraps
import time
import pandas as pd
from scipy.interpolate import interp1d
from simbev import __version__


def date_string_to_datetime(date_str):
    """Function that converts string to date-format.

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


def export_metadata(simbev, config):
    """Export metadata of run to JSON file in result's root directory

    Parameters
    ----------
    simbev : SimBEV
        SimBEV object with scenario information.
    config : ConfigParser
        Object for parsing config.
    """
    cars = simbev.region_data[
        [
            "bev_mini",
            "bev_medium",
            "bev_luxury",
            "phev_mini",
            "phev_medium",
            "phev_luxury",
        ]
    ]
    meta_dict = {
        "simBEV_version": __version__,
        "scenario": simbev.name,
        "timestamp_start": simbev.timestamp,
        "timestamp_end": datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S"),
        "config": config._sections,
        "tech_data": simbev.tech_data.to_dict(orient="index"),
        "charge_prob_slow": simbev.charging_probabilities["slow"].to_dict(
            orient="index"
        ),
        "charge_prob_fast": simbev.charging_probabilities["fast"].to_dict(
            orient="index"
        ),
        "car_sum": cars.sum().to_dict(),
        "car_amounts": cars.to_dict(orient="index"),
    }
    outfile = Path(simbev.save_directory, "metadata_simbev_run.json")
    with open(outfile, "w") as f:
        json.dump(meta_dict, f, indent=4)


def export_analysis(analysis_array, directory, start_date, end_date, region_id):
    """Generates csv and json file for analysis of simulation-output.

    Parameters
    ---------
    analysis_array: ndarray
        Contains Data for analysis of characteristic values.
    directory: WindowsPath
        Directory for saving files.
    start_date: datetime
        Start of simulation.
    end_date: date
        End of simulation.
    region_id: str
        Identifier of region.
    """

    vehicle_array = [
        "bev_mini",
        "bev_medium",
        "bev_luxury",
        "phev_mini",
        "phev_medium",
        "phev_luxury",
    ]
    destination_array = [
        "distance_home",
        "distance_work",
        "distance_business",
        "distance_school",
        "distance_shopping",
        "distance_private",
        "distance_leisure",
        "distance_hpc",
    ]

    analysis_mid_dict = {
        "average_drive_time": float,
        "average_distance": float,
        "average_trip_count": int,
        "by_car_type": {
            "average_trip_count": {
                "bev_mini": float,
                "bev_medium": float,
                "bev_luxury": float,
                "phev_mini": float,
                "phev_medium": float,
                "phev_luxury": float,
            },
            "average_drive_time": {
                "bev_mini": float,
                "bev_medium": float,
                "bev_luxury": float,
                "phev_mini": float,
                "phev_medium": float,
                "phev_luxury": float,
            },
            "average_distance": {
                "bev_mini": float,
                "bev_medium": float,
                "bev_luxury": float,
                "phev_mini": float,
                "phev_medium": float,
                "phev_luxury": float,
            },
        },
        "by_destination": {
            "average_distance": {
                "distance_home": float,
                "distance_work": float,
                "distance_business": float,
                "distance_school": float,
                "distance_shopping": float,
                "distance_private": float,
                "distance_leisure": float,
                "distance_hpc": float,
            }
        },
    }
    df = pd.DataFrame(
        analysis_array,
        columns=[
            "car_type",
            "drive_count",
            "drive_max_length",
            "drive_min_length",
            "drive_mean_length",
            "drive_max_consumption",
            "drive_min_consumption",
            "drive_mean_consumption",
            "average_driving_time",
            "average_distance",
            "distance_home",
            "distance_work",
            "distance_business",
            "distance_school",
            "distance_shopping",
            "distance_private",
            "distance_leisure",
            "distance_hpc",
            "distance_cumulated",
            "charge_count",
            "hpc_count",
            "charge_max_length",
            "charge_min_length",
            "charge_mean_length",
            "charge_max_energy",
            "charge_min_energy",
            "charge_mean_energy",
            "hpc_mean_energy",
            "home_mean_energy",
            "work_mean_energy",
            "public_mean_energy",
            "public_count",
            "private_count",
        ],
    )

    df.to_csv(Path(directory, "analysis.csv"), index=False)

    # extract further analysis data and save it in json-format.
    array_to_numeric = [
        "drive_count",
        "average_driving_time",
        "average_distance",
        "private_count",
        "public_count",
    ]
    a = array_to_numeric + destination_array
    for item in a:
        df[item] = df[item].replace("nan", "-1")
        df[item] = pd.to_numeric(df[[item]].squeeze())

    start_date = start_date.date()
    number_of_days = end_date - start_date
    number_of_days = number_of_days.days + 1

    # general
    analysis_mid_dict["average_trip_count"] = round(
        df["drive_count"].mean() / number_of_days, 4
    )
    analysis_mid_dict["average_drive_time"] = round(
        df["average_driving_time"].mean(), 4
    )
    analysis_mid_dict["average_distance"] = round(df["average_distance"].mean(), 4)

    analysis_mid_dict["charging_event_share_private"] = round(
        df[["private_count"]].sum().iloc[0]
        / (df[["private_count"]].sum().iloc[0] + df[["public_count"]].sum()).iloc[0],
        4,
    )
    analysis_mid_dict["charging_event_share_public"] = round(
        df[["public_count"]].sum().iloc[0]
        / (df[["private_count"]].sum().iloc[0] + df[["public_count"]].sum()).iloc[0],
        4,
    )

    # by car-type
    # trip count by day
    for vehicle in vehicle_array:
        analysis_mid_dict["by_car_type"]["average_trip_count"][vehicle] = round(
            df["drive_count"].loc[df["car_type"] == vehicle].mean() / number_of_days, 4
        )
    # average drive time by trip
    for vehicle in vehicle_array:
        analysis_mid_dict["by_car_type"]["average_drive_time"][vehicle] = round(
            df["average_driving_time"].loc[df["car_type"] == vehicle].mean(), 4
        )
    # average distance by trip
    for vehicle in vehicle_array:
        analysis_mid_dict["by_car_type"]["average_distance"][vehicle] = round(
            df["average_distance"].loc[df["car_type"] == vehicle].mean(), 4
        )
    # by destination
    for destination in destination_array:
        analysis_mid_dict["by_destination"]["average_distance"][destination] = round(
            df[destination].loc[df[destination] != (-1)].mean(), 4
        )

    # save json-file
    with open(
        Path(directory, "analysis_mid_{}.json".format(region_id)), "w"
    ) as outfile:
        json.dump(analysis_mid_dict, outfile, indent=4, sort_keys=False)


def timeitlog(timing, save_directory):
    """Timing decorator for functions.

    Parameters
    ----------
    timing : bool
        Flag that indicates if decorated function should be timed or not.
    save_directory : pathlib.Path
        Path to the directory where simulation results are saved.

    """

    def decorator(func):
        path_to_log_file = Path(save_directory, "timing_log_file_simbev.txt")

        @wraps(func)
        def timeit_wrapper(*args, **kwargs):
            if timing:
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                total_time = end_time - start_time
                with open(path_to_log_file, "a") as f:
                    f.write(
                        "Function {} ran on {} took {} seconds \n".format(
                            func, datetime.datetime.now(), total_time
                        )
                    )
            else:
                result = func(*args, **kwargs)
            return result

        return timeit_wrapper

    return decorator


def interpolate_charging_curve(x, y):
    """Cubic interpolation between x and y.

    Wrapper for scipys interp1d function.

    Parameters
    ----------

    x : array_like
    y : array_like

    """
    f = interp1d(x, y, kind="cubic", fill_value="extrapolate")

    return f
