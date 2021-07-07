# -*- coding: utf-8 -*-
"""Household.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1UKefSH5fSHdKtfZtT3rbXcWXDkLZoZl6
"""

class Household:
    """ Class Household:
      - provides meta information about households 
          (dataset queries are adjusted to MOP-data)
      - generates mobility profiles for cars of households (arrays with 
          a) mobility states profiles
          b) speed profiles)
    """

    def __init__(self, household_ID):
        """ inits Household class with:
        Args: 
          - household_ID:     ID of household
        Instance attributes:
          - positions:        list with row indices in dataset belonging to hh
          - household_meta:   list with complete meta_data entries for hh
          - dates:            dates of data collection (SPS-format)
          - states:           all states of all occupants in obervation period
          - driver positions: list with positions of all household drivers

          - meta_data for household (# of occupants, # of cars, # of drivers, 
              net income, # of inhabitants in area, year of birth, job,
              driven distance)
        """
        self.household_ID = household_ID
        self.positions = np.where(meta_mop_data[:,0] == self.household_ID)[0]
        self.household_meta = meta_mop_data.astype(int)[np.where(
            meta_mop_data[:,0] == self.household_ID)]
        self.dates = meta_mop_data[self.positions,32:39] [0]
        self.number_of_occupants = self.household_meta[0,5]
        self.number_of_cars = self.household_meta[0,7]
        self.states = self.get_states(0, no_of_ts)
        self.number_of_drivers = self.get_number_of_drivers()
        self.driver_positions = self.get_driver_positions()
        self.income = self.household_meta[0,6]
        self.population = self.household_meta[0,4]
        self.year_of_birth = self.household_meta[0,10]
        self.job = self.household_meta[0,11]
        self.driven_distance = self.get_driven_distance()
    

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
        if self.check_merge() == True:
            cars_states_prf = self.states_merge(start, end)
        else:
            cars_states_prf = np.array([self.get_states(start, end)[0]]) 
            for i in range(1, len(self.driver_positions)):
                cars_states_prf = np.append(cars_states_prf, 
                                            [self.get_states(start, end)[i]],
                                            axis=0)

        return cars_states_prf

    def generate_mobility_speeds_profiles(self, start, end):
        """ generates mobility speeds profiles for all hosuehold cars 
              (array with all car speeds profiles)
          - start: first timestep of observation period
          - end: last timestep of observation period
        """
        states = np.array(self.generate_mobility_states_profiles(start, end))

        # check for merge (same as above)
        if self.check_merge() == True:
            cars_speeds_prf = self.speed_merge(start, end)
        else:
            cars_speeds_prf = np.array([self.get_speeds(start, end)[0]])
            for i in range(1, len(self.driver_positions)):
                cars_speeds_prf = np.append(cars_speeds_prf, 
                                            [self.get_speeds(start, end)[i]], 
                                            axis=0)
        speeds = np.array(cars_speeds_prf)

        # filter all speeds not belonging to driving states (state = 14)
        mask = np.where((states == 14), False, True)
        cars_speeds_prf = speeds.copy()
        cars_speeds_prf[mask] = 0

        return cars_speeds_prf
           
    
    def get_data_position(self):
        """ returns indeces of chosen household in data set
        """
        position_lst = []
        for i in self.positions:
            position_lst.append(i)
        return position_lst

    def get_states(self, start, end):
        """ returns all states for timespace between start and end
        """
        for i in self.positions:
            return states_mop_data[self.positions, start:end]

    def get_speeds(self, start, end):
        """ returns all speeds for timespace between start and end
        """
        for i in self.positions:
            return speed_mop_data[self.positions, start:end]

    def get_number_of_drivers(self):
        """ returns number of drivers 
        count all occupants who drive (state = 14) at least once in period
        """
        no_of_drivers = 0
        for i in range(0,len(self.states)):
            if ((self.states[i]==14).sum() > 0):
                no_of_drivers += 1
        return no_of_drivers

    def get_driver_positions(self):
        """ returns list of positions of all drivers (sorted by driving dist.)
        """
        drivers = []
        for i in range(0,len(self.states)):
            if ((self.states[i]==14).sum() > 0):
                drivers.append(self.get_data_position()[i])
        persons = []

        # create a Person object for each driver
        # sort drivers by total driven distance
        for i in drivers:
            persons.append(Person(position = i, 
                                  household_ID = self.household_ID))
        persons_sorted = sorted(persons, 
                                key = lambda x: x.total_distance, 
                                reverse = True)
        driver_pos_sorted = []
        for i in range(0,len(persons_sorted)):
            driver_pos_sorted.append(persons_sorted[i].position)
        return driver_pos_sorted

    def get_driven_distance(self):
        """ returns array with all driven distances for one household member
        """
        distances = self.get_speeds(0, no_of_ts).copy()
        for i in range(len(distances)):
            distances[i] = distances[i] * ts_length / 60

        # adjust distances[arg] for different hh member ([0] for 1st etc.)
        driven_distance = np.sum(distances[0])
        return driven_distance

    def check_merge(self):
        """ checks whether a mobility profile merge is necessary (return True) 
        or not (return False)
        """
        if (self.number_of_drivers > self.number_of_cars):
            return True
        else:
            return False

    def states_merge(self, start, end):
        """ returns merged states profiles between start and end
        """
        x = self.get_number_of_drivers()
        while x > self.number_of_cars:       
            states_drivers = np.array([self.get_states(start, end)[0]])
            for i in range(1, len(self.driver_positions)):
              
                # array with lists of all states (one list for each driver)
                states_drivers = np.append(states_drivers, 
                                           [self.get_states(start, end)[i]], 
                                           axis=0)

            # array of only last two drivers
            drivers_last_2 = states_drivers[-2:]

            # positions of all states=14 for last driver
            last_driver = [i for i in range(len(drivers_last_2[-1])) if (
                drivers_last_2[-1][i] == 14)]

            drivers_last_2_merged = states_drivers[-2].copy()   
            for i in last_driver:
                 # second to last driver (complete profile) 
                 # + all states=14 of last driver
                drivers_last_2_merged[i] = 14

             # delete last and second to last driver from original array    
            states_drivers = np.delete(states_drivers, [-1,-2], axis=0)

            # add merged driver profile (second to last + last driver) 
            # on last position
            drivers_merged_states_profiles = np.vstack((states_drivers, 
                                                        drivers_last_2_merged))

            x -= 1
        return drivers_merged_states_profiles

    def speed_merge(self, start, end):
        """ returns merged speeds profiles between start and end
        """
        x = self.get_number_of_drivers()
        while x > self.number_of_cars:
            states_drivers = np.array([self.get_states(start,end)[0]])
            speeds_drivers = np.array([self.get_speeds(start,end)[0]]) 
            for i in range(1, len(self.driver_positions )):

                # array with lists of all states (one list for each driver)
                states_drivers = np.append(states_drivers,
                                           [self.get_states(start,end)[i]],
                                           axis=0)

            for i in range(1, len(self.driver_positions )):

                # array with lists of all speeds (one list for each driver)
                speeds_drivers = np.append(speeds_drivers,
                                           [self.get_speeds(start,end)[i]],
                                           axis=0)

            # array of only the last two drivers (states)
            drv_last_2_states = states_drivers[-2:]

            # positions of all states=14 for last driver
            last_driver = [i for i in range(len(drv_last_2_states[-1])) if (
                drv_last_2_states[-1][i] == 14)]       
            drv_last_2_speeds_merged = speeds_drivers[-2].copy()
            for i in last_driver:

                # second to last driver (complete profile)
                # + all states=14 of last driver
                drv_last_2_speeds_merged[i] = speeds_drivers[-1][i]

            # delete last and second to last driver from original array   
            speeds_drivers = np.delete(speeds_drivers, [-1,-2], axis=0)

            # add merged driver profile (second to last + last driver) 
            # on last position
            drv_merged_speed_prf = np.vstack((speeds_drivers, 
                                              drv_last_2_speeds_merged))

            x -= 1
        return drv_merged_speed_prf