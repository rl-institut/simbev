import argparse
from simbev.simbev_class import SimBEV
import simbev.helpers.helpers as helpers
import pathlib
import datetime
import copy

scenario_dict = {

    "multi_scenario_run": True,
    "years": [2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2035],
    "scenarios": ["reference", "low_availability", "high_availability", "digital_offers", "parking_management", "hpc"],
    "scenario_paths": {"reference": "scenarios/default/configs/default.cfg",
                       "low_availability": "scenarios/default/configs/default.cfg",
                       "high_availability": "scenarios/default/configs/default.cfg",
                       "digital_offers": "scenarios/default/configs/default.cfg",
                       "parking_management": "scenarios/default/configs/default.cfg",
                       "hpc": "scenarios/default/configs/default.cfg",
                       }
}


def wrapper():
    print("---starting wrapper for lis_2030_update---")
    for year in scenario_dict["years"]:
        print(year)

        for scenario in scenario_dict["scenarios"]:

            print(scenario)
            config_path = pathlib.Path(scenario_dict["scenario_paths"][scenario])

            # run simbev here as module

            simbev_obj, cfg = SimBEV.from_config(config_path)

            path_parent = simbev_obj.save_directory.parent
            folder_name = simbev_obj.save_directory.name
            simbev_obj.save_directory = pathlib.Path(
                path_parent, str(year), folder_name + "_scenario_" + str(scenario)
            )
            print(simbev_obj.save_directory)

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
        default="scenarios/default/configs/default.cfg",
        nargs="?",
        help="Set the config path.",
    )
    parser.add_argument("--timing", default=False, action="store_true")
    p_args = parser.parse_args()

    config_path = pathlib.Path(p_args.config_path)
    simbev_obj, cfg = SimBEV.from_config(config_path)

    if scenario_dict["multi_scenario_run"]:
        # run analysis for specific parameter
        wrapper()
    else:
        # run simulation with optional timing
        helpers.timeitlog(simbev_obj.output_options["timing"], simbev_obj.save_directory)(
            simbev_obj.run_multi
        )()

        helpers.export_metadata(simbev_obj, cfg)


if __name__ == "__main__":

    main()