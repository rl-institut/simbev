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
                 work_capacity, home_capacity, soc: float = 1., status: str = "home"):

        self.car_type = car_type
        self.soc = soc
        self.work_parking = work_parking
        self.home_parking = home_parking
        self.work_capacity = work_capacity
        self.home_capacity = home_capacity
        self.status = status  # replace with enum?
        self.number = number
        self.user_spec = 0
        self.hpc_pref = 0

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
            "nominal_charging_capacity": [],  # TODO rethink these?
            "charging_power": [],
            "consumption": []
        }

        self.file_name = "{}_{:05d}_{}kWh_events.csv".format(car_type.name, number,
                                                             car_type.battery_capacity)
        # Set user specificationn and hpc preference
        self.set_user_spec()

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

    def charge(self, trip, power, charging_type, step_size=None):
        if charging_type == "slow":
            usable_power = min(power, self.car_type.charging_capacity[charging_type])
            self.soc = min(self.soc + trip.park_time * usable_power / self.car_type.battery_capacity, 1)
            self._update_activity(trip.park_timestamp, trip.park_start, trip.park_time,
                                  nominal_charging_capacity=power, charging_power=usable_power)
        elif charging_type == "fast":
            return self.charging_curve(trip, power, step_size)
        else:
            raise ValueError("Charging type {} is not accepted in charge function!".format(charging_type))

    def charge_home(self, trip):
        self.charge(trip, self.home_capacity, "slow")

    def charge_work(self, trip):
        self.charge(trip, self.work_capacity, "slow")

    def charging_curve(self, trip, power, step_size):
        soc_start = self.soc

        soc_end = trip.rng.uniform(0.8, 1)

        usable_power = min(
            power,
            self.car_type.charging_capacity["fast"]
        )

        delta = (soc_end - soc_start) / 10
        soc_load_list = np.arange(soc_start + delta / 2, soc_end + delta / 2, delta)
        p_soc = np.zeros(len(soc_load_list))
        t_load = np.zeros(len(soc_load_list))

        for i, soc in enumerate(soc_load_list):
            p_soc[i] = (-0.01339 * (soc * 100) ** 2 + 0.7143 * (
                    soc * 100) + 84.48) * usable_power / 100  # polynomial iteration of the loadcurve
            t_load[i] = delta * self.car_type.battery_capacity / p_soc[i] * 60

        charging_time = sum(t_load)
        charged_energy_list = []
        time_steps = math.ceil(charging_time / step_size)

        for i in range(time_steps):
            t_sum = 0
            k = 0
            # fill array for loading in timestep
            while t_sum <= step_size and k < len(t_load):
                t_sum = t_sum + t_load[k]
                k += 1
            t_load_new = t_load[:k]

            t_diff = t_sum - step_size  # last loading-step in timestep
            t_load_new[-1] -= t_diff
            p_soc_new = p_soc[:k]
            e_load = t_load_new * p_soc_new / 60

            charged_energy_list.append(round(sum(e_load), 4))

            t_load = t_load[k - 1:]
            t_load[0] = t_diff

            p_soc = p_soc[k - 1:]

        self.soc = soc_end
        self._update_activity(trip.park_timestamp, trip.park_start, time_steps,
                              nominal_charging_capacity=power, charging_power=usable_power)

        # TODO add region grid series, also in charge

        return time_steps

    def drive(self, distance, start_time, timestamp, duration, destination):
        self.status = "driving"
        # TODO check for min soc
        range_remaining = self.soc * self.car_type.battery_capacity / self.car_type.consumption
        if distance > range_remaining and self.car_type.label == "BEV":
            return False
        else:
            self.soc -= self.car_type.consumption * distance / self.car_type.battery_capacity
            self._update_activity(timestamp, start_time, duration)
            self.status = destination
            return True

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

    def set_user_spec(self):

        if self.home_capacity != 0 and self.home_parking:
            if self.work_capacity != 0 and self.work_parking:
                self.user_spec = 'A'  # private LIS at home and at work
                self.hpc_pref = 0.25
            else:
                self.user_spec = 'B'  # private LIS at home but not at work
                self.hpc_pref = 0.5
        else:
            if self.work_capacity != 0 and self.work_parking:
                self.user_spec = 'C'  # private LIS not at home but at work
                self.hpc_pref = 0.5
            else:
                self.user_spec = 'D'  # private LIS not at home and not at work. Primarily HPC
                self.hpc_pref = 0.75

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

        pre_demand = activity.at[activity.index[0], "charging_power"] * pre_event_length * simbev.step_size / 60
        new_demand = max(activity.at[activity.index[0], "charging_demand"] - pre_demand, 0)
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
