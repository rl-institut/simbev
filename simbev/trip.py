import math
from typing import TYPE_CHECKING
from simbev.helpers.errors import SoCError

if TYPE_CHECKING:
    from simbev.car import Car
    from simbev.region import Region
    from simbev.simbev_class import SimBEV


class Trip:
    """
    Represents a trip that a vehicle can make.

    Parameters
    ----------
    region : Region
        Object where the trip happens.
    car : Car
        Object of class Car.
    time_step : int
        Current time-step
    simbev : SimBEV
        Object that contains superior data.

    Attributes
    ----------
    region : Region
        Object that contains information about the region.
    car : Car
        Object contains information about the vehicle.
    simbev : SimBEV
        Object that contains superior data.
    park_start : int
        Time step where Trip gets initiated (start of parking event).
    park_time : int
        Number of time steps that the car parks.
    drive_start : int
        Time step where driving event starts.
    drive_time : int
        Number of time steps used to drive.
    trip_end : int
        Time step where driving concludes and trip ends.
    drive_found : bool
        Checks if driving event is possible.
    destination : str
        Purpose/destination of next driving event.
    distance : float
        Distance to drive.
    speed : float
        Average driving speed.
    location : str
        Current parking location (purpose).

    Methods
    -------
    create:
        Finds next driving event and sets corresponding attributes.
    execute:
        Sets car to execute the created trip.
    """

    def __init__(
        self,
        region: "Region",
        car: "Car",
        time_step,
        simbev: "SimBEV",
        destination="",
        distance=0,
    ):
        self.destination = destination
        self.distance = distance
        self.speed = 0

        self.park_start = time_step
        self.park_time = 0
        self.real_park_time = None
        self.drive_start = 0
        self.drive_time = 0
        self.trip_end = region.last_time_step + 1
        self.park_timestamp = None
        self.drive_timestamp = None
        self.drive_found = False
        self.extra_urban = False

        self.location = car.status
        self.region = region
        self.car = car
        self.simbev = simbev
        self.rng = simbev.rng
        self.step_size = simbev.step_size
        self.charging_use_case = None

    @classmethod
    def from_driving_profile(cls, region: "Region", car: "Car", simbev: "SimBEV"):
        """
        Generate a list of `Trip` objects based on the driving profile of a car.

        Parameters
        ----------
        region : Region
            A `Region` object representing the geographic region in which the `Car` operates.
        car : Car
            A `Car` object for which to generate the list of `Trip` objects.
        simbev : SimBEV
            A `SimBEV` object representing the EV simulation parameters.

        Returns
        -------
        list of Trip
            A list of `Trip` objects representing the trips taken by the `Car` as defined in its driving profile.
        """
        first_trip = create_trip_from_profile_row(
            car.driving_profile.iloc[0, :], "home", 0, region, car, simbev
        )
        trip_list = [None] * len(car.driving_profile.index)
        trip_list[0] = first_trip

        previous_trip = first_trip
        for count, i in enumerate(car.driving_profile.index[1:]):
            start_step = previous_trip.trip_end
            if start_step > region.last_time_step:
                continue
            trip = create_trip_from_profile_row(
                car.driving_profile.loc[i, :],
                previous_trip.destination,
                start_step,
                region,
                car,
                simbev,
                car.driving_profile.loc[i - 1, "charging_use_case"],
            )
            previous_trip = trip
            trip_list[count + 1] = trip

        last_trip_end = previous_trip.trip_end
        if last_trip_end <= region.last_time_step:
            trip = Trip(region, car, last_trip_end, simbev)
            trip.park_time = region.last_time_step - trip.park_start
            trip.location = previous_trip.destination
            trip.fit_trip_to_timerange()
            trip._set_timestamps()
            trip_list.append(trip)
        return trip_list

    @classmethod
    def from_probability(
        cls, region: "Region", car: "Car", time_step: int, simbev: "SimBEV"
    ):
        """Generate a `Trip` object based on probability input data.

        Parameters
        ----------
        region : Region
            A `Region` object representing the geographic region in which the `Car` operates.
        car : Car
            A `Car` object for which to generate the `Trip`.
        time_step : int
            An integer representing the time step at which to start the `Trip`.
        simbev : SimBEV
            A `SimBEV` object representing the EV simulation parameters.

        Returns
        -------
        Trip
            A `Trip` object representing the trip taken by the `Car` based on the probability of a trip occurring.
        """
        trip = cls(region, car, time_step, simbev)
        trip.create()
        return trip

    def create(self):
        """
        Creates new trip, starting from park_start.
        Calculates standing time, next destination and driving time.
        """

        self.park_time = self.region.get_probability(self.rng, self.location, "stand")
        self.park_time = self.simbev.hours_to_time_steps(self.park_time)
        self.drive_start = self.park_start + self.park_time

        while not self.drive_found and (self.drive_start < self.region.last_time_step):
            if (
                self.rng.random()
                < self.region.region_type.trip_starts.iat[self.drive_start]
            ):
                self.destination = self.region.get_purpose(self.rng, self.drive_start)
                # don't use same destination in a row
                if self.destination == self.car.status:
                    self.drive_start += 1
                    continue
                self.distance = self.region.get_probability(
                    self.rng, self.destination, "distance"
                )
                # check if driving makes sense, max is set as x amount of hours TODO figure out better sanity check
                while self.speed < 5 or self.drive_time > 15:
                    self.speed = self.region.get_probability(
                        self.rng, self.destination, "speed"
                    )
                    self.drive_time = self.distance / self.speed
                self.drive_time = self.simbev.hours_to_time_steps(self.drive_time)
                self.trip_end = self.drive_start + self.drive_time
                self.drive_found = True
                # update park_time
                self.park_time = self.drive_start - self.park_start
            else:
                self.drive_start += 1
        self.fit_trip_to_timerange()
        self._set_timestamps()

    def get_max_parking_time(self, use_case):
        """Determine maximum parking time for this trip and a given use case.

        Parameters
        ----------
        use_case : str
            Charging use case

        Returns
        -------
        int
            maximum parking time in time steps
        """
        if self.real_park_time is None:
            self.real_park_time = self.park_time
        frac_park_start, whole_park_start = math.modf(
            self.park_start / (60 * 24 / self.step_size)
        )
        frac_park_end, whole_park_end = math.modf(
            (self.park_start + self.real_park_time) / (60 * 24 / self.step_size)
        )
        whole_park_start_steps = self.simbev.hours_to_time_steps(whole_park_start * 24)
        frac_park_start_steps = self.simbev.hours_to_time_steps(frac_park_start * 24)
        frac_park_end_steps = self.simbev.hours_to_time_steps(frac_park_end * 24)

        if use_case == "retail":
            if whole_park_end > whole_park_start:
                # if parking starts after the retail threshold time
                if (frac_park_start_steps) >= (
                    self.simbev.threshold_retail_limitation_steps
                ):
                    # put the park end somewhere between the start and midnight
                    upper_bound = self.simbev.hours_to_time_steps(
                        (whole_park_start + 1) * 24
                    )
                    lower_bound = self.park_start + 1
                    mean = (upper_bound + lower_bound) / 2
                    sigma = (mean - (lower_bound)) / 3
                    max_parking_end = int(self.rng.normal(mean, sigma))
                else:
                    # otherwise end somewhere between threshold and midnight
                    upper_bound = self.simbev.hours_to_time_steps(
                        (whole_park_start + 1) * 24
                    )
                    lower_bound = (
                        whole_park_start_steps
                        + self.simbev.threshold_retail_limitation_steps
                    )
                    mean = (upper_bound + lower_bound) / 2
                    sigma = (mean - (lower_bound)) / 3
                    max_parking_end = int(self.rng.normal(mean, sigma))
                return max_parking_end - self.park_start
            return self.park_time

        if use_case == "street":
            if self.simbev.street_night_charging_flag:
                # parking starts or ends after threshold or ends the next day
                if (
                    frac_park_start_steps >= self.simbev.threshold_street_limit_steps
                ) or (
                    (
                        (
                            frac_park_end_steps
                            >= self.simbev.threshold_street_limit_steps
                        )
                        or (whole_park_end > whole_park_start)
                    )
                    and (frac_park_start_steps)
                    >= (
                        self.simbev.threshold_street_limit_steps
                        - self.simbev.maximum_park_time
                    )
                ):
                    if (
                        self.location == "home"
                        or not self.simbev.home_night_charging_flag
                    ):
                        departure_time = self.rng.normal(
                            self.simbev.night_departure_time,
                            self.simbev.night_departure_standard_deviation,
                        )
                        # return departure time plus steps until midnight from previous parking event
                        return self.simbev.hours_to_time_steps(departure_time) + (
                            self.simbev.hours_to_time_steps(24) - frac_park_start_steps
                        )
                    return 0
                return self.simbev.maximum_park_time
            if self.real_park_time <= self.simbev.maximum_park_time:
                return self.simbev.maximum_park_time
            return 0

    def charge_decision(self, use_case):
        """Determine if a charging event is attractive enough.

        Parameters
        ----------
        use_case : str
            Charging use case

        Returns
        -------
        bool
        """
        return self.car.user_group.attractivity[use_case] >= self.rng.random()

    def execute(self):
        """Executes created trip. Charging/parking and driving"""
        if self.distance > self.simbev.distance_threshold_extra_urban:
            self.extra_urban = True

        if self.location == "home" and self.car.home_parking:
            if (self.charge_decision("home_detached") and self.car.home_detached) or (
                self.charge_decision("home_apartment") and not self.car.home_detached
            ):
                self.car.charge_home(self)
            else:
                self.car.park(self)

        elif self.location == "work" and self.car.work_parking:
            if self.charge_decision("work"):
                self.car.charge_work(self)
            else:
                self.car.park(self)
        elif not self.car.private_only:
            if (
                self.car.soc <= self.simbev.hpc_data["soc_start_threshold"]
                and self.charge_decision("urban_fast")
                and self.park_time
                <= (self.simbev.hpc_data["park_time_max"] / self.step_size)
            ):
                # get parameters for charging at hpc station
                charging_capacity = self.simbev.get_charging_capacity(
                    location="hpc", use_case="hpc", distance=self.distance
                )
                self.car.charge(
                    self,
                    charging_capacity,
                    "fast",
                    "urban_fast",
                    step_size=self.simbev.step_size,
                    max_charging_time=self.park_time,
                )

            elif self.location == "shopping" or self.charging_use_case == "retail":
                if self.charge_decision("retail") and not (
                    self.simbev.maximum_park_time_flag
                    and self.park_time > self.simbev.maximum_park_time
                ):
                    station_capacity = self.simbev.get_charging_capacity(
                        self.location, "retail", self.distance
                    )
                    # todo exponentialfunktion
                    max_parking_time = self.get_max_parking_time("retail")
                    self.car.charge_public(
                        self, station_capacity, max_parking_time, "retail"
                    )
                else:
                    self.car.park(self)

            elif self.charge_decision("street") and not (
                self.simbev.maximum_park_time_flag
                and min(self.park_time, self.park_time_until_threshold)
                > self.simbev.maximum_park_time
            ):
                station_capacity = self.simbev.get_charging_capacity(
                    self.location, "street", self.distance
                )
                max_parking_time = self.get_max_parking_time("street")
                self.car.charge_public(
                    self, station_capacity, max_parking_time, "street"
                )

            else:
                self.car.park(self)

        else:
            self.car.park(self)

        if self.drive_found:
            trip_completed = self.car.drive(
                self.distance,
                self.drive_start,
                self.drive_timestamp,
                self.drive_time,
                self.destination,
                self.extra_urban,
            )

            # call hpc events if trip cant be completed
            if not trip_completed:
                if self.car.private_only and not self.extra_urban:
                    raise SoCError(
                        f"Vehicle {self.car.file_name} dropped below the minimum SoC "
                        f"while trying to charge private only."
                    )
                self._create_fast_charge_events()

    def _set_timestamps(self):
        """
        Sets timestep for drive and park.
        """
        self.park_timestamp = self.region.region_type.time_series.index[self.park_start]
        if self.drive_found:
            self.drive_timestamp = self.region.region_type.time_series.index[
                self.drive_start
            ]

    def _create_fast_charge_events(self):
        """Creates hpc-event."""
        remaining_distance = self.distance
        sum_hpc_drivetime = 0

        remaining_range = (
            self.car.remaining_range_highway
            if self.extra_urban
            else self.car.remaining_range
        )

        # check if next drive needs charging to be completed
        while remaining_distance > remaining_range and self.car.car_type.label == "BEV":
            precise_remaining_range = (
                self.car.precise_remaining_range_highway
                if self.extra_urban
                else self.car.precise_remaining_range
            )

            # get time and distance until next hpc station
            hpc_distance = (
                self.rng.uniform(
                    self.simbev.hpc_data["distance_min"],
                    self.simbev.hpc_data["distance_max"],
                )
                * precise_remaining_range
            )
            hpc_drive_time = math.ceil(hpc_distance / self.distance * self.drive_time)
            sum_hpc_drivetime += hpc_drive_time

            if self.drive_start + hpc_drive_time > self.region.last_time_step:
                new_drive_time = self.region.last_time_step - self.drive_start + 1
                if new_drive_time > 0:
                    new_distance = hpc_distance * new_drive_time / hpc_drive_time
                    self.car.drive(
                        new_distance,
                        self.drive_start,
                        self.drive_timestamp,
                        new_drive_time,
                        "hpc",
                        self.extra_urban,
                    )
                self.trip_end = self.region.last_time_step + 1
                return

            self.car.drive(
                hpc_distance,
                self.drive_start,
                self.drive_timestamp,
                hpc_drive_time,
                "hpc",
                self.extra_urban,
            )

            # get parameters for charging at hpc station
            charging_capacity = self.simbev.get_charging_capacity(
                location=self.car.status, use_case="hpc", distance=self.distance
            )
            self.park_start = self.drive_start + hpc_drive_time
            self.park_timestamp = self.region.region_type.time_series.index[
                self.park_start
            ]
            max_charging_time = self.region.last_time_step - self.park_start

            if self.extra_urban:
                charging_use_case = "highway_fast"
            else:
                charging_use_case = "urban_fast"

            charging_time = self.car.charge(
                self,
                charging_capacity,
                "fast",
                charging_use_case,
                self.step_size,
                max_charging_time=max_charging_time,
            )

            # set necessary parameters for next loop or the following drive
            remaining_distance -= hpc_distance
            remaining_range = (
                self.car.remaining_range_highway
                if self.extra_urban
                else self.car.remaining_range
            )
            self.drive_start = self.park_start + charging_time
            if self.drive_start > self.region.last_time_step:
                self.drive_found = False
                self.trip_end = self.region.last_time_step + 1
                return
            self._set_timestamps()

        last_drive_time = max(self.drive_time - sum_hpc_drivetime, 1)
        self.car.drive(
            remaining_distance,
            self.drive_start,
            self.drive_timestamp,
            last_drive_time,
            self.destination,
            self.extra_urban,
        )
        # update trip end to start next parking at correct time stamp
        self.trip_end = self.drive_start + last_drive_time

    def fit_trip_to_timerange(self):
        """
        Cuts off trip so it is inside the simulation time range.
        """
        self.real_park_time = self.park_time
        # check if trip ends after simulation end
        if self.trip_end > self.region.last_time_step:
            self.trip_end = self.region.last_time_step + 1
            self.drive_time = self.trip_end - self.drive_start

        # check if drive happens after simulation end
        if self.drive_start > self.region.last_time_step or not self.drive_found:
            self.park_time = self.region.last_time_step - self.park_start + 1
            self.drive_found = False
            # change the real park time depending on input type
            # pull actual driving profile data from the first (unused) week in the simulation
            # this is used to get correct projected standing times at end of simulation
            replacement_day_timestep = (
                self.region.last_time_step + 1
            ) % self.simbev.hours_to_time_steps(24 * 7)
            if self.simbev.input_type == "probability":
                for index, timestep in enumerate(self.car.output["event_start"]):
                    if (
                        timestep > replacement_day_timestep
                        and not self.car.output["location"][index] == "driving"
                    ):
                        next_drive_timesteps = timestep
                        break
                self.real_park_time = (
                    self.park_time + next_drive_timesteps - replacement_day_timestep
                )
            elif self.simbev.input_type == "profile":
                next_drive_timesteps = self.car.driving_profile.loc[
                    self.car.driving_profile["time_step"] > replacement_day_timestep
                ]["time_step"].iat[0]
                self.real_park_time = (
                    self.park_time + next_drive_timesteps - replacement_day_timestep
                )

    def delay(self, time_steps: int):
        """Change the trip according to a given delay.

        Parameters
        ----------
        time_steps : int
            Time steps to delay the start of the trip by

        Returns
        -------
        bool
        """
        max_delay = self.park_time - 1
        delay = min(max_delay, time_steps)
        # remove possible delay time from parking
        self.park_start += time_steps
        if self.park_start > self.region.last_time_step:
            return False
        self.park_time -= delay
        # add remaining delay (anything not caught by parking) to drive times
        self.drive_start = self.park_start + self.park_time
        self.trip_end = self.drive_start + self.drive_time
        self.fit_trip_to_timerange()
        self._set_timestamps()
        return True

    @property
    def park_time_until_threshold(self) -> int:
        """
        Returns time steps between park start and next threshold.

        Returns
        -------
        int
            time steps until threshold time on the same day. returns 0 if negative
        """
        # This function currently only works for street, could be improved to work with retail threshold as well
        # Get time of day when parking starts (in time steps)
        # Calculate hours until threshold, return 0 if negative
        park_start_steps_from_midnight = int(
            self.park_start % (24 * 60 / self.simbev.step_size)
        )
        steps_until_threshold_time = self.simbev.threshold_street_limit_steps - park_start_steps_from_midnight

        return max(steps_until_threshold_time, 0)


def create_trip_from_profile_row(
    row,
    current_location,
    last_time_step,
    region,
    car,
    simbev,
    charging_use_case=None,
):
    """
    Create a Trip object based on information from a driving profile row.

    This function takes various input parameters from a driving profile row and other context data
    to create a Trip object representing a driving trip. It calculates drive start time,
    drive time, destination, distance, parking time, and other attributes of the trip.

    Parameters:
    -----------
    row : pd.Series
        A row of data from the profile containing information about the trip.
    current_location : str
        The current location of the vehicle.
    last_time_step : int
        The time step of the last action taken by the vehicle.
    region : str
        The region in which the trip is taking place.
    car : Car
        The car involved in the trip.
    simbev : SimBEV
        An object representing the simulation environment.
    charging_use_case : str, optional
        A string indicating the charging use case for the trip, if applicable.

    Returns:
    --------
    Trip
        A Trip object representing the created trip.

    Notes:
    ------
    - The function calculates various attributes of the trip, such as drive start time,
      drive time, destination, distance, parking time, and more.
    - The `fit_trip_to_timerange()` method adjusts the trip to fit within the simulation
      time range.
    - The `_set_timestamps()` method sets the timestamps for the trip.

    """
    drive_start = int(row.time_step)
    drive_time = max((row.arrival_time - row.departure_time) / simbev.step_size, 1)
    drive_time = math.ceil(drive_time)
    destination = row.location
    distance = row.distance
    location = current_location
    park_start = last_time_step
    if drive_start <= park_start:
        drive_start = park_start + 1
    park_time = drive_start - park_start
    trip = Trip(region, car, park_start, simbev, destination, distance)
    trip.location = location
    trip.park_time = park_time
    trip.drive_start = drive_start
    trip.drive_time = drive_time
    trip.drive_found = True
    trip.trip_end = trip.drive_start + trip.drive_time
    trip.charging_use_case = charging_use_case
    trip.fit_trip_to_timerange()
    trip._set_timestamps()
    return trip
