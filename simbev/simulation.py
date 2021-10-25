from scenario import Scenario
import pandas as pd


class Simulation:

    def __init__(self, scenario: Scenario, start_date, end_date, timestep):
        self.scenario = scenario
        self.start = start_date
        self.end = end_date
        self.timestep = timestep

    def run(self):
        time = pd.date_range(self.start, self.end, freq=self.timestep)
        for i in time:
            return
            # car.status = 3
            # driving
            # parking
            # charging
