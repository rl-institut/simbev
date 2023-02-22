import pandas as pd
import random
import math
import datetime
from pathlib import Path


def get_season(date: datetime.date):
    """Determines season.

    Parameters
    ----------
    date : date
        Date request.

    Returns
    -------
    season : str
        Season of the date.
    """

    if date.month <= 2 or date.month == 12:
        season = "winter"
    elif date.month <= 5:
        season = "spring"
    elif date.month <= 8:
        season = "summer"
    elif date.month <= 11:
        season = "fall"
    else:
        raise ValueError()
    return season


def get_season_idx(date: datetime.date):
    """Gets index of season.

    Parameters
    ----------
    date : date
        Date requested.

    Returns
    -------
    season : int
        Index of the season.
    """
    if date.month <= 2 or date.month == 12:
        season = 0
    elif date.month <= 5:
        season = 1
    elif date.month <= 8:
        season = 2
    elif date.month <= 11:
        season = 3
    else:
        raise ValueError()
    return season


def get_cutoff(date: datetime.date):
    """Determines start date of next season.

    Parameters
    ----------
    date : date
        Date of request.

    Returns
    -------
        cutoff : date
            Start of next season.
    """
    if date.month == 12:
        year = date.year + 1
    else:
        year = date.year
    # set cutoff dates, jeweils erster Monat der nächsten Jahreszeit
    cutoff_dates = (3, 6, 9, 12)
    cutoff = datetime.date(year, cutoff_dates[get_season_idx(date)], 1)
    return cutoff


# Args: region (as string), example: get_name_csv("SR_Metro", get_season(datetime.date.today()))
def get_name_csv(region, season, data_directory):
    """Produces name of path for seasonal data.

    Parameters
    ----------
    region : str
        Current region.
    season : str
        Season the data is wanted for.
    Returns
    -------
    WindowsPath
        Path for the seasonal data in region.

    """
    return Path(data_directory, region, season + ".csv")


# main function, returns pandas
def get_timeseries(
    start: datetime.date, end: datetime.date, region, stepsize, data_directory
):
    """

    Parameters
    ----------
    start : date
        Start of simulation timeframe.
    end : date
        End of simulation timeframe.
    region : str
        Region.
    stepsize : int
        Stepsize of simulation.

    Returns
    -------
    pd_result : DataFrame
        Timeseries of processed MiD-data, that includes amount of trips started by usecase and time.
    """

    # build a matrix containing information about each season during the time span
    weekdays = 7
    min_per_day = 1440
    # set up variables
    pd_result = pd.DataFrame()
    weekdays_left = weekdays - start.weekday()
    # weeklist: 0 - season, 1 - weeks, 2 - days, 3 - start date, 4 - end date
    weeklist = []
    # build a matrix containing information about each season during the time span
    while start < end:
        cutoff = get_cutoff(start)
        if cutoff < end:  # use the whole season
            delta = cutoff - start
            weeklist.append(
                [
                    get_season(start),
                    math.floor(delta.days / 7),
                    delta.days % 7,
                    start,
                    cutoff,
                ]
            )
        else:  # end date is during this season
            delta = end - start + datetime.timedelta(1)
            weeklist.append(
                [
                    get_season(start),
                    math.floor(delta.days / 7),
                    delta.days % 7,
                    start,
                    end + datetime.timedelta(1),
                ]
            )
        start = cutoff

    # iteration over the created matrix. uses weeklist information to create time series dataframe
    for current_season in weeklist:
        file_name = get_name_csv(region, current_season[0], data_directory)
        data_df = pd.read_csv(file_name, sep=";", decimal=",", usecols=range(1, 8))
        temp = pd.DataFrame()
        # check if weekdays are left over from last month, add to start of series
        if weekdays_left < weekdays:
            if current_season[2] < weekdays_left and current_season[1] == 0:
                temp = pd.concat([temp, data_df.tail(current_season[2] * min_per_day)])
                current_season[2] = 0
            else:
                temp = pd.concat([temp, data_df.tail(weekdays_left * min_per_day)])
                if current_season[2] < weekdays_left:
                    current_season[2] = current_season[2] - weekdays_left + 7
                    current_season[1] = current_season[1] - 1
                else:
                    current_season[2] = current_season[2] - weekdays_left
        # add full weeks to the series
        for i in range(0, current_season[1]):
            temp = pd.concat([temp, data_df], ignore_index=True)
        # add leftover partial week at the end of series
        temp = pd.concat(
            [temp, data_df.head(current_season[2] * min_per_day)], ignore_index=True
        )

        date_rng = pd.date_range(
            current_season[3], current_season[4], freq="min", inclusive="left"
        )

        # date = pd.DatetimeIndex(date_rng)
        # day_key = date.day_name()

        temp.index = date_rng
        temp = temp.resample(datetime.timedelta(minutes=stepsize)).sum()
        pd_result = pd.concat([pd_result, temp])
        weekdays_left = weekdays - current_season[2]

    pd_result.columns = [
        "work",
        "business",
        "school",
        "shopping",
        "private",
        "leisure",
        "home",
    ]
    return pd_result


def get_profile_time_series(start_date, end_date, df):
    """
    Returns a time series starting from the start date up until the end date filled with
    week data chosen at random from the input DataFrame for each week.

    Parameters
    ----------
    start_date : str or datetime
        The start date of the time series in yyyy-mm-dd format.
    end_date : str or datetime
        The end date of the time series in yyyy-mm-dd format.
    df : pandas DataFrame
        The input DataFrame containing week data, where each entry with the same ID belongs to the same week.

    Returns
    -------
    pandas DataFrame
        The resulting time series.
    """
    # Convert start and end dates to datetime if needed
    if not isinstance(start_date, pd.Timestamp):
        start_date = pd.to_datetime(start_date)
    if not isinstance(end_date, pd.Timestamp):
        end_date = pd.to_datetime(end_date)
    
    # Create an empty DataFrame to hold the time series
    time_series = pd.DataFrame(columns=df.columns)
    ids = df['id'].unique()
    # Loop through each week between the start and end dates
    week_start = start_date
    while week_start <= end_date:
        # Select a random ID from the input DataFrame

        random_id = random.choice(ids)

        # Get the week data for the chosen ID
        week_data = df[df['id'] == random_id]

        # Determine the end date for the current week
        week_end = week_start + pd.Timedelta(days=6 - week_start.weekday())

        # If the week end date is beyond the end date of the time series, adjust it accordingly
        if week_end > end_date:
            week_end = end_date

        # Get the data for this week that falls within the desired date range
        week_data_filtered = week_data[(week_data['day'] >= (week_start.weekday())) & (week_data['day'] <= (week_end.weekday()))]

        # Append the filtered week data to the time series
        time_series = pd.concat([time_series, week_data_filtered])

        # Move to the next week
        week_start = week_end + pd.Timedelta(days=1)

        # TODO include dates or timesteps in timeseries

    return time_series


# TODO use this function to add timestamps to region time series?
def get_weekday_date(date: pd.Timestamp, weekday: int) -> pd.Timestamp:
    """
    Calculate the date of a given weekday within the same week as a given date.

    Parameters
    ----------
    date : pandas.Timestamp
        Input date.
    weekday : int
        Integer representing the desired weekday (0 = Monday, 1 = Tuesday, ..., 6 = Sunday).

    Returns
    -------
    pandas.Timestamp
        Date of the desired weekday within the same week as the input date.
    """
    weekday_date = date + pd.offsets.Day(weekday - date.weekday())
    return weekday_date
