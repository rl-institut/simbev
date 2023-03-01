from dataclasses import dataclass
import numpy as np
import pandas as pd
import pathlib
import math
from scipy.interpolate import interp1d


@dataclass
class UserGroup:
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
    output : bool
        Setting for output.
    hpc_data : dict
        Config parameters for hpc
    analyze_mid : bool
        Setting for analysis-output
    label : str
        Drive type of vehicle.
    """

    name: str
    battery_capacity: float
    charging_capacity: dict
    soc_min: float
    charging_threshold: float
    energy_min: dict
    charging_curve: interp1d
    # TODO consumption based on speed instead of constant
    consumption: float
    output: bool
    attractivity: pd.DataFrame
    analyze_mid: bool = False
    label: str = None


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
    use_cases = ["home", "work", "public", "retail", "public_fast", "public_highway"]
    # todo: addapt analysis to new use cases
    charge_events = output_df.loc[output_df["energy"] > 0]
    event_count = str(len(charge_events.index))
    hpc_count = len(
        charge_events.loc[
            (charge_events["use_case"] == "hpc")
            | (charge_events["use_case"] == "public_fast")
            | (charge_events["use_case"] == "public_highway")
        ].index
    )
    max_time = charge_events["event_time"].max()
    min_time = charge_events["event_time"].min()
    avg_time = round(charge_events["event_time"].mean(), 4)
    max_charge = charge_events["energy"].max()
    min_charge = round(charge_events["energy"].min(), 4)
    avg_charge = round(charge_events["energy"].mean(), 4)
    hpc_avg_charge = (
        charge_events["energy"]
        .loc[
            (charge_events["use_case"] == "hpc")
            | (charge_events["use_case"] == "public_fast")
            | (charge_events["use_case"] == "public_highway")
        ]
        .mean()
    )
    home_avg_charge = (
        charge_events["energy"].loc[charge_events["use_case"] == "home"].mean()
    )
    work_avg_charge = (
        charge_events["energy"].loc[charge_events["use_case"] == "work"].mean()
    )
    public_avg_charge = (
        charge_events["energy"]
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
            | (charge_events["use_case"] == "public_fast")
            | (charge_events["use_case"] == "public_highway")
            | (charge_events["use_case"] == "retail")
        ].index
    )
    private_count = len(
        charge_events.loc[
            (charge_events["use_case"] == "home")
            | (charge_events["use_case"] == "work")
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

    drive_events = output_df.loc[output_df["energy"] < 0]
    event_count = len(drive_events.index)
    max_time = drive_events["event_time"].max()
    min_time = drive_events["event_time"].min()
    avg_time = round(drive_events["event_time"].mean(), 4)
    max_consumption = abs(drive_events["energy"].min())
    min_consumption = abs(drive_events["energy"].max())
    avg_consumption = round(abs(drive_events["energy"].mean()), 4)
    # mid analysis
    avg_time = round(drive_events["event_time"].mean(), 4)
    avg_distance = round(drive_events["distance"].mean(), 4)
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
        ]
    )


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
        soc: float = 1.0,
        status: str = "home",
        private_only=False,
    ):
        self.car_type = car_type
        self.user_group = user_group
        self.soc_start = soc
        self.soc = soc
        self.work_parking = work_parking
        self.home_parking = home_parking
        self.work_capacity = work_capacity
        self.home_capacity = home_capacity
        self.status = status  # replace with enum?
        self.number = number
        self.region = region
        self.home_detached = home_detached  # Describes if Car is at home in apartment building or detached house
        self.private_only = private_only

        # lists to track output data
        # TODO: swap to np.array for better performance?
        self.output = {
            "timestamp": [],
            "event_start": [],
            "event_time": [],
            "location": [],
            "use_case": [],
            "charging_use_case": [],
            "soc_start": [],
            "soc_end": [],
            "energy": [],
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
            self.output["use_case"].append(self._get_usecase(nominal_charging_capacity))
            self.output["charging_use_case"].append(
                self._get_charging_usecase(nominal_charging_capacity)
            )
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
            self.output["energy"].append(np.float32(charging_demand + consumption))
            self.output["station_charging_capacity"].append(
                np.float32(nominal_charging_capacity)
            )
            self.output["average_charging_power"].append(
                round(np.float32(charging_power), 4)
            )
            self.output["distance"].append(np.float32(distance))
            self.output["destination"].append(destination)

    def park(self, trip):
        # TODO: delete function because not in use

        """Parking Event.

        Parameters
        ----------
        trip : Trip
            .
        """
        self._update_activity(trip.park_timestamp, trip.park_start, trip.park_time)

    def charge(
        self,
        trip,
        power,
        charging_type,
        step_size=None,
        long_distance=None,
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
            Type of charging.
        step_size : int
            Step-size of simulation.
        long_distance : bool
            Indicates if trip is a long distance drive.
        max_charging_time : int
            Maximum possible time spend charging.
        """

        if self.soc >= self.car_type.charging_threshold:
            power = 0

        if charging_type == "slow":
            avg_power = 0

            if power != 0:
                charging_time, avg_power, power, soc = self.charging_curve(
                    trip, power, step_size, max_charging_time, charging_type, soc_end=1
                )
                self.soc = soc

            self._update_activity(
                trip.park_timestamp,
                trip.park_start,
                trip.park_time,
                nominal_charging_capacity=power,
                charging_power=avg_power,
            )

        elif charging_type == "fast":
            if self.car_type.charging_capacity["fast"] == 0:
                raise ValueError(
                    "Vehicle {} has no fast charging capacity but got assigned a HPC event.".format(
                        self.car_type.name
                    )
                )
            soc_end = trip.rng.uniform(
                trip.simbev.hpc_data["soc_end_min"], trip.simbev.hpc_data["soc_end_max"]
            )
            charging_time, avg_power, power, soc = self.charging_curve(
                trip, power, step_size, max_charging_time, charging_type, soc_end
            )
            self.soc = soc
            if long_distance:
                self._update_activity(
                    trip.park_timestamp,
                    trip.park_start,
                    charging_time,
                    nominal_charging_capacity=power,
                    charging_power=avg_power,
                )
            else:
                # update trip properties
                trip.park_time = charging_time
                trip.drive_start = trip.park_start + trip.park_time
                trip.trip_end = trip.drive_start + trip.drive_time
                self._update_activity(
                    trip.park_timestamp,
                    trip.park_start,
                    trip.park_time,
                    nominal_charging_capacity=power,
                    charging_power=avg_power,
                )
            return charging_time
        else:
            raise ValueError(
                "Charging type {} is not accepted in charge function!".format(
                    charging_type
                )
            )

    def charge_home(self, trip):
        """Function for initiation of charging-event in use-case home.

        Parameters
        ----------
        trip : Trip
            Includes information about current trip.
        """

        if self.home_capacity is not None:
            self.charge(
                trip,
                self.home_capacity,
                "slow",
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
                step_size=self.region.region_type.step_size,
                max_charging_time=trip.park_time,
            )
        else:
            raise ValueError("Work charging attempted but power is None!")

    def charging_curve(
        self, trip, power, step_size, max_charging_time, charging_type, soc_end
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
            Type of charging.
        soc_end : int
            Soc-target of charging-event.

        Returns
        -------
        tuple[int,float,float,float]
            Returns charging parameters including charging-time, average power, power of charging-point and target-soc.
        """

        soc_start = self.soc

        # check if min charging energy is charged
        if (
            (soc_end - soc_start) * self.car_type.battery_capacity
        ) <= self.car_type.energy_min[self._get_usecase(power)]:
            return trip.park_time, 0, 0, soc_start

        # set up parameters for charging curve
        soc_delta = (soc_end - soc_start) / 10
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
                soc_delta * self.car_type.battery_capacity / power_array[index] * 60
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
                    + sum(charged_energy_list) / self.car_type.battery_capacity,
                )
                # check if min charging energy is charged
                if (
                    (soc_end - soc_start) * self.car_type.battery_capacity
                ) <= self.car_type.energy_min[self._get_usecase(power)]:
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
            energy_sections = charging_time_sections * power_sections / 60

            charged_energy_list.append(round(sum(energy_sections), 4))

            charging_time_array = charging_time_array[charging_section_counter - 1 :]
            charging_time_array[0] = time_cutoff

            power_array = power_array[charging_section_counter - 1 :]
            chargepower_timestep = sum(energy_sections) * 60 / step_size

            charging_use_case = self._get_charging_usecase(power)

            if (
                charging_use_case == "hpc"
                or charging_use_case == "urban_fast"
                or charging_use_case == "highway_fast"
            ) and trip.car.status == "hpc":
                park_timestep_end = trip.park_start + time_steps

            else:
                park_timestep_end = trip.park_start + max_charging_time

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
        soc_delta = (
            self.car_type.consumption * distance / self.car_type.battery_capacity
        )
        if soc_delta >= self.usable_soc and self.car_type.label == "BEV":
            return False
        else:
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
            )
            self.status = destination
            return True

    @property
    def precise_remaining_range(self):
        """Calculation of precise remaining range of vehicle.

        Returns
        -------
        float
            Returns remaining range of vehicle.
        """
        return (
            self.usable_soc * self.car_type.battery_capacity / self.car_type.consumption
        )

    @property
    def remaining_range(self):
        """Returns remaining range of vehicle."""
        # eta used to prevent rounding errors. reduces effective range by 100m
        eta = 0.1
        return max(
            self.usable_soc * self.car_type.battery_capacity / self.car_type.consumption
            - eta,
            0,
        )

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
        else:
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
        else:
            return 0

    def _get_usecase(self, power):
        """Determines use-case of parking-event.

        Parameters
        ----------
        power : int
            Power of charging-point.

        Returns
        -------
        str
            Returns use-case of event.
        """
        if self.status == "driving":
            return ""
        elif self.work_parking and self.status == "work":
            return "work"
        elif self.home_parking and self.status == "home":
            return "home"
        # TODO: decide on status an requirement for hpc
        elif power >= 150:
            return "hpc"
        else:
            return "public"

    # TODO maybe solve this in charging (Jakob)
    def _get_charging_usecase(self, power):
        """Determines use-case of parking-event.

        Parameters
        ----------
        power : int
            Power of charging-point.

        Returns
        -------
        str
            Returns use-case of event.
        """
        if self.status == "driving":
            return ""
        elif self.work_parking and self.status == "work":
            return "work"
        elif self.home_parking and self.status == "home" and self.home_detached:
            return "home_detached"
        elif self.home_parking and self.status == "home" and not self.home_detached:
            return "home_apartment"
        # TODO: decide on status an requirement for hpc
        elif self.status == "hpc":
            return "highway_fast"
        elif power >= 150:
            return "urban_fast"
        elif self.status == "shopping":
            return "retail"
        else:
            return "street"

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
                if activity.at[activity.index[0], "energy"] > 0:
                    pre_demand = (
                        activity.at[activity.index[0], "average_charging_power"]
                        * pre_event_len
                        * simbev.step_size
                        / 60
                    )
                    new_demand = round(
                        max(activity.at[activity.index[0], "energy"] - pre_demand, 0), 4
                    )
                    activity.at[activity.index[0], "energy"] = new_demand

                # change driving events
                elif activity.at[activity.index[0], "energy"] < 0:
                    new_consumption = round(
                        activity.at[activity.index[0], "energy"]
                        * (post_event_len / event_len),
                        4,
                    )
                    activity.at[activity.index[0], "energy"] = new_consumption

                # adjust value for starting soc in first row
                activity.at[activity.index[0], "soc_start"] = round(
                    np.float32(
                        activity.at[activity.index[0], "soc_end"]
                        - activity.at[activity.index[0], "energy"]
                        / self.car_type.battery_capacity
                    ),
                    4,
                )

                # adjust value for average charging power in first row
                activity.at[activity.index[0], "average_charging_power"] = activity.at[
                    activity.index[0], "energy"
                ] / (post_event_len * simbev.step_size / 60)

                # fit first row event to start at time step 0
                activity.at[activity.index[0], "event_start"] = 0
                activity.at[activity.index[0], "event_time"] = post_event_len
                activity.at[activity.index[0], "timestamp"] = simbev.start_date_output

                activity["event_start"] = activity["event_start"]
                activity["event_time"] = activity["event_time"]

            drive_array = analyze_drive_events(activity, self.car_type.name)
            charge_array = analyze_charge_events(activity)
            if simbev.output_options["car"]:
                activity = activity.drop(columns=["destination", "distance"])
                activity = activity.reset_index(drop=True)
                activity.to_csv(
                    pathlib.Path(region_directory, self.file_name), index=False
                )

            return np.hstack((drive_array, charge_array))
