--- vorläufig: in input die beiden Dateien "data_mop_priority.pkl" und "TANK18.csv" einfügen (liegen nicht auf Github) ---

# SOC_Profile_Generation

The SOC_profile_generation tool generates electric load profiles for households based on their mobility behaviour.
For all drivers in one household, the tool assigns a household car and generates a car mobility profile accordingly.
Each household car is substituted with a simlilar electric car, assuming no change in driving behaviour.
The tool calculates the overall energy demand of each electric car and, as a result, the energy demand for mobility of the household.
Focus is set on realistic simulation of energy consumption of electric cars in everyday use.

![grafik](https://user-images.githubusercontent.com/82574125/129238207-677d8718-e0dc-4c56-be73-8cb6a87a15ef.png)

# Application

The tool calculates the energy demand for driving mobility behaviour of individual household occupants. 
It assumes that all trips are made using electric cars. If trips in input data are made using conventional cars, the tools assigns a suitable electric car.
Driving mobility energy demand can be used to model future energy demand by households. 
As predicted by reseachers, households will electrify most of their energy consumption such as heating and mobility. 
This tool can be used to model the increased mobility power demand which can be useful for further research on this topic and help to forecast power demand for suppliers.
Different sociodemographic groups can be analysed which allows to model mobility behaviour for specific groups or comparisons between groups.\
Using synthetic data exemplary applications can be made. [1]

# Installation

1. Download code from github
2. Unzip file and save in one directory
3. Open "Run_SOC_Profile_Generation" in Google Colab
4. Change directory in Colab file.
5. Run all cells in Colab file.

# Dependencies

The tool requires the following Python packages:
- numpy
- matplotlib
- csv
- pickle
- os.path

# Input Data

The input data can be found in ...\SOC_profile_generation\inputs.
Own datasets with same format can be used.
Codeplan for all relevant data can be found in Codeplan_SOC_Profile_Generation:\
https://github.com/Tobi-KL/SOC_profile_generation/blob/main/Codeplan_SOC_Profile_Generation.txt

The following data sets are required:
- pkl file with mobility data for households (e.g. MOP-data, Germany)
- csv file with temperatures for each timestep (download via http://www.soda-pro.com/web-services/meteo-data/merra) [2]
- csv file with electric cars for each car segment
- csv file which holds information about electric cars' battery capacity (kWh), WLTP consumption (kWh) and charging power (kW)

# Detailed Description of Tool

The tool can be subdivided into the following sections:

## Household Selection
The tool allows the user to choose specific households from the data set. For this the user adjusts a set of input variables.
A list of the 10 best fitting households is returned according to the user's input, following these rules:
- Required factors (1,2,3) need to be fulfilled exactly.
- Optional factors (4,5,6,7,8) need to be fulfilled as good as possible. Soft factors are weighted according to user's input.

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

## Electric Car Substitution and Feasibilty Check
Each car is substituted with an electric car according to the car segment defined by Kraftfahrtbundesamt, Germany.
Car substitution can be easily adjusted in the code since car characteristics, technical specifications, prices and segments change regularly.

Ahead of State-of-Charge-Profile-Generation, it is checked whether the chosen electric car can manage the mobility profile with its battery capacity.
If not, the segment is increased as long as feasibility is reached.
If the segment with the highest battery capacity is reached and the car still can not manage the mobility profile, State-of-Charge-Profile-Generation is stopped for this car.

## State-of-Charge-Profile Generation
The tool calculates the state-of-charge of the current timestep. The calculation for each timestep can be simplified as follows:
- Car is driving: state-of-charge decreases
- Car is charging: state-of-charge increases
- neither: state-of-charge does not change

Charging is simulated for two charging strategies:
- Max strategy: anytime car is at a place where it can charge and battery not already full -> charge to max
- Min strategy: hold state-of-charge as low as possible, only charge right before driving and only the amount that will be used

### Simulation of Driving
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

### Simulation of Charging
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

### Energy Demand Calculation
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

![grafik](https://user-images.githubusercontent.com/82574125/129238023-ccdc7fe9-8666-4adc-80db-d7973399b0ff.png)

# References
[1] Kleinebrahm, Max; Torriti, Jacopo; McKenna, Russell; Ardone, Armin; Fichtner, Wolf;\
Using neural networks to model long-term dependencies in occupancy behavior;\
Energy and Buildings 240 (2021)

[2] Global Modeling and Assimilation Office (GMAO) (2015), MERRA-2 tavg1_2d_slv_Nx: 2d,1-Hourly,Time-Averaged,Single-Level,Assimilation,Single-Level Diagnostics V5.12.4, Greenbelt, MD, USA, Goddard Earth Sciences Data and Information Services Center (GES DISC), Accessed [09.08.2021] DOI:10.5067/VJAFPLI1CSIV
