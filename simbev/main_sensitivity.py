import argparse
from simbev.simbev_class import SimBEV
import simbev.helpers.helpers as helpers
from simbev.sensitivity_analysis import sensitivity_analysis
import pathlib
import datetime
import copy

analysis_dict = {

    "sensitivity_analysis": True,
    "analysis_variable": "tech_data-max_charging_capacity_slow-bev_mini",
    "analysis_values": [11, 22, 50]
}


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

    if analysis_dict["sensitivity_analysis"]:
        # run analysis for specific parameter
        sensitivity_analysis(simbev_obj, cfg, analysis_dict)
    else:
        # run simulation with optional timing
        helpers.timeitlog(simbev_obj.output_options["timing"], simbev_obj.save_directory)(
            simbev_obj.run_multi
        )()

        helpers.export_metadata(simbev_obj, cfg)


if __name__ == "__main__":

    main()
