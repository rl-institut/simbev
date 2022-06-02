import pandas as pd
import numpy as np
from simbev.car import Car
import pathlib
from simbev.mid_timeseries import get_timeseries
import simbev.helpers.helpers as helpers


class RegionType:
    def __init__(self, rs7_type):
        self.rs7_type = rs7_type
        self.time_series = None
        self.trip_starts = None
        self.probabilities = {}
        self.header_grid_ts = []
        self.grid_time_series = []

    def create_timeseries(self, start_date, end_date, step_size):
        if not self.time_series:
            self.time_series = get_timeseries(start_date, end_date, self.rs7_type, step_size)
            self.trip_starts = self.time_series.sum(axis=1)
            self.trip_starts = self.trip_starts / self.trip_starts.max()

    def create_grid_timeseries(self):
        time_series = self.time_series
        time_stamps = np.array(time_series.index.to_pydatetime())
        self.header_grid_ts = ['timestamp', 'ges', 'ges_home', 'ges_work', 'ges_public', 'ges_hpc',
                               'home_3.7', 'home_11', 'home_22', 'home_50',
                               'work_3.7', 'work_11', 'work_22', 'work_50',
                               'public_3.7', 'public_11', 'public_22', 'public_50', 'public_150', 'public_350',
                               'hpc_150', 'hpc_350']
        self.grid_time_series = np.zeros((len(time_stamps), len(self.header_grid_ts)+1))

    def get_probabilities(self, data_directory):

        self.probabilities = {
            "speed": {},
            "distance": {},
            "stand": {},
            "charge": {},
        }

        region_directory = pathlib.Path(data_directory, self.rs7_type)

        # get all csv files in this region directory
        files = region_directory.glob("*.csv")
        for file in files:
            if "charge" in file.stem:
                self.probabilities["charge"] = pd.read_csv(file, sep=";", decimal=",")
            else:
                key = file.stem.split('_')[0]
                if key in self.probabilities:
                    # distance, speed or stand
                    df = pd.read_csv(file, sep=",", decimal=".")
                    purpose_key = file.stem.split('_')[-1]
                    if purpose_key == "ridesharing":
                        purpose_key = "private"
                    self.probabilities[key][purpose_key] = df


class Region:
    def __init__(self, region_id, region_type: RegionType, region_counter, simbev_obj):
        self.id = region_id
        self.region_type = region_type
        self.number = region_counter
        self.simbev = simbev_obj

        self.last_time_step = len(self.region_type.trip_starts.index)

        self.car_dict = {}
        self.cars = []

    def add_cars_from_config(self, car_dict):
        self.car_dict = car_dict
        for car_type_name, car_count in car_dict.items():
            for car_number in range(car_count):
                car_type = self.simbev.car_types[car_type_name]
                # create new car objects
                # TODO: parking parameters that change by region
                work_parking = self.simbev.work_parking[self.region_type.rs7_type] >= self.simbev.rng.random()
                home_parking = self.simbev.home_parking[self.region_type.rs7_type] >= self.simbev.rng.random()
                # TODO: Moritz no fixed charing power if public
                work_power = self.simbev.get_charging_capacity("work")
                home_power = self.simbev.get_charging_capacity("home")
                # SOC init value for the first monday
                # formula from Kilian, TODO maybe not needed anymore
                soc_init = self.simbev.rng.random() ** (1 / 3) * 0.8 + 0.2 if self.simbev.rng.random() < 0.12 else 1
                new_car = Car(car_type, car_number, work_parking, home_parking, work_power, home_power, soc_init)
                self.cars.append(new_car)

    def update_grid_timeseries(self, demand, use_case, chargepower, timestep):
        # Aufteilung auf die UC nach Leistung
        code = '{}_{}'.format(use_case, chargepower)
        if code in self.region_type.header_grid_ts:
            column = self.region_type.header_grid_ts.index(code)
            self.region_type.grid_time_series[timestep, column] += demand
            self.region_type.grid_time_series[timestep, 1] += demand
        else:
            print('Error in grid_time_series')
        # Aufteilung auf die UC
        code_uc_ges = 'ges_{}'.format(use_case)
        if code_uc_ges in self.region_type.header_grid_ts:
            column = self.region_type.header_grid_ts.index(code_uc_ges)
            self.region_type.grid_time_series[timestep, column] += demand
        else:
            print('Error in grid_time_series')
        # Aufaddieren auf Gesamtleistung
        self.region_type.grid_time_series[timestep, 1] += demand

    def get_purpose(self, rng, time_step):
        random_number = rng.random()
        purpose_probabilities = self.region_type.time_series.iloc[time_step]
        return helpers.get_column_by_random_number(purpose_probabilities, random_number)

    def get_probability(self, rng, destination, key):
        probabilities = self.region_type.probabilities[key][destination]
        prob = probabilities.sample(n=1, weights="distribution", random_state=rng)
        return prob.iat[0, -1]
