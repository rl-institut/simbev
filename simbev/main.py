from simbev import SimBEV
import pandas as pd
import pathlib
import datetime


def main():
    # TODO: get these and more parameters via argparse and configparser
    scenario_name = "default_multi"
    region_df = pd.read_csv(pathlib.Path("scenarios", scenario_name, "regions.csv"), sep=',')
    tech_df = pd.read_csv(pathlib.Path("scenarios", scenario_name, "tech_data.csv"), sep=',',
                          index_col=0)
    cfg_dict = {'step_size': 15,
                'soc_min': 0.2,
                'rng': 3,
                'eta_cp': 1,
                'start_date': datetime.date(2022, 5, 6),
                'end_date': datetime.date(2022, 6, 2),
                'home_private': 0.5,
                'work_private': 0.7,
                }
    simbev = SimBEV(region_df, {}, tech_df, cfg_dict, scenario_name)
    simbev.run_multi()
    print(simbev.regions[0].cars[0].car_type.name)


if __name__ == '__main__':
    main()
