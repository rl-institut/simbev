import numpy as np
import pytest

from simbev.car import (
    Car,
    CarType,
    UserGroup,
    default_starting_status,
    vehicle_group_has_role,
)


class _FakeSimbev:
    """Minimal stand-in for SimBEV, exposing only what Car.charge()/
    charging_curve() read."""

    def __init__(self, mcs_power=1000, mcs_time_threshold=45):
        self.hpc_data = {
            "soc_end_min": 0.9,
            "soc_end_max": 0.9,
            "soc_start_threshold": 0.6,
            "park_time_max": 90000,
            "distance_min": 0.6,
            "distance_max": 1.0,
        }
        self.mcs_power = mcs_power
        self.mcs_time_threshold = mcs_time_threshold
        self.eta_cp = 1.0
        self.fast_charge_threshold = 50


class _FakeTrip:
    """Minimal stand-in for Trip, exposing only what Car.charge()/
    charging_curve() read."""

    def __init__(self, park_time=10, park_start=0):
        self.rng = np.random.default_rng(1)
        self.simbev = _FakeSimbev()
        self.park_time = park_time
        self.park_start = park_start
        self.park_timestamp = "2021-01-01"


def _make_heavy_duty_car_type(fast_capacity=350):
    return CarType(
        name="bev_heavy_duty_vehicle",
        battery_capacity=300,
        charging_capacity={"slow": 22, "fast": fast_capacity},
        soc_min=0.2,
        charging_threshold=0.8,
        energy_min={"hpc": 20, "mcs": 20},
        charging_curve=lambda soc: 1.0,
        consumption=1.0,
        consumption_factor_winter=1.15,
        consumption_factor_summer=0.95,
        speed_optimal=50,
        speed_consumption_coefficient_low=0.00001,
        speed_consumption_coefficient_high=0.00004,
        output=False,
        attractivity={},
        vehicle_group="heavy_duty_vehicle",
    )


def test_basic_car():
    hpc_dict = {'soc_end_min': 0.8, 'soc_end_max': 0.95, 'soc_start_threshold': 0.6, 'park_time_max': 90.0,
                'distance_min': 0.6, 'distance_max': 1.0, 'hpc_pref_A': 0.25, 'hpc_pref_B': 0.5, 'hpc_pref_C': 0.5,
                'hpc_pref_D': 0.75}
    car_type = CarType(
        "bev_mini", 30, {"slow": 11, "fast": 50}, 0.2, 0.8, {}, {}, 0.14,
        1.15, 0.95, 50, 0.00001, 0.00004, hpc_dict, "BEV",
    )
    user_group = UserGroup(1, {})
    car = Car(car_type, user_group, 0, True, True, 11, 22, None, True)
    assert car._get_usecase(50) == "home"


def test_car_type_vehicle_group_defaults_to_private():
    # tech_data.csv files without a vehicle_group column must keep behaving
    # exactly like today (private Pkw only).
    car_type = CarType(
        "bev_mini", 30, {"slow": 11, "fast": 50}, 0.2, 0.8, {}, {}, 0.14,
        1.15, 0.95, 50, 0.00001, 0.00004, {}, "BEV",
    )
    assert car_type.vehicle_group == "private"


def test_depot_usecase_for_commercial_vehicle_group():
    car_type = CarType(
        "light_duty_vehicle_transporter", 60, {"slow": 22, "fast": 50}, 0.2, 0.8, {}, {}, 0.2,
        1.15, 0.95, 50, 0.00001, 0.00004, {}, "BEV",
        vehicle_group="light_duty_vehicle",
    )
    user_group = UserGroup(1, {})
    car = Car(
        car_type, user_group, 0, False, False, None, None, None, False,
        status="rueckfahrt_betrieb", depot_parking=True, depot_capacity=22,
    )
    assert car._get_usecase(22) == "depot"


def test_no_depot_usecase_for_private_vehicle_group():
    # A "private" car standing at a location literally named "rueckfahrt_betrieb"
    # (which cannot happen in practice, since MiD purposes never produce that
    # string) must not accidentally get private charging - private's role map
    # simply has no entry for it.
    car_type = CarType(
        "bev_mini", 30, {"slow": 11, "fast": 50}, 0.2, 0.8, {}, {}, 0.14,
        1.15, 0.95, 50, 0.00001, 0.00004, {}, "BEV",
    )
    user_group = UserGroup(1, {})
    car = Car(
        car_type, user_group, 0, False, False, None, None, None, False,
        status="rueckfahrt_betrieb", depot_parking=True, depot_capacity=22,
    )
    assert car._get_usecase(22) == "public"


def test_vehicle_group_has_role():
    assert vehicle_group_has_role("private", "home")
    assert vehicle_group_has_role("private", "work")
    assert not vehicle_group_has_role("private", "depot")

    assert vehicle_group_has_role("pkw_commercial", "home")
    assert vehicle_group_has_role("pkw_commercial", "work")
    assert vehicle_group_has_role("pkw_commercial", "depot")

    # light_duty_vehicle/heavy_duty_vehicle have no home/work role - their
    # user_group selection must fall back to depot availability instead.
    assert not vehicle_group_has_role("light_duty_vehicle", "home")
    assert not vehicle_group_has_role("light_duty_vehicle", "work")
    assert vehicle_group_has_role("light_duty_vehicle", "depot")
    assert not vehicle_group_has_role("heavy_duty_vehicle", "home")
    assert vehicle_group_has_role("heavy_duty_vehicle", "depot")


def test_default_starting_status():
    # private/pkw_commercial start at their home-role purpose
    assert default_starting_status("private") == "home"
    assert default_starting_status("pkw_commercial") == "nach_hause"
    # light_duty_vehicle/heavy_duty_vehicle have no home role - they start at
    # their depot-role purpose instead
    assert default_starting_status("light_duty_vehicle") == "rueckfahrt_betrieb"
    assert default_starting_status("heavy_duty_vehicle") == "rueckfahrt_betrieb"


def test_car_starting_status_matches_vehicle_group():
    # Regression test: Car used to default status="home" unconditionally,
    # which crashed with a KeyError for vehicle_groups whose probability data
    # has no "home" purpose at all (e.g. light_duty_vehicle/heavy_duty_vehicle).
    car_type = CarType(
        "bev_heavy_duty_vehicle", 300, {"slow": 11, "fast": 0}, 0.2, 0.8, {}, {}, 1.0,
        1.15, 0.95, 50, 0.00001, 0.00004, {}, "BEV",
        vehicle_group="heavy_duty_vehicle",
    )
    user_group = UserGroup(1, {})
    car = Car(car_type, user_group, 0, False, False, None, None, None, False)
    assert car.status == "rueckfahrt_betrieb"


def test_estimate_fast_charging_minutes():
    # fast_capacity=1000 so the 1000 kW MCS draw below isn't itself capped by
    # the vehicle's own onboard charging capacity - see
    # test_mcs_power_is_still_capped_by_vehicle_fast_charging_capacity for
    # what happens when it is.
    car_type = _make_heavy_duty_car_type(fast_capacity=1000)
    user_group = UserGroup(1, {})
    car = Car(
        car_type, user_group, 0, False, False, None, None, None, False, soc=0.2
    )
    # 0.7 soc * 300 kWh = 210 kWh needed, at a constant power (below the
    # 1000 kW cap, so the curve factor of 1.0 never binds) - roughly
    # 210 kWh / 100 kW * 60 = 126 minutes (np.arange's step-count rounding
    # can add one extra 10%-sized slice at these bounds, hence the range
    # rather than an exact match).
    minutes_100kw = car._estimate_fast_charging_minutes(100, 0.9)
    assert 120 < minutes_100kw < 145
    # 10x the power must yield exactly 1/10th the time, regardless of that
    # step-count rounding (it affects both calls identically).
    minutes_1000kw = car._estimate_fast_charging_minutes(1000, 0.9)
    assert minutes_1000kw == pytest.approx(minutes_100kw / 10, rel=1e-6)


def test_mcs_power_is_still_capped_by_vehicle_fast_charging_capacity():
    # A vehicle's fast-charging capacity (max_charging_capacity_fast in
    # tech_data.csv) caps the effective power for MCS exactly like it does
    # for HPC - MCS only actually speeds things up if that capacity is
    # raised to match real MCS hardware (~1000 kW), not left at a regular
    # HPC-tier value like 350 kW.
    car_type = _make_heavy_duty_car_type(fast_capacity=350)
    user_group = UserGroup(1, {})
    car = Car(
        car_type, user_group, 0, False, False, None, None, None, False, soc=0.2
    )
    minutes_at_350kw_cap = car._estimate_fast_charging_minutes(1000, 0.9)
    minutes_at_100kw = car._estimate_fast_charging_minutes(100, 0.9)
    # requesting 1000 kW is throttled down to the 350 kW cap, so the time
    # only improves by the 100->350 kW ratio, not the 100->1000 kW ratio
    assert minutes_at_350kw_cap == pytest.approx(minutes_at_100kw * 100 / 350, rel=1e-6)
    # nothing to charge -> zero estimated time
    assert car._estimate_fast_charging_minutes(100, 0.2) == 0.0


def test_heavy_duty_vehicle_switches_to_mcs_when_hpc_too_slow():
    car_type = _make_heavy_duty_car_type()
    user_group = UserGroup(1, {})
    car = Car(
        car_type, user_group, 0, False, False, None, None, None, False, soc=0.2
    )
    trip = _FakeTrip(park_time=100)

    # 100 kW HPC would take ~126 min (> the 45 min mcs_time_threshold), so
    # this heavy_duty_vehicle must switch to the configured 1000 kW MCS power.
    car.charge(trip, 100, "fast", "urban_fast", step_size=15, max_charging_time=100)

    assert car.grid_timeseries_list
    assert all(
        event["charging_use_case"] == "mcs" for event in car.grid_timeseries_list
    )
    assert all(
        event["power"] == pytest.approx(1000) for event in car.grid_timeseries_list
    )


def test_get_usecase_distinguishes_mcs_from_hpc():
    # "use_case" (analysis output) and the energy_min lookup must tell MCS
    # apart from a regular HPC event, even though both draw power above
    # fast_charging_threshold - only charging_use_case=="mcs" can do that.
    car_type = _make_heavy_duty_car_type()
    user_group = UserGroup(1, {})
    car = Car(
        car_type, user_group, 0, False, False, None, None, None, False,
        status="rueckfahrt_betrieb",
    )
    assert car._get_usecase(1000, "mcs") == "mcs"
    assert car._get_usecase(1000, "urban_fast") == "hpc"
    assert car._get_usecase(1000, "highway_fast") == "hpc"
    assert car._get_usecase(1000) == "hpc"


def test_heavy_duty_vehicle_keeps_hpc_when_fast_enough():
    car_type = _make_heavy_duty_car_type()
    user_group = UserGroup(1, {})
    car = Car(
        car_type, user_group, 0, False, False, None, None, None, False, soc=0.2
    )
    trip = _FakeTrip(park_time=100)

    # 1000 kW HPC would only take ~12.6 min (well under the 45 min
    # threshold), so no MCS switch should happen even though this is a
    # heavy_duty_vehicle.
    car.charge(trip, 1000, "fast", "urban_fast", step_size=15, max_charging_time=100)

    assert car.grid_timeseries_list
    assert all(
        event["charging_use_case"] == "urban_fast" for event in car.grid_timeseries_list
    )


def test_non_heavy_duty_vehicle_never_switches_to_mcs():
    # Same slow-HPC scenario as the switching test above, but for a vehicle
    # group other than heavy_duty_vehicle - MCS must never apply there.
    car_type = CarType(
        name="bev_light_duty_vehicle",
        battery_capacity=300,
        charging_capacity={"slow": 22, "fast": 350},
        soc_min=0.2,
        charging_threshold=0.8,
        energy_min={"hpc": 20},
        charging_curve=lambda soc: 1.0,
        consumption=1.0,
        consumption_factor_winter=1.15,
        consumption_factor_summer=0.95,
        speed_optimal=50,
        speed_consumption_coefficient_low=0.00001,
        speed_consumption_coefficient_high=0.00004,
        output=False,
        attractivity={},
        vehicle_group="light_duty_vehicle",
    )
    user_group = UserGroup(1, {})
    car = Car(
        car_type, user_group, 0, False, False, None, None, None, False, soc=0.2
    )
    trip = _FakeTrip(park_time=100)

    car.charge(trip, 100, "fast", "urban_fast", step_size=15, max_charging_time=100)

    assert car.grid_timeseries_list
    assert all(
        event["charging_use_case"] == "urban_fast" for event in car.grid_timeseries_list
    )
