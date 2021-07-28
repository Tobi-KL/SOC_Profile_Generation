# SOC_profile_generation

The SOC_profile_generation tool generates electric load profiles for households based on their mobility behaviour.
For all drivers in one household, the tool assigns a household car and generates a car mobility profile accordingly.
Each household car is substituted with a simlilar electric car, assuming no change in driving behaviour.
The tool calculates the overall energy demand of each electric car and, as a result, the energy demand for mobility of the household.
Focus is set on realistic simulation of energy consumption of electric cars in everyday use.

![grafik](https://user-images.githubusercontent.com/82574125/125078652-ff833c00-e0c2-11eb-8cde-49c4aff18817.png)

# Installation

Load the ipynb file "Run_SOC_Profile_Generation" into Google Colab.
Download and save all classes and functions into one directory and change directory in Colab-file.
Download all input data.
Adjust all paths in Colab file depending where classes, functions and input data are saved.

# Dependencies

The tool requires the following Python packages:
- numpy
- matplotlib
- csv
- pickle
- os.path

# Input data

The input data can be found in ...\SOC_profile_generation\inputs.
Own datasets with same format can be used.

The following data is required:
- pkl file with mobility data for households (e.g. MOP-data, Germany)
- csv file with temperatures for each timestep
- csv file with electric cars for each car segment
- csv file which holds information about electric cars' battery capacity (kWh), WLTP consumption (kWh) and charging power (kW)

# Detailed description of tool

The tool can be subdivided into the following sections:

## Household selection
The tool allows the user to choose specific households from the data set. For this the user adjusts a set of input variables.
A list of the 10 best fitting households is returned according to the user's input, following these rules:
- Main factors (1,2,3) need to be fulfilled exactly.
- Soft factors (4,5,6,7,8) need to be fulfilled as good as possible. Soft factors are weighted according to user's input.

Household selection factors are:
1) number of occupants in household
2) number of drivers in household
3) number of cars in household
4) net income of household
5) number of inhabitants in area
6) year of birth of first household member
7) occupation of first household member
8) total driven distance by first household member

## Driver/Car Allocation
The driver with the highest driven distance in the observation periode is allocated to the car with the highest driven distance in the observation periode etc.
For Households with fewer cars than drivers, the mobility profiles of the drivers with the lowest total driven distance are merged to one mobility profile until number of drivers matches number of cars.
As a consequence, one mobility profile is created for each household car.

## Electric car substitution and feasibilty check
Each car is substituted with an electric car according to the car segment defined by Kraftfahrtbundesamt, Germany.
Car substitution can be easily adjusted in the code since car characteristics, technical specifications, prices and segments change regularly.

Ahead of State-of-Charge-Profile-Generation, it is checked whether the chosen electric car can manage the mobility profile with its battery capacity.
If not, the segment is increased as long as feasibility is reached.
If the segment with the highest battery capacity is reached and the car still can not manage the mobility profile, State-of-Charge-Profile-Generation is stopped for this car.

## State-of-Charge-Profile-Generation
The tool calculates the state-of-charge of the current timestep. The calculation for each timestep can be simplified as follows:
- Car is driving: state-of-charge decreases
- Car is charging: state-of-charge increases
- neither: state-of-charge does not change

Charging is simulated for two charging strategies:
- Max strategy: anytime car is at a place where it can charge and battery not already full -> charge to max
- Min strategy: hold state-of-charge as low as possible, only charge right before driving and only the amount that will be used

### Simulation of driving
The consumption (kWh) in each driving timestep is calculated based on the following influence variables:
- distance (calculated with WLTP consumption (kWh/100km)
- speed factor (consumption is multiplied by factor depending on driving speed, see below)
- temperature: adds heating/cooling power, if car is driving in timestep (see below)

Speed factor:
Electric cars have lowest consumption if speed is around 60 km/h. Research has resulted in the following assumption:
- speed <= 30 km/h: multiply WLTP consumption by 1.473
- speed <= 50 km/h: multiply WLTP consumption by 1.08
- speed <= 70 km/h: multiply WLTP consumption by 0.955
- speed > 70 km/h: multiply WLTP consumption by 1.286

Temperature:
Influence of outside temperature on consumption (heating/cooling battery, cabin) can be modelled with a linear model. 
Assuming that there is no additional consumption for outside temperature = 20°C, the following heating/cooling additions are used:
- temperature is 5°C below 20°C: 0,5 kW heating power
- temperature is 10°C below 20°C: 1 kW heating power 
- etc.
- temperature is 5°C above 20°C: 0.25 kW cooling power
- temperature is 10°C above 20°C: 0.5 kW cooling power
- etc.

### Simulation of charging
User can input lower and upper bound for state-of-charge, e.g. 10% and 90% of battery capacity.
Max charging power is restricted by max car charging power and by max charging station power. Amount of energy being charged is restricted by capacity of battery.
The user can enter individual max charging power for both charging at home and at work (or only one of both).
As state-of-charge approaches battery capacity, car charging power is lowered as followed:
- 80% < state-of-charge <= 85%: 1/2 charging power
- 85% < state-of-charge <= 90%: 1/4 charging power
- 90% < state-of-charge <= 95%: 1/8 charging power
- 95% < state-of-charge <= 100%: 1/16 charging power

### Max Strategy
State-of-charge at first timestep is set to max. Anytime the car drives, state-of-charge is reduced accordingly (see "Simulation of driving").
Anytime the car is located at a possible charging station (state: car at home and/or car at work) and the battery is not full, charging is simulated (see "Simulation of charging").

### Min Strategy
State-of-charge at last timestep is as low as possible. Tool uses backwards iteration to determine when charging has to start before a trip. Charging occurs only until amount of energy is charged that is just enough for the following trip.

### Energy demand calculation
The user has the possibility to influence the efficiency of both charging stations (home, work). The energy demand of a charging station is therefore higher than the energy which can later be used by the car.

## Output
For each timestep and car the tool calculates the following timeseries and saves each in an individual array:
- Consumption of car (kWh)
- Possible charging power (kW, 0 if car not at home/work)
- State-of-charge for Max charging strategy (kWh)
- Charging profile for Max charging strategy (kWh)
- Energy demand home for Max charging strategy (kWh)
- Energy demand home for Max charging strategy (kWh)
- State-of-charge for Min charging strategy (kWh)
- Charging profile for Min charging strategy (kWh)
- Energy demand home for Min charging strategy (kWh)
- Energy demand home for Min charging strategy (kWh)

The timeseries can be exported as csv. files, e.g.:

![grafik](https://user-images.githubusercontent.com/82574125/124777507-8b208f80-df40-11eb-953e-96811ee93323.png)

The tool also delivers the following outputs:
- Cumulative energy demand for car (kWh)
- Cumulative energy demand at home charging station and Max charging strategy (kWh)
- Cumulative energy demand at work charging station and Max charging strategy (kWh)
- Cumulative energy demand at home charging station and Min charging strategy (kWh)
- Cumulative energy demand at work charging station and Min charging strategy (kWh)

The user is informed whether the car segment is adjusted to fit the profile, as can be seen in the following example.

![grafik](https://user-images.githubusercontent.com/82574125/124933008-d18af280-e003-11eb-9989-bcba3b430149.png)


Plots can be created, e.g. State-of-charge plot for Max and Min charging strategy:

![grafik](https://user-images.githubusercontent.com/82574125/124934352-e87e1480-e004-11eb-8756-5c2004808f52.png)
