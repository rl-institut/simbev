import simbevMiD

import os
import argparse
import configparser as cp
from datetime import datetime
import numpy as np
import pandas as pd
from pathlib import Path
from helpers.helpers import single_to_multi_scenario


# regiotypes:
# Ländliche Regionen
# LR_Klein - Kleinstädtischer, dörflicher Raum
# LR_Mitte - Mittelstädte, städtischer Raum
# LR_Zentr - Zentrale Stadt
# Stadtregionen
# SR_Klein - Kleinstädtischer, dörflicher Raum
# SR_Mitte - Mittelstädte, städtischer Raum
# SR_Gross - Regiopolen, Großstädte
# SR_Metro - Metropole


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='SimBEV modelling tool for generating timeseries of electric '
                                                 'vehicles.')
    parser.add_argument('scenario', default="default_single", nargs='?', help='Set the scenario which is located in ./scenarios .')
    args = parser.parse_args()

    # check if scenario exists
    scenario_path = os.path.join('.', 'scenarios', args.scenario)
    if not os.path.isdir(scenario_path):
        raise FileNotFoundError(f'Scenario "{args.scenario}" not found in ./scenarios .')

    # read config file
    cfg = cp.ConfigParser()
    cfg_file = os.path.join(scenario_path, 'simbev_config.cfg')
    if not os.path.isfile(cfg_file):
        raise FileNotFoundError(f'Config file {cfg_file} not found.')
    try:
        cfg.read(cfg_file)
    except:
        raise FileNotFoundError(f'Cannot read config file {cfg_file} - malformed?')

    # set number of threads for parallel computation
    num_threads = cfg.getfloat('sim_params', 'num_threads')

    # create directory for standing times data
    directory = "res"
    directory = Path(directory)

    # dir strings
    if num_threads > 1:
        # Multi processing calculates datetime.now() multiple times
        # A "hard" path is needed
        date = args.scenario
    else:
        date = f'{args.scenario}_{datetime.now().strftime("%Y-%m-%d_%H%M%S")}'

    sub_directory = str(date) + "_simbev_run"

    # path joins
    main_path = directory.joinpath(sub_directory)

    # make dirs
    main_path.mkdir(exist_ok=True)

    print("Writing to {}".format(main_path))

    # get timestep (in minutes)
    stepsize = cfg.getint('basic', 'stepsize')

    # get days for simulation
    days = cfg.getfloat('basic', 'days')

    # get minimum soc value in %
    soc_min = cfg.getfloat('basic', 'soc_min')

    # read chargepoint probabilities
    charge_prob_slow = pd.read_csv(os.path.join(scenario_path, cfg['charging_probabilities']['slow']))
    charge_prob_slow = charge_prob_slow.set_index('destination')
    charge_prob_fast = pd.read_csv(os.path.join(scenario_path, cfg['charging_probabilities']['fast']))
    charge_prob_fast = charge_prob_fast.set_index('destination')

    # set random seed from config or truly random if none is given
    rng_seed = cfg['sim_params'].getint('seed', None)
    rng = np.random.default_rng(rng_seed)

    # init charging demand df
    ca = {
        "location": "init",
        "SoC": 0,
        "chargingdemand": 0,
        "charge_time": 0,
        "charge_start": 0,
        "charge_end": 0,
        "netto_charging_capacity": 0,
        "consumption": 0,
        "drive_start": 0,
        "drive_end": 0,
    }

    columns = [
        "location",
        "SoC",
        "chargingdemand",
        "charge_time",
        "charge_start",
        "charge_end",
        "netto_charging_capacity",
        "consumption",
        "drive_start",
        "drive_end",
    ]

    charging_all = pd.DataFrame(
        data=ca,
        columns=columns,
        index=[0],
    )

    # get the region mode (single or multi) and get params
    region_mode = cfg.get('region_mode', 'region_mode')
    if region_mode == 'single':
        regions, tech_data = single_to_multi_scenario(
            region_type=cfg.get('basic', 'regio_type'),
            rampup=dict(cfg['rampup_ev']),
            max_charging_capacity_slow=dict(cfg['tech_data_cc_slow']),
            max_charging_capacity_fast=dict(cfg['tech_data_cc_fast']),
            battery_capacity=dict(cfg['tech_data_bc']),
            energy_consumption=dict(cfg['tech_data_ec'])
        )
    elif region_mode == 'multi':
        # load region data
        regions = pd.read_csv(os.path.join(scenario_path, cfg.get('rampup_ev', 'rampup'))).set_index('region_id')
        tech_data = pd.read_csv(os.path.join(scenario_path, cfg.get('tech_data', 'tech_data'))).set_index('type')
    else:
        raise ValueError('Invalid value for parameter "region_mode" in config, please use "single" or "multi".')

    car_type_list = sorted([t for t in regions.columns if t != 'RegioStaR7'])

    # run for each region
    for region_ctr, (region_id, region_data) in enumerate(regions.iterrows()):
        print(f'===== Region: {region_id} ({region_ctr+1}/{len(regions)}) =====')

        # get probabilities
        probdata, wd = simbevMiD.get_prob(
            region_data.RegioStaR7,
            stepsize,
        )

        # get number of cars
        numcar_list = list(region_data[car_type_list])

        # SOC init value for the first monday
        SoC_init = [
            rng.random() ** (1 / 3) * 0.8 + 0.2 if rng.random() < 0.12 else 1
            for _ in range(sum(numcar_list))
        ]
        count_cars = 0

        # loop for types of cars
        for idx, car_type_name in enumerate(car_type_list):
            tech_data_car = tech_data.loc[car_type_name]
            numcar = numcar_list[idx]

            if "bev" in car_type_name:
                car_type = "BEV"
            else:
                car_type = "PHEV"

            # loop for number of cars
            for icar in range(numcar):
                print("\r{}% {} {} / {}".format(
                    round((count_cars + 1) * 100 / sum(numcar_list)),
                    car_type_name,
                    (icar + 1), numcar
                ), end="", flush=True)
                charging_car = pd.DataFrame(
                    data=ca,
                    columns=columns,
                    index=[0],
                )
                # print(icar)
                # indices to ensure home and work charging capacity does not alternate
                idx_home = 0
                idx_work = 0
                home_charging_capacity = 0
                work_charging_capacity = 0

                # init data for car status
                range_day = int(1440 / stepsize)
                carstatus = np.zeros(int(range_day / 2))
                carstatus[:int(range_day / 4)] = 2
                car_data = {
                    "place": "6_home",
                    "status": carstatus,
                    "distance": 0,
                }

                # init availability df
                a = {
                    "status": 0,
                    "location": "init",
                    "distance": 0,
                }
                availability = pd.DataFrame(
                    data=a,
                    columns=[
                        "status",
                        "location",
                        "distance",
                    ],
                    index=[0],
                )

                soc_start = SoC_init[count_cars]

                last_charging_capacity = min(
                    simbevMiD.slow_charging_capacity(
                        charge_prob_slow,
                        '6_home',
                        rng,
                    ),
                    tech_data_car.max_charging_capacity_slow,
                ) * cfg.getfloat('basic', 'eta_cp')

                # loop for days of the week
                for key in wd:
                    # create availability timeseries and charging times
                    (av, car_data, demand,
                     soc_start, idx_home,
                     idx_work, home_charging_capacity,
                     work_charging_capacity) = simbevMiD.availability(
                        car_data,
                        key,
                        probdata,
                        stepsize,
                        tech_data_car.battery_capacity,
                        tech_data_car.energy_consumption,
                        tech_data_car.max_charging_capacity_slow,
                        tech_data_car.max_charging_capacity_fast,
                        soc_start,
                        car_type,
                        charge_prob_slow,
                        charge_prob_fast,
                        idx_home,
                        idx_work,
                        home_charging_capacity,
                        work_charging_capacity,
                        last_charging_capacity,
                        rng,
                        cfg.getfloat('basic','eta_cp'),
                        soc_min,
                    )
                    # add results for this day to availability timeseries
                    availability = availability.append(av).reset_index(drop=True)

                    # print("Auto Nr. " + str(count) + " / " + str(icar))
                    # print(str(home_charging_capacity) + " kW")
                    # print(demand.loc[demand.location == "6_home"].netto_charging_capacity)

                    # add results for this day to demand time series
                    charging_all = charging_all.append(demand)

                    # add results for this day to demand time series for a single car
                    charging_car = charging_car.append(demand)
                    # print(key, charging_car)

                    last_charging_capacity = charging_car.netto_charging_capacity.iat[-1]
                    # print("car" + str(icar) + "done")

                # clean up charging_car

                # drop init row of availability df
                availability = availability.iloc[1:]
                # save availability df
                # availability.to_csv("res/availability_car" + str(icar) + ".csv")

                region_path = main_path.joinpath(str(region_id))
                region_path.mkdir(exist_ok=True)

                # Export timeseries for each car
                simbevMiD.charging_flexibility(
                    charging_car,
                    car_type_name,
                    icar,
                    stepsize,
                    len(wd),
                    tech_data_car.battery_capacity,
                    rng,
                    cfg.getfloat('basic','eta_cp'),
                    region_path,
                )

                count_cars += 1
            if numcar > 1:
                print(" - done")
