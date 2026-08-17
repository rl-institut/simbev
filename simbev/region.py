import pathlib

import pandas as pd
import numpy as np

from simbev.mid_timeseries import (
    get_timeseries,
    get_empty_timeseries,
    get_purpose_columns,
    strip_numeric_prefix,
)
from simbev.helpers import helpers

# kept as an alias for backward compatibility with existing call sites/tests
_strip_purpose_prefix = strip_numeric_prefix


class RegionType:
    """Constructor for class RegionType.
    Parameters
    ----------
    rs7_type : str
        Type of the region defined by RegioStaR7.
    grid_output : bool
        Identifier if grid output is activated.
    step_size : int
        Step-size of simulation.
    charging_probabilities : dict
        Probabilities for power of charging-point.
    mcs_power : float
        Fixed MCS (Megawatt Charging System) charging power in kW, used for
        heavy_duty_vehicle grid-timeseries column naming.

    Attributes
    ----------
    charging_probabilities : dict
        Probabilities for power of charging-point.
    output : bool
        Identifier if grid output is activated.
    probabilities : dict
        Probabilities related to trip that are dependent on region-type, keyed by vehicle_group.
    rs7_type : int
        Type of the region defined by RegioStaR7.
    step_size : int
        Step-size of simulation.
    time_series : dict
        Timeseries of processed trip-purpose data by vehicle_group, that includes amount of trips started by destination and datetime.
    trip_starts : dict
        Probabilities for start of a trip by datetime, by vehicle_group.
    mcs_power : float
        Fixed MCS charging power in kW.
    """

    def __init__(self, rs7_type, grid_output, step_size, charging_probabilities, mcs_power):
        self.rs7_type = rs7_type
        self.rs3_type = _get_rs3_type(rs7_type)
        self.step_size = step_size
        self.charging_probabilities = charging_probabilities
        self.time_series = {}
        self.trip_starts = {}
        self.probabilities = {}
        self.output = grid_output
        self.mcs_power = mcs_power

    def create_timeseries(self, simbev):
        """Creating timeseries for vehicle, once per active vehicle_group.

        Parameters
        ----------
        simbev : SimBEV object
            Used attributes are start_date, end_date, step_size, input_directory
            and (if commercial vehicles are enabled) commercial_input_directory
            and commercial_vehicle_groups.
        """

        if not self.time_series:
            if simbev.input_type == "probability":
                for vehicle_group, data_directory, purpose_columns in self._vehicle_group_sources(
                    simbev
                ):
                    self.time_series[vehicle_group] = get_timeseries(
                        simbev.start_date,
                        simbev.end_date,
                        self.rs7_type,
                        simbev.step_size,
                        data_directory,
                        purpose_columns=purpose_columns,
                    )
                    trip_starts = self.time_series[vehicle_group].sum(axis=1)
                    self.trip_starts[vehicle_group] = trip_starts / trip_starts.max()
            else:
                self.time_series["private"] = get_empty_timeseries(
                    simbev.start_date,
                    simbev.end_date,
                    simbev.step_size,
                )

    def get_probabilities(self, simbev):
        """Unites probabilities for trip, once per active vehicle_group.

        Parameters
        ----------
        simbev : SimBEV object
            Used attributes are input_directory and (if commercial vehicles
            are enabled) commercial_input_directory and commercial_vehicle_groups.
        """

        self.probabilities = {}
        for vehicle_group, data_directory, _ in self._vehicle_group_sources(simbev):
            self.probabilities[vehicle_group] = self._load_probabilities(
                data_directory, vehicle_group
            )
            self.eliminate_unavailable_purposes(vehicle_group)

    def eliminate_unavailable_purposes(self, vehicle_group):
        """Drops departure-time-series columns for purposes with no
        distance/speed/stand distribution data for this vehicle_group.

        The weekly departure-profile files (winter/spring/summer/fall.csv)
        don't apply the same minimum-record threshold as the distance/speed/
        stand files, so a purpose can have a nonzero departure share in a
        region while having no distribution data to actually compute a trip
        there. Dropping it here (rather than failing later in Trip.create())
        makes get_purpose() only ever select destinations we can sample a
        distance/speed/stand for; its weight is proportionally redistributed
        across the remaining purposes since get_column_by_random_number
        already normalizes by the row sum.
        """
        if vehicle_group not in self.time_series:
            return
        probabilities = self.probabilities[vehicle_group]
        available_purposes = (
            set(probabilities["distance"])
            & set(probabilities["speed"])
            & set(probabilities["stand"])
        )
        time_series = self.time_series[vehicle_group]
        unavailable_columns = [
            column for column in time_series.columns if column not in available_purposes
        ]
        if not unavailable_columns:
            return
        self.time_series[vehicle_group] = time_series.drop(columns=unavailable_columns)
        trip_starts = self.time_series[vehicle_group].sum(axis=1)
        self.trip_starts[vehicle_group] = trip_starts / trip_starts.max()

    def _vehicle_group_sources(self, simbev):
        """Provides (vehicle_group, data_directory, purpose_columns) for every active
        vehicle_group."""

        yield "private", simbev.input_directory, None
        for vehicle_group in simbev.commercial_vehicle_groups:
            data_directory = pathlib.Path(simbev.commercial_input_directory, vehicle_group)
            purpose_columns = get_purpose_columns(data_directory, self.rs7_type)
            yield vehicle_group, data_directory, purpose_columns

    def _load_probabilities(self, data_directory, vehicle_group):
        """Loads distance/speed/stand/charge probabilities for one vehicle_group.

        Parameters
        ----------
        data_directory : pathlib.Path
            Directory of input-data for this vehicle_group.
        vehicle_group : str
            Vehicle group these probabilities belong to.

        Returns
        -------
        dict
        """

        probabilities = {
            "speed": {},
            "distance": {},
            "stand": {},
            "charge": {},
        }

        region_directory = pathlib.Path(data_directory, self.rs7_type)

        # get all csv files in this region directory
        files = region_directory.glob("*.csv")
        for file in files:
            if "charge" in file.stem:
                probabilities["charge"] = pd.read_csv(file, sep=";", decimal=",")
            else:
                key = file.stem.split("_")[0]
                if key in probabilities:
                    # distance, speed or stand
                    df = pd.read_csv(file, sep=",", decimal=".")
                    prefix = "{}_{}_".format(key, self.rs7_type)
                    if file.stem.startswith(prefix):
                        purpose_key = file.stem[len(prefix):]
                    else:
                        purpose_key = file.stem.split("_")[-1]
                    purpose_key = _strip_purpose_prefix(purpose_key)
                    if vehicle_group == "private" and purpose_key == "ridesharing":
                        purpose_key = "private"
                    probabilities[key][purpose_key] = df
        return probabilities


class Region:
    """
    Class that contains information and methods related to the region.

    Parameters
    ----------
    region_id : str
        Identifier for region-type
    region_type : RegionType
        Object of class RegionType
    region_counter : int
        Number of region
    car_dict : dict
        Distribution of cars in region.

    Attributes
    ----------
    analyze_array : ndarray
        Array that contains values of analysis.
    car_amount : int
        Amount of cars in region.
    car_dict : dict
        Distribution of car-types.
    file_name : str
        Name of csv-file for grid timeseries of specific region.
    grid_data_frame : list
        Summarized time-series for whole region.
    grid_time_series : ndarray
        Summarized time-series for whole region.
    header_grid_ts : list
        Header of grid-time-series.
    id : str
        Identifier of region.
    last_time_step : int
        Last time-step of simulation.
    number : int
        Counter of regions simulated
    region_type : RegionType
        Object of class RegionType
    """

    def __init__(
        self, region_id, region_type: RegionType, region_counter, car_dict, scaling
    ):
        self.id = region_id
        self.region_type = region_type
        self.number = region_counter

        self.last_time_step = len(self.region_type.time_series["private"].index) - 1

        self.car_dict = {}

        self.header_grid_ts = []
        self.grid_time_series = []
        self.grid_data_frame = []
        self.car_dict = car_dict
        self.analyze_array = None
        self.scaling = scaling

        self.file_name = "{}_grid_time_series_{}.csv".format(self.number, self.id)

        self.create_grid_timeseries()

    @property
    def car_amount(self):
        """Returns number of vehicles

        Returns
        -------
        int
            Number of vehicles
        """
        return sum(self.car_dict.values())

    def update_grid_timeseries(
        self,
        use_case,
        chargepower,
        power_lis,
        timestep_start,
        timestep_end,
        i,
        park_ts_end,
        car_type,
    ):
        """Writes values in grid-time-series

        Parameters
        ----------
        use_case : str
            Use-case of event.
        chargepower : float
            Average power of charging-event.
        power_lis : float
            Maximum power of charging-point.
        timestep_start : int
            Start of event.
        timestep_end : int
            End of event.
        i : int
            Counter for steps in charging curve.
        park_ts_end : int
            End of parking-time.
        car_type : str
            Type of car (BEV/PHEV and Segment).
        """

        # distribute power to use cases dependent on power
        if self.region_type.output:
            code = "cars_{}_{}".format(use_case, power_lis)
            if code in self.header_grid_ts:
                column = self.header_grid_ts.index(code)
                if i == 0:
                    self.grid_time_series[
                        timestep_start:park_ts_end, column
                    ] += np.float32(1 * self.scaling[car_type])
            # distribute to use cases total
            code_uc_ges = "{}_total_power".format(use_case)
            if code_uc_ges in self.header_grid_ts:
                column = self.header_grid_ts.index(code_uc_ges)
                self.grid_time_series[
                    timestep_start:timestep_end, column
                ] += np.float32(chargepower * self.scaling[car_type])

            # add to total amount
            column = self.header_grid_ts.index("total_power")
            self.grid_time_series[timestep_start:timestep_end, column] += np.float32(
                chargepower * self.scaling[car_type]
            )

    def get_purpose(self, rng, time_step, vehicle_group="private"):
        """Determinants purpose of trip.

        Parameters
        ----------
        rng : Generator
            Random number generator
        time_step : int
            Time-step of simulation.
        vehicle_group : str
            Vehicle group of the car (determines which trip-purpose
            distribution to sample from). Defaults to "private".

        Returns
        -------
        str
            Destination of trip.
        """
        random_number = rng.random()
        purpose_probabilities = self.region_type.time_series[vehicle_group].iloc[
            time_step
        ]
        return helpers.get_column_by_random_number(purpose_probabilities, random_number)

    def get_probability(self, rng, destination, key, vehicle_group="private"):
        """Gets properties for trip in use of probabilities

        Parameters
        ----------
        rng : Generator
            Random number generator.
        destination : str
            Destination of trip.
        key : str
            Key for probability.
        vehicle_group : str
            Vehicle group of the car (determines which probability data to
            sample from). Defaults to "private".

        Returns
        -------
        float
            probability for parameter.

        Raises
        ------
        ValueError
            If destination is hpc.
        """

        if destination == "hpc":
            raise ValueError(
                "Destination {} is not accepted in get probability!".format(destination)
            )
        probabilities = self.region_type.probabilities[vehicle_group][key][destination]
        prob = probabilities.sample(n=1, weights="distribution", random_state=rng)
        return prob.iat[0, -1]

    def create_grid_timeseries(self):
        """Constructs grid-time-series"""
        header_slow = list(self.region_type.charging_probabilities["slow"].columns)
        header_fast = list(self.region_type.charging_probabilities["fast"].columns)
        if "0" in header_slow:
            header_slow.remove("0")
        if "0" in header_fast:
            header_fast.remove("0")
        time_series = self.region_type.time_series["private"]
        time_stamps = np.array(time_series.index.to_pydatetime())
        self.header_grid_ts = ["timestep", "timestamp", "total_power"]
        use_cases = [
            "home_detached",
            "home_apartment",
            "work",
            "street",
            "retail",
            "urban_fast",
            "highway_fast",
        ]
        # commercial vehicle_groups are only present once at least one is active
        if len(self.region_type.time_series) > 1:
            use_cases.append("depot")
        if "heavy_duty_vehicle" in self.region_type.time_series:
            use_cases.append("mcs")
        private_use_cases = ("home_detached", "home_apartment", "work", "retail", "street", "depot")
        for uc in use_cases:
            self.header_grid_ts.append("{}_total_power".format(uc))
            if uc in private_use_cases:
                for power in header_slow:
                    self.header_grid_ts.append("cars_{}_{}".format(uc, power))

            if "_fast" in uc:
                for power in header_fast:
                    self.header_grid_ts.append("cars_{}_{}".format(uc, power))

            if uc == "mcs":
                # MCS has a single fixed power, not a probability-drawn tier
                self.header_grid_ts.append(
                    "cars_mcs_{}".format(self.region_type.mcs_power)
                )

        self.grid_time_series = np.float32(
            np.zeros((len(time_stamps), len(self.header_grid_ts)))
        )

    def export_grid_timeseries(self, region_directory):
        """
        Exports the grid time series to a .csv file.

        Parameters
        ----------
        region_directory : WindowsPath
            Save-directory for the region.
        """
        if self.region_type.output:
            data = pd.DataFrame(self.grid_time_series)
            data.columns = self.header_grid_ts
            data["timestamp"] = self.region_type.time_series["private"].index

            # remove first week from dataframe
            week_time_steps = int(24 * 7 * 60 / self.region_type.step_size)
            data["timestep"] = data.index
            data["timestep"] -= week_time_steps
            data = data.loc[(data["timestep"]) >= 0]
            data = data.drop(columns=["timestep"])
            data = data.round(4)
            timestamp = data["timestamp"]
            cars_per_uc = data.filter(regex="cars").apply(np.ceil).astype(int)
            totals = data.filter(regex="total")
            self.grid_data_frame = pd.concat([timestamp, totals, cars_per_uc], axis=1)
            self.grid_data_frame.to_csv(
                pathlib.Path(region_directory, self.file_name), index=False
            )


def _get_rs3_type(rs7_type):
    rs7_to_3_type_dict = {
        "SR_Metro": "urban",
        "SR_Gross": "urban",
        "SR_Mitte": "suburban",
        "LR_Zentr": "suburban",
        "LR_Mitte": "suburban",
        "SR_Klein": "rural",
        "LR_Klein": "rural",
    }
    return rs7_to_3_type_dict[rs7_type]
