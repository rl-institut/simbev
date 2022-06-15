from simbev.car import Car, CarType


def test_basic_car():
    car_type = CarType("bev_mini", 30, {"slow": 11, "fast": 50}, {}, 0.14, False, "BEV")
    car = Car(car_type, 0, True, True, 11, 22, None)
    assert car._get_usecase(50) == "home"
