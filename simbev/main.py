import argparse
import configparser as cp
from simbev_class import SimBEV
import pandas as pd
import pathlib
import helpers.helpers


def main():
    parser = argparse.ArgumentParser(description="SimBEV modelling tool for generating timeseries of electric "
                                                 "vehicles.")
    parser.add_argument("scenario", default="default", nargs='?',
                        help="Set the scenario which is located in ./scenarios .")
    p_args = parser.parse_args()

    scenario_path = pathlib.Path("scenarios", p_args.scenario)
    if not scenario_path.is_dir():
        raise FileNotFoundError(f'Scenario "{p_args.scenario}" not found in ./scenarios .')

    # read config file
    cfg = cp.ConfigParser()
    cfg_file = pathlib.Path(scenario_path, "simbev_config.cfg")
    if not cfg_file.is_file():
        raise FileNotFoundError(f"Config file {cfg_file} not found.")
    try:
        cfg.read(cfg_file)
    except Exception:
        raise FileNotFoundError(f"Cannot read config file {cfg_file} - malformed?")

    region_df = pd.read_csv(pathlib.Path(scenario_path, "regions.csv"), sep=',')

    # read chargepoint probabilities
    charge_prob_slow = pd.read_csv(pathlib.Path(scenario_path, cfg["charging_probabilities"]["slow"]))
    charge_prob_slow = charge_prob_slow.set_index("destination")
    charge_prob_fast = pd.read_csv(pathlib.Path(scenario_path, cfg["charging_probabilities"]["fast"]))
    charge_prob_fast = charge_prob_fast.set_index("destination")
    charge_prob_dict = {"slow": charge_prob_slow,
                        "fast": charge_prob_fast}

    tech_df = pd.read_csv(pathlib.Path(scenario_path, "tech_data.csv"), sep=',',
                          index_col=0)

    start_date = cfg.get("basic", "start_date")
    start_date = helpers.helpers.date_string_to_datetime(start_date)
    end_date = cfg.get("basic", "end_date")
    end_date = helpers.helpers.date_string_to_datetime(end_date)

    cfg_dict = {"step_size": cfg.getint("basic", "stepsize"),
                "soc_min": cfg.getfloat("basic", "soc_min"),
                "rng_seed": cfg["sim_params"].getint("seed", None),
                "eta_cp": cfg.getfloat("basic", "eta_cp"),
                "start_date": start_date,
                "end_date": end_date,
                "home_private": cfg.getfloat("charging_probabilities", "private_charging_home", fallback=1.0),
                "work_private": cfg.getfloat("charging_probabilities", "private_charging_work", fallback=1.0),
                }
    # num_threads = cfg.getint('sim_params', 'num_threads')
    num_threads = 1

    simbev = SimBEV(region_df, charge_prob_dict, tech_df, cfg_dict, p_args.scenario, num_threads)
    simbev.run_multi()
    print(simbev.regions[0].cars[0].car_type.name)


if __name__ == "__main__":
    main()
