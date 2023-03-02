from simbev.car import Car, CarType, UserGroup


def test_basic_car():
    hpc_dict = {'soc_end_min': 0.8, 'soc_end_max': 0.95, 'soc_start_threshold': 0.6, 'park_time_max': 90.0,
                'distance_min': 0.6, 'distance_max': 1.0, 'hpc_pref_A': 0.25, 'hpc_pref_B': 0.5, 'hpc_pref_C': 0.5,
                'hpc_pref_D': 0.75}
    car_type = CarType("bev_mini", 30, {"slow": 11, "fast": 50}, 0.2, 0.8, {}, {}, 0.14, False, hpc_dict, "BEV")
    user_group = UserGroup(1, {})
    car = Car(car_type, user_group, 0, True, True, 11, 22, None, True)
    assert car._get_usecase(50) == "home"
