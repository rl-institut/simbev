from dataclasses import dataclass
import numpy as np
import pandas as pd
import pathlib


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

    def drive(self, trip):
        # is this needed or does it happen in the simulation?
        # TODO implement
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
        # fit first row event to start at time step 0
        activity.at[activity.index[0], "event_start"] = 0
        activity.at[activity.index[0], "event_time"] = activity.at[activity.index[1], "event_start"]
        activity.at[activity.index[0], "timestamp"] = simbev.start_date_output
        # TODO change first row event if it has charging_demand or consumption

        activity = activity.reset_index(drop=True)
        # TODO: decide format
        activity.to_csv(pathlib.Path(region_directory, self.file_name))
