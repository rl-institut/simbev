import pandas as pd
import os.path
import numpy as np
from pathlib import Path
import math

# # debug warnings
# import warnings
# warnings.filterwarnings('error')


def get_prob(
        regioname,
        stepsize,
):
    destinations = [
        "time",
        "0_work",
        "1_business",
        "2_school",
        "3_shopping",
        "4_private/ridesharing",
        "5_leisure",
        "6_home",
    ]
    str_stepsize = str(stepsize) + "min"
    folder_name = os.path.join("data")
    subfolder_name = Path(folder_name + "/" + regioname)
    purpose = dict()
    speed = dict()
    distance = dict()
    stand = dict()
    start = dict()
    wd = []
    files = os.listdir(subfolder_name)
    files.sort()
    for file in files:
        file_name = Path(folder_name + "/" + regioname + "/" + file)
        if file.find("start") is not -1:
            day_key = file[:file.index("y") + 1]
            tp = pd.read_csv(
                file_name,
                sep=",",
                decimal=".",
                names=[
                    "time",
                    "trips",
                ],
                index_col=["time"],
                skiprows=1,
                parse_dates=True,
            )
            tp_stepsize = tp.resample(str_stepsize).sum()
            tp_prob = tp_stepsize / tp_stepsize.sum()
            # Normierung
            tp_norm = tp_prob / tp_prob.max()
            tp_norm = pd.DataFrame(
                data=tp_norm,
                columns=["trips"]
            )
            start[day_key] = tp_norm
            wd.append(day_key)

        if file.find("purpose") is not -1:
            day_key = file[:file.index("y") + 1]
            tp = pd.read_csv(
                file_name,
                sep=",",
                decimal=".",
                names=destinations,
                index_col=["time"],
                skiprows=1,
                parse_dates=True,
            )
            tp_stepsize = tp.resample(str_stepsize).sum()
            purpose[day_key] = tp_stepsize

        if file.find("speed") is not -1:
            ts = pd.read_csv(
                file_name,
                sep=",",
                decimal="."
            )
            for i, c in enumerate(file):
                if c.isdigit():
                    idx = i
                    break
            purp_key = file[idx:file.index(".")]
            if purp_key == "41_private":
                purp_key = "4_private/ridesharing"
            speed[purp_key] = ts
        if file.find("distance") is not -1:
            td = pd.read_csv(file_name, sep=",", decimal=".")
            for i, c in enumerate(file):
                if c.isdigit():
                    idx = i
                    break
            purp_key = file[idx:file.index(".")]
            if purp_key == "41_private":
                purp_key = "4_private/ridesharing"
            distance[purp_key] = td
        if file.find("stand") is not -1:
            tst = pd.read_csv(file_name, sep=",", decimal=".")
            for i, c in enumerate(file):
                if c.isdigit():
                    idx = i
                    break
            purp_key = file[idx:file.index(".")]
            if purp_key == "41_private":
                purp_key = "4_private/ridesharing"
            stand[purp_key] = tst
        if file.find("charge") is not -1:
            charge = pd.read_csv(file_name, sep=";", decimal=",")

    probdata = {
        "start": start,
        "purpose": purpose,
        "speed": speed,
        "distance": distance,
        "stay": stand,
        "charge": charge,
    }

    wd = sorted(wd, key=lambda x: int("".join([r for r in x if r.isdigit()])))
    return probdata, wd


def get_purpose(
        probability,
        ix,
        rng,
):
    x = probability.iloc[ix]
    y = x / x.sum()
    # folding

    for n in range(len(y) - 1):
        y[n + 1] = y[n + 1] + y[n]


    random_number = rng.random()

    purp_temp = (random_number < y).sum()
    purp_num = len(y) - purp_temp
    keys_purp = y.index
    try:
        purp_key = keys_purp[purp_num]
    except IndexError:
        breakpoint()

    return purp_key


def availability(
        cardata,
        daykey,
        probdata,
        stepsize,
        batcap,
        con,
        chargepower_slow,
        chargepower_fast,
        soc_start,
        car_type,
        charge_prob_slow,
        charge_prob_fast,
        # indices to ensure home and work charging capacity does not alternate
        idx_home,
        idx_work,
        home_charging_capacity,
        work_charging_capacity,
        last_charging_capacity,
        rng,
        eta,
):

    day_mins = 1440
    range_day = day_mins / stepsize
    # get data from MiD
    s = probdata["stay"]
    d = probdata["distance"]
    sp = probdata["speed"]
    ch = probdata["charge"]
    st = probdata["start"]
    # probability for trip purpose depending on weekday
    p_all = probdata["purpose"]
    p = p_all[daykey]
    # init car_status, 1,5 days for trips over 24h
    car_status = np.zeros(int(range_day) + int(range_day / 2))
    # rule: before 5:00 no trips, will be changed when trips are implemented over 24 h
    car_status[:int(range_day / 2)] = cardata["status"]

    # first location of the day: the end location of the previous day, on Monday: 6_home
    p_now = cardata["place"]
    # first distance of the day: the last distance of the previous day
    distance = cardata["distance"]
    # init location/purpose list
    purp_list = [p_now]
    # init distance list
    distance_list = []
    # init distance list with unique values
    distance_unique = []
    # init speed list
    speed_list = []
    # init place/location list
    place_list = []
    # init charge time list
    ch_time = []
    # init list for start times of charging
    ch_start = []
    # init list of end times of charging
    ch_end = []
    # init list charging capacity
    ch_capacity = []
    # init list of start times for driving
    dr_start = []
    # init list of end times for driving
    dr_end = []
    # init first drive question
    firstdrive = 1
    # init soc
    soc_list = [soc_start]
    # init consumption
    consumption = []
    # init demandlist
    demand = []
    # init break_key
    break_key = 0
    # day number
    if daykey[1] == "_":
        day_num = int(daykey[:1]) - 1
    else:
        if daykey[2] == "_":
            day_num = int(daykey[:2]) - 1
        else:
            day_num = int(daykey[:3]) - 1


    # loop minutes per day
    for im in range(int(range_day)):
        # print("timestep: " + str(im))
        # get the current purpose of the car
        p_now = purp_list[-1]
        # set purpose to driving and add distance to list
        if car_status[im] == 3:
            p_now = "driving"
            distance_list.append(distance)
        else:
            distance_list.append(0)
        # get start probabilities
        st_day = st[daykey]
        st_day = st_day["trips"]
        st_now = st_day.iloc[im]

        # get car status
        go = car_status[im]

        # add current purpose to place list
        place_list.append(p_now)
        # car can only start with a new trip when status is 0
        if go == 0:
            # get random probability between 0 and 1 for start
            random_number = rng.random()
            if random_number < st_now:
                # specific behavior for first trip
                if firstdrive == 1:
                    ch_start.append(1)
                    ch_end.append(im)
                    ch_time.append(im)
                    consumption.append(0)
                    demand.append(0)
                    dr_start.append(0)
                    dr_end.append(0)
                    firstdrive = 0
                    ch_capacity.append(last_charging_capacity)

                # get purpose for the new trip
                if p.iloc[im].sum() == 0.0:
                    car_status[im] = car_status[im - 1]
                    continue
                p_now = get_purpose(
                    p,
                    im,
                    rng,
                )
                origin = place_list[-1]

                # business trips allowed only from work
                if p_now == "1_business" and origin != "0_work":
                    car_status[im] = car_status[im - 1]
                    continue

                # same purpose twice in a row is not allowed
                destination = p_now
                if origin == destination:
                    p_now = get_purpose(
                        p,
                        im,
                        rng,
                    )
                    destination = p_now
                    if origin == destination:
                        car_status[im] = car_status[im - 1]
                        continue

                # print("purpose done: " + p_now)

                # get distance for new trip
                distance_range = d[p_now]
                population_dis = distance_range["distance"].tolist()
                weights_dis = distance_range["distribution"].tolist()
                weights_sum = sum(weights_dis)
                weights_dis = [
                    dis / weights_sum for dis in weights_dis
                ]
                distance = 0
                while 2 > distance:  # or distance > 1000:
                    distance = rng.choice(
                        population_dis,
                        p=weights_dis,
                    )
                distance_unique.append(distance)
                # print("distance done: " + str(distance))

                # get speed for new trip
                speed_range = sp[p_now]
                # init speed
                speed = 0
                population_sp = speed_range["speed"].tolist()
                weights_sp = speed_range["distribution"].tolist()
                weights_sum = sum(weights_sp)
                weights_sp = [
                    dis / weights_sum for dis in weights_sp
                ]

                drivetime = 0
                # minimum speed with car 5 km/h and maximum driving hours: 4
                while speed < 5 or drivetime > 240:
                    speed = rng.choice(
                        population_sp,
                        p=weights_sp,
                    )
                    drivetime = (distance / speed) * 60

                drivetime = math.ceil(drivetime / stepsize)
                speed_list.append(speed)
                # print("speed done: " + str(speed))

                # get time to stay at new trip destination
                staytime_range = s[p_now]
                population_st = staytime_range["stand"].tolist()
                weights_st = staytime_range["distribution"].tolist()
                weights_sum = sum(weights_st)
                weights_st = [
                    dis / weights_sum for dis in weights_st
                ]
                staytime = 0
                # rule: staytime has to be over 5 minutes
                while staytime < 5:
                    staytime = rng.choice(
                        population_st,
                        p=weights_st,
                    )
                    staytime = int(staytime * 60)
                staytime = math.ceil(staytime / stepsize)
                # print("staytime done: " + str(staytime))

                driveconsumption = distance * con
                range_remaining = (soc_list[-1] * batcap) / con

                # fast charging events for longer distances
                bat_range = ((1 - 0.1) * batcap)/con
                if distance > bat_range and car_type == 'BEV':
                    #print('Fast Charging')
                    range_remaining = (soc_list[-1]*batcap)/con
                    if range_remaining < 20:
                        fastcharge = min(
                            fast_charging_capacity(
                                charge_prob_fast,
                                distance,
                                rng,
                            ),
                            chargepower_fast,
                        ) * eta
                        # fastcharging for 15 minutes
                        chen = min(((15 / 60) * fastcharge), ((0.8 - soc_list[-1]) * batcap))
                        ch_time.append(1)
                        ch_capacity.append(fastcharge)
                        demand.append(chen)
                        soc = soc_list[-1] + (chen / batcap)
                        soc_list.append(soc)
                        place_list.append("7_charging_hub")
                        purp_list.append("7_charging_hub")
                        dr_start.append(0)
                        dr_end.append(0)
                        consumption.append(0)
                        charge_start = im + 1
                        ch_start.append(charge_start)
                        ch_end.append(charge_start + 1)
                        car_status[charge_start-1] = 2
                        im = charge_start + 1

                    # driving for the rest of the current batcap/soc
                    range_remaining = (soc_list[-1] * batcap) / con
                    # driving until range remaining is 20 km
                    distance_stop = range_remaining - 20
                    distance_remaining = distance - distance_stop
                    drivetime = (distance_stop / speed) * 60
                    drivetime = math.ceil(drivetime / stepsize)
                    driveconsumption = distance_stop * con
                    purp_list.append("driving")
                    # get timesteps for car status of driving
                    drive_start = im + 1
                    drive_end = int(drive_start + drivetime)
                    dr_start.append(drive_start)
                    dr_end.append(drive_end)
                    consumption.append(driveconsumption)
                    soc = soc_list[-1] - (driveconsumption / batcap)
                    soc_list.append(soc)
                    ch_start.append(0)
                    ch_end.append(0)
                    ch_time.append(0)
                    ch_capacity.append(0)
                    demand.append(0)
                    car_status[drive_start - 1:drive_end] = 3
                    im = drive_end

                    # fast charging
                    fastcharge = min(
                        fast_charging_capacity(
                            charge_prob_fast,
                            distance,
                            rng,
                        ),
                        chargepower_fast,
                    ) * eta
                    # fastcharging for 15 minutes
                    chen = min(((15 / 60) * fastcharge), ((0.8 - soc_list[-1]) * batcap))
                    ch_time.append(1)
                    ch_capacity.append(fastcharge)
                    demand.append(chen)
                    soc = soc_list[-1] + (chen / batcap)
                    soc_list.append(soc)
                    place_list.append("7_charging_hub")
                    purp_list.append("7_charging_hub")
                    dr_start.append(0)
                    dr_end.append(0)
                    consumption.append(0)
                    charge_start = im + 1
                    ch_start.append(charge_start)
                    ch_end.append(charge_start + 1)
                    car_status[charge_start-1] = 2
                    im = charge_start + 1

                    # calculate remainig charging events for the rest of the distance
                    range_bat = (soc_list[-1] * batcap) / con
                    range_bat = range_bat - 20
                    num_stops = math.floor(distance_remaining/range_bat)
                    distance_stop = range_bat
                    for stops in range(num_stops):

                        # driving
                        drivetime = (distance_stop / speed) * 60
                        drivetime = math.ceil(drivetime / stepsize)
                        driveconsumption = distance_stop * con
                        purp_list.append("driving")
                        # get timesteps for car status of driving
                        drive_start = im + 1
                        drive_end = int(drive_start + drivetime)
                        dr_start.append(drive_start)
                        dr_end.append(drive_end)
                        consumption.append(driveconsumption)
                        soc = soc_list[-1] - (driveconsumption / batcap)
                        soc_list.append(soc)
                        ch_start.append(0)
                        ch_end.append(0)
                        ch_time.append(0)
                        ch_capacity.append(0)
                        demand.append(0)
                        if drive_end > len(car_status):
                            drive_end = len(car_status)
                            car_status[drive_start-2:drive_end] = 3
                            im = drive_end
                            break
                        car_status[drive_start-2:drive_end] = 3
                        im = drive_end

                        # fast charging
                        fastcharge = min(
                            fast_charging_capacity(
                                charge_prob_fast,
                                distance,
                                rng,
                            ),
                            chargepower_fast,
                        ) * eta
                        # fastcharging for 15 minutes
                        chen = min(((15 / 60) * fastcharge), ((0.8 - soc_list[-1]) * batcap))
                        ch_time.append(1)
                        ch_capacity.append(fastcharge)
                        demand.append(chen)
                        soc = soc_list[-1] + (chen / batcap)
                        soc_list.append(soc)
                        place_list.append("7_charging_hub")
                        purp_list.append("7_charging_hub")
                        dr_start.append(0)
                        dr_end.append(0)
                        consumption.append(0)
                        charge_start = im + 1
                        ch_start.append(charge_start)
                        ch_end.append(charge_start + 1)
                        if charge_start > len(car_status):
                            charge_start = len(car_status)
                            car_status[charge_start] = 2
                            break
                        car_status[charge_start-1] = 2
                        im = charge_start + 1

                        # update values
                        distance_remaining = distance_remaining - distance_stop

                    distance = distance_remaining

                if im == len(car_status):
                    continue

                # fast charging event when next trip cannot be done with current soc
                if range_remaining < distance and car_type == 'BEV':
                    # driving for 15 minutes to the charging hub
                    drivetime = int(rng.choice(15, 1))
                    distance_stop = (drivetime/60) * speed
                    drivetime = math.ceil(drivetime / stepsize)
                    driveconsumption = distance_stop * con
                    purp_list.append("driving")
                    # get timesteps for car status of driving
                    drive_start = im + 1
                    drive_end = int(drive_start + drivetime)
                    dr_start.append(drive_start)
                    dr_end.append(drive_end)
                    consumption.append(driveconsumption)
                    soc = soc_list[-1] - (driveconsumption / batcap)
                    soc_list.append(soc)
                    ch_start.append(0)
                    ch_end.append(0)
                    ch_time.append(0)
                    ch_capacity.append(0)
                    demand.append(0)
                    if drive_end > len(car_status):
                        drive_end = len(car_status)
                        car_status[drive_start-1:drive_end] = 3
                        im = drive_end
                        continue
                    car_status[drive_start - 1:drive_end] = 3
                    im = drive_end

                    #charging
                    fastcharge = min(
                        fast_charging_capacity(
                            charge_prob_fast,
                            distance,
                            rng,
                        ),
                        chargepower_fast,
                    ) * eta
                    # fastcharging for 15 minutes
                    chen = min(((15 / 60) * fastcharge), ((0.8 - soc_list[-1]) * batcap))
                    ch_time.append(1)
                    ch_capacity.append(fastcharge)
                    demand.append(chen)
                    soc = soc_list[-1] + (chen / batcap)
                    soc_list.append(soc)
                    soc_list.append(soc_list[-1])
                    ch_time.append(0)
                    demand.append(0)
                    consumption.append(0)
                    place_list.append("7_charging_hub")
                    purp_list.append("7_charging_hub")
                    dr_start.append(0)
                    dr_end.append(0)
                    charge_start = im + 1
                    ch_start.append(charge_start)
                    ch_end.append(charge_start + 1)
                    if charge_start > len(car_status):
                        charge_start = len(car_status)
                        car_status[charge_start] = 2
                        continue
                    car_status[charge_start-1] = 2
                    im = charge_start + 1

                # driving
                driveconsumption = distance * con
                soc = soc_list[-1] - (driveconsumption / batcap)
                if car_type == "PHEV":
                    # SOC can't be negative
                    soc = max(
                        soc,
                        0,
                    )

                drivetime = (distance / speed) * 60
                drivetime = math.ceil(drivetime / stepsize)
                purp_list.append("driving")
                # get timesteps for car status of driving
                drive_start = im + 1
                drive_end = int(drive_start + drivetime)
                dr_start.append(drive_start)
                dr_end.append(drive_end)
                consumption.append(driveconsumption)
                ch_start.append(0)
                ch_end.append(0)
                ch_time.append(0)
                ch_capacity.append(0)
                demand.append(0)
                soc_list.append(soc)
                # status: 3 - driving
                car_status[drive_start - 1:drive_end] = 3

                # get timesteps for parking at destination
                park_start = drive_end + 1
                if park_start <= range_day:
                    # Limit staytime to not fall into the next day if parking
                    # begins before the end of the day
                    staytime = min(
                        staytime,
                        range_day - park_start,
                    )
                    staytime = int(staytime)
                park_end = park_start + staytime
                # add current location
                purp_list.append(p_now)

                # get charging capacity at destination
                if p_now.find("home") is not -1:
                    # make sure home charging capacity stays constant
                    if idx_home == 0:
                        charging_capacity = min(
                            slow_charging_capacity(
                                charge_prob_slow,
                                p_now,
                                rng,
                            ),
                            chargepower_slow,
                        ) * eta
                        home_charging_capacity = charging_capacity
                    else:
                        charging_capacity = home_charging_capacity
                    idx_home += 1
                elif p_now.find("work") is not -1:
                    # make sure work charging capacity stays constant
                    if idx_work == 0:
                        charging_capacity = min(
                            slow_charging_capacity(
                                charge_prob_slow,
                                p_now,
                                rng,
                            ),
                            chargepower_slow,
                        ) * eta
                        work_charging_capacity = charging_capacity
                    else:
                        charging_capacity = work_charging_capacity
                    idx_work += 1
                else:
                    charging_capacity = min(
                        slow_charging_capacity(
                            charge_prob_slow,
                            p_now,
                            rng,
                        ),
                        chargepower_slow,
                    ) * eta

                # if firstdrive == 1:
                #     charging_capacity = last_charging_capacity
                #     firstdrive = 0

                if charging_capacity > 0:
                    # status: 2 - charging
                    car_status[park_start - 1:park_end] = 2
                    chtime = park_end - park_start + 1
                    ch_start.append(park_start)
                    ch_end.append(park_end)
                    ch_capacity.append(charging_capacity)
                    dr_start.append(0)
                    dr_end.append(0)

                    chargetime = chtime * stepsize
                    cap_left = (1 - soc_list[-1]) * batcap
                    fullchargetime = (cap_left / charging_capacity) * 60
                    charge_prob = charging_probability_SoC(
                        soc_list[-1],
                        p_now,
                    )
                    random_number = rng.random()


                    if charge_prob < random_number:
                        soc_list.append(soc_list[-1])
                        ch_time.append(0)
                        demand.append(0)
                        consumption.append(0)
                        continue
                    if fullchargetime > chargetime:
                        soc = soc_list[-1] + (((chargetime / 60) * charging_capacity) / batcap)
                        chen = ((chargetime / 60) * charging_capacity)
                        soc_list.append(soc)
                        demand.append(chen)
                        ch_time.append(chtime)
                        consumption.append(0)
                    else:
                        soc = soc_list[-1] + (cap_left / batcap)
                        chen = cap_left
                        soc_list.append(soc)
                        demand.append(chen)
                        ch_time.append(chtime)
                        consumption.append(0)
                else:
                    # status: 1 - parking
                    car_status[park_start - 1:park_end] = 1
                    ch_start.append(park_start)
                    ch_end.append(park_end)
                    consumption.append(0)
                    dr_start.append(0)
                    dr_end.append(0)
                    ch_time.append(0)
                    ch_capacity.append(0)
                    demand.append(0)
                    soc_list.append(soc_list[-1])


    status_list = car_status[:int(range_day)].tolist()
    status_nextday = car_status[int(range_day):]
    data_availability = list(
        zip(
            status_list,
            place_list,
            distance_list
        )
    )
    # set range for weekdays
    startrange = int(day_num * range_day)
    endrange = int((day_num + 1) * range_day)
    if daykey == "7_sunday":
        ch_end = [int((24 * (60 / stepsize))) if x > (24 * (60 / stepsize)) else x for x in ch_end]
        dr_end = [int((24 * (60 / stepsize))) if x > (24 * (60 / stepsize)) else x for x in dr_end]
    rangeweekday = range(startrange, endrange)
    data_availability = pd.DataFrame(
        data=data_availability,
        columns=[
            "status",
            "location",
            "distance"
        ],
        index=rangeweekday,
    )
    ch_start = [x if x == 0 else x + startrange for x in ch_start]
    ch_end = [x if x == 0 else x + startrange for x in ch_end]
    dr_start = [x if x == 0 else x + startrange for x in dr_start]
    dr_end = [x if x == 0 else x + startrange for x in dr_end]
    cardata["place"] = purp_list[-1]
    cardata["status"] = status_nextday
    cardata["distance"] = distance_list[-1]
    times_energy = list(
        zip(
            purp_list,
            soc_list,
            demand,
            ch_time,
            ch_start,
            ch_end,
            ch_capacity,
            consumption,
            dr_start,
            dr_end,
        )
    )
    times_energy = pd.DataFrame(
        data=times_energy,
        columns=[
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
        ],
    )
    soc_start = soc_list[-1]

    return (data_availability, cardata,
            times_energy, soc_start,
            idx_home, idx_work,
            home_charging_capacity, work_charging_capacity)



# Charging probability depending on SoC
def charging_probability_SoC(
        SoC,
        destination,
        upper_bar=0.95,
        upper_bar_public=0.8,
        lower_bar_public=0.5,
):
    """
    Calculate the probability a car is charged depending on destination and SoC.

    Parameters
    ----------
    SoC : float
        SoC at destination.
    destination : str
        Destination of the trip.
    upper_bar : float
        Soc-Limit over which no charging takes place. Default: 0.95.
    upper_bar_public : float
        SoC-Limit over which no charging takes place at public chargers. Default: 0.8.
    lower_bar_public : float
        SoC-Limit under which a car is always charged if a charging point is present. Default: 0.5.

    Returns
    -------
    probability : float
        Probability that a car is charged at the given destination if a charging point is present.

    """
    # differentiate between public and private charging
    work_home = [
        "0_work",
        "6_home",
    ]

    # difference between the public upper and lower bar
    bar_diff = upper_bar_public - lower_bar_public

    # if SoC is >= upper bar --> no charging takes place
    if SoC >= upper_bar:
        probability = 0
    # if SoC is <= public lower bar --> charge if possible
    elif SoC <= lower_bar_public:
        probability = 1
    else:
        # if the charging point is private --> charge if possible
        if destination in work_home:
            probability = 1
        # if SoC is >= public upper bar --> no charging takes place
        elif SoC >= upper_bar_public:
            probability = 0
        # otherwise linear interpolate the probability
        else:
            probability = -1 / bar_diff * SoC + upper_bar_public / bar_diff

    return probability


# Fix times_energy
# when switching from one day to the next
# Car Charging Times for Flex Charging
def charging_flexibility(
        charging_car,
        car_type,
        car_number,
        stepsize,
        day_count,
        bat_cap,
        rng,
        eta,
        path,
):
    """

    Parameters
    ----------
    charging_car : pandas:`pandas.DataFrame<dataframe>`
        pandas:`pandas.DataFrame<dataframe>` with driving and standing times for a car
    car_type : str
        Car type
    car_number : int
        Number of car in it's car type group
    stepsize : int
        Stepsize of timestamps
    day_count : int
        Number of simulated days
    bat_cap : int
        Battery Capacity of the car type
    directory : str
        Directory with sub-directories. Default: res.
    sub_directory : str
        Sub-directory with the standing times CSVs. Default: SR_Metro.

    """

    # renaming SOC column to SOC_end
    charging_car.rename(
        columns={
            "SoC": "SoC_end"
        },
        inplace=True,
    )

    # creating row with SoC_start
    charging_car["SoC_start"] = charging_car.SoC_end.shift(1)

    # drop init row and init parking without a charging capacity
    charging_car = charging_car.iloc[1:].copy()

    # reset index
    charging_car.reset_index(
        drop=True,
        inplace=True,
    )

    # clean up timestamps
    for row in range(len(charging_car)):
        current_loc = charging_car.loc[row, 'location']
        if row == len(charging_car) - 1:
            break
        next_loc = charging_car.loc[row+1, 'location']
        if next_loc == current_loc:
            val = charging_car.loc[row+1, 'charge_end']
            charging_car.loc[row, 'charge_end'] = val
            charging_car.loc[row+1, 'drop'] = 1

    if 'drop' in charging_car.columns:
        charging_car = charging_car.drop(charging_car[charging_car['drop']==1].index, axis=0)

    # reset index
    charging_car.reset_index(
        drop=True,
        inplace=True,
    )

    charging_car = charging_car.drop('drop', axis=1)


    day_mins = 1440
    ts_range = int(day_count * day_mins / stepsize)


    # sometimes charge_end is zero
    # fix: set charge_end to charge_start --> 1 ts charging time
    charging_car.charge_end = [
        min(
            max(
                ts,
                charging_car.loc[count, "charge_start"],
            ),
            ts_range,
        ) for count, ts in enumerate(charging_car.charge_end)
    ]

    # set the last charging process to end at ts_range
    # if it takes place at home or work and is really near the end
    if charging_car.location.iat[-1] in ["0_work", "6_home"] and charging_car.charge_end.iat[-1] > 0.95 * ts_range:
        charging_car.charge_end.iat[-1] = ts_range


    # check for plausibility at timestamps
    for row in range(len(charging_car)):
        if row == len(charging_car) - 2:
            break
        diff = charging_car.loc[row + 1, 'drive_start'] - charging_car.loc[row, 'charge_end']
        if diff > 1:
            val = charging_car.loc[row + 1, 'drive_start'] - 1
            charging_car.loc[row, 'charge_end'] = val

        diff = charging_car.loc[row + 2, 'charge_start'] - charging_car.loc[row + 1, 'drive_end']
        if diff > 1:
            val = charging_car.loc[row + 1, 'drive_end'] + 1
            charging_car.loc[row + 2, 'charge_start'] = val

    # recalculate chargingdemand an charge_time
    # TODO: sometimes the recharging energy is too high for the number of timesteps
    # # The loss is around 5% of energy, which is missing in the load timeseries due to that
    # mask_zero = charging_car.chargingdemand == 0
    # charging_car.loc[~mask_zero, 'charge_time'] = charging_car.loc[~mask_zero, 'charge_end'] - charging_car.loc[~mask_zero, 'charge_start'] + 1
    #
    # chargingdemand_soc = ((charging_car.SoC_end - charging_car.SoC_start) * bat_cap).to_list()
    # chargingdemand_time = (charging_car.netto_charging_capacity * charging_car.charge_time * stepsize / 60).to_list()
    #
    # chargingdemand = [
    #     min(
    #         chargingdemand,
    #         chargingdemand_time[count],
    #     ) for count, chargingdemand in enumerate(chargingdemand_soc)
    # ]
    #
    # charging_car.iloc[0, 2] = chargingdemand[0]
    #
    # # recalculate soc_end
    # mask_drive = charging_car.location == "driving"
    # soc_start = charging_car.loc[~mask_drive, 'SoC_start'].to_list()
    #
    # new_soc_end = [
    #     min(
    #         soc + charging_car.iloc[count, 2] / bat_cap,
    #         1,
    #     ) for count, soc in enumerate(soc_start)
    # ]
    #
    #
    # charging_car.loc[~mask_drive, 'SoC_end'] = new_soc_end

    # get charging capacity work and home
    charging_capacity_home = charging_car[charging_car.location == "6_home"]

    if len(charging_capacity_home) > 0:
        charging_capacity_home = charging_capacity_home.netto_charging_capacity.iat[0]
        charging_capacity_home = int(round(charging_capacity_home / eta, 0))
    else:
        charging_capacity_home = 0

    charging_capacity_work = charging_car[charging_car.location == "0_work"]

    if len(charging_capacity_work) > 0:
        charging_capacity_work = charging_capacity_work.netto_charging_capacity.iat[0]
        charging_capacity_work = int(round(charging_capacity_work / eta, 0))
    else:
        charging_capacity_work = 0


    # add row with car_type
    charging_car["car_type"] = car_type

    # add row with battery capacity
    charging_car["bat_cap"] = int(bat_cap)

    # reset index
    charging_car.reset_index(
        drop=True,
        inplace=True,
    )

    charging_car.loc[charging_car['location'] == 'driving', 'charge_start'] = 0
    charging_car.loc[charging_car['location'] == 'driving', 'charge_end'] = 0
    charging_car.loc[charging_car['location'] == 'driving', 'charge_time'] = 0


    charging_car.rename(columns={"charge_start": "park_start"}, inplace=True)
    charging_car.rename(columns={"charge_end": "park_end"}, inplace=True)

    # reorder columns
    charging_car = charging_car[
        [
            "car_type",
            "bat_cap",
            "location",
            "netto_charging_capacity",
            "SoC_start",
            "SoC_end",
            "chargingdemand",
            "charge_time",
            "park_start",
            "park_end",
            "drive_start",
            "drive_end",
            "consumption",
        ]
    ]

    filename = "{}_{:05d}_standing_times.csv".format(car_type, car_number)

    file_path = os.path.join(
        path,
        filename)

    # export charging times per car
    charging_car.to_csv(file_path)

# Slow Charging
def slow_charging_capacity(
        normal_charging_probability,
        destination,
        rng,
):
    """

    Parameters
    ----------
    normal_charging_probability : :obj:`df`
        Scenario dataframe for slow charging probabilities
    destination : :obj:`str`
        Trip destination
    rnd_seed : :obj:`int`
        seed for use of random

    Returns
    -------
    charging_capacity : :obj:`float`
        Charging Point Capacity

    """

    for dest in normal_charging_probability.index.unique():
        if destination.find(dest) is not -1:
            destination = dest
            break

    random_number = rng.random()

    charging_capacities = normal_charging_probability.columns
    charging_probabilities = normal_charging_probability.loc[destination]
    sum_prob = 0

    for idx, prob in enumerate(charging_probabilities):
        sum_prob = sum_prob + prob

        # eliminate rounding errors
        if abs(sum_prob - 1) < 0.001:
            sum_prob = 1

        if random_number <= sum_prob:
            charging_capacity = float(charging_capacities[idx])
            break

    return charging_capacity


# Fast Charging
def fast_charging_capacity(
        fast_charging_probability,
        distance,
        rng,
        distance_limit=50,
):
    """

    Parameters
    ----------
    fast_charging_probability : :obj:`df`
        Scenario dataframe for fast charging probabilities
    distance : :obj:`int`
        Driven distance to destination
    distance_limit : :obj:`int`
        Limit after it assumed that a charging takes place in an ex-urban area
        and therefore has a higher likeliness of a higher charging capacity,
        unit km: e.g. 50

    Returns
    -------
    fastcharge : :obj:`int`
        Fast Charging Capacity (150 kW or 350 kW)

    """

    if distance > distance_limit:
        area = r"ex-urban"
    else:
        area = "urban"

    prob_50 = fast_charging_probability.loc[area].iloc[0]
    prob_150 = fast_charging_probability.loc[area].iloc[1] + prob_50


    random_number = rng.random()

    if random_number <= prob_50:
        fast_charging_capacity = 50
    elif random_number <= prob_150:
        fast_charging_capacity = 150
    else:
        fast_charging_capacity = 350

    return fast_charging_capacity


