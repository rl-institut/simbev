class Car:
    def __init__(self, battery_capacity: float, charging_capacity, charging_curve, consumption: float,
                 soc: float, car_type: str, work_station, home_station, status: str = "parking"):
        self.battery_capacity = battery_capacity
        self.charging_capacity = charging_capacity
        self.charging_curve = charging_curve
        self.consumption = consumption
        self.soc = soc
        self.type = car_type
        self.work_station = work_station
        self.home_station = home_station
        self.status = status  # replace with enum?
