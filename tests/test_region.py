from types import SimpleNamespace

import numpy as np
import pandas as pd

from simbev.region import Region


def _charging_probabilities(use_case=True):
    probabilities = {
        "slow": pd.DataFrame(
            [[0.5, 0.1, 0.2, 0.2, 0.0]],
            index=["home"],
            columns=["0", "3.7", "11.0", "22.0", "50.0"],
        ),
        "fast": pd.DataFrame(
            [[0.8, 0.2]], index=["urban"], columns=["150.0", "350.0"]
        ),
    }
    if use_case:
        probabilities["use_case"] = pd.DataFrame(
            [
                [1, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0],
                [0, 0.75, 0.15, 0.1, 0, 0],
                [0, 0.9, 0.075, 0.025, 0, 0],
                [0, 0, 0, 0.5, 0.45, 0.05],
                [0, 0, 0, 0.2, 0.7, 0.1],
                [0, 0.7, 0.2, 0.1, 0, 0],
            ],
            index=["home", "work", "retail", "street", "urban_fast", "highway_fast", "depot"],
            columns=["11.0", "22.0", "50.0", "150.0", "250.0", "350.0"],
        )
    return probabilities


def _make_region(use_case=True):
    index = pd.date_range("2011-01-01", periods=96, freq="15min")
    time_series = {
        "private": pd.DataFrame(index=index),
        "pkw_commercial": pd.DataFrame(index=index),
        "heavy_duty_vehicle": pd.DataFrame(index=index),
    }
    region_type = SimpleNamespace(
        time_series=time_series,
        charging_probabilities=_charging_probabilities(use_case),
        mcs_power=1000.0,
        fast_charge_threshold=50.0,
        output=True,
        step_size=15,
    )
    return Region("region", region_type, 0, {}, {"bev_mini": 1})


def _cars_columns(region, use_case):
    prefix = f"cars_{use_case}_"
    return [
        column.removeprefix(prefix)
        for column in region.header_grid_ts
        if column.startswith(prefix)
    ]


def test_cars_columns_cover_the_powers_of_the_use_case_file():
    region = _make_region()

    # powers of the fast file plus 250 kW of the use case file, in order
    assert _cars_columns(region, "urban_fast") == ["150.0", "250.0", "350.0"]
    assert _cars_columns(region, "highway_fast") == ["150.0", "250.0", "350.0"]
    # depot can charge with 150 kW, which is slow charging there
    assert _cars_columns(region, "depot") == ["3.7", "11.0", "22.0", "50.0", "150.0"]
    assert _cars_columns(region, "mcs") == ["1000.0"]


def test_cars_columns_of_public_use_cases_stop_at_the_fast_threshold():
    region = _make_region()

    # 150 kW at street and retail is booked as urban_fast
    assert _cars_columns(region, "street") == ["3.7", "11.0", "22.0", "50.0"]
    assert _cars_columns(region, "retail") == ["3.7", "11.0", "22.0", "50.0"]


def test_cars_columns_without_use_case_file_are_the_probability_file_powers():
    region = _make_region(use_case=False)

    assert _cars_columns(region, "urban_fast") == ["150.0", "350.0"]
    assert _cars_columns(region, "depot") == ["3.7", "11.0", "22.0", "50.0"]


def test_charge_with_250_kw_is_counted_as_occupied_charge_point():
    region = _make_region()

    region.update_grid_timeseries(
        "urban_fast", np.float32(100), np.float32(250), 10, 11, 0, 14, "bev_mini"
    )

    column = region.header_grid_ts.index("cars_urban_fast_250.0")
    assert list(region.grid_time_series[:, column].nonzero()[0]) == [10, 11, 12, 13]
