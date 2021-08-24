import pandas as pd
# import numpy as np
import math
import datetime
from pathlib import Path

# set cutoff dates, jeweils erster Monat der nächsten Jahreszeit
cutoff_dates = (3, 6, 9, 12)


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
    cutoff = datetime.date(year, cutoff_dates[get_season_idx(date)], 1)
    return cutoff


# Args: region (as string), example: get_name_csv("SR_Metro", get_season(datetime.date.today()))
def get_name_csv(region, season):
    return Path('data', 'seasonal', region + "_" + season + ".csv")


# main function, returns pandas
def get_timeseries(start: datetime.date, end: datetime.date, region, stepsize, weekdays, min_per_day):
    # build a matrix containing information about each season during the time span
    weeklist = []
    while start < end:
        cutoff = get_cutoff(start)
        if cutoff < end:
            delta = cutoff - start
            weeklist.append([get_season(start), math.floor(delta.days / 7), delta.days % 7, start, cutoff])
        else:
            delta = end - start + datetime.timedelta(1)
            weeklist.append([get_season(start), math.floor(delta.days / 7), delta.days % 7, start,
                             end + datetime.timedelta(1)])
        start = cutoff

    # set up variables
    pd_result = pd.DataFrame()
    weekday = weekdays
    minutes_per_day = min_per_day

    # iteration over the created matrix. uses weeklist information to create time series dataframe
    for t in weeklist:
        file_name = get_name_csv(region, t[0])
        data_df = pd.read_csv(file_name, sep=';', decimal=',', usecols=range(1, 8))
        temp = pd.DataFrame()

        if weekday < 7:
            if t[2] < weekday and t[1] == 0:
                temp = temp.append(data_df.tail(t[2] * minutes_per_day))
                t[2] = 0
            else:
                temp = temp.append(data_df.tail(weekday * minutes_per_day))
                if t[2] < weekday:
                    t[2] = t[2] - weekday + 7
                    t[1] = t[1] - 1
                else:
                    t[2] = t[2] - weekday

        for i in range(0, t[1]):
            temp = temp.append(data_df, ignore_index=True)
        temp = temp.append(data_df.head(t[2] * minutes_per_day), ignore_index=True)

        date_rng = pd.date_range(t[3], t[4], freq='min', closed='left')

        # date = pd.DatetimeIndex(date_rng)
        # day_key = date.day_name()

        temp.index = date_rng
        temp = temp.resample(datetime.timedelta(minutes=stepsize)).sum()
        pd_result = pd_result.append(temp)
        weekday = 7 - t[2]

    pd_result.columns = ['0_work', '1_business', '2_school', '3_shopping',
                         '4_private/ridesharing', '5_leisure', '6_home']
    return pd_result


# tests
# if __name__ == '__main__':
#    x = get_timeseries(datetime.date.today(), datetime.date(2021, 12, 1), "LR_Klein")
#    print(x)
