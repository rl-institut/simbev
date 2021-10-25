import pandas as pd
from simbev import car


class Scenario:
    def __init__(self, regions: pd.DataFrame):
        self.regions = regions
        self.region_count = len(regions.index)


if __name__ == '__main__':
    region_list = pd.DataFrame()
    s1 = Scenario(region_list)
    s1.run('H', '2017-1-1', '2018-1-1')
