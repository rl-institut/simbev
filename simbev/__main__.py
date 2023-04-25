import argparse
from copy import deepcopy
import pathlib
import datetime

from simbev.simbev_class import SimBEV
import simbev.helpers.helpers as helpers


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
    parser.add_argument(
        "-r",
        "--repeat",
        nargs="?",
        default=1,
        type=int,
        help="Decide how often the simulation will be run.",
    )
    p_args = parser.parse_args()

    config_path = pathlib.Path(p_args.config_path)
    simbev_obj, cfg = SimBEV.from_config(config_path)

    if p_args.repeat > 1:
        simbev_list = [None] * p_args.repeat
        for i in range(p_args.repeat):
            simbev_copy = deepcopy(simbev_obj)
            simbev_copy.rng_seed += i
            simbev_copy.rng = simbev_copy.get_rng()
            simbev_copy.save_directory = pathlib.Path(
                simbev_copy.save_directory, f"iteration_{i}"
            )
            simbev_list[i] = simbev_copy
    else:
        simbev_list = [simbev_obj]

    for simbev in simbev_list:
        # setup simbev object
        simbev.setup()
        # run simulation with optional timing
        helpers.timeitlog(simbev.output_options["timing"], simbev_obj.save_directory)(
            simbev.run_multi
        )()

        helpers.export_metadata(simbev, cfg)


if __name__ == "__main__":
    main()
