import pandas as pd
# import numpy as np
import math
import datetime
from pathlib import Path


# returns season as string
def get_season(date: datetime.date):
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
    return Path("simbev", "data", region,  season + ".csv")


# main function, returns pandas
def get_timeseries(start: datetime.date, end: datetime.date, region, stepsize):
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
        if cutoff < end:    # use full season
            delta = cutoff - start
            weeklist.append([get_season(start), math.floor(delta.days / 7), delta.days % 7, start, cutoff])
        else:   # end date is during this season
            delta = end - start + datetime.timedelta(1)
            weeklist.append([get_season(start), math.floor(delta.days / 7), delta.days % 7, start,
                             end + datetime.timedelta(1)])
        start = cutoff

    # iteration over the created matrix. uses weeklist information to create time series dataframe
    for current_season in weeklist:
        file_name = get_name_csv(region, current_season[0])
        data_df = pd.read_csv(file_name, sep=';', decimal=',', usecols=range(1, 8))
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
        temp = pd.concat([temp, data_df.head(current_season[2] * min_per_day)], ignore_index=True)

        date_rng = pd.date_range(current_season[3], current_season[4], freq='min', inclusive='left')

        # date = pd.DatetimeIndex(date_rng)
        # day_key = date.day_name()

        temp.index = date_rng
        temp = temp.resample(datetime.timedelta(minutes=stepsize)).sum()
        pd_result = pd.concat([pd_result, temp])
        weekdays_left = weekdays - current_season[2]

    pd_result.columns = ['work', 'business', 'school', 'shopping',
                         'private', 'leisure', 'home']
    return pd_result


# tests
# if __name__ == '__main__':
#    x = get_timeseries(datetime.date.today(), datetime.date(2022, 12, 1), "LR_Klein", 15, 1440)
#    print(x)
