import pandas as pd
from car import Car


class Region:
    def __init__(self, region_id, region_type, car_list=[]):
        self.id = region_id
        self.type = region_type
        self.cars = car_list

    def add_cars_from_config(self, car_dict, tech_data: pd.DataFrame):
        for car_type, car_count in car_dict.items():
            for i in range(car_count):
                bat_cap = tech_data.at[car_type, 'battery_capacity']
                consumption = tech_data.at[car_type, 'energy_consumption']
                charging_capacity_slow = tech_data.at[car_type, 'max_charging_capacity_slow']
                charging_capacity_fast = tech_data.at[car_type, 'max_charging_capacity_fast']
                charging_capacity = {'slow': charging_capacity_slow, 'fast': charging_capacity_fast}
                new_car = Car(bat_cap, charging_capacity, [], consumption, 1, car_type, None, None)  # TODO: check all parameters
                self.cars.append(new_car)
