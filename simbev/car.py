from dataclasses import dataclass
import numpy as np
import pandas as pd
import pathlib
import math


@dataclass
class CarType:
    name: str
    battery_capacity: float
    charging_capacity: dict
    charging_curve: dict
    consumption: float
    label: str = None


class Car:
    def __init__(self, car_type: CarType, number: int, work_parking, home_parking,
                 work_capacity, home_capacity, soc: float = 1., status: str = "home", user_spec: int = 0,
                 hpc_attrac: float = 0):

        self.car_type = car_type
        self.soc = soc
        self.work_parking = work_parking
        self.home_parking = home_parking
        self.work_capacity = work_capacity
        self.home_capacity = home_capacity
        self.status = status  # replace with enum?
        self.number = number
        self.user_spec = user_spec
        self.hpc_attrac = hpc_attrac

        # lists to track output data
        # TODO: swap to np.array for better performance?
        self.output = {
            "timestamp": [],
            "event_start": [],
            "event_time": [],
            "location": [],
            "use_case": [],
            "soc": [],
            "charging_demand": [],
            "nominal_charging_capacity": [],  # rethink these?
            "charging_power": [],
            "consumption": []
        }

        self.file_name = "{}_{:05d}_{}kWh_events.csv".format(car_type.name, number,
                                                             car_type.battery_capacity)

    def _update_activity(self, timestamp, event_start, event_time,
                         nominal_charging_capacity=0, charging_power=0):
        """Records newest energy and activity"""
        self.soc = round(self.soc, 4)
        self.output["timestamp"].append(timestamp)
        self.output["event_start"].append(event_start)
        self.output["event_time"].append(event_time)
        self.output["location"].append(self.status)
        self.output["use_case"].append(self._get_usecase())
        self.output["soc"].append(self.soc)
        self.output["charging_demand"].append(self._get_last_charging_demand())
        self.output["nominal_charging_capacity"].append(nominal_charging_capacity)
        self.output["charging_power"].append(charging_power)
        self.output["consumption"].append(self._get_last_consumption())

    def park(self, trip):
        self._update_activity(trip.park_timestamp, trip.park_start, trip.park_time)

    def charge(self, trip, power, charging_type):
        # TODO: implement charging function here
        usable_power = min(power, self.car_type.charging_capacity[charging_type])
        self.soc = min(self.soc + trip.park_time * usable_power / self.car_type.battery_capacity, 1)
        self._update_activity(trip.park_timestamp, trip.park_start, trip.park_time,
                              nominal_charging_capacity=power, charging_power=usable_power)

    def charge_home(self, trip):
        self.charge(trip, self.home_capacity, "slow")

    def charge_work(self, trip):
        self.charge(trip, self.work_capacity, "slow")

    def hpc_charge(self, trip, charging_type, simbev):
        # print("hpc_event")
        # get end
        self.status = "hpc_hub"
        soc_start = self.soc

        random_soc = trip.rng.uniform(0.8, 1)
        soc_end = random_soc
        charging_capacity = simbev._get_hpc_charging_capacity(trip)
        fastcharge = min(
            charging_capacity,
            self.car_type.charging_capacity["fast"]
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
            p_soc[i] = (-0.01339 * (soc * 100) ** 2 + 0.7143 * (
                    soc * 100) + 84.48) * fastcharge / 100  # polynomial iteration of the loadcurve
            e_load[i] = delta * self.car_type.battery_capacity
            t_load[i] = delta * self.car_type.battery_capacity / p_soc[i] * 60

        # print('p_soc:', p_soc)
        # print('e_load:', e_load)
        # print('t_load:', t_load)

        charging_time = sum(t_load)
        # print('charging_time:', charging_time)

        charge_start = trip.drive_start + trip.drive_time
        counter_c = 0
        chen_timestep = []

        # Aufteilung des Ladevorgangs in 15 min Schritte
        while charging_time > simbev.step_size:
            # print("loop")
            i = 0
            t_sum = 0
            # fill array for loading in timestep
            while t_sum <= simbev.step_size:
                t_sum = t_sum + t_load[i]
                i += 1
                t_load_new = t_load[:i]
            t_diff = simbev.step_size - t_sum  # last loading-step in timestep

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

            charging_time = charging_time - simbev.step_size
            # print('neue Ladezeit:', charging_time)

            counter_c += 1
            trip.park_time = counter_c

        # append timeseries charging timestep
        chen_timestep.append(sum(e_load))

        chen = (soc_end - soc_start) * self.car_type.battery_capacity  # sum(chen_timestep)
        usable_power = chen/counter_c/15*60
        self.soc = soc_end
        # print('chen', chen)
        trip.park_start = charge_start
        trip._set_timestamps
        self._update_activity(trip.park_timestamp, trip.park_start, trip.park_time,
                              nominal_charging_capacity=fastcharge, charging_power=usable_power)

        range_remaining = ((soc_end) * self.car_type.battery_capacity) / self.car_type.consumption

    def drive(self, trip, simbev):
        # is this needed or does it happen in the simulation?
        # TODO implement
        self.status = "driving"

        # TODO: can i make the trip? => HPC
        range_remaining = self.soc*self.car_type.battery_capacity/self.car_type.consumption
        while trip.distance > range_remaining and self.car_type.label == "BEV":     # Todo SoC_min definieren
            # Drive until HPC Station
            #print('trip_distance', trip.distance)
            #print('timestep', trip.drive_start)
            rn_dist = trip.rng.uniform(0.6, 1)
            # driving until HPC-Station
            distance_stop = range_remaining * rn_dist
            # print("range_remaining", range_remaining)
            # print("distance",distance)
            # print("distance_stop", distance_stop)
            distance_remaining = trip.distance - distance_stop
            drive_time = round(distance_stop / trip.speed)
            trip.drive_time = math.ceil(drive_time / simbev.step_size)
            driveconsumption = distance_stop * self.car_type.consumption
            # get timesteps for car status of driving

            self.status = 'driving'
            self.soc -= self.car_type.consumption * distance_stop / self.car_type.battery_capacity
            self._update_activity(trip.drive_timestamp, trip.drive_start, drive_time)

            #print('charging')
            # "7_charging_hub"

            charging_type = "hpc"                                            # get_charging_power_hpc
            self.hpc_charge(trip, charging_type, simbev)

            range_remaining = self.soc * self.car_type.battery_capacity / self.car_type.consumption
            trip.distance = distance_remaining
            #print('trip_distance', trip.distance)

        trip.drive_start = trip.park_start + trip.park_time
        trip.drive_time = round(trip.distance / trip.speed)
        trip._set_timestamps()
        self.status = "driving"
        self.soc -= self.car_type.consumption * trip.distance / self.car_type.battery_capacity
        # TODO: can i make the trip? => HPC
        self._update_activity(trip.drive_timestamp, trip.drive_start, trip.drive_time)
        self.status = trip.destination

    def _get_last_charging_demand(self):
        if len(self.output["soc"]) > 1:
            charging_demand = (self.output["soc"][-1] - self.output["soc"][-2])
            charging_demand *= self.car_type.battery_capacity
            return max(round(charging_demand, 4), 0)
        else:
            return 0

    def _get_last_consumption(self):
        if len(self.output["soc"]) > 1:
            last_consumption = self.output["soc"][-1] - self.output["soc"][-2]
            last_consumption *= self.car_type.battery_capacity
            return abs(min(round(last_consumption, 4), 0))
        else:
            return 0

    # TODO maybe solve this in charging (Jakob)
    def _get_usecase(self):
        if self.status == "driving":
            return ""
        elif self.work_parking and self.status == "work":
            return "work"
        elif self.home_parking and self.status == "home":
            return "home"
        # TODO: decide on status for hpc
        elif self.status == "hub":
            return "hpc"
        else:
            return "public"

    def get_user_spec(self, region, rng):
        prob_home = 0

        if region.id == 'LR_Klein':
            prob_home_private = 0.9
            prob_home = 0.55
        elif region.id == 'LR_Mitte':
            prob_home_private = 0.85
            prob_home = 0.525
        elif region.id == 'LR_Zentr':
            prob_home_private = 0.725
            prob_home = 0.49
        elif region.id == 'SR_Gross':
            prob_home_private = 0.6
            prob_home = 0.485
        elif region.id == 'SR_Klein':
            prob_home_private = 0.875
            prob_home = 0.53
        elif region.id == 'SR_Metro':
            prob_home_private = 0.4
            prob_home = 0.475
        elif region.id == 'SR_Mittel':
            prob_home_private = 0.8
            prob_home = 0.495

        prob_work = 0.875
        # random_number = rng.random()
        user_spec = ''

        if rng.random() <= prob_home:
            if rng.random() <= prob_work:
                self.user_spec = 'A'  # LIS at home and at work
            else:
                self.user_spec = 'B'  # LIS at home but not at work
        else:
            if rng.random() <= prob_work:
                self.user_spec = 'C'  # LIS not at home but at work
            else:
                self.user_spec = 'D'  # LIS not at home and not at work. Primarily HPC

        # print(self.user_spec)

    def get_hpc_attrac(self):
        if self.user_spec == 'A':
            self.hpc_attrac = 0.25
        if self.user_spec == 'B':
            self.hpc_attrac = 0.5
        if self.user_spec == 'C':
            self.hpc_attrac = 0.5
        if self.user_spec == 'D':
            self.hpc_attrac = 0.75

    def export(self, region_directory, simbev):
        """
        Exports the output values collected in car object to a csv file.

        Parameters
        ----------
        region_directory : :obj:`pathlib.Path`
            save directory for the region
        simbev : :obj:`SimBEV`
            SimBEV object with scenario information

        """
        activity = pd.DataFrame(self.output)
        # remove first week from dataframe
        week_time_steps = int(24 * 7 * 60 / simbev.step_size)
        activity["event_start"] -= week_time_steps
        activity = activity.loc[(activity["event_start"] + activity["event_time"]) >= 0]

        # change first row event if it has charging demand or consumption
        event_length = activity.at[activity.index[0], "event_time"]
        post_event_length = activity.at[activity.index[1], "event_start"]
        pre_event_length = event_length - post_event_length

        new_demand = max(activity.at[activity.index[0], "charging_demand"] -
                         activity.at[activity.index[0], "charging_power"] * pre_event_length * simbev.step_size / 60, 0)
        activity.at[activity.index[0], "charging_demand"] = new_demand
        new_consumption = round(activity.at[activity.index[0], "consumption"] / (pre_event_length / event_length), 4)
        activity.at[activity.index[0], "consumption"] = new_consumption

        # fit first row event to start at time step 0
        activity.at[activity.index[0], "event_start"] = 0
        activity.at[activity.index[0], "event_time"] = post_event_length
        activity.at[activity.index[0], "timestamp"] = simbev.start_date_output

        activity = activity.reset_index(drop=True)
        # TODO: decide format
        activity.to_csv(pathlib.Path(region_directory, self.file_name))
