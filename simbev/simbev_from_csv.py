import simbevMiD
import os.path
from pathlib import Path
import pandas as pd
import numpy as np
from numpy.random import default_rng
from datetime import datetime
import gc
import configparser as cp

gc.collect()

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

# read config file
config_file = r"simbev_config_default.cfg"
config_file = Path(config_file)
cfg = cp.RawConfigParser()
cfg.read(config_file)
config_dict = cfg._sections

# set random seed
rng = default_rng(int(config_dict['sim_params']['seed']))

# set number of threads for parallel computation
num_threads = float(config_dict['sim_params']['num_threads'])

# create directory for standing times data
directory = r"res"
directory = Path(directory)

# dir strings
if num_threads > 1:
    # Multi processing calculates datetime.now() multiple times
    # A "hard" path is needed
    date = "final_Reference_2050"  # TODO: set current date
else:
    date = datetime.now().strftime("%Y-%m-%d_%H%M%S")

sub_directory = str(date) + "_simbev_run"

# path joins
main_path = os.path.join(
    directory,
    sub_directory,
)

# make dirs
os.makedirs(
    main_path,
    exist_ok=True,
)


# get timestep (in minutes)
stepsize = float(config_dict['basic']['stepsize'])

# get days for simulation
days = float(config_dict['basic']['days'])

# set list of car types
car_type_list = ['bev_mini', 'bev_medium', 'bev_luxury', 'phev_mini', 'phev_medium', 'phev_luxury']

# read chargepoint probabilities
charge_prob_slow = pd.read_csv(config_dict['charging_probabilities']['slow'], sep=';', decimal=',')
charge_prob_slow = charge_prob_slow.set_index('destination')
charge_prob_fast = pd.read_csv(config_dict['charging_probabilities']['fast'], sep=';', decimal=',')
charge_prob_fast = charge_prob_fast.set_index('destination')

count_dirs = 0

def run_simbev():

    #try:
        # select regio type
        regio_type = config_dict['basic']['regio_type']

        # get probabilities
        probdata, wd = simbevMiD.get_prob(
            regio_type,
            stepsize,
        )

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

        # reduction_factor = reduction_df.reduction_factor.iloc[gem_idx]#.iat[0]
        # print(reduction_factor)

        # get number of cars per Gemeinde
        numcar_list = []
        for cartype in car_type_list:
            numcar_list.append(int(config_dict['rampup_ev'][cartype]))

        #soc init value for the first monday
        SoC_init = [
            rng.random() ** (1 / 3) * 0.8 + 0.2 if rng.random() < 0.12 else 1
            for _ in range(sum(numcar_list))
        ]
        count_cars = 0

        # loop for types of cars
        for count_car_types, idx in enumerate(car_type_list):
            bat_cap = float(config_dict['tech_data_bc'][idx])
            con = float(config_dict['tech_data_ec'][idx])
            chargepower_slow = float(config_dict['tech_data_cc_slow'][idx])
            chargepower_fast = float(config_dict['tech_data_cc_fast'][idx])
            numcar = numcar_list[count_car_types]
            # print(idx)

            if idx.find("bev") is not -1:
                car_type = "BEV"
            else:
                car_type = "PHEV"

            # loop for number of cars
            for icar in range(numcar):
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
                    chargepower_slow,
                ) * float(config_dict['basic']['eta_cp'])

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
                        bat_cap,
                        con,
                        chargepower_slow,
                        chargepower_fast,
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
                        float(config_dict['basic']['eta_cp']),
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

                # Export timeseries for each car
                simbevMiD.charging_flexibility(
                    charging_car,
                    idx,
                    icar,
                    stepsize,
                    len(wd),
                    bat_cap,
                    rng,
                    float(config_dict['basic']['eta_cp']),
                    main_path,
                )

                count_cars += 1



        print("Standing times are done!")

        #print(setup_dict["random.seed"])
        gc.collect()


run_simbev()