from typing import List
import simbev.helpers.helpers as helpers
import pandas as pd
import numpy as np
from simbev.region import Region, RegionType
from simbev.car import CarType
from simbev.trip import Trip, HPCTrip
import multiprocessing as mp
import pathlib
import datetime
import math
import configparser as cp


class SimBEV:
    def __init__(self, region_data: pd.DataFrame, charging_prob_dict, tech_data: pd.DataFrame,
                 config_dict, name, home_work_private, num_threads=1):
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
        self.start_date_output = datetime.datetime.combine(self.start_date_input,
                                                           datetime.datetime.min.time())
        self.end_date = config_dict["end_date"]
        self.home_parking = home_work_private.loc["home", :]
        self.work_parking = home_work_private.loc["work", :]

        self.num_threads = num_threads

        # additional parameters
        self.regions: List[Region] = []
        self.created_region_types = {}
        self.car_types = {}

        self.name = name
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        save_directory_name = "{}_{}_simbev_run".format(
            self.name, self.timestamp)
        self.save_directory = pathlib.Path("simbev", "res", save_directory_name)
        self.data_directory = pathlib.Path("simbev", "data")

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
        rs7_region.create_grid_timeseries()
        rs7_region.get_probabilities(self.data_directory)
        self.created_region_types[region_type] = rs7_region

    def _add_regions_from_dataframe(self):
        # variable to check which region types have been created
        for region_counter in range(len(self.region_data.index)):
            # get data from inputs
            region_id = self.region_data.index[region_counter]
            region_type = self.region_data.iat[region_counter, 0]
            car_dict = self.region_data.iloc[region_counter, 1:].to_dict()

            # create region_type
            if region_type not in self.created_region_types.keys():
                self._create_region_type(region_type)

            # create region objects
            new_region = Region(region_id, self.created_region_types[region_type], region_counter, self)
            new_region.add_cars_from_config(car_dict)
            self.regions.append(new_region)

    def run_multi(self):
        self.num_threads = min(self.num_threads, len(self.regions))
        if self.num_threads == 1:
            for region in self.regions:
                self.run(region)
        else:
            pool = mp.Pool(processes=self.num_threads)

            for region_ctr, region in enumerate(self.regions):
                pool.apply_async(self.run, (region,))

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
            self.simulate_car(car, region)

            # export vehicle csv
            car.export(region_directory, self)

        print(" - done")

    def get_charging_capacity(self, location=None, distance=None, distance_limit=50):
        # TODO: check if this destination is used for fast charging
        if location == "hub" and distance:
            if distance > distance_limit:
                location = "ex-urban"
            else:
                location = "urban"
            probability = self.charging_probabilities["fast"]
            probability = probability.loc[[d for d in probability.index if location == d]]
            probability = probability.squeeze()
            return float(helpers.get_column_by_random_number(probability, self.rng.random()))

        elif location:
            probability = self.charging_probabilities["slow"]
            probability = probability.loc[[d for d in probability.index if location in d]]
            probability = probability.squeeze()
            return float(helpers.get_column_by_random_number(probability, self.rng.random()))

        else:
            raise ValueError("Missing arguments in get_charging_capacity.")

    def _get_hpc_charging_capacity(self, trip, distance_limit=50):
        """

        Parameters
        ----------
        fast_charging_probability : :obj:`df`
            Scenario dataframe for fast charging probabilities
        distance : :obj:`int`
            Driven distance to destination
        distance_limit : :obj:`int`
            Limit after it assumed that a charging takes place in an ex-urban area
            and therefore has a higher likeliness of a higher charging capacity,
            unit km: e.g. 50

        Returns
        -------
        fastcharge : :obj:`int`
            Fast Charging Capacity (150 kW or 350 kW)

        """

        if trip.distance > distance_limit:
            area = r"ex-urban"
        else:
            area = "urban"

        prob_50 = self.charging_probabilities['fast'].loc[area].iloc[0]
        prob_150 = self.charging_probabilities['fast'].loc[area].iloc[1] + prob_50

        random_number = self.rng.random()  # random number between 0 and 1

        if random_number <= prob_150:
            charging_capacity = 150
        else:
            charging_capacity = 350

        return charging_capacity

    def hours_to_time_steps(self, t):
        return math.ceil(t * 60 / self.step_size)

    def simulate_car(self, car, region):
        # create first trip
        trip = Trip(region, car, 0, self)
        # iterate through all time steps
        for step in range(len(region.region_type.trip_starts.index)):
            # check if current trip is done
            if step >= trip.trip_end:
                # find next trip
                trip = Trip(region, car, step, self)
                trip.execute()

    @classmethod
    def from_config(cls, scenario_path):
        """
        Creates a SimBEV object from a specified scenario name. The scenario needs to be located in /simbev/scenarios.

        Returns:
            SimBEV Object
            ConfigParser Object
        """
        if not scenario_path.is_dir():
            raise FileNotFoundError(f'Scenario "{scenario_path.stem}" not found in ./scenarios .')

        # read config file
        cfg = cp.ConfigParser()
        cfg_file = pathlib.Path(scenario_path, "simbev_config.cfg")
        if not cfg_file.is_file():
            raise FileNotFoundError(f"Config file {cfg_file} not found.")
        try:
            cfg.read(cfg_file)
        except Exception:
            raise FileNotFoundError(f"Cannot read config file {cfg_file} - malformed?")

        region_df = pd.read_csv(pathlib.Path(scenario_path, "regions.csv"), sep=',', index_col=0)

        # read chargepoint probabilities
        charge_prob_slow = pd.read_csv(pathlib.Path(scenario_path, cfg["charging_probabilities"]["slow"]))
        charge_prob_slow = charge_prob_slow.set_index("destination")
        charge_prob_fast = pd.read_csv(pathlib.Path(scenario_path, cfg["charging_probabilities"]["fast"]))
        charge_prob_fast = charge_prob_fast.set_index("destination")
        charge_prob_dict = {"slow": charge_prob_slow,
                            "fast": charge_prob_fast}

        home_work_private = pd.read_csv(pathlib.Path(scenario_path, cfg['charging_probabilities']['home_work_private']))
        home_work_private = home_work_private.set_index('region')

        tech_df = pd.read_csv(pathlib.Path(scenario_path, "tech_data.csv"), sep=',',
                              index_col=0)

        start_date = cfg.get("basic", "start_date")
        start_date = helpers.date_string_to_datetime(start_date)
        end_date = cfg.get("basic", "end_date")
        end_date = helpers.date_string_to_datetime(end_date)

        cfg_dict = {"step_size": cfg.getint("basic", "stepsize"),
                    "soc_min": cfg.getfloat("basic", "soc_min"),
                    "rng_seed": cfg["sim_params"].getint("seed", None),
                    "eta_cp": cfg.getfloat("basic", "eta_cp"),
                    "start_date": start_date,
                    "end_date": end_date,
                    "home_private": cfg.getfloat("charging_probabilities", "private_parking_home", fallback=0.5),
                    "work_private": cfg.getfloat("charging_probabilities", "private_parking_work", fallback=0.5),
                    }
        num_threads = cfg.getint('sim_params', 'num_threads')

        return SimBEV(region_df, charge_prob_dict, tech_df, cfg_dict, scenario_path.stem, home_work_private,
                      num_threads), cfg
