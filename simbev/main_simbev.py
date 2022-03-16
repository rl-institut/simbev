import simbevMiD

import os
import argparse
import configparser as cp
import datetime as dt
import numpy as np
import pandas as pd
from pathlib import Path
import multiprocessing as mp
import helpers.helpers as helper

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


def run_simbev(region_ctr, region_id, region_data, cfg_dict, charge_prob,
               regions, tech_data, main_path):
    """Run simbev for single region"""
    print(f'===== Region: {region_id} ({region_ctr + 1}/{len(regions)}) =====')

    # set variables from cfg
    stepsize = cfg_dict['stepsize']
    eta_cp = cfg_dict['eta_cp']
    rng = cfg_dict['rng']
    soc_min = cfg_dict['soc_min']
    heating = cfg_dict['heating']
    cooling = cfg_dict['cooling']
    temp_inside = cfg_dict['temp_inside']

    # get temperature timeline
    temperature = pd.read_csv("C:/Users/Tim.Kirschner/python_projects/simbev/simbev/simbev/scenarios"
                              "/Wetterdaten_Berlin.csv", sep=";", skiprows=1)
    temperature = temperature[['date', 'tavg']]
    # get probabilities
    probdata, tseries_purpose, days = simbevMiD.get_prob(
        region_data.RegioStaR7,
        stepsize, cfg_dict['start_date'], cfg_dict['end_date'])

    car_type_list = sorted([t for t in regions.columns if t != 'RegioStaR7'])

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

    # get number of cars
    numcar_list = list(region_data[car_type_list])

    # SOC init value for the first monday
    soc_init = [
        rng.random() ** (1 / 3) * 0.8 + 0.2 if rng.random() < 0.12 else 1
        for _ in range(sum(numcar_list))
    ]
    count_cars = 0

    region_path = main_path.joinpath(str(region_id))
    region_path.mkdir(exist_ok=True)

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
            range_sim = len(tseries_purpose)
            carstatus = np.zeros(int(range_sim))

            car_data = {
                "place": "6_home",
                "status": carstatus,
                "distance": 0,
            }

            # init availability df
            # a = {
            #     "status": 0,
            #     "location": "init",
            #     "distance": 0,
            # }
            # availability = pd.DataFrame(
            #     data=a,
            #     columns=[
            #         "status",
            #         "location",
            #         "distance",
            #     ],
            #     index=[0],
            # )

            soc_start = soc_init[count_cars]

            last_charging_capacity = min(
                simbevMiD.slow_charging_capacity(
                    charge_prob['slow'],
                    '6_home',
                    rng,
                ),
                tech_data_car.max_charging_capacity_slow,
            ) * eta_cp

            # loop for days of the week
            # for key in wd:
            # create availability timeseries and charging times
            (av, car_data, demand,
             soc_start, idx_home,
             idx_work, home_charging_capacity,
             work_charging_capacity) = simbevMiD.availability(
                car_data,
                probdata,
                stepsize,
                tech_data_car.battery_capacity,
                tech_data_car.energy_consumption,
                tech_data_car.max_charging_capacity_slow,
                tech_data_car.max_charging_capacity_fast,
                soc_start,
                car_type,
                charge_prob['slow'],
                charge_prob['fast'],
                idx_home,
                idx_work,
                home_charging_capacity,
                work_charging_capacity,
                last_charging_capacity,
                rng,
                eta_cp,
                soc_min,
                tseries_purpose,
                carstatus,
                cooling,
                heating,
                temp_inside,
                temperature,
            )

            # add results for this day to availability timeseries
            # availability = availability.append(av).reset_index(drop=True)

            # print("Auto Nr. " + str(count) + " / " + str(icar))
            # print(str(home_charging_capacity) + " kW")
            # print(demand.loc[demand.location == "6_home"].netto_charging_capacity)

            # add results for this day to demand time series
            # charging_all = charging_all.append(demand)

            # add results for this day to demand time series for a single car
            charging_car = charging_car.append(demand)
            # print(key, charging_car)

            # last_charging_capacity = charging_car.netto_charging_capacity.iat[-1]
            # print("car" + str(icar) + "done")

            simbevMiD.charging_flexibility(
                charging_car,
                car_type_name,
                icar,
                tech_data_car.battery_capacity,
                rng,
                cfg_dict["home_private"],
                cfg_dict["work_private"],
                eta_cp,
                region_path,
                tseries_purpose,
                days,
                tech_data_car.battery_capacity,
                region_data.RegioStaR7,
            )

        # clean up charging_car

            # drop init row of availability df
        # availability = availability.iloc[1:]
            # save availability df
            # availability.to_csv("res/availability_car" + str(icar) + ".csv")

            count_cars += 1
        if numcar >= 1:
            print(" - done")


def init_simbev(args):
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
    except Exception:
        raise FileNotFoundError(f'Cannot read config file {cfg_file} - malformed?')

    # set number of threads for parallel computation
    num_threads = cfg.getint('sim_params', 'num_threads')

    # set random seed from config or truly random if none is given
    rng_seed = cfg['sim_params'].getint('seed', None)
    rng = np.random.default_rng(rng_seed)

    # set eta cp from config
    eta_cp = cfg.getfloat('basic', 'eta_cp')
    cooling = cfg.getfloat('basic', 'energy_use_cooling'),
    heating = cfg.getfloat('basic', 'energy_use_heating'),
    temp_inside = cfg.getint('basic', 'temp_carinside'),
    heating = float('.'.join(str(ele) for ele in heating))
    cooling = float('.'.join(str(ele) for ele in cooling))
    temp_inside = float('.'.join(str(ele) for ele in temp_inside))
    # get minimum soc value in %
    soc_min = cfg.getfloat('basic', 'soc_min')

    # read chargepoint probabilities
    charge_prob_slow = pd.read_csv(os.path.join(scenario_path, cfg['charging_probabilities']['slow']))
    charge_prob_slow = charge_prob_slow.set_index('destination')
    charge_prob_fast = pd.read_csv(os.path.join(scenario_path, cfg['charging_probabilities']['fast']))
    charge_prob_fast = charge_prob_fast.set_index('destination')
    charge_prob = {'slow': charge_prob_slow,
                   'fast': charge_prob_fast}

    home_private = cfg.getfloat('charging_probabilities', 'private_charging_home', fallback=1.0)
    work_private = cfg.getfloat('charging_probabilities', 'private_charging_work', fallback=1.0)

    # get timestep (in minutes)
    stepsize = cfg.getint('basic', 'stepsize')

    # get start and end date
    start_date = cfg.get('basic', 'start_date')   # kann man so mit isoformat benutzen wenn man python 3.9 hat
    end_date = cfg.get('basic', 'end_date')
    start_date = start_date.split('-')
    s_date = []
    for it in start_date:
        it = int(it)
        s_date.append(it)
    end_date = end_date.split('-')
    e_date = []
    for it in end_date:
        it = int(it)
        e_date.append(it)

    # get output option
    grid_output = cfg.getboolean('basic', 'grid_timeseries', fallback=False)
    uc_output = cfg.getboolean('basic', 'grid_timeseries_by_usecase', fallback=False)

    # combine config params in one dict
    cfg_dict = {'stepsize': stepsize,
                'soc_min': soc_min,
                'rng': rng,
                'eta_cp': eta_cp,
                'start_date': s_date,
                'end_date': e_date,
                'home_private': home_private,
                'work_private': work_private,
                'cooling': cooling,
                'heating': heating,
                'temp_inside': temp_inside,
                }

    # create directory for standing times data
    directory = "res"
    directory = Path(directory)

    # result dir
    timestamp_start = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    result_dir = f'{args.scenario}_{timestamp_start}_simbev_run'

    # path join
    main_path = directory.joinpath(result_dir)

    # make dirs
    main_path.mkdir(exist_ok=True)

    print("Writing to {}".format(main_path))

    # get the region mode (single or multi) and get params
    region_mode = cfg.get('region_mode', 'region_mode')
    if region_mode == 'single':
        if num_threads > 1:
            num_threads = 1
            print('Warning: Single region mode selected, therefore number of threads is set to 1.')

        regions, tech_data = helper.single_to_multi_scenario(
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

    print(f'Running simbev in {num_threads} thread(s)...')
    if num_threads == 1:
        for region_ctr, (region_id, region_data) in enumerate(regions.iterrows()):
            run_simbev(region_ctr, region_id, region_data, cfg_dict, charge_prob,
                       regions, tech_data, main_path)
    else:
        pool = mp.Pool(processes=num_threads)

        for region_ctr, (region_id, region_data) in enumerate(regions.iterrows()):
            pool.apply_async(run_simbev, (region_ctr, region_id, region_data, cfg_dict, charge_prob,
                                          regions, tech_data, main_path))

        pool.close()
        pool.join()

    start = dt.date(s_date[0], s_date[1], s_date[2])
    end = dt.date(e_date[0], e_date[1], e_date[2])

    helper.export_metadata(
        main_path,
        args.scenario,
        cfg,
        tech_data,
        charge_prob_slow,
        charge_prob_fast,
        timestamp_start
    )

    if grid_output:
        helper.compile_output(main_path, start, end, region_mode, cfg_dict["stepsize"])
    if uc_output:
        helper.compile_output_by_usecase(main_path, start, end, region_mode, cfg_dict["stepsize"])


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='SimBEV modelling tool for generating timeseries of electric '
                                                 'vehicles.')
    parser.add_argument('scenario', default="default_single", nargs='?',
                        help='Set the scenario which is located in ./scenarios .')
    p_args = parser.parse_args()
    init_simbev(p_args)
