import pandas as pd
from simbev import car

class Scenario:
    def __init__(self, config):
        self.regio = config

    def run(self, timedelta, start, end):
        time = pd.date_range(start, end, freq=timedelta)
        for i in time:
            car.status = 3
            # driving
            # parking
            # charging

config = 71
s1 = Scenario(config)
s1.run('H', '2017-1-1', '2018-1-1')