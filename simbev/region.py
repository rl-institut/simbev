import pandas as pd
from car import Car, CarType
import pathlib
from mid_timeseries import get_timeseries


class RegionType:
    def __init__(self, rs7_type):
        self.rs7_type = rs7_type
        self.time_series = None
        self.probabilities = {}

    def create_timeseries(self, start_date, end_date, step_size):
        self.time_series = get_timeseries(start_date, end_date, self.rs7_type, step_size)
        self.time_series["trips"] = self.time_series.sum(axis=1)
        self.time_series["trips"] = self.time_series["trips"] / self.time_series["trips"].max()

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
                    purpose_key = '_'.join(file.stem.split('_')[-1])
                    if purpose_key == "ridesharing":
                        purpose_key = "private"
                    self.probabilities[key][purpose_key] = df


class Region:
    def __init__(self, region_id, region_type: RegionType):
        self.id = region_id
        self.region_type = region_type
        self.cars = []

    def add_cars_from_config(self, car_dict, tech_data: pd.DataFrame):
        for car_type_name, car_count in car_dict.items():
            # create new car type
            # TODO: add charging curve and implement in code
            bat_cap = tech_data.at[car_type_name, 'battery_capacity']
            consumption = tech_data.at[car_type_name, 'energy_consumption']
            charging_capacity_slow = tech_data.at[car_type_name, 'max_charging_capacity_slow']
            charging_capacity_fast = tech_data.at[car_type_name, 'max_charging_capacity_fast']
            charging_capacity = {'slow': charging_capacity_slow, 'fast': charging_capacity_fast}
            # TODO: add charging curve
            car_type = CarType(car_type_name, bat_cap, charging_capacity, {}, consumption)
            for car_number in range(car_count):
                # create new car objects
                # TODO: randomize starting SoC and location, charging station availability
                new_car = Car(1, car_type, False, False, car_number)
                self.cars.append(new_car)
