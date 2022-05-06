import pandas as pd
from region import Region
import multiprocessing as mp
import pathlib
import datetime


class SimBEV:
    def __init__(self, region_data: pd.DataFrame, charging_prob_dict, tech_data: pd.DataFrame,
                 config_dict, name, num_threads=1):
        # parameters from arguments
        self.region_data = region_data
        self.charging_prob = charging_prob_dict
        self.tech_data = tech_data

        # parameters from config_dict
        self.step_size = config_dict["step_size"]
        self.soc_min = config_dict["soc_min"]
        self.rng = config_dict["rng"]
        self.eta_cp = config_dict["eta_cp"]
        self.start_date = config_dict["start_date"]
        self.end_data = config_dict["end_date"]
        self.home_private = config_dict["home_private"]
        self.work_private = config_dict["work_private"]

        self.num_threads = num_threads

        # additional parameters
        self.regions = []
        directory_name = name + "_" + datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S") + \
                         "_simbev_run"
        self.save_directory = pathlib.Path("res", directory_name)

        self._add_regions_from_dataframe()
        # time_step = str(self.step_size) + "min"
        # self.time_series = pd.date_range(self.start_date, self.end_data, freq=time_step)
        self.time_series = []

    def _add_regions_from_dataframe(self):
        for i in range(len(self.region_data.index)):
            region_id = self.region_data.iat[i, 0]
            region_type = self.region_data.iat[i, 1]
            car_dict = self.region_data.iloc[i, 2:].to_dict()
            new_region = Region(region_id, region_type)
            new_region.add_cars_from_config(car_dict, self.tech_data)
            self.regions.append(new_region)

    def run_multi(self):
        self.num_threads = min(self.num_threads, len(self.regions))
        if self.num_threads == 1:
            for region_ctr in range(len(self.regions)):
                self.run(region_ctr)
        else:
            pool = mp.Pool(processes=self.num_threads)

            for region_ctr, region in enumerate(self.regions):
                pool.apply_async(self.run, (region, region_ctr))

            pool.close()
            pool.join()

    def run(self, region_number):
        region = self.regions[region_number]
        print(f'===== Region: {region.id} ({region_number + 1}/{len(self.regions)}) =====')
        region_directory = pathlib.Path(self.save_directory, region.id)
        region_directory.mkdir(parents=True, exist_ok=True)

        for car in region.cars:
            # TODO: simulate car

            # export vehicle csv
            car.export(pathlib.Path(region_directory, car.name))
