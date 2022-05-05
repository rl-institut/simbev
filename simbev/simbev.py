import pandas as pd
from region import Region


class SimBEV:
    def __init__(self, region_data: pd.DataFrame, charging_prob_dict,
                 tech_data: pd.DataFrame, config_dict):
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

        # additional parameters
        self.regions = []

        self._add_regions_from_dataframe()

    def _add_regions_from_dataframe(self):
        for i in range(len(self.region_data.index)):
            region_id = self.region_data.iat[i, 0]
            region_type = self.region_data.iat[i, 1]
            car_dict = self.region_data.iloc[i, 2:].to_dict()
            new_region = Region(region_id, region_type)
            new_region.add_cars_from_config(car_dict, self.tech_data)
            self.regions.append(new_region)

    def run(self):
        time = pd.date_range(self.start_date, self.end_data, freq=self.step_size)
        for i in time:
            return


# tests
if __name__ == '__main__':
    region_df = pd.read_csv("scenarios/default_multi/regions.csv", sep=',')
    tech_df = pd.read_csv("scenarios/default_multi/tech_data.csv", sep=',', index_col=0)
    cfg_dict = {'step_size': 15,
                'soc_min': 0.2,
                'rng': 3,
                'eta_cp': 1,
                'start_date': [2022, 5, 6],
                'end_date': [2022, 6, 2],
                'home_private': 0.5,
                'work_private': 0.7,
                }
    s1 = SimBEV(region_df, {}, tech_df, cfg_dict)
    print(s1.regions[0].cars[0].consumption)
