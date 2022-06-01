
class Trip:
    """
    Represents a trip that a vehicle can make.

    Attributes
    ----------
    region : Region
        region object where the trip happens
    car : Car
        car object that takes the trip
    simbev : SimBEV
        SimBEV object
    park_start : int
        time step where Trip gets initiated (start of parking event)
    park_time : int
        number of time steps that the car parks
    drive_start : int
        time step where driving event starts
    drive_time : int
        number of time steps used to drive
    trip_end : int
        time step where driving concludes and trip ends
    drive_found : bool
        checks if driving event is possible
    destination : str
        purpose/destination of next driving event
    distance : float
        distance to drive
    speed : float
        average driving speed
    location : str
        current parking location (purpose)

    Methods
    -------
    create:
        finds next driving event and sets corresponding attributes
    execute:
        sets car to execute the created trip
    """
    def __init__(self, region, car, time_step, simbev):
        self.destination = ""
        self.distance = 0
        self.speed = 0

        self.park_start = time_step
        self.park_time = 0
        self.drive_start = 0
        self.drive_time = 0
        self.trip_end = 0
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
            if self.rng.random() < self.region.region_type.trip_starts.iat[self.drive_start]:
                self.destination = self.region.get_purpose(self.rng, self.drive_start)
                # don't use same destination in a row
                if self.destination == self.car.status:
                    self.drive_start += 1
                    continue
                self.distance = self.region.get_probability(self.rng, self.destination, "distance")
                # check if driving makes sense, max is set as x amount of hours TODO figure out better sanity check
                while self.speed < 5 or self.drive_time > 20:
                    self.speed = self.region.get_probability(self.rng, self.destination, "speed")
                    self.drive_time = self.distance / self.speed
                self.drive_time = self.simbev.hours_to_time_steps(self.drive_time)
                self.trip_end = self.drive_start + self.drive_time
                if self.trip_end > self.region.last_time_step:
                    self.trip_end = self.region.last_time_step
                    self.drive_time = self.trip_end - self.drive_start
                self.drive_found = True
                # update park_time
                self.park_time = self.drive_start - self.park_start
            else:
                self.drive_start += 1

        # check if drive happens after simulation end
        if self.drive_start > self.region.last_time_step:
            self.park_time = self.region.last_time_step - self.park_start
            self.trip_end = self.region.last_time_step

        self._set_timestamps()

    def execute(self):
        """
        Executes created trip. Charging/parking and driving
        """
        # TODO charging and driving logic here
        if self.location == "home":
            self.car.charge_home(self)
        elif self.location == "work":
            self.car.charge_work(self)
        else:
            station_capacity = self.simbev.get_charging_capacity(self.location, self.distance)
            self.car.charge(self, station_capacity, "slow")

        if self.drive_found:
            trip_completed = self.car.drive(self, self.simbev)
            # create new HPC trip if trip can't be completed
            if not trip_completed:
                range_remaining = self.car.soc * self.car.car_type.battery_capacity / self.car.car_type.consumption
                hpc_distance = self.rng.uniform(0.6, 1) * range_remaining
                remaining_distance = self.distance - hpc_distance
                # change current trip to go until first hpc stop
                self.distance = hpc_distance
                self.drive_time = hpc_distance / self.speed
                self.drive_time = self.simbev.hours_to_time_steps(self.drive_time)
                # TODO add tests if trip is possible now
                self.car.drive(self, self.simbev)

                trip = HPCTrip(self.region, self.car, self.drive_start + self.drive_time, self.simbev, remaining_distance)
                trip.execute()
            # TODO add all charging times from HPC trips to the first trip
            self.trip_end += trip.charging_time
        # return True if no drive is started (end of simulation) to skip checking for hpc events
        else:
            return True

    def _set_timestamps(self):
        self.park_timestamp = self.region.region_type.trip_starts.index[self.park_start]
        if self.drive_found:
            self.drive_timestamp = self.region.region_type.trip_starts.index[self.drive_start]


class HPCTrip(Trip):

    def create(self):
        # TODO function for trips that get called when hpc is needed to complete drive

        # TODO hpc charging which returns charging time and updates the car

        # TODO calculate next driving part of trip
        # if that cant be completed, start a new hpc trip

        pass
