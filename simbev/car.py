from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass
class CarType:
    name: str
    battery_capacity: float
    charging_capacity: dict
    charging_curve: dict
    consumption: float
    label: str = None


class Car:
    def __init__(self, soc: float, car_type: CarType, work_station, home_station, number: int,
                 status: str = "home"):
        self.car_type = car_type
        self.soc = soc
        self.work_station = work_station
        self.home_station = home_station
        self.status = status  # replace with enum?
        self.number = number

        # lists to track output data
        # TODO: swap to np.array for better performance?
        self.output = {
            "location": [],
            "use_case": [],
            "soc": [],
            "charging_demand": [],
            "event_start": [],
            "event_time": [],  # or event end? only one needed
            "nominal_charging_capacity": [],  # rethink these?
            "charging_power": [],
            "consumption": []
        }
        self._update_activity(0, 0)  # TODO: set initial event time

        self.file_name = "{}_{:05d}_{}kWh_events.csv".format(car_type.name, number,
                                                             car_type.battery_capacity)

    def _update_activity(self, event_start, event_time, charging_demand=0,
                         nominal_charging_capacity=0, charging_power=0, driving_consumption=0):
        """Records newest energy and activity"""
        # TODO: save corresponding event time steps somewhere (maybe in simbev.run())
        self.output["location"].append(self.status)
        self.output["use_case"].append(self._get_usecase())
        self.output["soc"].append(self.soc)
        self.output["event_start"].append(event_start)
        self.output["event_time"].append(event_time)
        self.output["charging_demand"].append(charging_demand)
        self.output["nominal_charging_capacity"].append(nominal_charging_capacity)
        self.output["charging_power"].append(charging_power)
        self.output["consumption"].append(driving_consumption)

    def park(self, start, time, location):
        self.status = location
        self._update_activity(start, time)

    def charge(self, start, time, power, location):
        # TODO: implement charging function here
        self.soc = min(self.soc + time * power / self.car_type.battery_capacity, 1)
        self.park(start, time, location)

    def drive(self, start, time, distance):
        # is this needed or does it happen in the simulation?
        self.status = "driving"
        self.soc -= self.car_type.consumption * distance / self.car_type.battery_capacity
        self._update_activity(start, time)

    def _get_usecase(self):
        if self.status == "driving":
            return ""
        elif self.work_station and self.status == "work":
            return "work"
        elif self.home_station and self.status == "home":
            return "home"
        # TODO: decide on status for hpc
        elif self.status == "hub":
            return "hpc"
        else:
            return "public"

    def export(self, save_path):
        activity = pd.DataFrame(self.output)
        # TODO: decide format
        activity.to_csv(save_path)
