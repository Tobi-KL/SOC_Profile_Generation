# -*- coding: utf-8 -*-

import numpy as np
import csv
import os.path
import matplotlib.pyplot as plt
from household import Household
from car import Car

def create_profiles(households,
                    meta_data_all,
                    states_all,
                    speeds_all,
                    start,
                    end,
                    no_of_ts,
                    ts_length,
                    home_charging_power,
                    work_charging_power,
                    charging_efficiency,
                    discharging_efficiency,
                    min_charge,
                    max_charge,
                    csv_weather,
                    csv_cars,
                    csv_database_electric_cars,
                    path,
                    bool_plot = False,
                    bool_create_csv = False):
    """ create_output():
    Creates csv.-files with profiles for each car according
      to input parameters and saves them.
    Generates one csv.-file for one car (multiple files per household possible)
    with the following entries at each timestep and for both max and min 
    charging strategies:
        - Consumption [kWh]
        - possbible charging power [kW]
        - state of charge [kWh]
        - charged power by car [kWh]
        - consumed power at charging station [kWh]
    Args:
    - *IDs:                   hh ID or list of household IDs (if multiple)
    - start:                  first timestep
    - end:                    last timestep
    - home_charging_power:    power of home charging station [kW]
    - work_charging_power:    power of work charging station [kW]
    - charging_efficiency:    efficiency of charging, default: 0.95
    - discharging_efficiency: efficiency of discharging, default: 0.95
    - min_state_of_charge:    min possible state of charge in %, default = 10%
    - max_state_of_charge:    min possible state of charge in %, default = 90%
    - path:                   path to folder for csv.-file creation
    - bool_plot:              if true: plots are created, default: False
    - bool_create_csv:        if true: csv-files are created, default: False
    """

    # create profiles for all of the following hosueholds:
    households_profiles = households    # result from rank_households

    # create household objects
    for i in range(0, len(households)):
        ID = households_profiles[i]    # Id of current HH

        print("\n")
        print("Household:", ID)

        # indices of household in data set
        positions = np.where(meta_data_all[:,0] == ID)[0]

        # meta data of all household members
        meta_data = meta_data_all.astype(int)[np.where(meta_data_all[:,0]==ID)]

        # states of all household members
        for i in positions:
            states = states_all[positions, 0 : no_of_ts]

        # speeds of all household members
        for i in positions:
            speeds = speeds_all[positions, 0 : no_of_ts]
            states = states_all[positions, 0 : no_of_ts]

        # create new Household object
        household = Household(positions, 
                              meta_data, 
                              states, 
                              speeds, 
                              no_of_ts, 
                              ts_length)
        
        # create states_profiles and speed_profiles for each car in household
        states_profiles = household.generate_mobility_states_profiles(start, end)
        speeds_profiles = household.generate_mobility_speeds_profiles(start, end)

        # get temperatures for correct dates from csv.-file
        dates = household.dates
        temperatures = []
        for i in dates:
            x = np.where(csv_weather[:,0]==i)
            temperatures.append(csv_weather[x,1].astype(int)[0])
            result = np.concatenate(temperatures[0:7])
            weather_consumption = result[start:end].astype(float)   

        # create Car objects
        for i in range(0, len(states_profiles)):
          
            # get car segment
            cars = csv_cars[np.where(csv_cars[:,0] == household.household_ID)]
            segment = cars[i : i + 1 , 174]
            if segment not in range(1, 14):  # if no segment is given, set it to 3
                segment = [3]
            else:
                segment = segment.astype(int)

            car = Car(states_profiles[i], # only profiles for ith car
                      speeds_profiles[i],  
                      weather_consumption,
                      segment,
                      csv_database_electric_cars,
                      min_charge, 
                      max_charge,
                      ts_length)
            
            print("Car:", i + 1)
            print("Segment:", segment)

            # Create profiles:
            # max_states_of_charge_profile() has to run first because of 
            # possible car segment adjustment
            max_strategy = car.max_state_of_charge_profile(start, 
                                                           end, 
                                                           home_charging_power, 
                                                           work_charging_power, 
                                                           charging_efficiency, 
                                                           discharging_efficiency)
            
            min_strategy = car.min_state_of_charge_profile(start, 
                                                           end, 
                                                           home_charging_power, 
                                                           work_charging_power, 
                                                           charging_efficiency, 
                                                           discharging_efficiency)
            
            charging_pwr_profile = car.get_charging_power(start, 
                                                          end, 
                                                          home_charging_power, 
                                                          work_charging_power)
            
            consumption_profile = car.generate_consumption_profile(start, end)

            states = car.states
            states = np.where(states == 8, 8,
                              np.where(states == 1, 1, 
                                       np.where(states == 2, 2,
                                                np.where(states == 14, 14, 0))))

            if max_strategy:     # if array not empty -> generation possible
                max_state_of_charge_profile = max_strategy[0]
                max_charge_profile = max_strategy[1]
                max_home_profile = max_strategy[2]
                max_work_profile = max_strategy[3]

                min_state_of_charge_profile = min_strategy[0]
                min_charge_profile = min_strategy[1]
                min_home_profile = min_strategy[2]
                min_work_profile = min_strategy[3]

                print("\nOverall energy demand, Household", 
                      household.household_ID, ", Car",
                      i + 1, "[kWh]:", sum(consumption_profile))
                print("\nHome energy demand max strategy, Household", 
                      household.household_ID, ", Car",
                      i + 1, "[kWh]:", sum(max_home_profile))
                print("\nWork energy demand max strategy, Household", 
                      household.household_ID, ", Car", i + 1,
                      "[kWh]:", sum(max_work_profile))
                print("\nHome energy demand min strategy, Household", 
                      household.household_ID, ", Car", i + 1,
                      "[kWh]:", sum(min_home_profile))
                print("\nWork energy demand min strategy, Household", 
                     household.household_ID, ", Car", i + 1,
                     "[kWh]:", sum(min_work_profile))
                print("\n")

                if bool_plot == True:
                    figure_title = ("\nPlot Household " 
                                    + str (household.household_ID) 
                                    + " - Car " 
                                    + str (i + 1) 
                                    + ":")
                    plt.figure()
                    plt.plot(max_state_of_charge_profile, 
                             label = "Max charging strategy")
                    plt.plot(min_state_of_charge_profile, 
                             label = "Min charging strategy")
                    plt.hlines(car.capacity, 0, end-start-1, "red", 
                               label = "Battery constraint State of charge")
                    plt.hlines(0, 0, end-start-1, "red")
                    plt.xlabel("Timestep")
                    plt.ylabel("State of charge [kWh]")

                    for i in range(len(states) - 1):
                        if (((states[i] == 1) | (states[i] == 2) | (states[i] == 8)) & (charging_pwr_profile[i] != 0)):
                            plt.axvspan(i, i+1, facecolor = "green", alpha = 0.1)

                    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                    plt.title(figure_title)
                    plt.show()
                    print("\n")
            
                if bool_create_csv == True:
                    path_file = os.path.join(path,
                                             'SOC_profile_ID_' 
                                             + str (household.household_ID) 
                                             + '_car_nr_' 
                                             + str (i + 1) + '.csv')
                    np.savetxt(path_file, 
                               np.column_stack((consumption_profile,
                                                charging_pwr_profile,
                                                max_state_of_charge_profile,
                                                max_charge_profile,
                                                max_home_profile,
                                                max_work_profile,
                                                min_state_of_charge_profile,
                                                min_charge_profile,
                                                min_home_profile,
                                                min_work_profile,
                                                states)),
                                delimiter=";",
                                encoding = "ISO-8859-1",
                                fmt="%1.2f",
                                header='Consumption;Possible Charging power;'\
                                'State-of-charge MAX;Charging energy MAX;'\
                                'Home demand MAX;Work demand MAX;State-of-charge MIN;'\
                                'Charging energy MIN;Home demand MIN;Work demand MIN;States',
                                comments='')
