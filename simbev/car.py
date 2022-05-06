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

        self.activity = []
        self.energy = []
        self._update_activity()

        self.file_name = "{}_{:05d}_{}kWh_events.csv".format(car_type.name, number,
                                                             car_type.battery_capacity)

    def _update_activity(self):
        """Records newest energy and activity"""
        # TODO: save corresponding event time steps somewhere (maybe in simbev.run())
        self.activity.append([self.status, self._get_usecase()])
        self.energy.append(self.soc)

    def charge(self, power, time):
        # TODO: implement charging function here
        new_soc = 1
        self.soc = new_soc

    def drive(self, time, destination, distance):
        # is this needed or does it happen in the simulation?
        self.status = destination
        self.soc = self.car_type.consumption * distance
        self._update_activity()

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
        activity = pd.DataFrame(self.activity)
        # TODO: decide format
        activity.to_csv(save_path)
