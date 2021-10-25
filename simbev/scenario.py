import pandas as pd
from simbev import car
from region import Region


class Scenario:
    def __init__(self, charging_prob_dict, region_list=[]):
        self.charging_prob = charging_prob_dict
        self.regions = region_list

    def add_regions_from_dataframe(self, regions: pd.DataFrame, tech_data: pd.DataFrame):
        for i in range(len(regions.index)):
            region_id = regions.iat[i, 0]
            region_type = regions.iat[i, 1]
            car_dict = regions.iloc[i, 2:].to_dict()
            new_region = Region(region_id, region_type)
            new_region.add_cars_from_config(car_dict, tech_data)
            self.regions.append(new_region)


# tests
if __name__ == '__main__':
    region_df = pd.read_csv("regions.csv", sep=',')
    tech_data = pd.read_csv("tech_data.csv", sep=',', decimal='.', index_col=0)
    s1 = Scenario({})
    s1.add_regions_from_dataframe(region_df, tech_data)
    print(s1.regions[0].cars[0].consumption)

