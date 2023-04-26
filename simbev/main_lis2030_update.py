import argparse
from simbev.simbev_class import SimBEV
import simbev.helpers.helpers as helpers
import pathlib
import datetime
import pandas as pd
import copy

scenario_dict = {

    "multi_scenario_run": True,
    "years": [2025, 2030, 2035],
    "run_up_path": "lis_2030_update_input/run_up",
    "scenarios": ["reference"], #, "low_availability", "high_availability", "digital_offers", "parking_management", "hpc"],
    "scenario_paths": {"reference": "lis_2030_update_input/scenarios/1_reference",
                       "low_availability": "lis_2030_update_input/scenarios/2_low_availability",
                       "high_availability": "lis_2030_update_input/scenarios/3_high_availability",
                       "digital_offers": "lis_2030_update_input/scenarios/4_digital_offers",
                       "parking_management": "lis_2030_update_input/scenarios/5_parking_management",
                       "hpc": "lis_2030_update_input/scenarios/6_hpc",
                       }
}


def wrapper(simbev_obj):
    print("---starting wrapper for lis_2030_update---")
    for year in scenario_dict["years"]:
        print("-> Year:", year)

        # read run-up
        run_up_path = pathlib.Path(scenario_dict["run_up_path"], f"regions_{year}.csv")
        run_up = pd.read_csv(
            run_up_path,
            sep=",",
            index_col=0,
        )

        # read tech_data
        tech_data_path = pathlib.Path(scenario_dict["run_up_path"], f"tech_data_{year}.csv")
        tech_data = pd.read_csv(
            tech_data_path,
            sep=",",
            index_col=0,
        )

        for scenario in scenario_dict["scenarios"]:

            home_work_private_path = pathlib.Path(scenario_dict["scenario_paths"][scenario])
            home_work_private = pd.read_csv(
                pathlib.Path(
                    home_work_private_path, f"home_work_private_{year}.csv"
                )
            )
            home_work_private = home_work_private.set_index("region")

            print("-> Scenario:", scenario)
            config_path = pathlib.Path(scenario_dict["scenario_paths"][scenario] + "/configs/default.cfg")

            # change config for run
            simbev_obj_base, cfg = SimBEV.from_config(config_path)
            simbev_obj = copy.deepcopy(simbev_obj_base)
            path_parent = simbev_obj_base.save_directory.parent
            folder_name = simbev_obj_base.save_directory.name
            simbev_obj.save_directory = pathlib.Path(
                path_parent, str(year), folder_name + "_scenario_" + str(scenario)
            )
            print(simbev_obj.save_directory)

            # replace timedependent data (run_up, tech_data, home_work_private) in simbev_obj
            simbev_obj.region_data = run_up
            simbev_obj.tech_data = tech_data
            simbev_obj.home_parking = home_work_private.loc["home", :]
            simbev_obj.work_parking = home_work_private.loc["work", :]
            #simbev_obj.probability_detached_home = home_work_private.loc["probability_detached_home", :]


            #setup simbev_obj
            simbev_obj.setup()

            # run simulation with optional timing
            helpers.timeitlog(simbev_obj.output_options["timing"], simbev_obj.save_directory)(
                simbev_obj.run_multi
            )()

            helpers.export_metadata(simbev_obj, cfg)


def main():
    print(datetime.datetime.now())
    parser = argparse.ArgumentParser(
        description="SimBEV modelling tool for generating timeseries of electric "
        "vehicles."
    )
    parser.add_argument(
        "config_path",
        default="lis_2030_update_input/scenarios/scenario_base/configs/default.cfg",
        nargs="?",
        help="Set the config path.",
    )
    parser.add_argument("--timing", default=False, action="store_true")
    p_args = parser.parse_args()

    config_path = pathlib.Path(p_args.config_path)
    simbev_obj, cfg = SimBEV.from_config(config_path)

    if scenario_dict["multi_scenario_run"]:
        # run analysis for specific parameter
        wrapper(simbev_obj)
    else:
        # run simulation with optional timing
        helpers.timeitlog(simbev_obj.output_options["timing"], simbev_obj.save_directory)(
            simbev_obj.run_multi
        )()

        helpers.export_metadata(simbev_obj, cfg)


if __name__ == "__main__":

    main()