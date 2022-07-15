import argparse
from simbev.simbev_class import SimBEV
import simbev.helpers.helpers as helpers
import pathlib


def main():
    parser = argparse.ArgumentParser(description="SimBEV modelling tool for generating timeseries of electric "
                                                 "vehicles.")
    parser.add_argument("scenario", default="default", nargs='?',
                        help="Set the scenario which is located in ./scenarios .")
    p_args = parser.parse_args()

    scenario_path = pathlib.Path("simbev", "scenarios", p_args.scenario)
    simbev_obj, cfg = SimBEV.from_config(scenario_path)
    simbev_obj.run_multi()

    helpers.export_metadata(simbev_obj, cfg)


if __name__ == "__main__":
    main()
