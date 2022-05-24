import argparse
from simbev_class import SimBEV
import helpers.helpers


def main():
    parser = argparse.ArgumentParser(description="SimBEV modelling tool for generating timeseries of electric "
                                                 "vehicles.")
    parser.add_argument("scenario", default="default", nargs='?',
                        help="Set the scenario which is located in ./scenarios .")
    p_args = parser.parse_args()

    simbev_obj, cfg = SimBEV.from_config(p_args.scenario)
    simbev_obj.run_multi()

    helpers.helpers.export_metadata(simbev_obj, cfg)


if __name__ == "__main__":
    main()
