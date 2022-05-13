import pandas as pd
from car import Car, CarType
import pathlib
from mid_timeseries import get_timeseries
import helpers.helpers


class RegionType:
    def __init__(self, rs7_type):
        self.rs7_type = rs7_type
        self.time_series = None
        self.trip_starts = None
        self.probabilities = {}

    def create_timeseries(self, start_date, end_date, step_size):
        if not self.time_series:
            self.time_series = get_timeseries(start_date, end_date, self.rs7_type, step_size)
            self.trip_starts = self.time_series.sum(axis=1)
            self.trip_starts = self.trip_starts / self.trip_starts.max()

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
    def __init__(self, region_id, region_type: RegionType, region_counter):
        self.id = region_id
        self.region_type = region_type
        self.number = region_counter

        self.last_time_step = len(self.region_type.trip_starts.index) - 1

        self.car_dict = {}
        self.cars = []

    def add_cars_from_config(self, car_dict, car_types, rng):
        self.car_dict = car_dict
        for car_type_name, car_count in car_dict.items():
            for car_number in range(car_count):
                car_type = car_types[car_type_name]
                # create new car objects
                # TODO: randomize starting SoC and location, charging station availability
                # SOC init value for the first monday
                # TODO: check formula (taken from main_simbev line 74)
                soc_init = rng.random() ** (1 / 3) * 0.8 + 0.2 if rng.random() < 0.12 else 1
                new_car = Car(soc_init, car_type, False, False, car_number)
                self.cars.append(new_car)

    def get_purpose(self, rng, time_step):
        random_number = rng.random()
        purpose_probabilities = self.region_type.time_series.iloc[time_step]
        return helpers.helpers.get_column_by_random_number(purpose_probabilities, random_number)

    def get_probability(self, rng, destination, key):
        probabilities = self.region_type.probabilities[key][destination]
        prob = probabilities.sample(n=1, weights="distribution", random_state=rng)
        return prob.iat[0, -1]
