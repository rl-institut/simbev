import pandas as pd
from simbev import car
from region import Region


class Scenario:
    def __init__(self, tech_data: pd.DataFrame, charging_prob_dict, region_list=[]):
        self.tech_data = tech_data
        self.charging_prob = charging_prob_dict
        self.regions = region_list

    def add_regions_from_dataframe(self, regions: pd.DataFrame):
        for i in range(len(regions.index)):
            region_id = regions.iat[i, 0]
            region_type = regions.iat[i, 1]
            car_dict = regions.iloc[i, 2:].to_dict()
            new_region = Region(region_id, region_type, car_dict)
            self.regions.append(new_region)


# tests
if __name__ == '__main__':
    region_df = pd.read_csv("regions.csv", sep=',')
    s1 = Scenario(pd.DataFrame(), {})
    s1.add_regions_from_dataframe(region_df)
    print(s1.regions)

