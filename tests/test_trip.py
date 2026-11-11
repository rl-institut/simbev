from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from simbev.trip import Trip


class _FakeRegion:
    def __init__(self, last_time_step):
        self.last_time_step = last_time_step
        index = pd.date_range("2011-01-01", periods=last_time_step + 1, freq="15min")
        self.region_type = SimpleNamespace(
            time_series={"private": pd.DataFrame(index=index)}
        )


class _FakeCar:
    """BEV that needs exactly one charging stop on its trip."""

    status = "work"
    car_type = SimpleNamespace(label="BEV")

    def __init__(self):
        self.drives = []
        self.charged = False

    def remaining_range(self, speed, month):
        return 1000 if self.charged else 40

    def precise_remaining_range(self, speed, month):
        return 40

    def drive(
        self, distance, start, timestamp, duration, destination, consumption_speed=None
    ):
        self.drives.append(
            {"distance": distance, "start": start, "time": duration, "to": destination}
        )
        return True

    def charge(self, trip, power, charging_type, use_case, step_size, **kwargs):
        self.charged = True
        return 2


def _make_trip(last_time_step, drive_start):
    simbev = SimpleNamespace(
        rng=np.random.default_rng(1),
        step_size=15,
        hpc_data={"distance_min": 0.5, "distance_max": 0.5},
        get_charging_capacity=lambda **kwargs: 150,
    )
    trip = Trip(_FakeRegion(last_time_step), _FakeCar(), 0, simbev, "home", 100)
    trip.speed = 10
    trip.drive_time = 10
    trip.drive_start = drive_start
    trip.drive_timestamp = trip.region.region_type.time_series["private"].index[
        drive_start
    ]
    return trip


def test_final_leg_after_charging_stop_is_cut_at_simulation_end():
    # 20 km to the stop take 2 steps and charging 2 more, so the remaining
    # 80 km (8 steps) would start at step 99, the last one
    trip = _make_trip(last_time_step=99, drive_start=95)

    assert trip._create_fast_charge_events()

    to_stop, final_leg = trip.car.drives
    assert to_stop["to"] == "hpc"
    assert final_leg["start"] == 99
    assert final_leg["time"] == 1
    # distance scales down with the time that is left
    assert final_leg["distance"] == pytest.approx(80 / 8)
    assert trip.trip_end == 100


def test_final_leg_inside_simulation_is_not_changed():
    trip = _make_trip(last_time_step=1000, drive_start=95)

    assert trip._create_fast_charge_events()

    final_leg = trip.car.drives[-1]
    assert final_leg["time"] == 8
    assert final_leg["distance"] == pytest.approx(80)
    assert trip.trip_end == 99 + 8
