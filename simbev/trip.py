import math
from simbev.helpers.errors import SoCError


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

    def __init__(self, region, car, time_step, simbev):
        self.destination = ""
        self.distance = 0
        self.speed = 0

        self.park_start = time_step
        self.park_time = 0
        self.drive_start = 0
        self.drive_time = 0
        self.trip_end = region.last_time_step
        self.park_timestamp = None
        self.drive_timestamp = None
        self.drive_found = False

        self.location = car.status
        self.region = region
        self.car = car
        self.simbev = simbev
        self.rng = simbev.rng
        self.step_size = simbev.step_size

        self.create()

    def create(self):
        """
        Creates new trip, starting from park_start.
        Calculates standing time, next destination and driving time.
        """

        self.park_time = self.region.get_probability(self.rng, self.location, "stand")
        self.park_time = self.simbev.hours_to_time_steps(self.park_time)
        self.drive_start = self.park_start + self.park_time

        while not self.drive_found and self.drive_start < self.region.last_time_step:
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

    def execute(self):
        """
        Executes created trip. Charging/parking and driving
        """
        # todo: implement attractivity for all charging use cases
        if self.location == "home" and self.car.home_parking:
            self.car.charge_home(self)
        elif self.location == "work" and self.car.work_parking:
            self.car.charge_work(self)
        elif not self.car.private_only:
            if (
                self.car.soc <= self.simbev.hpc_data["soc_start_threshold"]
                and self.car.user_group.attractivity["hpc_urban"] >= self.rng.random()
                and self.park_time
                <= (self.simbev.hpc_data["park_time_max"] / self.step_size)
                and self.car.car_type.label != "PHEV"
            ):
                # get parameters for charging at hpc station
                charging_capacity = self.simbev.get_charging_capacity(
                    location="hpc", distance=self.distance
                )
                max_charging_time = self.region.last_time_step - self.park_start
                self.car.charge(
                    self,
                    charging_capacity,
                    "fast",
                    self.step_size,
                    max_charging_time=self.park_time,
                )
            else:
                station_capacity = self.simbev.get_charging_capacity(
                    self.location, self.distance
                )
                self.car.charge(
                    self,
                    station_capacity,
                    "slow",
                    step_size=self.simbev.step_size,
                    max_charging_time=self.park_time,
                )
        else:
            self.car.park(self)

        if self.drive_found:
            trip_completed = self.car.drive(
                self.distance,
                self.drive_start,
                self.drive_timestamp,
                self.drive_time,
                self.destination,
            )

            # call hpc events if trip cant be completed
            if not trip_completed:
                if self.car.private_only:
                    raise SoCError(
                        f"Vehicle {self.car.file_name} dropped below the minimum SoC "
                        f"while trying to charge private only."
                    )
                self._create_fast_charge_events()

    def _set_timestamps(self):
        """
        Sets timestep for drive and park.
        """
        self.park_timestamp = self.region.region_type.trip_starts.index[self.park_start]
        if self.drive_found:
            self.drive_timestamp = self.region.region_type.trip_starts.index[
                self.drive_start
            ]

    def _create_fast_charge_events(self):
        """Creates hpc-event."""
        remaining_distance = self.distance
        sum_hpc_drivetime = 0

        # check if next drive needs charging to be completed
        while (
            remaining_distance > self.car.remaining_range
            and self.car.car_type.label == "BEV"
        ):
            # get time and distance until next hpc station
            hpc_distance = (
                self.rng.uniform(
                    self.simbev.hpc_data["distance_min"],
                    self.simbev.hpc_data["distance_max"],
                )
                * self.car.precise_remaining_range
            )
            hpc_drive_time = math.ceil(hpc_distance / self.distance * self.drive_time)
            sum_hpc_drivetime += hpc_drive_time

            if self.drive_start + hpc_drive_time >= self.region.last_time_step:
                new_drive_time = self.region.last_time_step - self.drive_start
                if new_drive_time > 0:
                    new_distance = hpc_distance * new_drive_time / hpc_drive_time
                    self.car.drive(
                        new_distance,
                        self.drive_start,
                        self.drive_timestamp,
                        new_drive_time,
                        "hpc",
                    )
                self.trip_end = self.region.last_time_step
                return

            self.car.drive(
                hpc_distance,
                self.drive_start,
                self.drive_timestamp,
                hpc_drive_time,
                "hpc",
            )

            # get parameters for charging at hpc station
            charging_capacity = self.simbev.get_charging_capacity(
                location=self.car.status, distance=self.distance
            )
            self.park_start = self.drive_start + hpc_drive_time
            self.park_timestamp = self.region.region_type.trip_starts.index[
                self.park_start
            ]
            max_charging_time = self.region.last_time_step - self.park_start
            charging_time = self.car.charge(
                self,
                charging_capacity,
                "fast",
                self.step_size,
                long_distance=True,
                max_charging_time=max_charging_time,
            )

            # set necessary parameters for next loop or the following drive
            remaining_distance -= hpc_distance
            self.drive_start = self.park_start + charging_time
            if self.drive_start >= self.region.last_time_step:
                self.drive_found = False
                self.trip_end = self.region.last_time_step
                return
            self._set_timestamps()

        last_drive_time = max(self.drive_time - sum_hpc_drivetime, 1)
        self.car.drive(
            remaining_distance,
            self.drive_start,
            self.drive_timestamp,
            last_drive_time,
            self.destination,
        )
        # update trip end to start next parking at correct time stamp
        self.trip_end = self.drive_start + last_drive_time

    def fit_trip_to_timerange(self):
        """
        Cuts of time-series so it is in simulation-timerange.
        """
        # check if trip ends after simulation end
        if self.trip_end > self.region.last_time_step:
            self.trip_end = self.region.last_time_step
            self.drive_time = self.trip_end - self.drive_start

        # check if drive happens after simulation end
        if self.drive_start > self.region.last_time_step or not self.drive_found:
            self.park_time = self.region.last_time_step - self.park_start
