from dataclasses import dataclass
import pathlib
import math

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d


@dataclass
class UserGroup:
    """
    Represents a user group with attributes for identification and attractivity values.

    Parameters
    ----------
    user_group : int
        An integer representing the identification of the user group.
    attractivity : dict
        A dictionary containing charging attractivity information for the user group.

    Attributes
    ----------
    user_group : int
        An integer representing the identification of the user group.
    attractivity : dict
        A dictionary containing charging attractivity information for the user group.
    """

    user_group: int
    attractivity: dict


@dataclass
class CarType:
    """Object that describes car-types.

    Attributes
    ----------
    name : str
        Type and class of vehicle.
    battery_capacity : float
        Capacity of battery.
    charging_capacity : dict
        maximum charging-power of vehicle.
    soc_min : soc_min
        Minimum soc that is allowed.
    charging_threshold : float
        Soc threshold for tripping a charging event.
    energy_min : dict
        Minimum energy for charging events by use case.
    charging_curve : dict
        curve that describes charging-power dependent of soc.
    consumption : float
        consumption of car.
    consumption_factor_winter : float
        Multiplicative consumption factor applied during winter months (Dec-Feb).
    consumption_factor_summer : float
        Multiplicative consumption factor applied during summer months (Jun-Aug).
    speed_optimal : float
        Driving speed in km/h at which consumption is lowest.
    speed_consumption_coefficient_low : float
        Coefficient of the speed-consumption curve for speeds at or below speed_optimal.
    speed_consumption_coefficient_high : float
        Coefficient of the speed-consumption curve for speeds above speed_optimal.
    output : bool
        Setting for output.
    attractivity : pd.DataFrame

    analyze_mid : bool
        Setting for analysis-output
    label : str
        Drive type of vehicle.
    vehicle_group : str
        Vehicle group the car-type belongs to (determines which trip-purpose
        distributions and private-charging roles apply, see
        PRIVATE_CHARGING_ROLES). Defaults to "private" (private Pkw, today's
        behavior). Commercial vehicle groups are "pkw_commercial" (gewerbliche
        Pkw), "light_duty_vehicle" and "heavy_duty_vehicle".
    """

    name: str
    battery_capacity: float
    charging_capacity: dict
    soc_min: float
    charging_threshold: float
    energy_min: dict
    charging_curve: interp1d
    consumption: float
    consumption_factor_winter: float
    consumption_factor_summer: float
    speed_optimal: float
    speed_consumption_coefficient_low: float
    speed_consumption_coefficient_high: float
    output: bool
    attractivity: pd.DataFrame
    analyze_mid: bool = False
    label: str = None
    vehicle_group: str = "private"


# Maps a vehicle-group's trip-purpose destinations to the private-charging
# use case they trigger. Purposes not listed here fall through to the
# existing public street/retail/hpc cascade (unchanged behavior). "private"
# is today's exact private-Pkw logic, re-expressed as data.
PRIVATE_CHARGING_ROLES = {
    "private": {
        "home": "home",
        "work": "work",
        "shopping": "retail",
    },
    "pkw_commercial": {
        "nach_hause": "home",
        "arbeitsplatz": "work",
        "rueckfahrt_betrieb": "depot",
        "einkauf": "retail",
    },
    "light_duty_vehicle": {
        "rueckfahrt_betrieb": "depot",
    },
    "heavy_duty_vehicle": {
        "rueckfahrt_betrieb": "depot",
    },
}


def vehicle_group_has_role(vehicle_group, role):
    """Returns whether vehicle_group's PRIVATE_CHARGING_ROLES mapping includes
    the given private-charging role (e.g. "home", "work").

    Parameters
    ----------
    vehicle_group : str
    role : str

    Returns
    -------
    bool
    """
    return role in PRIVATE_CHARGING_ROLES.get(vehicle_group, {}).values()


def default_starting_status(vehicle_group):
    """Returns the purpose destination a car of vehicle_group is assumed to
    be parked at when the simulation starts (seeds Car.status, i.e. the
    location of the very first trip's "stand"/dwell-time lookup).

    Prefers the group's "home"-role purpose (e.g. "home" for private Pkw,
    "nach_hause" for pkw_commercial - the vehicle's private residence).
    Vehicle_groups without a home role (light_duty_vehicle, heavy_duty_vehicle)
    fall back to their "depot"-role purpose (e.g. "rueckfahrt_betrieb") - the
    vehicle's base/depot is the closest equivalent starting location. Falls
    back to "home" for an unknown/unmapped vehicle_group, matching the
    private-Pkw default.

    Parameters
    ----------
    vehicle_group : str

    Returns
    -------
    str
    """
    roles = PRIVATE_CHARGING_ROLES.get(vehicle_group, {})
    for purpose, role in roles.items():
        if role == "home":
            return purpose
    for purpose, role in roles.items():
        if role == "depot":
            return purpose
    return "home"


def analyze_charge_events(output_df: pd.DataFrame):
    """Analyzes charging events in the timeseries of one vehicle.

    Parameters
    ----------
    output_df : Dataframe
        Specific time series for given vehicle.

    Returns
    -------
    ndarray
        Returns information about charging events of vehicle in whole timeframe.
    """
    # todo: addapt analysis to new use cases
    charge_events = output_df.loc[output_df["energy_grid"] > 0]
    event_count = str(len(charge_events.index))
    hpc_count = len(
        charge_events.loc[
            (charge_events["use_case"] == "hpc")
            | (charge_events["use_case"] == "mcs")
            | (charge_events["use_case"] == "public_fast")
            | (charge_events["use_case"] == "public_highway")
        ].index
    )
    max_time = charge_events["event_time"].max()
    min_time = charge_events["event_time"].min()
    avg_time = round(charge_events["event_time"].mean(), 4)
    max_charge = charge_events["energy_grid"].max()
    min_charge = round(charge_events["energy_grid"].min(), 4)
    avg_charge = round(charge_events["energy_grid"].mean(), 4)
    hpc_avg_charge = (
        charge_events["energy_grid"]
        .loc[
            (charge_events["use_case"] == "hpc")
            | (charge_events["use_case"] == "mcs")
            | (charge_events["use_case"] == "public_fast")
            | (charge_events["use_case"] == "public_highway")
        ]
        .mean()
    )
    home_avg_charge = (
        charge_events["energy_grid"].loc[charge_events["use_case"] == "home"].mean()
    )
    work_avg_charge = (
        charge_events["energy_grid"].loc[charge_events["use_case"] == "work"].mean()
    )
    public_avg_charge = (
        charge_events["energy_grid"]
        .loc[
            (charge_events["use_case"] == "public")
            | (charge_events["use_case"] == "retail")
        ]
        .mean()
    )

    # counting public and private charging events
    public_count = len(
        charge_events.loc[
            (charge_events["use_case"] == "public")
            | (charge_events["use_case"] == "hpc")
            | (charge_events["use_case"] == "mcs")
            | (charge_events["use_case"] == "public_fast")
            | (charge_events["use_case"] == "public_highway")
            | (charge_events["use_case"] == "retail")
        ].index
    )
    private_count = len(
        charge_events.loc[
            (charge_events["use_case"] == "home")
            | (charge_events["use_case"] == "work")
            | (charge_events["use_case"] == "depot")
        ].index
    )

    return np.array(
        [
            event_count,
            hpc_count,
            max_time,
            min_time,
            avg_time,
            max_charge,
            min_charge,
            avg_charge,
            hpc_avg_charge,
            home_avg_charge,
            work_avg_charge,
            public_avg_charge,
            public_count,
            private_count,
        ]
    )


def analyze_drive_events(output_df: pd.DataFrame, car_type: str):
    """Analyzes driving events in the timeseries of one vehicle.

    Parameters
    ----------
    output_df : Dataframe
        Specific time series for given vehicle.
    car_type : str
        Type of vehicle.

    Returns
    -------
    ndarray
        Returns information about driving events of vehicle in whole timeframe.
    """

    drive_events = output_df.loc[output_df["energy_battery"] < 0]
    event_count = len(drive_events.index)
    max_time = drive_events["event_time"].max()
    min_time = drive_events["event_time"].min()
    avg_time = round(drive_events["event_time"].mean(), 4)
    max_consumption = abs(drive_events["energy_battery"].min())
    min_consumption = abs(drive_events["energy_battery"].max())
    avg_consumption = round(abs(drive_events["energy_battery"].mean()), 4)
    # mid analysis
    avg_distance = round(drive_events["distance"].mean(), 4)
    distance_cumulated = round(drive_events["distance"].sum(), 4)
    distance_home = round(
        drive_events["distance"].loc[drive_events["destination"] == "home"].mean(), 4
    )
    distance_work = round(
        drive_events["distance"].loc[drive_events["destination"] == "work"].mean(), 4
    )
    distance_private = round(
        drive_events["distance"].loc[drive_events["destination"] == "private"].mean(), 4
    )
    distance_leisure = round(
        drive_events["distance"].loc[drive_events["destination"] == "leisure"].mean(), 4
    )
    distance_shopping = round(
        drive_events["distance"].loc[drive_events["destination"] == "shopping"].mean(),
        4,
    )
    distance_hpc = round(
        drive_events["distance"].loc[drive_events["destination"] == "hpc"].mean(), 4
    )
    distance_school = round(
        drive_events["distance"].loc[drive_events["destination"] == "school"].mean(), 4
    )
    distance_business = round(
        drive_events["distance"].loc[drive_events["destination"] == "business"].mean(),
        4,
    )

    return np.array(
        [
            car_type,
            event_count,
            max_time,
            min_time,
            avg_time,
            max_consumption,
            min_consumption,
            avg_consumption,
            avg_time,
            avg_distance,
            distance_home,
            distance_work,
            distance_business,
            distance_school,
            distance_shopping,
            distance_private,
            distance_leisure,
            distance_hpc,
            distance_cumulated,
        ]
    )


def get_consumption_factor(
    month,
    speed,
    consumption_factor_winter,
    consumption_factor_summer,
    speed_optimal,
    speed_consumption_coefficient_low,
    speed_consumption_coefficient_high,
):
    """Determines the multiplicative consumption factor of a drive based on season and speed.

    The seasonal influence models effects like heating/cooling and battery efficiency
    losses in cold weather. The speed influence follows an asymmetric parabola with its
    minimum at speed_optimal: consumption stays close to the minimum for speeds at or
    below speed_optimal (BEVs stay efficient in low-speed/city driving thanks to
    regenerative braking and low aerodynamic drag), while consumption rises noticeably
    for speeds above speed_optimal (aerodynamic drag grows with the square of speed).

    Parameters
    ----------
    month : int
        Month of the drive (1-12), used to determine the season.
    speed : float
        Average driving speed of the drive in km/h.
    consumption_factor_winter : float
        Consumption factor applied during winter months (Dec, Jan, Feb).
    consumption_factor_summer : float
        Consumption factor applied during summer months (Jun, Jul, Aug).
    speed_optimal : float
        Driving speed in km/h at which consumption is lowest.
    speed_consumption_coefficient_low : float
        Coefficient of the speed-consumption curve for speeds at or below speed_optimal.
    speed_consumption_coefficient_high : float
        Coefficient of the speed-consumption curve for speeds above speed_optimal.

    Returns
    -------
    float
        Combined consumption factor to be multiplied with the base consumption of a car.
    """
    if month in (12, 1, 2):
        season_factor = consumption_factor_winter
    elif month in (6, 7, 8):
        season_factor = consumption_factor_summer
    else:
        season_factor = 1.0

    speed_consumption_coefficient = (
        speed_consumption_coefficient_low
        if speed <= speed_optimal
        else speed_consumption_coefficient_high
    )
    speed_factor = 1 + speed_consumption_coefficient * (speed - speed_optimal) ** 2

    return season_factor * speed_factor


class Car:
    """Describes a vehicle. Contains all information and methods of that vehicle.

    Parameters
    ----------
    car_type : CarType
        Includes all information regarding the vehicle.
    number : int
        Number of the vehicle.
    work_parking : bool
        Identifier for private parking at work.
    home_parking : bool
        Identifier for private parking at work.
    work_capacity
        Power of LIS at work
    home_capacity
        Power of LIS at work
    depot_parking : bool
        Identifier for private parking/charging at the vehicle's Betriebsgelände (company depot). Only relevant for commercial vehicle_groups.
    depot_capacity
        Power of LIS at the depot.
    region : Region
        Includes data related to current region
    soc : float
        Soc of car.
    status : str
        Location of car.

    Attributes
    ----------
    car_type : CarType
        Includes all information regarding the vehicle.
    file_name : str
        Name of the csv-file that contains.
    home_capacity
        Power of charging-point at work.
    home_parking : bool
        Identifier if there is private-parking at home.
    hpc_data : dict
        Configuration-data for hpc charging.
    hpc_pref : float
        Value of attraction for hpc of vehicle.
    number : int
        Number of the vehicle.
    output : dict
        timeseries of vehicle that contains output-data for every event of vehicle.
    region : Region
        Includes data related to current region.
    remaining_range : float
        Remaining range of vehicle.
    soc : float
        Soc of vehicle.
    soc_start : float
        Soc at start of event.
    status : str
        Location of car.
    usable_soc : float
        soc that is usable for the next drive.
    user_spec : str
        Specification of the user-group the vehicle belongs to.
    work_parking : bool
        Identifier for private parking at work.
    work_capacity
        Power of charging-point at work
    """

    def __init__(
        self,
        car_type: CarType,
        user_group: UserGroup,
        number: int,
        work_parking,
        home_parking,
        work_capacity,
        home_capacity,
        region,
        home_detached,
        eta_cp: float = 1.0,
        soc: float = 1.0,
        status: str = None,
        private_only=False,
        fast_charging_threshold=50,
        depot_parking=False,
        depot_capacity=None,
    ):
        self.car_type = car_type
        self.user_group = user_group
        self.soc_start = soc
        self.soc = soc
        self.work_parking = work_parking
        self.home_parking = home_parking
        self.work_capacity = work_capacity
        self.home_capacity = home_capacity
        self.depot_parking = depot_parking
        self.depot_capacity = depot_capacity
        self.status = (
            status if status is not None else default_starting_status(car_type.vehicle_group)
        )
        self.number = number
        self.region = region
        self.home_detached = home_detached  # Describes if car is at home in apartment building or detached house
        self.eta_cp = eta_cp
        self.private_only = private_only
        self.fast_charging_threshold = fast_charging_threshold
        self.driving_profile = None

        # lists to track output data
        self.output = {
            "timestamp": [],
            "event_start": [],
            "event_time": [],
            "location": [],
            "use_case": [],
            "charging_use_case": [],
            "soc_start": [],
            "soc_end": [],
            "energy_battery": [],
            "energy_grid": [],
            "station_charging_capacity": [],
            "average_charging_power": [],
            "destination": [],
            "distance": [],
        }

        self.grid_timeseries_list = []

        self.file_name = "{}_{:05d}_{}kWh_events.csv".format(
            car_type.name, number, car_type.battery_capacity
        )

    def _update_activity(
        self,
        timestamp,
        event_start,
        event_time,
        distance=0,
        destination="",
        nominal_charging_capacity=0,
        charging_power=0,
        charging_use_case=None,
    ):
        """Records newest energy and activity

        Parameters
        ----------
        timestamp : Timestamp
            Date and time of event.
        event_start : int
            start timestep of event
        event_time : int
            duration of event in timesteps.
        nominal_charging_capacity : int
            Nominal charging-power of event.
        charging_power : int
            Charging-power of event.
        """
        if self.car_type.output:
            self.output["timestamp"].append(timestamp)
            self.output["event_start"].append(np.int32(event_start))
            self.output["event_time"].append(np.int32(event_time))
            self.output["location"].append(self.status)
            self.output["use_case"].append(
                self._get_usecase(nominal_charging_capacity, charging_use_case)
            )
            self.output["charging_use_case"].append(charging_use_case)
            self.output["soc_start"].append(
                round(
                    np.float32(
                        self.output["soc_end"][-1]
                        if len(self.output["soc_end"]) > 0
                        else self.soc_start
                    ),
                    4,
                )
            )
            self.output["soc_end"].append(round(np.float32(self.soc), 4))
            charging_demand = self._get_last_charging_demand()
            consumption = self._get_last_consumption()
            # Fills in charging demand or consumption for battery (one is always zero).
            self.output["energy_battery"].append(
                np.float32(charging_demand + consumption)
            )
            # Fills in charging demand for that is pulled by the grid (only when charging).
            self.output["energy_grid"].append(
                round(np.float32(charging_demand / self.eta_cp), 3)
            )
            self.output["station_charging_capacity"].append(
                np.float32(nominal_charging_capacity)
            )
            self.output["average_charging_power"].append(
                round(np.float32(charging_power), 4)
            )
            self.output["distance"].append(np.float32(distance))
            self.output["destination"].append(destination)

    def park(self, trip):
        """Parking event, used for standing times without charging.

        Parameters
        ----------
        trip : Trip
        """
        self._update_activity(
            trip.park_timestamp, trip.park_start, trip.park_time, charging_use_case=""
        )

    def charge(
        self,
        trip,
        power,
        charging_type,
        charging_use_case,
        step_size=None,
        max_charging_time=None,
    ):
        """Function for charging.

        Parameters
        ----------
        trip : Trip
            Includes information about trip.
        power : float
            Power of charging-point.
        charging_type : str
            Type of charging (slow or fast)
        charging_use_case : str
            Charging use case of charging event.
        step_size : int
            Step-size of simulation.
        max_charging_time : int
            Maximum possible time spend charging.
        """

        if self.soc >= self.car_type.charging_threshold:
            power = 0

        avg_power = 0

        soc_end = 1
        if charging_type == "fast":
            soc_end = trip.rng.uniform(
                trip.simbev.hpc_data["soc_end_min"], trip.simbev.hpc_data["soc_end_max"]
            )
            if (
                power != 0
                and self.car_type.vehicle_group == "heavy_duty_vehicle"
                and self._estimate_fast_charging_minutes(power, soc_end)
                > trip.simbev.mcs_time_threshold
            ):
                # HPC would take too long for this truck - switch to MCS
                # (Megawatt Charging System) instead. Everything else about
                # the charging decision (soc_end target, max_charging_time,
                # ...) stays exactly as for a normal fast-charge.
                power = trip.simbev.mcs_power
                charging_use_case = "mcs"

        if max_charging_time > trip.park_time and charging_type == "slow":
            max_charging_time = trip.park_time

        if power != 0:
            charging_time, avg_power, power, soc = self.charging_curve(
                trip,
                power,
                step_size,
                max_charging_time,
                charging_type,
                charging_use_case,
                soc_end,
            )
            self.soc = soc
        else:
            charging_time = 0

        park_time = (
            charging_time
            if charging_type == "fast" and charging_time > 0
            else trip.park_time
        )
        self._update_activity(
            trip.park_timestamp,
            trip.park_start,
            park_time,
            nominal_charging_capacity=power,
            charging_power=avg_power,
            charging_use_case=charging_use_case,
        )

        return charging_time

    def charge_home(self, trip):
        """Function for initiation of charging-event in use-case home.

        Parameters
        ----------
        trip : Trip
            Includes information about current trip.
        """
        if self.home_detached:
            charging_use_case = "home_detached"
        else:
            charging_use_case = "home_apartment"

        if self.home_capacity is not None:
            self.charge(
                trip,
                self.home_capacity,
                "slow",
                charging_use_case,
                step_size=self.region.region_type.step_size,
                max_charging_time=trip.park_time,
            )
        else:
            raise ValueError("Home charging attempted but power is None!")

    def charge_work(self, trip):
        """Function for initiation of charging-event in use-case work.

        Parameters
        ----------
        trip : Trip
            Includes information about current trip.
        """

        if self.work_capacity is not None:
            self.charge(
                trip,
                self.work_capacity,
                "slow",
                "work",
                step_size=self.region.region_type.step_size,
                max_charging_time=trip.park_time,
            )
        else:
            raise ValueError("Work charging attempted but power is None!")

    def charge_depot(self, trip):
        """Function for initiation of charging-event in use-case depot (Betriebsgelände).

        Parameters
        ----------
        trip : Trip
            Includes information about current trip.
        """

        if self.depot_capacity is not None:
            self.charge(
                trip,
                self.depot_capacity,
                "slow",
                "depot",
                step_size=self.region.region_type.step_size,
                max_charging_time=trip.park_time,
            )
        else:
            raise ValueError("Depot charging attempted but power is None!")

    def charge_public(self, trip, station_capacity, max_parking_time, use_case):
        """Function for initiation of charging-event in public use cases.

        Parameters
        ----------
        trip : Trip
            Includes information about current trip.
        station_capacity : float
            Charging power of charging infrastructure in kW.
        max_parking_time : int
            Maximum possible parking time in timesteps
        use_case : str
            Charging use case
        """
        charge_type = "slow"
        if station_capacity > trip.simbev.fast_charge_threshold:
            use_case = "urban_fast"
            charge_type = "fast"
        self.charge(
            trip,
            station_capacity,
            charge_type,
            use_case,
            step_size=self.region.region_type.step_size,
            max_charging_time=max_parking_time,
        )

    def _estimate_fast_charging_minutes(self, power, soc_end):
        """Analytically estimates fast-charging duration in minutes for a
        given power and target soc_end, without drawing random numbers or
        mutating any state.

        Used only to decide whether MCS should replace HPC for
        heavy_duty_vehicle (see charge()). Mirrors the time computation at
        the core of charging_curve(), skipping its per-timestep grid-dict
        bookkeeping and max_charging_time truncation, since only the total
        untruncated time is needed for that decision.

        Parameters
        ----------
        power : float
            Power of the charging-point under consideration (e.g. the
            HPC power that was drawn).
        soc_end : float
            Soc-target of the charging-event.

        Returns
        -------
        float
            Estimated charging duration in minutes.
        """
        soc_start = self.soc
        if self.car_type.charging_capacity["fast"] == 0 or soc_end <= soc_start:
            return 0.0

        soc_delta = (soc_end - soc_start) / 10
        charging_soc_array = np.arange(
            soc_start + soc_delta / 2, soc_end + soc_delta / 2, soc_delta
        )
        charging_soc_array[-1] = min(charging_soc_array[-1], 1)

        charging_minutes = 0.0
        for soc in charging_soc_array:
            power_at_soc = min(
                self.car_type.charging_curve(soc) * self.car_type.charging_capacity["fast"],
                power,
            )
            charging_minutes += (
                soc_delta * self.car_type.battery_capacity / (power_at_soc * self.eta_cp) * 60
            )
        return charging_minutes

    def charging_curve(
        self,
        trip,
        power,
        step_size,
        max_charging_time,
        charging_type,
        charging_use_case,
        soc_end,
    ):
        """Implementation of charging curve. The charging-curve is based on a 3rd degree polynomial function.
        The charging-functions is sliced into 10 sections. These sections are fitted into the time-steps.

        Parameters
        ----------
        trip : Trip
            Includes information about current trip.
        power : float
            Power of charging-point.
        step_size : int
            Step-size of simulation.
        max_charging_time : int
            Maximum possible time spend charging.
        charging_type : str
            Type of charging ("fast" or "slow")
        charging_use_case : str
            Charging use case (relevant for end of charging calculation)
        soc_end : float
            Soc-target of charging-event.

        Returns
        -------
        tuple[int,float,float,float]
            Returns charging parameters including charging-time, average power, power of charging-point and target-soc.
        """

        soc_start = self.soc

        if power >= trip.simbev.fast_charge_threshold:
            charging_type = "fast"
            soc_end = trip.rng.uniform(
                trip.simbev.hpc_data["soc_end_min"],
                trip.simbev.hpc_data["soc_end_max"],
            )

        if self.car_type.charging_capacity[charging_type] == 0:
            return trip.park_time, 0, 0, soc_start

        # check if min charging energy is charged
        if (
            (soc_end - soc_start) * self.car_type.battery_capacity
        ) <= self.car_type.energy_min[self._get_usecase(power, charging_use_case)]:
            return trip.park_time, 0, 0, soc_start

        # set up parameters for charging curve
        soc_delta = (soc_end - soc_start) / 10
        # get array for avarge soc for each charging-step. Needed to get charging-power of soc-dependent charging-curve.
        charging_soc_array = np.arange(
            soc_start + soc_delta / 2, soc_end + soc_delta / 2, soc_delta
        )
        charging_soc_array[-1] = min(charging_soc_array[-1], 1)
        power_array = np.zeros(len(charging_soc_array))
        charging_time_array = np.zeros(len(charging_soc_array))

        for index, soc in enumerate(charging_soc_array):
            power_array[index] = min(
                (
                    (self.car_type.charging_curve(soc))
                    * self.car_type.charging_capacity[charging_type]
                ),
                power,
            )
            charging_time_array[index] = (
                soc_delta
                * self.car_type.battery_capacity
                / (power_array[index] * trip.simbev.eta_cp)
                * 60
            )

        charging_time = sum(charging_time_array)
        charged_energy_list = []
        time_steps = math.ceil(charging_time / step_size)

        # iterate through all timesteps the charging event is part of
        for charging_time_step in range(time_steps):
            if (
                max_charging_time is not None
                and charging_time_step >= max_charging_time
            ):
                soc_end = min(
                    1,
                    soc_start
                    + sum(charged_energy_list)
                    * trip.simbev.eta_cp
                    / self.car_type.battery_capacity,
                )
                # check if min charging energy is charged
                if (
                    (soc_end - soc_start) * self.car_type.battery_capacity
                ) <= self.car_type.energy_min[self._get_usecase(power, charging_use_case)]:
                    return trip.park_time, 0, 0, soc_start
                time_steps = max_charging_time
                break

            time_sum = 0  # duration of section in charging curve
            charging_section_counter = (
                0  # counter for charging section fitted in timeframe
            )
            # fill array for charging in timestep
            while time_sum <= step_size and charging_section_counter < len(
                charging_time_array
            ):
                time_sum = time_sum + charging_time_array[charging_section_counter]
                charging_section_counter += 1
            charging_time_sections = charging_time_array[:charging_section_counter]

            time_cutoff = time_sum - step_size  # last charging-step in timestep
            charging_time_sections[
                -1
            ] -= time_cutoff  # charging times of sections that are fitted to timestep
            power_sections = power_array[:charging_section_counter]
            energy_sections_grid = charging_time_sections * power_sections / 60
            energy_sections_battery = (
                charging_time_sections * power_sections * trip.simbev.eta_cp / 60
            )

            charged_energy_list.append(round(sum(energy_sections_grid), 4))

            charging_time_array = charging_time_array[charging_section_counter - 1 :]
            charging_time_array[0] = time_cutoff

            power_array = power_array[charging_section_counter - 1 :]
            chargepower_timestep = sum(energy_sections_grid) * 60 / step_size

            if charging_use_case in ("urban_fast", "highway_fast"):
                park_timestep_end = trip.park_start + time_steps + 1

            else:
                park_timestep_end = (
                    trip.park_start + max_charging_time
                    if max_charging_time < trip.park_time
                    else trip.park_start + trip.park_time
                )

            grid_dict = {
                "charging_use_case": charging_use_case,
                "chargepower_timestep": np.float32(chargepower_timestep),
                "power": np.float32(power),
                "start": trip.park_start + charging_time_step,
                "end": trip.park_start + charging_time_step + 1,
                "time": charging_time_step,
                "park_ts_end": park_timestep_end,
            }
            self.grid_timeseries_list.append(grid_dict)

        chargepower_avgerage = (
            sum(charged_energy_list) / len(charged_energy_list) * 60 / step_size
        )

        return time_steps, chargepower_avgerage, power, soc_end

    def drive(self, distance, start_time, timestamp, duration, destination):
        """Method for driving.

        Parameters
        ----------
        distance : float
            Distance of drive.
        start_time : int
            Start time of drive.
        timestamp : Timestamp
            Start time of drive.
        duration : int
            Duration of drive in time
        destination : str
            Location of destination.

        Returns
        -------
        bool
            Returns if drive is possible.
        """
        if duration <= 0:
            raise ValueError(
                f"Drive duration of vehicle {self.file_name} is {duration} at {timestamp}"
            )

        speed = distance / (duration * self.region.region_type.step_size / 60)
        consumption_factor = get_consumption_factor(
            timestamp.month,
            speed,
            self.car_type.consumption_factor_winter,
            self.car_type.consumption_factor_summer,
            self.car_type.speed_optimal,
            self.car_type.speed_consumption_coefficient_low,
            self.car_type.speed_consumption_coefficient_high,
        )
        soc_delta = (
            self.car_type.consumption
            * distance
            / self.car_type.battery_capacity
            * consumption_factor
        )

        if soc_delta >= self.usable_soc and self.car_type.label == "BEV":
            return False

        self.status = "driving"
        self.soc -= soc_delta
        if self.soc < 0:
            if self.car_type.label == "PHEV":
                self.soc = 0
            else:
                raise ValueError(
                    "SoC of car {} became negative ({})".format(
                        self.car_type.name, self.soc
                    )
                )
        self._update_activity(
            timestamp,
            start_time,
            duration,
            distance=distance,
            destination=destination,
            charging_use_case="",
        )
        self.status = destination
        return True

    def precise_remaining_range(self, speed, month):
        """Calculation of precise remaining range of vehicle for a given speed and month.

        Parameters
        ----------
        speed : float
            Assumed driving speed in km/h for the remaining range.
        month : int
            Month (1-12) of the drive, used to determine the season.

        Returns
        -------
        float
            Returns remaining range of vehicle.
        """
        consumption_factor = get_consumption_factor(
            month,
            speed,
            self.car_type.consumption_factor_winter,
            self.car_type.consumption_factor_summer,
            self.car_type.speed_optimal,
            self.car_type.speed_consumption_coefficient_low,
            self.car_type.speed_consumption_coefficient_high,
        )
        return (
            self.usable_soc
            * self.car_type.battery_capacity
            / (self.car_type.consumption * consumption_factor)
        )

    def remaining_range(self, speed, month):
        """Returns remaining range of vehicle for a given speed and month.

        Parameters
        ----------
        speed : float
            Assumed driving speed in km/h for the remaining range.
        month : int
            Month (1-12) of the drive, used to determine the season.
        """
        # eta used to prevent rounding errors. reduces effective range by 100m
        eta = 0.1
        return max(self.precise_remaining_range(speed, month) - eta, 0)

    @property
    def usable_soc(self):
        """Calculation of usable soc.

        Returns
        -------
        float
            Returns soc that is usable.
        """
        return self.soc - self.car_type.soc_min

    def _get_last_charging_demand(self):
        """Calculates energy used for last charging-event.

        Returns
        -------
        float
            Returns energy used for last charging-event.
        """
        if len(self.output["soc_start"]):
            charging_demand = self.output["soc_end"][-1] - self.output["soc_start"][-1]
            charging_demand *= self.car_type.battery_capacity
            return max(round(charging_demand, 4), 0)
        return 0

    def _get_last_consumption(self):
        """Calculates energy used for last driving-event.

        Returns
        -------
        float
            Returns energy used for last driving-event.
        """
        if len(self.output["soc_start"]):
            last_consumption = self.output["soc_end"][-1] - self.output["soc_start"][-1]
            last_consumption *= self.car_type.battery_capacity
            return min(round(last_consumption, 4), 0)
        return 0

    def _get_usecase(self, power, charging_use_case=None):
        """Determines use-case of parking-event.

        Parameters
        ----------
        power : int
            Power of charging-point.
        charging_use_case : str, optional
            Charging use case of the current charging event, if any (e.g.
            "mcs"). Used to distinguish MCS from regular HPC charging, since
            both draw power above fast_charging_threshold.

        Returns
        -------
        str
            Returns use-case of event.
        """
        if self.status == "driving":
            return ""
        role = PRIVATE_CHARGING_ROLES.get(self.car_type.vehicle_group, {}).get(
            self.status
        )
        if role == "work" and self.work_parking:
            return "work"
        if role == "home" and self.home_parking:
            return "home"
        if role == "depot" and self.depot_parking:
            return "depot"
        if charging_use_case == "mcs":
            return "mcs"
        if power >= self.fast_charging_threshold:
            return "hpc"
        return "public"

    def export(self, region_directory, simbev):
        """
        Exports the output values collected in car object to .csv file.

        Parameters
        ----------
        region_directory : :obj:`pathlib.Path`
            save directory for the region
        simbev : :obj:`SimBEV`
            SimBEV object with scenario information

        Returns
        -------
        ndarray
            Returns summarized information on charging- and driving-events.
        """

        for charge_event in self.grid_timeseries_list:
            self.region.update_grid_timeseries(
                charge_event["charging_use_case"],
                charge_event["chargepower_timestep"],
                charge_event["power"],
                charge_event["start"],
                charge_event["end"],
                charge_event["time"],
                charge_event["park_ts_end"],
                self.car_type.name,
            )
        if self.car_type.output:
            activity = pd.DataFrame(self.output)

            # remove first week from dataframe
            week_time_steps = int(24 * 7 * 60 / simbev.step_size)
            activity["event_start"] -= week_time_steps
            activity = activity.loc[
                (activity["event_start"] + activity["event_time"]) > 0
            ]

            # change first row event if it has charging demand or consumption if it doesn't start at time step 0
            if activity.at[activity.index[0], "event_start"] < 0:
                event_len = activity.at[activity.index[0], "event_time"]
                post_event_len = activity.at[activity.index[1], "event_start"]
                pre_event_len = event_len - post_event_len

                # change charging events
                if activity.at[activity.index[0], "energy_grid"] > 0:
                    pre_demand = (
                        activity.at[activity.index[0], "average_charging_power"]
                        * pre_event_len
                        * simbev.step_size
                        / 60
                    )
                    new_demand = round(
                        max(
                            activity.at[activity.index[0], "energy_grid"] - pre_demand,
                            0,
                        ),
                        4,
                    )
                    activity.at[activity.index[0], "energy_grid"] = float(new_demand)

                # change driving events
                elif activity.at[activity.index[0], "energy_grid"] < 0:
                    new_consumption = round(
                        activity.at[activity.index[0], "energy_grid"]
                        * (post_event_len / event_len),
                        4,
                    )
                    activity.at[activity.index[0], "energy_grid"] = float(
                        new_consumption
                    )

                # adjust value for starting soc in first row
                activity.at[activity.index[0], "soc_start"] = round(
                    np.float32(
                        activity.at[activity.index[0], "soc_end"]
                        - activity.at[activity.index[0], "energy_grid"]
                        / self.car_type.battery_capacity
                    ),
                    4,
                )

                # adjust value for average charging power in first row
                activity.at[activity.index[0], "average_charging_power"] = float(
                    activity.at[activity.index[0], "energy_grid"]
                    / (post_event_len * simbev.step_size / 60)
                )

                # fit first row event to start at time step 0
                activity.at[activity.index[0], "event_start"] = 0
                activity.at[activity.index[0], "event_time"] = post_event_len
                activity.at[activity.index[0], "timestamp"] = simbev.start_date_output

                activity["event_start"] = activity["event_start"]
                activity["event_time"] = activity["event_time"]

            drive_array = analyze_drive_events(activity, self.car_type.name)
            charge_array = analyze_charge_events(activity)
            activity["energy_grid"] = round(activity["energy_grid"], 3)
            if simbev.output_options["car"]:
                activity = activity.drop(columns=["destination", "distance"])
                activity = activity.reset_index(drop=True)
                activity.to_csv(
                    pathlib.Path(region_directory, self.file_name), index=False
                )

            return np.hstack((drive_array, charge_array))
