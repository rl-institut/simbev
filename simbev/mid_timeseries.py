import pandas as pd
# import numpy as np
import math
import datetime
from pathlib import Path


# set cutoff dates, jeweils erster Monat der nächsten Jahreszeit
cutoff_dates = (3, 6, 9, 12)


# Ausgabe der Jahreszeit als String
def get_season(date: datetime.date):
    if date.month <= 2 or date.month == 12: season = "Winter"
    elif date.month <= 5: season = "Fruehling"
    elif date.month <= 8: season = "Sommer"
    elif date.month <= 11: season = "Herbst"
    else: season = "error"
    return season


# returns index of season to be used for cutoff_dates
def get_season_idx(date: datetime.date):
    if date.month <= 2 or date.month == 12: season = 0
    elif date.month <= 5: season = 1
    elif date.month <= 8: season = 2
    elif date.month <= 11: season = 3
    else: season = "error"
    return season


# returns date where the next season starts
def get_cutoff(date: datetime.date):
    if date.month == 12: year = date.year + 1
    else: year = date.year
    cutoff = datetime.date(year, cutoff_dates[get_season_idx(date)], 1)
    return cutoff


# Args: region (als Zahl 71-77), season aus get_season als String
def get_name_csv(r, s):
    # Bestimmen der Region (evtl mit dictionary?)
    if r == 71: name = "SR_Metropole_"
    elif r == 72: name = "SR_Grossstadt_"
    elif r == 73: name = "SR_Mittelstadt_"
    elif r == 74: name = "SR_Kleinstadt_"
    elif r == 75: name = "LR_Zentralstadt_"
    elif r == 76: name = "LR_Mittelstadt_"
    elif r == 77: name = "LR_Kleinstadt_"
    else: name = "Error"
    return Path('data', 'seasonal', name + s + ".csv")


# function that gets used in code, returns pandas
def get_timeseries(start: datetime.date, end: datetime.date, region: int, timestep: int = 15):
    weeklist = []
    while start < end:
        cutoff = get_cutoff(start)
        if cutoff < end:
            delta = cutoff - start
            weeklist.append((get_season(start), math.floor(delta.days / 7), delta.days % 7, start, cutoff))
        else:
            delta = end - start + datetime.timedelta(1)
            weeklist.append((get_season(start), math.floor(delta.days / 7), delta.days % 7, start, end + datetime.timedelta(1)))
        start = cutoff

    pd_result = pd.DataFrame()
    for t in weeklist:
        file_name = get_name_csv(region, t[0])
        pan = pd.read_csv(file_name, sep=';', decimal=',', usecols=range(1, 8))
        temp = pd.DataFrame()
        for i in range(0, t[1]):
            temp=temp.append(pan, ignore_index=True)
        temp=temp.append(pan.head(t[2]*60*24), ignore_index=True)
        date_rng = pd.date_range(t[3], t[4], freq='min', closed='left')
        temp.index=date_rng
        temp=temp.resample(datetime.timedelta(minutes=timestep)).sum()
        pd_result=pd_result.append(temp)
    pd_result.columns = ['0_work', '1_business', '2_school', '3_shopping', '4_private/ridesharing', '5_leisure', '6_home']
    return pd_result


# tests
if __name__ == '__main__':
    x = get_timeseries(datetime.date.today(), datetime.date(2021, 12, 6), 72)
    print(x)