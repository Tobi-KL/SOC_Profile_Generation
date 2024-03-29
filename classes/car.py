# -*- coding: utf-8 -*-
"""Car.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/16ih-loia-sF2CB8cC06WaVXcZBdfuWc8
"""

import numpy as np

class Car:
    """ Class Car:
    - holds information about one car
    - calculates consumption of car & used charging stations for each timestep
    - simulates charging with 2 strategies and determines charging profiles:
      - max strategy: when possible, car is charged to max state of charge
      - min strategy: state of chrg is held as low as possible, but just enough
    - max strategy has to be run before min strategy (possible segment adjust.)
    """
    def __init__(self, 
                 states_profile, 
                 speeds_profile,
                 temperature_array,
                 segment, 
                 csv_database_electric_cars,
                 min_charge,
                 max_charge,
                 ts_length):
        """ inits Car class with:
        Args: 
          - states_profile:       array with all states (from Household class)
          - speeds_profile:       array with all speeds (while driving)
          - wheather consumption: array with consumption due to temperature
          - segment:              car segment (before possible adjustment)
          - csv_database_el.:     table with meta data electric cars
          - min_charge:           min state of charge allowed [in %]
          - max_charge:           max state of charge allowed
          - ts_length:            timestep length
        Instance attributes:
          - segment:              segment of car 
              (can be increased, if battery cap. not enough for profile gen.)
          - capacity:             battery capacity of car [kWh](can be incr.)
          - car_charging_power:   max poss chrg power of car [kW](can be incr.)
          - min_state_of_charge:  min state of chrg allowed [kWh](can be incr.)
          - max_state_of_charge:  max state of chrg allowed [kWh](can be incr.)
          - time_z:               timestep with lowest capacity in period
        """
        self.states = states_profile
        self.speeds = speeds_profile
        self.min_charge = min_charge
        self.max_charge = max_charge
        self.csv_database_electric_cars = csv_database_electric_cars
        self.segment = segment
        self.temperature_array = temperature_array
        self.capacity = self.csv_database_electric_cars[self.segment, 3]
        self.car_charging_power = self.csv_database_electric_cars[self.segment, 5]    
        self.min_state_of_charge = self.min_charge * self.capacity
        self.max_state_of_charge = self.max_charge * self.capacity
        self.ts_length = ts_length
        self.time_z = 0

    def max_state_of_charge_profile(self, 
                                    start, 
                                    end, 
                                    home_chrg_pwr, 
                                    work_chrg_pwr, 
                                    chrg_eff, 
                                    dischrg_eff):
        """
        - checks whether car can manage profile
        - generates state of charge profile for max strategy
        - max_state_of_charge_profile() has to be run before min_state_of_
              charge_profile() and before generate_consumption_profile()

        feasibility check:
        1. create state of charge profile for max strategy for current segment
        2. check, if any state_of_charge is below min_state_of_charge
        3. increase car segment to segment with higher battery capacity
        4. adjust segment, capacity, min_soc, max_soc of car object and retry
        5. if not possible with highest segment (6): don´t return profile

        Args:
        - start:          first timestep
        - last:           last timestep
        - home_chrg_pwr:  max power of charging station at home
        - work_chrg_pwr:  max power of charging station at work
        - chrg_eff:       efficiency of charging
        - dischrg_eff:    efficiency of discharging
        """

        # as long as there are timesteps when state_of_charge is lower than 
        # min_state_of_charge and segment can be incr. (max cap.: segment 6):
        # increase segment
        # increase cap., min_state_of_charge, max_state_of_charge accordingly
        while ((self.segment in [1,2,3,4,5]) and 
               any(x < self.min_state_of_charge for x in
                  self.max_profile_generation(start, 
                                              end, 
                                              home_chrg_pwr, 
                                              work_chrg_pwr, 
                                              chrg_eff, 
                                              dischrg_eff)[0])):    
            self.segment = self.segment + 1
            self.capacity = self.csv_database_electric_cars[self.segment, 3]
            self.min_state_of_charge = self.min_charge * self.capacity
            self.max_state_of_charge = self.max_charge * self.capacity

            # !! Warning-Output für Erstellung der MA rausgenommen (ergibt sehr lange Ausgaben) !!
            #print("Warning: Battery Capacity of car not high enough." \
             #     "Segment is adjusted to segment:", self.segment)

        else:
            # if no adjustment needed or all adjustments done:
            # get max_state_of_charge_profile for final car segment
            profiles = self.max_profile_generation(start, 
                                                   end, 
                                                   home_chrg_pwr,
                                                   work_chrg_pwr, 
                                                   chrg_eff, 
                                                   dischrg_eff)
            max_state_of_charge_profile = profiles[0]
            chrg_profile = profiles[1]
            home_profile = profiles[2]
            work_profile = profiles[3]
            load_profile = profiles[4]
            load_profile_home = profiles[5]
            load_profile_work = profiles[6]
        
        if any(x < self.min_state_of_charge 
               for x in max_state_of_charge_profile):
            # if after adjustment to highest segment still not possible
            # !! Warning-Output für Erstellung der MA rausgenommen (ergibt sehr lange Ausgaben) !!
            #print("Profile generation not possible. Capacity too low.")
            #print("\n")
            temp = 0 # Platzhalter

        else:
            # return consists of 4 parts:
            # 1. max_SOC_profile:           SOC for every timestep
            # 2. chrg_profile:              possible chrg power for every ts
            # 3. home_profile:              charged energy at home for every ts
            # 4. work_profile:              charged energy at home for every ts 

            return (max_state_of_charge_profile, 
                    chrg_profile, 
                    home_profile, 
                    work_profile,
                    load_profile,
                    load_profile_home,
                    load_profile_work)
  
    def min_state_of_charge_profile(self, 
                                    start,
                                    end, 
                                    home_chrg_pwr, 
                                    work_chrg_pwr, 
                                    chrg_eff, 
                                    dischrg_eff):
        """
        - gives state of charge profile for min strategy (w/o feas. check)
        - max_state_of_charge_profile() has to be run before 
            min_state_of_charge_profile() in order to calculate time_z
        - time_z: timestep with lowest state_of_charge for max strategy 
            -> slice here for backwards iteration
        backwards iteration: 
        1. start at time_z: set soc to min_soc
        2. iterate until timestep 0 and add/substract to soc_profile
        3. start at last timestep and iterate until time_z
        """
        consumption_profile = self.generate_consumption_profile(start, end)
        chrg_opts = self.get_charging_options(start, end)
        state_of_charge = self.min_state_of_charge      # at time_z
        state_of_charge_profile = np.zeros(end-start)
        load_profile = np.zeros(end-start)
        load_profile_home = np.zeros(end-start)
        load_profile_work = np.zeros(end-start)
        chrg_profile = np.zeros(end-start)
        home_profile = np.zeros(end-start)    # create empty profile for home
        work_profile = np.zeros(end-start)    # create empty profile for work

        # first backwards iteration (from z-1 to first timestep)
        for i in range(self.time_z-1, -1, -1):

            # car is driving in next periode
            if (consumption_profile[i+1] != 0):
                diff = consumption_profile[i+1]  # consumption in next timestep

                # state of charge from next timestep 
                # + consumption from next timestep
                # depending on dischrg_eff: consumption is higher
                state_of_charge_profile[i] = state_of_charge + (diff / dischrg_eff)
                state_of_charge = state_of_charge + (diff / dischrg_eff)

            # if car at home/work in next periode
            elif ((chrg_opts[i+1] == "home") 
                    | (chrg_opts[i+1] == "work") 
                    & (state_of_charge > self.min_state_of_charge)):
                charging_location = chrg_opts[i+1]   # in next periode

                # simulate charging
                charging_results = self.min_charging(home_chrg_pwr, 
                                                     work_chrg_pwr, 
                                                     charging_location, 
                                                     state_of_charge, 
                                                     chrg_eff, 
                                                     dischrg_eff, 
                                                     timestep=i)
                state_of_charge_profile[i] = charging_results[0]
                state_of_charge = charging_results[1]

                # [i+1] because of backwards iteration
                chrg_profile[i+1] = charging_results[2]

                # add consumed power to consumption profile of chrg stations
                if chrg_opts[i] == "home":
                    home_profile[i+1] = charging_results[2] * (2 - dischrg_eff)
                elif chrg_opts[i] == "work":
                    work_profile[i+1] = charging_results[2] * (2 - dischrg_eff)

            # car not driving and battery empty at min_state_of_charge
            else:
                state_of_charge_profile[i] = state_of_charge

        # last entry has to be min_state_of_charge
        state_of_charge_profile[end-start-1] = self.min_state_of_charge
        state_of_charge = self.min_state_of_charge

        # second backwards iteration (from last timestep to z): 
        # start with second to last
        for i in range((end-start-2), self.time_z-1, -1):
            if (i==self.time_z-1):
                state_of_charge_profile[i] = self.min_state_of_charge
                state_of_charge = self.min_state_of_charge

            # car is driving in next periode
            elif (consumption_profile[i+1] != 0):
                diff = consumption_profile[i+1] # consumption in next timestep

                # state of charge from next timestep 
                # + consumption from next timestep
                state_of_charge_profile[i] = state_of_charge + (diff / dischrg_eff)
                state_of_charge = state_of_charge + (diff / dischrg_eff)

              
            # if car at home/work in next periode
            elif ((chrg_opts[i+1] == "home") 
                    | (chrg_opts[i+1] == "work") 
                    & (state_of_charge > self.min_state_of_charge)):
                charging_location = chrg_opts[i+1]  #in next periode

                # simulate charging
                charging_results = self.min_charging(home_chrg_pwr, 
                                                     work_chrg_pwr, 
                                                     charging_location, 
                                                     state_of_charge, 
                                                     chrg_eff, 
                                                     dischrg_eff, 
                                                     timestep=i)
                state_of_charge_profile[i] = charging_results[0]
                state_of_charge = charging_results[1]

                # [i+1] because of backwards iteration
                chrg_profile[i+1] = charging_results[2]

                # add consumed power to consumption profile of chrg stations
                if chrg_opts[i] == "home":
                    home_profile[i+1] = charging_results[2] * (2 - dischrg_eff)
                elif chrg_opts[i] == "work":
                    work_profile[i+1] = charging_results[2] * (2 - dischrg_eff)

             # car not driving and battery empty at min_state_of_charge
            else: 
                state_of_charge_profile[i] = state_of_charge


        #load profiles
        for i in range(len(home_profile)):
            if home_profile[i] != 0:
                load_profile_home[i] = home_chrg_pwr
        for i in range(len(work_profile)):
            if work_profile[i] != 0:
                load_profile_work[i] = work_chrg_pwr
        load_profile = load_profile_home + load_profile_work

        # return consists of 4 parts:
        # 1. max_state_of_charge_profile: SOC for every timestep
        # 2. chrg_profile:                possible chrg power for every ts
        # 3. home_profile:                charged energy at home for every ts
        # 4. work_profile:                charged energy at home for every ts
        # 5.-7. load profiles   
        return (state_of_charge_profile, 
                chrg_profile, 
                home_profile, 
                work_profile,
                load_profile,
                load_profile_home,
                load_profile_work)
    
    def generate_consumption_profile(self, start, end):
        """ returns consumption profile of car
        consumption is influenced by:
        - car segment
        - car speed
        - speed factor (depending on speed)
        - outside temperature (additional consumption due to outside temp)
        Args:
        - start: first timestep
        - end: last timestep
        """
        weather_cons_prf = self.get_weather_consumption(start, 
                                                        end, 
                                                        self.temperature_array)
        dist_prf = self.get_distance_profile(start, end)
        base_cons = self.csv_database_electric_cars[self.segment, 4]  # base consumption
        speed_factors = self.get_speed_factors(start, end)  # speed factors
        cons_profile = np.zeros(end-start)

        # for each timestep: calculate consumption
        for i in range(len(cons_profile)):
            distance = dist_prf[i]                  
            speed_factor = speed_factors[i]
            cons_profile[i] = (speed_factor * distance * base_cons / 100)

        # add weather consumption only if car is driving
        for i in range(len(cons_profile)):
            if (cons_profile[i] != 0):
                cons_profile[i] = cons_profile[i] + weather_cons_prf[i]
                
        return cons_profile
    
    def get_charging_options(self, start, end):
        """ returns array with charging options ("home", "work" or "0")
        """
        chrg_opts = np.where((self.states == 8), 
                             "home", 
                             np.where(((self.states == 1) | (self.states == 2)), "work", 0)) 
        return chrg_opts

    def get_charging_power(self, start, end, home_chrg_pwr, work_chrg_pwr):
        """ returns array with charing options [kW]
        home_chrg_pwr = max power possible while charging at home
        work_chrg_pwr = max power possible while charging at work
        """
        poss_chrg_pwr = np.zeros(end-start)
        chrg_opts = self.get_charging_options(start, end)
        for i in range(len(chrg_opts)):
            poss_chrg_pwr[i] = np.where(chrg_opts[i] == "home", 
                                        home_chrg_pwr, 
                                        (np.where(chrg_opts[i] == "work", 
                                                  work_chrg_pwr, 
                                                  0)))
        return poss_chrg_pwr

    def get_distance_profile(self, start, end):
        """ returns array with driven distances (in each timestep) for car
        """
        distance = np.zeros(end-start)
        for i in range(len(distance)):
            distance[i] = (self.ts_length / 60) * self.speeds[i]
        return distance

    def get_speed_factors(self, start, end):
        """ returns factor (for multiplying consumption) for every timestep 
        depending on speed
        """
        # get speed profile and substitute entries for speed factor
        # hard coded based on assumptions
        speed_factors = self.speeds.copy()
        for i in range(len(speed_factors)):
            if speed_factors[i] == 0:
                speed_factors[i] = 0
            elif speed_factors[i] <= 30:
                speed_factors[i] = 1.473
            elif speed_factors[i] <= 50:
                speed_factors[i] = 1.08
            elif speed_factors[i] <= 70:
                speed_factors[i] = 0.955
            else:
                speed_factors[i] = 1.286
        return speed_factors

    def get_weather_consumption(self, start, end, temperature_array):
        """ returns additional consumption per timestep dep. on temperature
        - loads temperatures for dates of observation (from csv)
        - calculates heating/cooling consumption based on these assumptions:
          - heating power for 5 degrees deviation from 20°C: 0.5 [kW]
          - cooling power for 5 degrees deviation from 20°C: 0.25 [kW]
        """

        # get temperature profile and substitute entries for power consumption
        weather_consumption =  np.zeros(end-start)
        for i in range(len(temperature_array)):
            if temperature_array[i] <= (-20):
                weather_consumption[i] = 4 * (self.ts_length/60)      
            elif temperature_array[i] <= (-15):
                weather_consumption[i] = 3.5 * (self.ts_length/60)
            elif temperature_array[i] <= (-10):
                weather_consumption[i] = 3 * (self.ts_length/60)
            elif temperature_array[i] <= (-5):
                weather_consumption[i] = 2.5 * (self.ts_length/60)
            elif temperature_array[i] <= (0):
                weather_consumption[i] = 2 * (self.ts_length/60)
            elif temperature_array[i] <= (5):
                weather_consumption[i] = 1.5 * (self.ts_length/60)
            elif temperature_array[i] <= (10):
                weather_consumption[i] = 1 * (self.ts_length/60)
            elif temperature_array[i] <= (15):
                weather_consumption[i] = 0.5 * (self.ts_length/60)
            elif temperature_array[i] <= (20):
                weather_consumption[i] = 0 * (self.ts_length/60)
            elif temperature_array[i] <= (25):
                weather_consumption[i] = 0.25 * (self.ts_length/60)
            elif temperature_array[i] <= (30):
                weather_consumption[i] = 0.5 * (self.ts_length/60)
            elif temperature_array[i] <= (35):
                weather_consumption[i] = 0.75 * (self.ts_length/60)
            elif temperature_array[i] <= (40):
                weather_consumption[i] = 1 * (self.ts_length/60)
        return weather_consumption

    def max_charging(self, 
                     home_chrg_pwr, 
                     work_chrg_pwr, 
                     charging_location, 
                     state_of_charge, 
                     chrg_eff, 
                     dischrg_eff, 
                     timestep):
        """ simulates charging (at home or at work) with max-strategy
        if state of charge between 80% and 100%: charging power of car reduced
        consumed energy is added to consmption profile of charging station
        how much charging is possible depends on:
          - min(charging power of charging station, charging power of car)
          - duration (timestep)
          - efficiency of charging station
        """
        car_chrg_pwr = self.car_charging_power
        if (0.8 * self.capacity < state_of_charge <= 0.85 * self.capacity):
            car_chrg_pwr = 1/2 * car_chrg_pwr
        elif (0.85 * self.capacity < state_of_charge <= 0.9 * self.capacity):
            car_chrg_pwr = 1/4 * car_chrg_pwr
        elif (0.9 * self.capacity < state_of_charge <= 0.95 * self.capacity):
            car_chrg_pwr = 1/8 * car_chrg_pwr
        elif (0.95 * self.capacity < state_of_charge <= 1.0 * self.capacity):
            car_chrg_pwr = 1/16 * car_chrg_pwr

        if (charging_location == "home"):

            # how much charging is possible? [kWh]
            possible_kwh = ((min(home_chrg_pwr, car_chrg_pwr)) 
                * (self.ts_length/60) * chrg_eff)

            # how much does car need in this timestep? [kWh]
            needed_kwh = min(possible_kwh, 
                             self.max_state_of_charge - state_of_charge)

            # consumption of charging station
            consumed_kwh = needed_kwh * (2 - chrg_eff)

        elif (charging_location == "work"):

            # how much charging is possible? [kWh]
            possible_kwh = ((min(work_chrg_pwr, car_chrg_pwr)) 
                * (self.ts_length/60) * chrg_eff)

            # how much does car need in this timestep? [kWh]
            needed_kwh = min(possible_kwh, 
                             self.max_state_of_charge - state_of_charge)

             # consumption of charging station
            consumed_kwh = needed_kwh * (2 - chrg_eff)
        
        # adjust state_of_charge_profile and state_of_charge for this timestep
        # return also needed_kwh (actual used power [kWh])
        state_of_charge_profile = state_of_charge + needed_kwh
        state_of_charge = state_of_charge + needed_kwh
        
        return (state_of_charge_profile, state_of_charge, needed_kwh)

    def min_charging(self, 
                     home_chrg_pwr,
                     work_chrg_pwr,
                     charging_location,
                     state_of_charge,
                     chrg_eff, 
                     dischrg_eff, 
                     timestep):
        """ simulates charging (at home or at work) with min-strategy
        if state of charge between 80% and 100%: charging power of car reduced
        consumed energy is added to consmption profile of charging station
        how much charging is possible depends on:
          - min(charging power of charging station, charging power of car)
          - duration (timestep)
          - efficiency of charging station
        """
        car_chrg_pwr = self.car_charging_power
        if (0.8 * self.capacity < state_of_charge <= 0.85 * self.capacity):
            car_chrg_pwr = 1/2 * car_chrg_pwr
        elif (0.85 * self.capacity < state_of_charge <= 0.9 * self.capacity):
            car_chrg_pwr = 1/4 * car_chrg_pwr
        elif (0.9 * self.capacity < state_of_charge <= 0.95 * self.capacity):
            car_chrg_pwr = 1/8 * car_chrg_pwr
        elif (0.95 * self.capacity < state_of_charge <= 1.0 * self.capacity):
            car_chrg_pwr = 1/16 * car_chrg_pwr

        if (charging_location == "home"):

            # how much charging is possible? [kWh]
            possible_kwh = ((min(home_chrg_pwr, car_chrg_pwr)) 
                * (self.ts_length/60) * chrg_eff)

            # how much does car need in this timestep? [kWh]
            needed_kwh = min(possible_kwh, 
                             state_of_charge - self.min_state_of_charge)

            # consumption of charging station
            consumed_kwh = needed_kwh * (2 - chrg_eff)

        elif (charging_location == "work"):

            # how much charging is possible? [kWh]
            possible_kwh = ((min(work_chrg_pwr, car_chrg_pwr)) 
                * (self.ts_length/60) * chrg_eff)

            # how much does car need in this timestep? [kWh]
            needed_kwh = min(possible_kwh, 
                             state_of_charge - self.min_state_of_charge)

            # consumption of charging station
            consumed_kwh = needed_kwh * (2 - chrg_eff)
          
        # adjust state_of_charge_profile and state_of_charge for this timestep 
        # negative because of backwards iteration
        # return also needed_kwh (actual used power [kWh])
        state_of_charge_profile = state_of_charge - needed_kwh
        state_of_charge = state_of_charge - needed_kwh

        return (state_of_charge_profile, state_of_charge, needed_kwh)

    def max_profile_generation(self, 
                               start,
                               end, 
                               home_chrg_pwr, 
                               work_chrg_pwr, 
                               chrg_eff, 
                               dischrg_eff): 
        """ this method creates max_state_of_charge_profile and
        is needed for feasibility check in method max_state_of_charge_profile
        """
        state_of_charge = self.max_state_of_charge # max cap. at timestep 0
        state_of_charge_profile = np.zeros(end-start)
        load_profile = np.zeros(end-start)
        load_profile_home = np.zeros(end-start)
        load_profile_work = np.zeros(end-start)
        consumption_profile = self.generate_consumption_profile(start, end)
        chrg_opts = self.get_charging_options(start, end)
        chrg_profile = np.zeros(end-start) # create profile for actual pwr use
        home_profile = np.zeros(end-start) # create profile for home cons.
        work_profile = np.zeros(end-start) # create profile for work cons.

        for i in range(len(state_of_charge_profile)):
            if (consumption_profile[i] != 0):           # if car is driving
                diff = consumption_profile[i]

                # subtract consumption from state_of_charge
                # depending on dischrg_eff: consumption is higher
                state_of_charge_profile[i] = state_of_charge - (diff  * (2 - dischrg_eff))

                # adjust state_of_charge
                state_of_charge = state_of_charge - (diff  * (2 - dischrg_eff))

            # if car at home/work and battery not full
            elif (((chrg_opts[i] == "home") 
                    | (chrg_opts[i] == "work")) 
                    & (state_of_charge < self.max_state_of_charge)):
                charging_location = chrg_opts[i]

                # simulate charging
                charging_results = self.max_charging(home_chrg_pwr, 
                                                     work_chrg_pwr, 
                                                     charging_location,
                                                     state_of_charge,
                                                     chrg_eff, 
                                                     dischrg_eff,
                                                     timestep=i)

                # adjust state_of_charge_profile and state_of_charge
                # add concumed power to charging profile
                state_of_charge_profile[i] = charging_results[0]
                state_of_charge = charging_results[1]
                chrg_profile[i] = charging_results[2]

                # add consumed power to consumption profile of chrg stations
                if chrg_opts[i] == "home":
                    home_profile[i] = charging_results[2] * (2 - dischrg_eff)
                elif chrg_opts[i] == "work":
                    work_profile[i] = charging_results[2] * (2 - dischrg_eff)
            
            # car not driving, battery already full or not at charging point
            else:
                state_of_charge_profile[i] = state_of_charge

        # timestep with minimal state_of_charge
        self.time_z = np.where(
            state_of_charge_profile == state_of_charge_profile.min())[0][0]

        # load profiles
        for i in range(len(home_profile)):
            if home_profile[i] != 0:
                load_profile_home[i] = home_chrg_pwr
        for i in range(len(work_profile)):
            if work_profile[i] != 0:
                load_profile_work[i] = work_chrg_pwr
        load_profile = load_profile_home + load_profile_work

        # return consists of 4 parts:
        # 1. max_state_of_charge_profile: SOC for every timestep
        # 2. chrg_profile:                possible chrg power for every ts
        # 3. home_profile:                charged energy at home for every ts
        # 4. work_profile:                charged energy at work for every ts
        # 5.-7. load profiles
        return (state_of_charge_profile, 
                chrg_profile, 
                home_profile, 
                work_profile,
                load_profile,
                load_profile_home,
                load_profile_work)