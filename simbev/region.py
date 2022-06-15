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
    def __init__(self, region_id, region_type: RegionType, region_counter, simbev_obj):
        self.id = region_id
        self.region_type = region_type
        self.number = region_counter
        self.simbev = simbev_obj

        self.last_time_step = len(self.region_type.trip_starts.index)

        self.car_dict = {}
        self.cars = []

        self.header_grid_ts = []
        self.grid_time_series = []
        self.grid_data_frame = []

        self.file_name = "{}_grid_time_series_{}.csv".format(self.number, self.id)

        self.create_grid_timeseries()

    def add_cars_from_config(self, car_dict):
        self.car_dict = car_dict
        for car_type_name, car_count in car_dict.items():
            for car_number in range(car_count):
                car_type = self.simbev.car_types[car_type_name]
                # create new car objects
                # TODO: parking parameters that change by region
                work_parking = self.simbev.work_parking[self.region_type.rs7_type] >= self.simbev.rng.random()
                home_parking = self.simbev.home_parking[self.region_type.rs7_type] >= self.simbev.rng.random()

                work_power = self.simbev.get_charging_capacity("work") if work_parking else None
                home_power = self.simbev.get_charging_capacity("home") if home_parking else None
                # SOC init value for the first monday
                # formula from Kilian, TODO maybe not needed anymore
                soc_init = self.simbev.rng.random() ** (1 / 3) * 0.8 + 0.2 if self.simbev.rng.random() < 0.12 else 1
                new_car = Car(car_type, car_number, work_parking, home_parking, work_power, home_power, self, soc_init)
                self.cars.append(new_car)

    def update_grid_timeseries(self, use_case, chargepower, power_lis, timestep_start, timestep_end):
        # distribute power to use cases dependent on power
        code = 'cars_{}_{}'.format(use_case, power_lis)
        if code in self.header_grid_ts:
            column = self.header_grid_ts.index(code)
            self.grid_time_series[timestep_start:timestep_end, column] += 1

        # distribute to use cases total
        code_uc_ges = '{}_total'.format(use_case)
        if code_uc_ges in self.header_grid_ts:
            column = self.header_grid_ts.index(code_uc_ges)
            self.grid_time_series[timestep_start:timestep_end, column] += chargepower

        # add to total amount
        column = self.header_grid_ts.index('total')
        self.grid_time_series[timestep_start:timestep_end, column] += chargepower

    def get_purpose(self, rng, time_step):
        random_number = rng.random()
        purpose_probabilities = self.region_type.time_series.iloc[time_step]
        return helpers.get_column_by_random_number(purpose_probabilities, random_number)

    def get_probability(self, rng, destination, key):
        probabilities = self.region_type.probabilities[key][destination]
        prob = probabilities.sample(n=1, weights="distribution", random_state=rng)
        return prob.iat[0, -1]

    def create_grid_timeseries(self):
        header_slow = list(self.simbev.charging_probabilities['slow'].columns)
        header_fast = list(self.simbev.charging_probabilities['fast'].columns)
        if '0' in header_slow:
            header_slow.remove('0')
        if '0' in header_fast:
            header_fast.remove('0')
        time_series = self.region_type.time_series
        time_stamps = np.array(time_series.index.to_pydatetime())
        self.header_grid_ts = ['timestep', 'timestamp', 'total']
        use_cases = ['home', 'work', 'public', 'hpc']
        for uc in use_cases:
            self.header_grid_ts.append('{}_total'.format(uc))
            if uc == 'home':
                for power in header_slow:
                    self.header_grid_ts.append('cars_{}_{}'.format(uc, power))
            if uc == 'work':
                for power in header_slow:
                    self.header_grid_ts.append('cars_{}_{}'.format(uc, power))
            if uc == 'public':
                for power in header_slow:
                    self.header_grid_ts.append('cars_{}_{}'.format(uc, power))
                for power in header_fast:
                    self.header_grid_ts.append('cars_{}_{}'.format(uc, power))
            if uc == 'hpc':
                for power in header_fast:
                    self.header_grid_ts.append('cars_{}_{}'.format(uc, power))

        self.grid_time_series = np.zeros((len(time_stamps), len(self.header_grid_ts)))

    def export_grid_timeseries(self, region_directory):
        """
        Exports the grid time series to a csv file.

        Parameters
        ----------
        region_directory : :obj:`pathlib.Path`
            save directory for the region
        simbev : :obj:`SimBEV`
            SimBEV object with scenario information

        """

        data = pd.DataFrame(self.grid_time_series)
        data.columns = self.header_grid_ts
        data['timestamp'] = self.region_type.time_series.index

        # remove first week from dataframe
        week_time_steps = int(24 * 7 * 60 / self.simbev.step_size)
        data['timestep'] = data.index
        data['timestep'] -= week_time_steps
        data = data.loc[(data['timestep']) >= 0]
        data = data.drop(columns=['timestep'])
        data = data.round(4)
        self.grid_data_frame = data

        data.to_csv(pathlib.Path(region_directory, self.file_name))
