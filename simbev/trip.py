import math


class Trip:
    def __init__(self, region, car, time_step, simbev):
        self.destination = ""
        self.distance = 0
        self.speed = 0

        self.park_start = time_step
        self.park_time = 0
        self.drive_start = 0
        self.drive_time = 0
        self.trip_end = 0
        self.trip_found = False

        self.location = car.status
        self.region = region
        self.car = car
        self.simbev = simbev
        self.rng = simbev.rng
        self.step_size = simbev.step_size

    def create(self):
        """
        Create new trip, starting from park_start, calculates standing time, next destination and driving time.
        """
        self.park_time = self.region.get_probability(self.rng, self.location, "stand")
        self.park_time = self.simbev.to_time_steps(self.park_time)
        self.drive_start = self.park_start + self.park_time
        if self.drive_start < self.region.last_time_step:
            self.park_time = self.region.last_time_step - self.park_start

        while not self.trip_found and self.drive_start < self.region.last_time_step:
            if self.rng.random() < self.region.region_type.trip_starts.iat[self.drive_start]:
                self.destination = self.region.get_purpose(self.rng, self.drive_start)
                # don't use same destination in a row
                if self.destination == self.car.status:
                    self.drive_start += 1
                    continue
                self.distance = self.region.get_probability(self.rng, self.destination, "distance")
                # check if driving makes sense, max is set as x amount of hours TODO config?
                while self.speed < 5 or self.drive_time > 15:
                    self.speed = self.region.get_probability(self.rng, self.destination, "speed")
                    self.drive_time = self.distance / self.speed
                self.drive_time = self.simbev.to_time_steps(self.drive_time)
                self.trip_end = self.drive_start + self.drive_time
                if self.trip_end > self.region.last_time_step:
                    self.trip_end = self.region.last_time_step
                    self.drive_time = self.trip_end - self.drive_start
                self.trip_found = True
                # update park_time
                self.park_time = self.drive_start - self.park_start
            else:
                self.drive_start += 1

        return self

    def execute(self):
        """
        Execute created trip. Charging/parking and driving
        """
        # TODO charging and driving logic here
        station_capacity = self.simbev.get_charging_capacity(self.car.status, self.distance)
        self.car.charge(self, station_capacity, "slow")

        if self.trip_found:
            self.car.drive(self)
