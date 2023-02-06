import argparse
from simbev.simbev_class import SimBEV
import simbev.helpers.helpers as helpers
import pathlib


def main():
    parser = argparse.ArgumentParser(description="SimBEV modelling tool for generating timeseries of electric "
                                                 "vehicles.")
    parser.add_argument("config_path", default="scenarios/default/configs/default.cfg", nargs='?',
                        help="Set the config path.")
    p_args = parser.parse_args()

    config_path = pathlib.Path(p_args.config_path)
    simbev_obj, cfg = SimBEV.from_config(config_path)
    simbev_obj.run_multi()

    helpers.export_metadata(simbev_obj, cfg)


if __name__ == "__main__":
    main()
