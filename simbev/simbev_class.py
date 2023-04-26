from typing import List
import simbev.helpers.helpers as helpers
import pandas as pd
import numpy as np
from simbev.region import Region, RegionType
from simbev.car import CarType, Car, UserGroup
from simbev.trip import Trip
from simbev.mid_timeseries import get_profile_time_series
import simbev.plot as plot
from simbev.helpers.errors import SoCError
import multiprocessing as mp
import pathlib
import datetime
import math
import traceback
import configparser as cp
import json
import copy


class SimBEV:
    # TODO docstring
    def __init__(self, data_dict, config_dict, name):
        # parameters from data_dict
        self.region_data = data_dict["regions"]
        self.charging_probabilities = data_dict["charging_probabilities"]
        self.power_by_usecase = "use_case" in self.charging_probabilities
        self.tech_data = data_dict["tech_data"]
        self.energy_min = data_dict["energy_min"]
        self.home_parking = data_dict["private_probabilities"].loc["home", :]
        self.work_parking = data_dict["private_probabilities"].loc["work", :]

        self.hpc_data = data_dict["hpc_data"]
        self.attractivity = data_dict["user_groups_attractivity"]
        self.charging_curve_points = data_dict["charging_curve_points"]

        # parameters from config_dict
        self.step_size = config_dict["step_size"]
        self.soc_min = config_dict["soc_min"]
        self.charging_threshold = config_dict["charging_threshold"]
        self.distance_threshold_extra_urban = config_dict[
            "distance_threshold_extra_urban"
        ]
        self.fast_charge_threshold = config_dict["fast_charge_threshold"]
        self.consumption_factor_highway = config_dict["consumption_factor_highway"]
        self.occupation_time_max = config_dict["occupation_time_max"]
        self.rng_seed = config_dict["rng_seed"]
        self.rng = self.get_rng()
        self.eta_cp = config_dict["eta_cp"]
        self.start_date_input = config_dict["start_date"]
        self.start_date = self.start_date_input - datetime.timedelta(days=7)
        self.start_date_output = datetime.datetime.combine(
            self.start_date_input, datetime.datetime.min.time()
        )
        self.end_date = config_dict["end_date"]
        self.home_parking = data_dict["private_probabilities"].loc["home", :]
        self.work_parking = data_dict["private_probabilities"].loc["work", :]
        self.probability_detached_home = data_dict["private_probabilities"].loc[
            "probability_detached_home"
        ]
        self.energy_min = data_dict["energy_min"]
        self.private_only_run = config_dict["private_only_run"]

        self.num_threads = config_dict["num_threads"]
        self.output_options = config_dict["output_options"]

        self.input_type = config_dict["input_type"]
        self.input_directory = pathlib.Path(config_dict["input_directory"])
        self.input_data = {"rural": {}, "suburban": {}, "urban": {}}
        if self.input_type == "profile":
            for file_path in self.input_directory.glob("*.gzip"):
                file_path_parts = file_path.stem.split("_")
                self.input_data[file_path_parts[-2]][
                    file_path_parts[-1]
                ] = pd.read_parquet(file_path)
        self.scaling = config_dict["scaling"]
        # additional parameters
        self.regions: List[Region] = []
        self.created_region_types = {}
        self.car_types = {}
        self.user_groups = {}
        self.grid_data_list = []
        self.analysis_data_list = []
        self.terminated = False

        self.name = name
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        save_directory_name = "{}_{}_simbev_run".format(self.name, self.timestamp)
        self.save_directory = pathlib.Path(
            config_dict["scenario_path"], "results", save_directory_name
        )
        self.file_name_all = "grid_time_series_all_regions.csv"
        self.file_name_analysis_all = "analysis_all_regions.csv"
        self.file_name_analysis_all_json = "analysis_all_regions.json"

        self.step_size_str = str(self.step_size) + "min"

    def setup(self):
        # run setup functions
        self._create_user_groups()
        self._create_car_types()
        self._add_regions_from_dataframe()

    def _create_user_groups(self):
        for user_group_number in self.attractivity.index:
            user_group = UserGroup(
                user_group_number,
                self.attractivity.loc[user_group_number].to_dict(),
            )
            self.user_groups[user_group_number] = user_group

    def _create_car_types(self):
        """Creates car-types with all necessary properties.

        Parameters
        ----------
        output : bool
            Setting for output.
        """

        # create new car type
        for car_type_name in self.tech_data.index:
            bat_cap = self.tech_data.at[car_type_name, "battery_capacity"]
            consumption = self.tech_data.at[car_type_name, "energy_consumption"]

            charging_curve = helpers.interpolate_charging_curve(
                self.charging_curve_points["key"].tolist(),
                self.charging_curve_points[car_type_name].tolist(),
            )

            output = self.output_options["analyze"] or self.output_options["car"]

            if "bev" in car_type_name:
                energy_min = self.energy_min["bev"].to_dict()
            else:
                energy_min = self.energy_min["phev"].to_dict()

            if "max_charging_capacity_slow" in self.tech_data.columns:
                charging_capacity_slow = self.tech_data.at[
                    car_type_name, "max_charging_capacity_slow"
                ]
                charging_capacity_fast = self.tech_data.at[
                    car_type_name, "max_charging_capacity_fast"
                ]

                car_types_tuples = [
                    (charging_capacity_slow, charging_capacity_fast)
                ]
            else:
                # tech data by probability
                slow_cols = [col for col in self.tech_data.columns if 'slow' in col]
                fast_cols = [col for col in self.tech_data.columns if 'fast' in col]

                car_types_tuples = []
                for slow_col in slow_cols:
                    slow = float(slow_col.split("_")[-1])
                    for fast_col in fast_cols:
                        fast = float(fast_col.split("_")[-1])
                        car_types_tuples.append((slow, fast))

            for slow, fast in car_types_tuples:
                charging_capacity = {
                    "slow": slow,
                    "fast": fast,
                }
                car_type = CarType(
                    car_type_name,
                    bat_cap,
                    charging_capacity,
                    self.soc_min,
                    self.charging_threshold,
                    energy_min,
                    charging_curve,
                    consumption,
                    self.consumption_factor_highway,
                    output,
                    self.attractivity,
                    analyze_mid=True,
                )
                if "bev" in car_type.name:
                    car_type.label = "BEV"
                else:
                    car_type.label = "PHEV"
                if len(car_types_tuples) == 1:
                    self.car_types[car_type_name] = car_type
                else:
                    self.car_types["{}_{}_{}".format(car_type_name, slow, fast)] = car_type

    def _create_region_type(self, region_type):
        """Creates region-types with all necessary properties.

        Parameters
        ----------
        region_type : str
            Type of Region.
        """

        rs7_region = RegionType(
            region_type,
            self.output_options["grid"],
            self.step_size,
            self.charging_probabilities,
        )

        rs7_region.create_timeseries(self)
        if self.input_type == "probability":
            rs7_region.get_probabilities(self.input_directory)

        self.created_region_types[region_type] = rs7_region

    def _add_regions_from_dataframe(self):
        """TODO"""

        # variable to check which region types have been created
        for region_counter in range(len(self.region_data.index)):
            # get data from inputs
            region_id = self.region_data.index[region_counter]
            region_type = self.region_data.iat[region_counter, 0]

            car_dict = (
                (self.region_data.iloc[region_counter, 1:] / self.scaling)
                .apply(np.ceil)
                .astype(int)
            ).to_dict()
            scaling_factors = (
                (self.region_data.iloc[region_counter, 1:])
                / (self.region_data.iloc[region_counter, 1:] / self.scaling)
                .apply(np.ceil)
                .astype(int)
            ).to_dict()

            # create region_type
            if region_type not in self.created_region_types.keys():
                self._create_region_type(region_type)

            # create region objects
            new_region = Region(
                region_id,
                self.created_region_types[region_type],
                region_counter,
                car_dict,
                scaling_factors,
            )
            self.regions.append(new_region)

    def get_rng(self):
        return np.random.default_rng(self.rng_seed)

    def run_multi(self):
        """Runs Simulation for multiprocessing"""
        print(
            "Scaling set to {}: 1 simulated vehicle represents {} vehicles in grid time series".format(
                self.scaling, self.scaling
            )
        )
        self.num_threads = min(self.num_threads, len(self.regions))
        if self.num_threads == 1:
            for region in self.regions:
                grid_data = self.run(region)

                self._log_grid_data(grid_data)

        else:
            pool = mp.Pool(processes=self.num_threads)

            # define local callback function for error handling and data logging
            def callback(result):
                if result[0] is None:
                    self.terminated = True
                    pool.terminate()

                self._log_grid_data(result)

            for region in self.regions:
                pool.apply_async(self.run, (region,), callback=callback)
            pool.close()
            pool.join()
        if self.terminated:
            raise SystemExit(
                "Exception occured during multiprocessing, simulation stopped. See above for further information."
            )
        grid_time_series_all_regions = helpers.timeitlog(
            self.output_options["timing"], self.save_directory
        )(self.export_grid_timeseries_all_regions)()
        if self.output_options["region_plot"] or self.output_options["collective_plot"]:
            plot.plot_gridtimeseries_by_usecase(self, grid_time_series_all_regions)

    def run(self, region):
        """Runs Simulation for single-processing

        Parameters
        ----------
        region : Region
            Includes all properties of current region.

        Returns
        -------
        DataFrame
            Returns grid-data for current region.
        """

        try:
            if self.num_threads == 1:
                print(
                    f"===== Region: {region.id} ({region.number + 1}/{len(self.regions)}) ====="
                )
            else:
                print(
                    f"Starting Region {region.id} ({region.number + 1}/{len(self.regions)})"
                )
            region_directory = pathlib.Path(self.save_directory, str(region.id))
            region_directory.mkdir(parents=True, exist_ok=True)

            cars_simulated = 0
            exception_count = 0
            for car_type_name, car_count in region.car_dict.items():
                for car_number in range(car_count):
                    # Create new car
                    if "max_charging_capacity_slow" in self.tech_data.columns:
                        car_type = self.car_types[car_type_name]
                    else:
                        # tech data by probability
                        slow_cols = [col for col in self.tech_data.columns if 'slow' in col]
                        fast_cols = [col for col in self.tech_data.columns if 'fast' in col]

                        charging_capacity_slow = float(helpers.get_column_by_random_number(
                            self.tech_data.loc[
                            car_type_name, slow_cols
                        ],
                        self.rng.random()
                        ).split("_")[-1])

                        charging_capacity_fast = float(helpers.get_column_by_random_number(
                            self.tech_data.loc[
                            car_type_name, fast_cols
                        ],
                        self.rng.random()
                        ).split("_")[-1])
                        car_type = self.car_types["{}_{}_{}".format(car_type_name, charging_capacity_slow, charging_capacity_fast)]


                    # create new car objects
                    # TODO: parking parameters that change by region
                    work_parking = (
                        self.work_parking[region.region_type.rs7_type] >= self.rng.random()
                    )
                    home_parking = (
                        self.home_parking[region.region_type.rs7_type] >= self.rng.random()
                    )
                    work_power = (
                        self.get_charging_capacity("work") if work_parking else None
                    )
                    home_power = (
                        self.get_charging_capacity("home") if home_parking else None
                    )
                    user_group_id = self.set_user_group(
                        work_parking, home_parking, work_power, home_power
                    )
                    # todo decide if car is at home in detached house or apartment building

                    # SOC init value for the first monday
                    # formula from Kilian, TODO maybe not needed anymore
                    soc_init = (
                        self.rng.random() ** (1 / 3) * 0.8 + 0.2
                        if self.rng.random() < 0.12
                        else 1
                    )
                    home_detached = (
                        self.rng.random() <= self.probability_detached_home[region.region_type.rs7_type]
                    )

                    car = Car(
                        car_type,
                        self.user_groups[user_group_id],
                        car_number,
                        work_parking,
                        home_parking,
                        work_power,
                        home_power,
                        region,
                        home_detached,
                        soc_init,
                    )

                    if self.input_type == "profile":
                        car.driving_profile = get_profile_time_series(
                            self.start_date,
                            self.end_date,
                            self.step_size,
                            self.input_data[region.region_type.rs3_type][
                                car_type_name.split("_")[-1]
                            ],
                        )

                    if self.num_threads == 1:
                        print(
                            "\r{}% {} {} / {}".format(
                                round(
                                    (cars_simulated + car_number + 1)
                                    * 100
                                    / region.car_amount
                                ),
                                car.car_type.name,
                                (car.number + 1),
                                region.car_dict[car.car_type.name],
                            ),
                            end="",
                            flush=True,
                        )

                    # if private run, check if private charging infrastructure is available
                    if self.private_only_run and (work_power or home_power):
                        try:
                            private_car = copy.copy(car)
                            private_car.output = copy.deepcopy(car.output)
                            private_car.private_only = True
                            self.simulate_car(private_car, region)
                            car = private_car
                        except SoCError:
                            exception_count += 1
                            self.simulate_car(car, region)
                    else:
                        self.simulate_car(car, region)

                    # export vehicle csv
                    if self.output_options["analyze"]:
                        car_array = car.export(region_directory, self)
                        if region.analyze_array is None:
                            region.analyze_array = car_array
                        else:
                            region.analyze_array = np.vstack(
                                (region.analyze_array, car_array)
                            )
                    else:
                        car.export(region_directory, self)
                cars_simulated += car_count
            if self.private_only_run:
                print(
                    "\nNumber of cars that couldn't run private only: {}/{}".format(
                        exception_count, cars_simulated
                    )
                )

            region.export_grid_timeseries(region_directory)
            if self.output_options["analyze"]:
                helpers.export_analysis(
                    region.analyze_array,
                    region_directory,
                    self.start_date_output,
                    self.end_date,
                    region.id,
                )
            print(f" - done (Region {region.number + 1}) at {datetime.datetime.now()}")
            return region.grid_data_frame, region.analyze_array
        except Exception as e:
            if self.num_threads > 1:
                print("\n{}: {}".format(type(e).__name__, e))
                print(
                    "EXCEPTION TRACE  PRINT:\n{}".format(
                        "".join(traceback.format_exception(type(e), e, e.__traceback__))
                    )
                )

                return None, None
            else:
                raise e

    def get_charging_capacity(self, location=None, use_case=None, distance=None):
        """Determines charging capacity for specific charging event

        Parameters
        ----------
        location : str
            Current location of the vehicle.
        distance : float
            Distance of trip.
        distance_limit : int
            distance of trip, that determines the area of hpc charging.

        Returns
        -------
        Float
            Returns charging capacity.
        """

        if self.power_by_usecase:
            if use_case == "hpc":
                if distance > self.distance_threshold_extra_urban:
                    use_case = "highway_fast"
                else:
                    use_case = "urban_fast"
                probability = self.charging_probabilities["use_case"]
                probability = probability.loc[use_case, :]
                probability = probability.squeeze()
                return float(
                    helpers.get_column_by_random_number(probability, self.rng.random())
                )
            elif use_case:
                probability = self.charging_probabilities["use_case"]
                probability = probability.loc[use_case, :]
                probability = probability.squeeze()
                return float(
                    helpers.get_column_by_random_number(probability, self.rng.random())
                )

        if "hpc" in location:
            if distance > self.distance_threshold_extra_urban:
                location = "ex-urban"
            else:
                location = "urban"
            probability = self.charging_probabilities["fast"]
            probability = probability.loc[
                [d for d in probability.index if location == d]
            ]
            probability = probability.squeeze()
            return float(
                helpers.get_column_by_random_number(probability, self.rng.random())
            )

        elif location:
            probability = self.charging_probabilities["slow"]
            probability = probability.loc[
                [d for d in probability.index if location in d]
            ]
            probability = probability.squeeze()
            return float(
                helpers.get_column_by_random_number(probability, self.rng.random())
            )

        else:
            raise ValueError("Missing arguments in get_charging_capacity.")

    def hours_to_time_steps(self, t):
        """Converts time in hours to timesteps.

        Parameters
        ----------
        t : float
            Time in hours.

        Returns
        -------
        int
            Returns timesteps.
        """
        return math.ceil(t * 60 / self.step_size)

    def simulate_car(self, car, region):
        """Simulates driving profiles for a car.

        Parameters
        ----------
        car : Car
            Includes all properties of current car.
        region : Region
            Includes all properties of current region.
        """
        if self.input_type == "probability":
            # create first trip
            trip = Trip.from_probability(region, car, 0, self)
            # iterate through all time steps
            for step in range(region.last_time_step + 1):
                # check if current trip is done
                if step >= trip.trip_end:
                    # find next trip
                    trip = Trip.from_probability(region, car, step, self)
                    trip.execute()
        elif self.input_type == "profile":
            trips = Trip.from_driving_profile(region, car, self)
            previous_trip = Trip(region, car, 0, self)
            previous_trip.trip_end = 0
            trip_possible = True
            for trip in trips:
                if trip is not None:
                    delay = max(
                        previous_trip.trip_end - trip.park_start, 0
                    )  # TODO maybe add +1 to first term
                    if delay:
                        trip_possible = trip.delay(delay)
                    if trip_possible:
                        trip.execute()
                        previous_trip = trip

    def set_user_group(self, work_parking, home_parking, work_capacity, home_capacity):
        """Assigns specific user-group to vehicle."""
        if home_capacity and home_parking:
            if work_capacity and work_parking:
                user_group = 0  # private LIS at home and at work
            else:
                user_group = 1  # private LIS at home but not at work
        else:
            if work_capacity and work_parking:
                user_group = 2  # private LIS not at home but at work
            else:
                user_group = 3  # private LIS not at home and not at work
        return user_group

    def _log_grid_data(self, result):
        """Appends grid-timeseries of current region to a list.

        Parameters
        ----------
        result : DataFrame
            Grid-timeseries of current region.
        """
        result_grid = result[0]
        result_analysis = result[1]
        self.grid_data_list.append(result_grid)

        columns = [
            "car_type",
            "drive_count",
            "drive_max_length",
            "drive_min_length",
            "drive_mean_length",
            "drive_max_consumption",
            "drive_min_consumption",
            "drive_mean_consumption",
            "average_driving_time",
            "average_distance",
            "distance_home",
            "distance_work",
            "distance_business",
            "distance_school",
            "distance_shopping",
            "distance_private",
            "distance_leisure",
            "distance_hpc",
            "distance_cumulated",
            "charge_count",
            "hpc_count",
            "charge_max_length",
            "charge_min_length",
            "charge_mean_length",
            "charge_max_energy",
            "charge_min_energy",
            "charge_mean_energy",
            "hpc_mean_energy",
            "home_mean_energy",
            "work_mean_energy",
            "public_mean_energy",
            "public_count",
            "private_count",
        ]
        df_result_analysis = pd.DataFrame(result_analysis, columns=[columns])

        self.analysis_data_list.append(df_result_analysis)

    def export_grid_timeseries_all_regions(self):
        """Export of grid-timeseries of all regions.

        Returns
        -------
        DataFrame
            Returns grid-timeseries for all regions.
        """

        start_date = self.start_date
        number_of_days = self.end_date - start_date
        number_of_days = number_of_days.days - 6  # deduction of 7 day cutoff
        if self.output_options["analyze"]:
            analysis_collection = None
            for data in self.analysis_data_list:
                if analysis_collection is None:
                    analysis_collection = data.copy()
                else:
                    analysis_collection = pd.concat([analysis_collection, data])
            analysis_collection = analysis_collection.round(4)
            analysis_collection = analysis_collection.reset_index(drop=True)
            analysis_collection.to_csv(
                pathlib.Path(self.save_directory, self.file_name_analysis_all),
                index=False,
            )

            # get share of private and public charging events and save in .json.

            array_to_numeric = [
                "public_count",
                "private_count",
                "distance_cumulated",
                "drive_count",
            ]
            for item in array_to_numeric:
                analysis_collection[item] = pd.to_numeric(
                    analysis_collection[[item]].squeeze()
                )

            share_dict = {
                "share_private": round(
                    analysis_collection[["private_count"]].sum().iloc[0]
                    / (
                        analysis_collection[["private_count"]].sum().iloc[0]
                        + analysis_collection[["public_count"]].sum().iloc[0]
                    ),
                    4,
                ),
                "share_public": round(
                    analysis_collection[["public_count"]].sum().iloc[0]
                    / (
                        analysis_collection[["private_count"]].sum().iloc[0]
                        + analysis_collection[["public_count"]].sum().iloc[0]
                    ),
                    4,
                ),
                "trips_a_day": analysis_collection[["drive_count"]].sum().iloc[0]
                / len(analysis_collection)
                / number_of_days,
                "average_distance_per_trip:": round(
                    analysis_collection[["distance_cumulated"]].sum().iloc[0]
                    / analysis_collection[["drive_count"]].sum().iloc[0],
                    4,
                ),
                "average_distance_per_day": round(
                    analysis_collection[["distance_cumulated"]].sum().iloc[0]
                    / len(analysis_collection)
                    / number_of_days,
                    4,
                ),
            }

            with open(
                pathlib.Path(self.save_directory, self.file_name_analysis_all_json), "w"
            ) as outfile:
                json.dump(share_dict, outfile, indent=4, sort_keys=False)

        if self.output_options["grid"]:
            grid_ts_collection = None
            for data in self.grid_data_list:
                if grid_ts_collection is None:
                    grid_ts_collection = data.copy()
                else:
                    grid_ts_collection.loc[
                        :, grid_ts_collection.columns != "timestamp"
                    ] += data.loc[:, data.columns != "timestamp"]
            grid_ts_collection = grid_ts_collection.round(4)
            grid_ts_collection.to_csv(
                pathlib.Path(self.save_directory, self.file_name_all), index=False
            )
            return grid_ts_collection

    @classmethod
    def from_config(cls, config_path):
        """Creates a SimBEV object from a specified scenario name.
        The scenario needs to be located in /simbev/scenarios.

        Returns
        -------
        SimBEV
            SimBEV object, that contains all Parameters needed for simulation.
        cfg
            ConfigParser Object for reading config files.
        """
        scenario_path = config_path.parent.parent
        if not scenario_path.is_dir():
            raise FileNotFoundError(
                f'Scenario "{scenario_path.stem}" not found in ./scenarios .'
            )

        # read config file
        cfg = cp.ConfigParser()
        cfg_file = pathlib.Path(config_path)
        if not cfg_file.is_file():
            raise FileNotFoundError(f"Config file {cfg_file} not found.")
        try:
            cfg.read(cfg_file)
        except Exception:
            raise FileNotFoundError(f"Cannot read config file {cfg_file} - malformed?")

        region_df = pd.read_csv(
            pathlib.Path(scenario_path, cfg["rampup_ev"]["rampup"]),
            sep=",",
            index_col=0,
        )

        # read chargepoint probabilities
        charging_probabilities = {}
        for charging_type in ["slow", "fast", "use_case"]:
            file_path = cfg.get("charging_probabilities", charging_type, fallback=None)
            if file_path is not None:
                df = pd.read_csv(
                    pathlib.Path(
                        scenario_path, file_path
                    ),
                    index_col=0,
                )
                charging_probabilities[charging_type] = df

        home_work_private = pd.read_csv(
            pathlib.Path(
                scenario_path, cfg["charging_probabilities"]["home_work_private"]
            )
        )
        home_work_private = home_work_private.set_index("region")
        tech_df = pd.read_csv(
            pathlib.Path(scenario_path, cfg["tech_data"]["tech_data"]),
            sep=",",
            index_col=0,
        )
        hpc_df = pd.read_csv(
            pathlib.Path(scenario_path, cfg["tech_data"]["hpc_data"]),
            sep=",",
            index_col=0,
        )
        hpc_data = hpc_df.to_dict()["values"]

        user_groups_attractivity = pd.read_csv(
            pathlib.Path(scenario_path, cfg["user_data"]["user_groups"]),
            sep=",",
            index_col=0,
        )

        charging_curve_points = pd.read_csv(
            pathlib.Path(scenario_path, cfg["tech_data"]["charging_curve"]),
            sep=",",
            index_col=False,
        )

        energy_min = pd.read_csv(
            pathlib.Path(scenario_path, cfg["charging_probabilities"]["energy_min"])
        )
        energy_min = energy_min.set_index("uc")

        start_date = cfg.get("basic", "start_date")
        start_date = helpers.date_string_to_datetime(start_date)
        end_date = cfg.get("basic", "end_date")
        end_date = helpers.date_string_to_datetime(end_date)

        # get output options from config
        car_output = cfg.getboolean("output", "vehicle_csv", fallback=True)
        grid_output = cfg.getboolean("output", "grid_time_series_csv", fallback=True)
        region_plot = cfg.getboolean(
            "output", "plot_grid_time_series_split", fallback=False
        )
        collective_plot = cfg.getboolean(
            "output", "plot_grid_time_series_collective", fallback=False
        )
        timing_output = cfg.getboolean("output", "timing", fallback=False)
        analyze = cfg.getboolean("output", "analyze", fallback=False)
        output_options = {
            "car": car_output,
            "grid": grid_output,
            "region_plot": region_plot,
            "collective_plot": collective_plot,
            "timing": timing_output,
            "analyze": analyze,
        }

        cfg_dict = {
            "step_size": cfg.getint("basic", "stepsize", fallback=15),
            "soc_min": cfg.getfloat("basic", "soc_min", fallback=0.2),
            "charging_threshold": cfg.getfloat("basic", "charging_threshold"),
            "distance_threshold_extra_urban": cfg.getfloat(
                "basic", "distance_threshold_extra_urban"
            ),
            "consumption_factor_highway": cfg.getfloat(
                "basic", "consumption_factor_highway"
            ),
            "rng_seed": cfg["sim_params"].getint("seed", None),
            "eta_cp": cfg.getfloat("basic", "eta_cp"),
            "start_date": start_date,
            "end_date": end_date,
            "home_private": cfg.getfloat(
                "charging_probabilities", "private_parking_home", fallback=0.5
            ),
            "work_private": cfg.getfloat(
                "charging_probabilities", "private_parking_work", fallback=0.5
            ),
            "scenario_path": scenario_path,
            "input_type": cfg["basic"]["input_type"],
            "input_directory": cfg["basic"]["input_directory"],
            "num_threads": cfg.getint("sim_params", "num_threads", fallback=1),
            "output_options": output_options,
            "private_only_run": cfg.getboolean(
                "sim_params", "private_only_run", fallback=False
            ),
            "scaling": cfg.getint("sim_params", "scaling"),
            "occupation_time_max": cfg.getint("basic", "occupation_time_max"),
            "fast_charge_threshold": cfg.getfloat("basic", "dc_power_threshold", fallback=50.),
        }
        data_dict = {
            "charging_probabilities": charging_probabilities,
            "regions": region_df,
            "tech_data": tech_df,
            "private_probabilities": home_work_private,
            "energy_min": energy_min,
            "hpc_data": hpc_data,
            "charging_curve_points": charging_curve_points,
            "user_groups_attractivity": user_groups_attractivity,
        }

        return SimBEV(data_dict, cfg_dict, config_path.stem), cfg
