import numpy as np


def get_user_spec(rng, region, home_work_privat, charging_capacity_home, charging_capacity_work):
    # if region == 'LR_Klein':
    #     prob_home = home_work_privat
    # elif region == 'LR_Mitte':
    #     prob_home = 0.525
    # elif region == 'LR_Zentr':
    #     prob_home = 0.49
    # elif region == 'SR_Gross':
    #     prob_home = 0.485
    # elif region == 'SR_Klein':
    #     prob_home = 0.53
    # elif region == 'SR_Metro':
    #     prob_home = 0.475
    # elif region == 'SR_Mittel':
    #     prob_home = 0.495

    rng_home = rng.random()
    rng_work = rng.random()
    if charging_capacity_home != 0 and home_work_privat[region]['home'] <= rng_home:
        if charging_capacity_work != 0 and home_work_privat[region]['work'] <= rng_work:
            user_spec = 'A'  # LIS at home and at work
        else:
            user_spec = 'B'  # LIS at home but not at work
    else:
        if charging_capacity_work != 0 and home_work_privat[region]['work'] <= rng_work:
            user_spec = 'C'  # LIS not at home but at work
        else:
            user_spec = 'D'  # LIS not at home and not at work. Primarily HPC

    # print(user_spec)
    return user_spec


def get_attractivity(user_spec):
    # Attraktivität von 0 bis 1 festlegen (o = niedrig; 1 = hoch)
    if user_spec == 'A':
        hpc_attrac = 0.27
    if user_spec == 'B':
        hpc_attrac = 0.56
    if user_spec == 'C':
        hpc_attrac = 0.56
    if user_spec == 'D':
        hpc_attrac = 0.85
    return hpc_attrac


def hpc_event(rng, fast_charging_capacity, charge_prob_fast, distance, chargepower_fast, batcap, im,
              timestep, ch_time, ch_capacity, demand, soc_list, place_list, purp_list, dr_start, dr_end, consumption,
              ch_start, ch_end, car_status, soc_min, con, place):
    # print("hpc_event")
    # get socstart and end
    soc_start = soc_list[-1]
    random_soc = rng.uniform(0.8, 1)
    soc_end = random_soc
    # print("soc_start", soc_start)
    # print("soc_end", soc_end)
    # charging

    fastcharge = min(
        fast_charging_capacity(
            charge_prob_fast,
            distance,
            rng,
        ),
        chargepower_fast,
    )
    # print("Fastcharge", fastcharge)
    delta = (soc_end - soc_start) / 10
    # soc_range = np.arange(soc_start, soc_end, delta)
    soc_load_list = np.arange(soc_start + delta / 2, soc_end + delta / 2, delta)
    # print('soc_load_list', soc_load_list)
    p_soc = np.zeros(len(soc_load_list))
    t_load = np.zeros(len(soc_load_list))
    e_load = np.zeros(len(soc_load_list))

    for i, soc in enumerate(soc_load_list):
        p_soc[i] = min(fastcharge, (-0.01339 * (soc * 100) ** 2 + 0.7143 * (
                soc * 100) + 84.48) * fastcharge / 100)  # polynomial iteration of the loadcurve
        e_load[i] = delta * batcap
        t_load[i] = delta * batcap / p_soc[i] * 60

    # print('p_soc:', p_soc)
    # print('e_load:', e_load)
    # print('t_load:', t_load)

    charging_time = sum(t_load)
    # print('charging_time:', charging_time)

    charge_start = im
    counter_c = 0
    chen_timestep = []

    # Aufteilung des Ladevorgangs in 15 min Schritte
    while charging_time > timestep:
        # print("loop")
        i = 0
        t_sum = 0
        # fill array for loading in timestep
        while t_sum <= timestep:
            t_sum = t_sum + t_load[i]
            i += 1
            t_load_new = t_load[:i]
        t_diff = timestep - t_sum  # last loading-step in timestep

        t_load_new[i - 1] = t_load[i - 1] + t_diff
        p_soc_new = p_soc[:i]
        e_load_new = t_load_new * p_soc_new / 60  # e_load[:i]

        chen_timestep.append(sum(e_load_new))

        t_load = t_load[i - 1:]
        t_load[0] = -t_diff

        p_soc = p_soc[i - 1:]
        e_load = p_soc * t_load / 60
        # print("t_load", t_load)
        # print('e_load', e_load)

        charging_time = charging_time - timestep
        # print('neue Ladezeit:', charging_time)

        counter_c += 1
        im = charge_start + counter_c

    # append timeseries charging timestep
    chen_timestep.append(sum(e_load))

    chen = (soc_end - soc_start) * batcap  # sum(chen_timestep)
    # print('chen', chen)
    # if charge_start > (len(car_status) - 1):
    #     car_status[-1] = 2
    #     return 0, im
    ch_time.append(counter_c + 1)
    ch_capacity.append(fastcharge)
    demand.append(chen)
    # soc = soc_list[-1] + (chen / batcap)
    soc_list.append(soc_end)
    place_list.append(place)
    purp_list.append(place)
    dr_start.append(0)
    dr_end.append(0)
    consumption.append(0)

    ch_start.append(charge_start)
    ch_end.append(charge_start + counter_c)
    if charge_start > (len(car_status) - 1):
        car_status[-1] = 2
        return 0, im
    car_status[charge_start] = 2
    im = charge_start + counter_c

    # distance_remaining = distance_remaining - distance_stop
    # print("con", con, batcap, soc_end, soc_min)

    range_remaining = ((soc_end - soc_min) * batcap) / con

    return range_remaining, im
