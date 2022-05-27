import pandas as pd
# import numpy as np
import math
import datetime
from pathlib import Path


# returns season as string
def get_season(date: datetime.date):
    if date.month <= 2 or date.month == 12:
        season = "Winter"
    elif date.month <= 5:
        season = "Fruehling"
    elif date.month <= 8:
        season = "Sommer"
    elif date.month <= 11:
        season = "Herbst"
    else:
        raise ValueError()
    return season


# returns index of season to be used for cutoff_dates
def get_season_idx(date: datetime.date):
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


# returns date where the next season starts
def get_cutoff(date: datetime.date):
    if date.month == 12:
        year = date.year + 1
    else:
        year = date.year
    # set cutoff dates, jeweils erster Monat der nächsten Jahreszeit
    cutoff_dates = (3, 6, 9, 12)
    cutoff = datetime.date(year, cutoff_dates[get_season_idx(date)], 1)
    return cutoff


# Args: region (as string), example: get_name_csv("SR_Metro", get_season(datetime.date.today()))
def get_name_csv(region, season):
    return Path('data', 'seasonal', region + "_" + season + ".csv")


# main function, returns pandas
def get_timeseries(start: datetime.date, end: datetime.date, region, stepsize):
    # build a matrix containing information about each season during the time span
    weekdays = 7
    min_per_day = 1440
    days = (end - start).days - 7
    # set up variables
    pd_result = pd.DataFrame()
    weekdays_left = weekdays - start.weekday()
    minutes_per_day = min_per_day
    # weeklist: 0 - season, 1 - weeks, 2 - days, 3 - start date, 4 - end date
    weeklist = []
    # build a matrix containing information about each season during the time span
    while start < end:
        cutoff = get_cutoff(start)
        if cutoff < end:    # use full season
            delta = cutoff - start
            weeklist.append([get_season(start), math.floor(delta.days / 7), delta.days % 7, start, cutoff])
        else:   # end date is during this season
            delta = end - start + datetime.timedelta(1)
            weeklist.append([get_season(start), math.floor(delta.days / 7), delta.days % 7, start,
                             end + datetime.timedelta(1)])
        start = cutoff

    # iteration over the created matrix. uses weeklist information to create time series dataframe
    for t in weeklist:
        file_name = get_name_csv(region, t[0])
        data_df = pd.read_csv(file_name, sep=';', decimal=',', usecols=range(1, 8))
        temp = pd.DataFrame()
        # check if weekdays are left over from last month, add to start of series
        if weekdays_left < weekdays:
            if t[2] < weekdays_left and t[1] == 0:
                temp = temp.append(data_df.tail(t[2] * minutes_per_day))
                t[2] = 0
            else:
                temp = temp.append(data_df.tail(weekdays_left * minutes_per_day))
                if t[2] < weekdays_left:
                    t[2] = t[2] - weekdays_left + 7
                    t[1] = t[1] - 1
                else:
                    t[2] = t[2] - weekdays_left
        # add full weeks to the series
        for i in range(0, t[1]):
            temp = temp.append(data_df, ignore_index=True)
        # add leftover partial week at the end of series
        temp = temp.append(data_df.head(t[2] * minutes_per_day), ignore_index=True)

        date_rng = pd.date_range(t[3], t[4], freq='min', closed='left')

        # date = pd.DatetimeIndex(date_rng)
        # day_key = date.day_name()

        temp.index = date_rng
        temp = temp.resample(datetime.timedelta(minutes=stepsize)).sum()
        pd_result = pd_result.append(temp)
        weekdays_left = weekdays - t[2]

    pd_result.columns = ['0_work', '1_business', '2_school', '3_shopping',
                         '4_private/ridesharing', '5_leisure', '6_home']
    return pd_result, days


# tests
# if __name__ == '__main__':
#    x = get_timeseries(datetime.date.today(), datetime.date(2022, 12, 1), "LR_Klein", 15, 1440)
#    print(x)
