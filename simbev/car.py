from dataclasses import dataclass


class Car:
    def __init__(self,
                 soc: float, car_type, work_station, home_station, status: str = "parking"):
        self.car_type = car_type
        self.soc = soc
        self.work_station = work_station
        self.home_station = home_station
        self.status = status  # replace with enum?


@dataclass
class CarType:
    name: str
    battery_capacity: float
    charging_capacity: dict
    charging_curve: dict
    consumption: float
