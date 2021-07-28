# -*- coding: utf-8 -*-

from household import Household
import numpy as np

def rank_households(meta_data_all,
                    states_all,
                    speeds_all,
                    no_of_ts, 
                    ts_length,
                    number_of_occupants,
                    number_of_drivers,
                    number_of_cars,
                    income,
                    w_income,
                    population,
                    w_population,
                    year_of_birth,
                    w_year_of_birth,
                    job,
                    w_job,
                    distance,
                    w_distance,
                    quantity):
    """ Function rank_households():
    - searches for fitting households in dataset
    - returns list of up to 10 best fitting households according to user input
    - main factors (# of occupants, # of drivers, # of cars) are fulfilled
    - soft factors are checked for shortest distance to best fitting
    - shortest fitting is calculated with scoring system (based on weight) 
        (perfect fit (2 pts.), close fit (1 pt.), else (0 pts.))
    - soft factors are weighted according to user input (overall weight = 1.0)

    Args:
    - *_data_all:               data needed for Household object generation
    - no_of_ts:                 # of timesteps
    - ts_length:                timestep length
    - number_of_occupants:      # of occupants in household (main)
    - number_of_drivers:        # of drivers in household (main)
    - number_of_cars:           # of cars in household (main)
    - income, w_income:         net income of household, factor weight
    - population, w_population: # of inhabitants in area, factor weight
    - year_of_birth:            year of birth of first household member, weight
    - job:                      occupation of first household member, weight
    - distance:                 total driven distance by 1st hh member, weight
    """

    households = []

    # for every entry in dataset: create Household object
    # check the values for goodness of fit
    for i in range(0, len(meta_data_all)): 
        ID = meta_data_all[i,0 ]    # ID of current HH

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

        # hh is looked at more closely, only if all main factors are fulfilled
        if ((household.number_of_occupants == number_of_occupants) 
                and (household.number_of_drivers == number_of_drivers) 
                and (household.number_of_cars == number_of_cars)):          
            households.append(household.household_ID.astype(int))

    households = np.unique(households)    # delete duplicates

    score_array = []

    # determine score for all households that fulfill above condition
    for i in range(0, len(households)):
        ID = households[i]    # Id of current HH

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
        
        # income score
        income_hh = household.income
        income_diff = income_hh - income
        if (income_diff == 0):
            income_pts = 2
        elif (abs(income_diff) == 1):
            income_pts = 1
        else:
            income_pts = 0
        income_pts = income_pts * w_income    # weighted score

        # population score
        population_hh = household.population
        population_diff = population_hh - population
        if (population_diff == 0):
            pop_pts = 2
        elif (abs(population_diff) == 1):
            pop_pts = 1
        else:
            pop_pts = 0
        pop_pts = pop_pts * w_population  # weighted score

        # year of birth score
        year_of_birth_hh = household.year_of_birth
        year_of_birth_diff = year_of_birth_hh - year_of_birth
        if (abs(year_of_birth_diff) <= 10):
            year_o_b_pts = 2
        elif (abs(year_of_birth_diff) <= 20):
            year_o_b_pts = 1
        else:
            year_o_b_pts = 0
        year_o_b_pts = year_o_b_pts * w_year_of_birth   # weighted score

        # occupation score
        job_hh = household.job
        job_diff = job_hh - job
        if (job_diff == 0):
            job_pts = 2
        elif (abs(job_diff) == 1):
            job_pts = 1
        else:
            job_pts = 0
        job_pts = job_pts * w_job # weighted score

        # driven distance score
        distance_hh = household.driven_distance
        distance_diff = distance_hh - distance
        if (abs(distance_diff) <= 100):
            dist_pts = 2
        elif (abs(distance_diff) <= 200):
            dist_pts = 1
        elif (abs(distance_diff) <= 500):
            dist_pts = 0.5
        else:
            dist_pts = 0
        dist_pts = dist_pts * w_distance  # weighted score

        score = sum([income_pts, pop_pts, year_o_b_pts, job_pts, dist_pts])
        score_array.append(score)
    
    # sort hosueholds by overall score and return x best fitting
    households_fitting = [x for _, x in sorted(zip(score_array, households))]
    number_of_households = len(households_fitting)
    print("Number of fitting hosueholds:", number_of_households)

    # return only input quantity of fitting households (or all)
    if (quantity == "all"):
        ranked_households = list(reversed(households_fitting))
    else:
        ranked_households = list(reversed(households_fitting)) [0:quantity]

    return ranked_households
