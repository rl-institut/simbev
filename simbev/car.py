from dataclasses import dataclass
import numpy as np


class Car:
    def __init__(self,
                 soc: float, car_type, work_station, home_station, status: str = "parking"):
        self.car_type = car_type
        self.soc = soc
        self.work_station = work_station
        self.home_station = home_station
        self.status = status  # replace with enum?
        self.activity = np.array(self.status, dtype=str)
        self.energy = np.array(self.soc, dtype=float)

    def _update_activity(self):
        """Records newest energy and activity"""
        # TODO: save corresponding event time steps somewhere (maybe in simbev.run())
        self.activity = np.append(self.activity, self.status)
        self.energy = np.append(self.energy, self.status)


@dataclass
class CarType:
    name: str
    battery_capacity: float
    charging_capacity: dict
    charging_curve: dict
    consumption: float
