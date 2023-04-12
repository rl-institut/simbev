import pandas as pd
import numpy as np
import pathlib
from simbev.mid_timeseries import get_timeseries, get_empty_timeseries
import simbev.helpers.helpers as helpers


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

    Attributes
    ----------
    charging_probabilities : dict
        Probabilities for power of charging-point.
    output : bool
        Identifier if grid output is activated.
    probabilities : dict
        Probabilities related to trip that are dependent on region-type.
    rs7_type : int
        Type of the region defined by RegioStaR7.
    step_size : int
        Step-size of simulation.
    time_series : DataFrame
        Timeseries of processed MiD-data, that includes amount of trips started by destination and datetime.
    trip_starts : Series
        Probabilities for start of a trip by datetime.
    """

    def __init__(self, rs7_type, grid_output, step_size, charging_probabilities):
        self.rs7_type = rs7_type
        self.rs3_type = _get_rs3_type(rs7_type)
        self.step_size = step_size
        self.charging_probabilities = charging_probabilities
        self.time_series = None
        self.trip_starts = None
        self.probabilities = {}
        self.output = grid_output

    def create_timeseries(self, simbev):
        """Creating timeseries for vehicle.

        Parameters .start_date, self.end_date, self.step_size, self.input_directory
        ----------
        start_date : date
            Start-date of simulation.
        end_date : date
            End-date of simulation.
        step_size : int
            Step-size of simulation
        """

        if not self.time_series:
            if simbev.input_type == "probability":
                self.time_series = get_timeseries(
                    simbev.start_date,
                    simbev.end_date,
                    self.rs7_type,
                    simbev.step_size,
                    simbev.input_directory,
                )
                self.trip_starts = self.time_series.sum(axis=1)
                self.trip_starts = self.trip_starts / self.trip_starts.max()
            else:
                self.time_series = get_empty_timeseries(
                    simbev.start_date,
                    simbev.end_date,
                    simbev.step_size,
                )

    def get_probabilities(self, data_directory):
        """Unites probabilities for trip.

        Parameters
        ----------
        data_directory : WindowsPath
            Directory of input-data.
        """

        self.probabilities = {
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
                self.probabilities["charge"] = pd.read_csv(file, sep=";", decimal=",")
            else:
                key = file.stem.split("_")[0]
                if key in self.probabilities:
                    # distance, speed or stand
                    df = pd.read_csv(file, sep=",", decimal=".")
                    purpose_key = file.stem.split("_")[-1]
                    if purpose_key == "ridesharing":
                        purpose_key = "private"
                    self.probabilities[key][purpose_key] = df


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

        self.last_time_step = len(self.region_type.time_series.index) - 1

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

    def get_purpose(self, rng, time_step):
        """Determinants purpose of trip.

        Parameters
        ----------
        rng : Generator
            Random number generator
        time_step : int
            Time-step of simulation.

        Returns
        -------
        int
            Destination of trip.
        """
        random_number = rng.random()
        purpose_probabilities = self.region_type.time_series.iloc[time_step]
        return helpers.get_column_by_random_number(purpose_probabilities, random_number)

    def get_probability(self, rng, destination, key):
        """Gets properties for trip in use of probabilities

        Parameters
        ----------
        rng : Generator
            Random number generator.
        destination : str
            Destination of trip.
        key : str
            Key for probability.

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
        probabilities = self.region_type.probabilities[key][destination]
        prob = probabilities.sample(n=1, weights="distribution", random_state=rng)
        return prob.iat[0, -1]

    def create_grid_timeseries(self):
        """Constructs grid-time-series"""
        header_slow = list(self.region_type.charging_probabilities["slow"].columns) # TODO change if power by usecase
        header_fast = list(self.region_type.charging_probabilities["fast"].columns) # TODO change if power by usecase
        if "0" in header_slow:
            header_slow.remove("0")
        if "0" in header_fast:
            header_fast.remove("0")
        time_series = self.region_type.time_series
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
        for uc in use_cases:
            self.header_grid_ts.append("{}_total_power".format(uc))
            if (
                uc == "home_detached"
                or uc == "home_apartment"
                or uc == "work"
                or uc == "retail"
                or uc == "street"
            ):
                for power in header_slow:
                    self.header_grid_ts.append("cars_{}_{}".format(uc, power))

            if "_fast" in uc:
                for power in header_fast:
                    self.header_grid_ts.append("cars_{}_{}".format(uc, power))

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
            data["timestamp"] = self.region_type.time_series.index

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
