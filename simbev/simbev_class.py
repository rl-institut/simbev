from typing import List
import helpers.helpers as helpers
import pandas as pd
import numpy as np
from region import Region, RegionType
from car import CarType
import multiprocessing as mp
import pathlib
import datetime


class SimBEV:
    def __init__(self, region_data: pd.DataFrame, charging_prob_dict, tech_data: pd.DataFrame,
                 config_dict, name, num_threads=1):
        # parameters from arguments
        self.region_data = region_data
        self.charging_probabilities = charging_prob_dict
        self.tech_data = tech_data

        # parameters from config_dict
        self.step_size = config_dict["step_size"]
        self.soc_min = config_dict["soc_min"]
        self.rng = np.random.default_rng(config_dict["rng_seed"])
        self.eta_cp = config_dict["eta_cp"]
        self.start_date_input = config_dict["start_date"]
        self.start_date = self.start_date_input - datetime.timedelta(days=7)
        self.end_date = config_dict["end_date"]
        self.home_private = config_dict["home_private"]
        self.work_private = config_dict["work_private"]

        self.num_threads = num_threads

        # additional parameters
        self.regions: List[Region] = []
        self.created_region_types = {}
        self.car_types = {}

        save_directory_name = "{}_{}_simbev_run".format(
            name, datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S"))
        self.save_directory = pathlib.Path("res", save_directory_name)
        self.data_directory = pathlib.Path("data")

        self.step_size_str = str(self.step_size) + "min"

        # run setup functions
        self._create_car_types()
        self._add_regions_from_dataframe()

    def _create_car_types(self):
        # create new car type
        for car_type_name in self.tech_data.index:
            # TODO: add charging curve and implement in code
            bat_cap = self.tech_data.at[car_type_name, "battery_capacity"]
            consumption = self.tech_data.at[car_type_name, "energy_consumption"]
            charging_capacity_slow = self.tech_data.at[car_type_name, "max_charging_capacity_slow"]
            charging_capacity_fast = self.tech_data.at[car_type_name, "max_charging_capacity_fast"]
            charging_capacity = {"slow": charging_capacity_slow, "fast": charging_capacity_fast}
            # TODO: add charging curve
            car_type = CarType(car_type_name, bat_cap, charging_capacity, {}, consumption)
            if "bev" in car_type.name:
                car_type.label = "BEV"
            else:
                car_type.label = "PHEV"
            self.car_types[car_type_name] = car_type

    def _create_region_type(self, region_type):
        rs7_region = RegionType(region_type)
        rs7_region.create_timeseries(self.start_date, self.end_date, self.step_size)
        rs7_region.get_probabilities(self.data_directory)
        self.created_region_types[region_type] = rs7_region

    def _add_regions_from_dataframe(self):
        # variable to check which region types have been created
        for region_counter in range(len(self.region_data.index)):
            # get data from inputs
            region_id = self.region_data.iat[region_counter, 0]
            region_type = self.region_data.iat[region_counter, 1]
            car_dict = self.region_data.iloc[region_counter, 2:].to_dict()

            # create region_type
            if region_type not in self.created_region_types.keys():
                self._create_region_type(region_type)

            # create region objects
            new_region = Region(region_id, self.created_region_types[region_type], region_counter)
            new_region.add_cars_from_config(car_dict, self.car_types, self.rng)
            self.regions.append(new_region)

    def run_multi(self):
        self.num_threads = min(self.num_threads, len(self.regions))
        if self.num_threads == 1:
            for region in self.regions:
                self.run(region)
        else:
            pool = mp.Pool(processes=self.num_threads)

            # TODO: fix multiprocessing, produces no results (on windows)
            for region_ctr, region in enumerate(self.regions):
                pool.apply_async(self.run, (region, region_ctr))

            pool.close()
            pool.join()

    def run(self, region):
        print(f'===== Region: {region.id} ({region.number + 1}/{len(self.regions)}) =====')
        region_directory = pathlib.Path(self.save_directory, region.id)
        region_directory.mkdir(parents=True, exist_ok=True)

        for car_count, car in enumerate(region.cars):
            print("\r{}% {} {} / {}".format(
                round((car_count + 1) * 100 / len(region.cars)),
                car.car_type.name,
                (car.number + 1), region.car_dict[car.car_type.name]
            ), end="", flush=True)
            # TODO: simulate car

            # test
            distance = 10
            # TODO replace with standing time probability
            arrival_time = 0
            # iterate through all time steps
            for step in range(len(region.region_type.trip_starts.index)):
                # check if car isn't driving and if a trip can be started
                if step >= arrival_time and region.region_type.trip_starts.iat[step]:
                    # check if trip starts
                    # TODO: more checks, trips start too often currently
                    if self.rng.random() < region.region_type.trip_starts.iat[step]:
                        # combine into single function to call
                        # find next trip destination
                        destination = region.get_purpose(self.rng, step)
                        # don't use same destination twice in a row
                        if destination == car.status:
                            continue

                        if car.status == "hub":
                            distance = 100
                            charging_type = "fast"
                        else:
                            charging_type = "slow"

                        # TODO: fast or slow charging?
                        # process last charging event, since standing time is now known
                        station_capacity = self.get_charging_capacity(car.status, distance)
                        charging_time = step - arrival_time
                        car.charge(arrival_time, charging_time, station_capacity, charging_type)

                        # start new driving event
                        drive_time = 5  # TODO get this from region probabilities
                        car.drive(step, drive_time, distance, destination)
                        arrival_time = step + drive_time

            # export vehicle csv
            car.export(pathlib.Path(region_directory, car.file_name))

        # TODO: maybe drop region from self.regions to remove reference => let it be deleted?
        # might be necessary for big simulations
        print(" - done")

    def get_charging_capacity(self, destination=None, distance=None, distance_limit=50):
        # TODO: check if this destination is used for fast charging
        if destination == "hub" and distance:
            if distance > distance_limit:
                destination = "ex-urban"
            else:
                destination = "urban"
            probability = self.charging_probabilities["fast"]
            probability = probability.loc[[d for d in probability.index if destination == d]]
            probability = probability.squeeze()
            return float(helpers.get_column_by_random_number(probability, self.rng.random()))

        elif destination:
            probability = self.charging_probabilities["slow"]
            probability = probability.loc[[d for d in probability.index if destination in d]]
            probability = probability.squeeze()
            return float(helpers.get_column_by_random_number(probability, self.rng.random()))

        else:
            raise ValueError("Missing arguments in get_charging_capacity.")

    def get_trip(self):
        pass
