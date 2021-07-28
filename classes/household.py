import numpy as np

class Household:
    """ Class Household:
      - provides meta information about households 
          (dataset queries are adjusted to MOP-data)
      - generates mobility profiles for cars of households (arrays with 
          a) mobility states profiles
          b) speed profiles)
    """

    def __init__(self, 
                 positions, 
                 meta_data, 
                 states, 
                 speeds, 
                 no_of_ts, 
                 ts_length):
        """ inits Household class with:
        Args:
          - positions:        positions of all household members in dataset
          - meta_data:        meta_data entries for all household members
          - states:           states for hh members
          - speeds:           speeds for hh members
          - no_of_ts:         number of timesteps
          - ts_length:        timestep length [min]
        Attributes:
          - positions:        list with row indices in dataset belonging to hh
          - household_meta:   list with complete meta_data entries for hh
          - dates:            dates of data collection (SPS-format)
          - states:           all states of all occupants in obervation period
          - driver positions: list with positions of all household drivers

          - meta_data for household (# of occupants, # of cars, # of drivers, 
              net income, # of inhabitants in area, year of birth, job,
              driven distance)
        """
        self.ts_length = ts_length
        self.positions = positions
        self.first_position = min(self.positions)
        self.household_ID = meta_data[0,0]
        self.meta_data = meta_data
        self.dates = self.meta_data[0,32:39]
        self.number_of_occupants = self.meta_data[0,5]
        self.number_of_cars = self.meta_data[0,7]

        self.states = states
        self.speeds = speeds
        self.distances = self.get_distances(0, no_of_ts)

        self.number_of_drivers = self.get_number_of_drivers(0, no_of_ts)
        self.driver_positions = self.get_driver_positions(0, no_of_ts)
        self.income = self.meta_data[0,6]
        self.population = self.meta_data[0,4]
        self.year_of_birth = self.meta_data[0,10]
        self.job = self.meta_data[0,11]

        # total driven distance by first member
        self.driven_distance = self.get_driven_distances(0, no_of_ts)[0]
    

    def generate_mobility_states_profiles(self, start, end):
        """ generates mobility states profiles for all household cars 
              (array with all car states profiles)
          - start: first timestep of observation
          - end: last timestep of observation
        """
        # if more drivers than cars: merge necessary
        # number of cars has to match number of mobility profiles
        # merge: drivers who drive the least share a car
        # merge last driver and second to last driver
        # check for merge and repeat
        if (self.get_number_of_drivers(start, end) > self.number_of_cars):
            cars_states_prf = self.states_merge(start, end)
        else:
            drivers = self.get_driver_positions(start, end)   # all drivers
            positions = drivers - self.first_position   # get states order

            cars_states_prf = [self.get_states(start, end)[i] for i in positions]
            cars_states_prf = np.where(cars_states_prf, cars_states_prf, cars_states_prf)

            #cars_states_prf = []
            # sort states profiles correctly (longest distance -> first car)
            #for i in positions:
                #cars_states_prf.append(self.get_states(start, end)[i])

        return cars_states_prf

    def generate_mobility_speeds_profiles(self, start, end):
        """ generates mobility speeds profiles for all household cars 
              (array with all car speeds profiles)
          - start: first timestep of observation period
          - end: last timestep of observation period
        """
        
        states = np.array(self.generate_mobility_states_profiles(start, end))

        # check for merge
        if (self.get_number_of_drivers(start, end) > self.number_of_cars):
            cars_speeds_prf = self.speeds_merge(start, end)
        else:
            drivers = self.get_driver_positions(start, end)   #  all drivers
            positions = drivers - self.first_position  # get states in order

            cars_speeds_prf = [self.get_speeds(start, end)[i] for i in positions]
            cars_speeds_prf = np.where(cars_speeds_prf, cars_speeds_prf, cars_speeds_prf)

        speeds = np.array(cars_speeds_prf)

        # filter all speeds not belonging to driving states (state = 14)
        mask = np.where((states == 14), False, True)
        cars_speeds_prf = speeds.copy()
        cars_speeds_prf[mask] = 0

        return cars_speeds_prf

    def get_states(self, start, end):
        """ returns all states for timespace between start and end
        """
        states = self.states[:,start:end]
        return states

    def get_speeds(self, start, end):
        """ returns all speeds for timespace between start and end
        returns only speeds from car drives (state = 14) (no other speeds!)
        """
        speeds = self.speeds[:, start:end]
        states = self.get_states(start,end)
        return np.where(states == 14, speeds, 0)
    
    def get_distances(self, start, end):
        """ returns all distances for timespace between start and end (for states = 14)
        """
        speeds = self.get_speeds(start,end)
        states = self.get_states(start,end)
        return np.where(states == 14, speeds * self.ts_length / 60, 0)

    def get_number_of_drivers(self, start, end):
        """ returns number of drivers 
        counts all occupants who drive (state = 14) at least once in timespace
        """
        no_of_drivers = 0
        for i in range(0, len(self.get_states(start, end))):
            if ((self.get_states(start, end)[i] == 14).sum() > 0):
                no_of_drivers += 1
        return no_of_drivers

    def get_driven_distances(self, start, end):
        """ returns total driven distance for each household member
        """
        distances = []
        for i in range(0, len(self.positions)):
            distances.append(sum(self.get_distances(start, end)[i]))
        return distances

    def get_driver_positions(self, start, end):
        """ returns list of positions of all drivers in data set (sorted by driving dist.)
        """
        # find all drivers (at least one state = 14)
        drivers = []
        for i in range(0, len(self.positions)):
            if ((self.get_states(start, end)[i] == 14).sum() > 0):
                drivers.append(self.positions[i])
        
        # sort all drivers by their total driven distance
        distances = self.get_driven_distances(start, end)
        driver_pos_sorted = [x for _, x in sorted(zip(distances, drivers), reverse = True)]
        return driver_pos_sorted

    def states_merge(self, start, end):
        """ returns merged states profiles between start and end
        """
        drivers = self.get_driver_positions(start, end)   # all drivers
        positions = drivers - self.first_position   # get states in that order

        states = []
        # sort states profiles correctly (longest distance -> first car)
        for i in positions:
            states.append(self.get_states(start, end)[i])

        # merge last two profiles to one profile
        x = self.get_number_of_drivers(start,end)
        while x > self.number_of_cars:
            states[-2] = np.where(states[-1] == 14, 14, states[-2])
            states = np.delete(states,[-1], axis = 0)
            x -= 1
        return states   

    def speeds_merge(self, start, end):
        """ returns merged speeds profiles between start and end
        """
        drivers = self.get_driver_positions(start, end) # indices of all drivers
        positions = drivers - self.first_position   # get speeds in that order

        speeds = []
        # sort states profiles correctly (longest distance -> first car)
        for i in positions:
            speeds.append(self.get_speeds(start, end)[i])
        
        # merge last two profiles to one profile
        x = self.get_number_of_drivers(start,end)
        while x > self.number_of_cars:
            speeds[-2] = np.where(speeds[-1] != 0, speeds[-1], speeds[-2])
            speeds = np.delete(speeds,[-1], axis = 0)
            x -= 1
        return speeds
