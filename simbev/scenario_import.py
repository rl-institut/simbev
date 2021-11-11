# -----------------------------------------------------------
# change elmobile scenario csv to SimBEV required format
#
# author: Moritz
# -----------------------------------------------------------
import pandas as pd
from pathlib import Path


DISTRIBUTION = {
    "mini": 0.53,
    "medium": 0.25,
    "luxury": 0.22
}

CARTYPES = ["bev_mini", "bev_medium", "bev_luxury", "phev_mini", "phev_medium", "phev_luxury"]


def scenario_from_csv(path, scenario_name: str, v2g=False):
    """Changes Elmobile scenario csv to SimBEV required format.

    Parameters
    ----------
    path            --  path to input csv
    scenario_name   --  subdirectory of /scenarios that the result gets saved to
    """

    scenario_path = Path("scenarios", scenario_name)
    scenario_path.mkdir(exist_ok=True)
    if v2g:
        df = pd.read_csv(path, sep=";", usecols=[0, 2, 3, 4])
        df["RegioStaR7"] = "SR_Metro"
        df_v2g = pd.DataFrame(df[["PLZ", "V2G"]])
        df_v2g.to_csv(Path(scenario_path, "v2g_per_region.csv"), sep=";", index=False)
        df.drop(columns="V2G", inplace=True)
        for car in CARTYPES:
            car_vals = car.split("_")
            df.insert(len(df.columns), car,
                      pd.Series(df[car_vals[0].upper()] * DISTRIBUTION[car_vals[1]], dtype=int))
    else:
        df = pd.read_csv(path, sep=";", usecols=[0, 2, 3])
        df["RegioStaR7"] = "SR_Metro"
        for car in CARTYPES:
            car_vals = car.split("_")
            df.insert(len(df.columns), car,
                      pd.Series(df[car_vals[0].upper()] * DISTRIBUTION[car_vals[1]], dtype=int))

    df.drop(columns="BEV", inplace=True)
    df.drop(columns="PHEV", inplace=True)
    df.rename(columns={'PLZ': 'region_id'}, inplace=True)
    df.to_csv(Path(scenario_path, "regions.csv"), sep=",", index=False)


if __name__ == "__main__":
    scenario_from_csv("input_szenario1.csv", "elmobile_scenario_1", True)
