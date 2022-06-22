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
    soc_min: float
    charging_threshold: float
    energy_min: dict
    charging_curve: dict
    # TODO consumption based on speed instead of constant
    consumption: float
    output: bool
    label: str = None


class Car:
    def __init__(self, car_type: CarType, number: int, work_parking, home_parking,
                 work_capacity, home_capacity, region, soc: float = 1., status: str = "home"):

        self.car_type = car_type
        self.soc_start = soc
        self.soc = soc
        self.work_parking = work_parking
        self.home_parking = home_parking
        self.work_capacity = work_capacity
        self.home_capacity = home_capacity
        self.status = status  # replace with enum?
        self.number = number
        self.region = region
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
            "soc_start": [],
            "soc_end": [],
            "energy": [],
            "station_charging_capacity": [],
            "average_charging_power": []
        }

        self.file_name = "{}_{:05d}_{}kWh_events.csv".format(car_type.name, number,
                                                             car_type.battery_capacity)
        # Set user specificationn and hpc preference
        self.set_user_spec()

    def _update_activity(self, timestamp, event_start, event_time,
                         nominal_charging_capacity=0, charging_power=0):
        """Records newest energy and activity"""
        if self.car_type.output:
            self.soc = round(self.soc, 4)
            self.output["timestamp"].append(timestamp)
            self.output["event_start"].append(event_start)
            self.output["event_time"].append(event_time)
            self.output["location"].append(self.status)
            self.output["use_case"].append(self._get_usecase(nominal_charging_capacity))
            self.output["soc_start"].append(self.output["soc_end"][-1] if len(self.output["soc_end"]) > 0 else
                                            self.soc_start)
            self.output["soc_end"].append(self.soc)
            charging_demand = self._get_last_charging_demand()
            consumption = self._get_last_consumption()
            self.output["energy"].append(charging_demand + consumption)
            self.output["station_charging_capacity"].append(nominal_charging_capacity)
            self.output["average_charging_power"].append(round(charging_power, 4))

    def park(self, trip):
        self._update_activity(trip.park_timestamp, trip.park_start, trip.park_time)

    def charge(self, trip, power, charging_type, step_size=None, long_distance=None, max_charging_time=None):
        if self.soc >= self.car_type.charging_threshold:
            power = 0

        if charging_type == "slow":
            avg_power = 0

            if power != 0:
                charging_time, avg_power, power, soc = self.charging_curve(trip, power, step_size, max_charging_time,
                                                                           charging_type, soc_end=1)
                self.soc = soc

                trip.park_time = charging_time
                trip.drive_start = trip.park_start + trip.park_time
                trip.trip_end = trip.drive_start + trip.drive_time
            self._update_activity(trip.park_timestamp, trip.park_start, trip.park_time,
                                  nominal_charging_capacity=power, charging_power=avg_power)

        elif charging_type == "fast":
            if self.car_type.charging_capacity['fast'] == 0:
                raise ValueError("Vehicle {} has no fast charging capacity but got assigned a HPC event.".format(
                    self.car_type.name
                ))
            soc_end = trip.rng.uniform(0.8, 0.95)
            charging_time, avg_power, power, soc = self.charging_curve(trip, power, step_size, max_charging_time,
                                                                       charging_type, soc_end)
            self.soc = soc
            if long_distance:
                self._update_activity(trip.park_timestamp, trip.park_start, charging_time,
                                      nominal_charging_capacity=power, charging_power=avg_power)
            else:
                # update trip properties
                trip.park_time = charging_time
                trip.drive_start = trip.park_start + trip.park_time
                trip.trip_end = trip.drive_start + trip.drive_time
                self._update_activity(trip.park_timestamp, trip.park_start, trip.park_time,
                                      nominal_charging_capacity=power, charging_power=avg_power)
            return charging_time
        else:
            raise ValueError("Charging type {} is not accepted in charge function!".format(charging_type))

    def charge_home(self, trip):
        if self.home_capacity is not None:
            self.charge(trip, self.home_capacity, "slow", step_size=self.region.simbev.step_size,
                        max_charging_time=trip.park_time)
        else:
            raise ValueError("Home charging attempted but power is None!")

    def charge_work(self, trip):
        if self.work_capacity is not None:
            self.charge(trip, self.work_capacity, "slow", step_size=self.region.simbev.step_size,
                        max_charging_time=trip.park_time)
        else:
            raise ValueError("Work charging attempted but power is None!")

    def charging_curve(self, trip, power, step_size, max_charging_time, charging_type, soc_end):
        soc_start = self.soc

        # check if min charging energy is loaded
        if ((soc_end - soc_start) * self.car_type.battery_capacity) <= \
                self.car_type.energy_min[self._get_usecase(power)]:
            return trip.park_time, 0, 0, soc_start

        delta = (soc_end - soc_start) / 10
        soc_load_list = np.arange(soc_start + delta / 2, soc_end + delta / 2, delta)
        p_soc = np.zeros(len(soc_load_list))
        t_load = np.zeros(len(soc_load_list))

        for i, soc in enumerate(soc_load_list):
            p_soc[i] = min(((-0.01339 * (soc * 100) ** 2 + 0.7143 * (
                    soc * 100) + 84.48) * self.car_type.charging_capacity[charging_type] / 100), power)
            t_load[i] = delta * self.car_type.battery_capacity / p_soc[i] * 60

        charging_time = sum(t_load)
        charged_energy_list = []
        time_steps = math.ceil(charging_time / step_size)

        for i in range(time_steps):

            if max_charging_time is not None and i >= max_charging_time:
                soc_end = soc_start + sum(charged_energy_list) / self.car_type.battery_capacity
                # check if min charging energy is loaded
                if ((soc_end - soc_start) * self.car_type.battery_capacity) <= \
                        self.car_type.energy_min[self._get_usecase(power)]:
                    return trip.park_time, 0, 0, soc_start
                time_steps = max_charging_time
                break

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
            chargepower_timestep = sum(e_load)*60/15

            use_case = self._get_usecase(power)
            self.region.update_grid_timeseries(use_case, chargepower_timestep, power, trip.park_start + i,
                                               trip.park_start + i + 1)

        chargepower_avg = sum(charged_energy_list) / len(charged_energy_list)*60/15

        # TODO add region grid series, also in charge

        return time_steps, chargepower_avg, power, soc_end

    def drive(self, distance, start_time, timestamp, duration, destination):
        self.status = "driving"
        # TODO check for min soc
        if distance > self.remaining_range and self.car_type.label == "BEV":
            return False
        else:
            self.soc -= self.car_type.consumption * distance / self.car_type.battery_capacity
            if self.soc < 0:
                if self.car_type.label == "PHEV":
                    self.soc = 0
                else:
                    raise ValueError("SoC of car {} became negative ({})".format(self.car_type.name,
                                                                                 self.soc))
            self._update_activity(timestamp, start_time, duration)
            self.status = destination
            return True

    @property
    def remaining_range(self):
        return self.usable_soc * self.car_type.battery_capacity / self.car_type.consumption

    @property
    def usable_soc(self):
        return self.soc - self.car_type.soc_min

    def _get_last_charging_demand(self):
        if len(self.output["soc_start"]):
            charging_demand = self.output["soc_end"][-1] - self.output["soc_start"][-1]
            charging_demand *= self.car_type.battery_capacity
            return max(round(charging_demand, 4), 0)
        else:
            return 0

    def _get_last_consumption(self):
        if len(self.output["soc_start"]):
            last_consumption = self.output["soc_end"][-1] - self.output["soc_start"][-1]
            last_consumption *= self.car_type.battery_capacity
            return min(round(last_consumption, 4), 0)
        else:
            return 0

    # TODO maybe solve this in charging (Jakob)
    def _get_usecase(self, power):
        if self.status == "driving":
            return ""
        elif self.work_parking and self.status == "work":
            return "work"
        elif self.home_parking and self.status == "home":
            return "home"
        # TODO: decide on status an requirement for hpc
        elif power >= 150:
            return "hpc"
        else:
            return "public"

    def set_user_spec(self):
        if self.car_type.charging_capacity["fast"] == 0:
            self.user_spec = '0'  # Todo set better term?
            self.hpc_pref = -1
        elif self.home_capacity != 0 and self.home_parking:
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
        if self.car_type.output:
            activity = pd.DataFrame(self.output)
            # remove first week from dataframe
            week_time_steps = int(24 * 7 * 60 / simbev.step_size)
            activity["event_start"] -= week_time_steps
            activity = activity.loc[(activity["event_start"] + activity["event_time"]) >= 0]

            # change first row event if it has charging demand or consumption
            event_len = activity.at[activity.index[0], "event_time"]
            post_event_len = activity.at[activity.index[1], "event_start"]
            pre_event_len = event_len - post_event_len

            if activity.at[activity.index[0], "energy"] > 0:
                pre_demand = activity.at[activity.index[0], "average_charging_power"] * pre_event_len * \
                             simbev.step_size / 60
                new_demand = max(activity.at[activity.index[0], "energy"] - pre_demand, 0)
                activity.at[activity.index[0], "energy"] = new_demand

            elif activity.at[activity.index[0], "energy"] < 0:
                new_consumption = round(activity.at[activity.index[0], "energy"] / (pre_event_len / event_len), 4)
                activity.at[activity.index[0], "energy"] = new_consumption

            # fit first row event to start at time step 0
            activity.at[activity.index[0], "event_start"] = 0
            activity.at[activity.index[0], "event_time"] = post_event_len
            activity.at[activity.index[0], "timestamp"] = simbev.start_date_output

            activity = activity.reset_index(drop=True)
            activity.to_csv(pathlib.Path(region_directory, self.file_name))
