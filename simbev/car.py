import datetime
import pandas as pd

class Car:
    def __init__(self, bat_cap, cc):
        self.bat_cap = bat_cap
        self.charging_capacity = cc
        self.status = 0
        self.location = '6_home'




bev1 = Car(500, 11)


