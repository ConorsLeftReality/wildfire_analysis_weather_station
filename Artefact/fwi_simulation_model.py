## ----------------------------------------------------------------------
##
##    CompSci Higher Level 
##  - Leaving Cert Artefact -
##       Class of 2026
##
## ----------------------------------------------------------------------
##
##   School Roll No. REDACTED
##    Candidate No. REDACTED
##
## ----------------------------------------------------------------------
##
## External Packages Used:
##
## requests  - !!!OPTIONAL!!! For HTTP file collection, IF YOU DONT USE HTTP TO COLLECT A CSV FILE, IGNORE
## pandas    - Pandas is used for Dataframe Management
## plotly    - Plotly is the Dataframe plotting tool that we have used in the past
## 
## ----------------------------------------------------------------------


## ----------------------------------------------------------------------
## Modules Imported
## ----------------------------------------------------------------------

# File Collection
import requests # For HTTP file collection ONLY
import os # For file collection, IP and more

# FWI modules
import math # Used for Euler's Number

# Dataframe Management Modules
import pandas as pd # Pandas for dataframe 

# Dataframe Graphing Modules
import plotly.express as px
import plotly.io as pio
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import webbrowser

# General Modules
import time # For log function and timestamping data

## ----------------------------------------------------------------------
## FWI SYSTEM FUNCTIONS
## ----------------------------------------------------------------------
## FWI SYSTEM - Canadian Forest Fire Weather Index System 1985 
## By C.E. Van Wagner & T.L. Pickett, Petawawa National Forestry Institute
##
## Initialisation Functions
## - fire_season_check(my_df,my_headers) - If it hasn't rained for at least 3 days (< 0.5mm) AND the temperature is at least 6deg, fire season has started and it returns the exact date for this event
## - startup_FWI_sys(my_df, my_year, my_month, my_day, my_headers) - On the specified date that fire_season_check() returns True, generate Moisture Code values and enter them into the row for this date
##
## FWI MAIN FUNCTIONS
##  - fully_calculate_fwi(my_df, my_headers) - calls compute_fwi_variables() to compute per year, then creates full dataframe, sorts and returns
##  - compute_fwi_variables() - computes FWI variables for a 1 year dataframe, called and used by fully_compute_fwi iterably
## 
## FWI Variable Formulas
## - compute_FFMC(temp,humidity,rainfall,wind,FFMC_0)
## - compute_DMC(temp,humidity,rainfall,DMC_0,L)
## - compute_DC(temp,rainfall,DC_0,L)
## - compute_ISI(FFMC,wind) - Initial Spread Index, Higher number = faster fire spread on surface
## - compute_BUI(DMC,DC) - Buildup Index, Higher number = more fuel to burn (organics on forest floor, etc.)
## - compute_FWI(ISI,BUI) - Fire Weather Index ===> THIS IS THE VARIABLE WE WANT, WE LIKE THIS ONE, GOOD VARIABLE
## - compute_DSR(FWI) - Daily Severity Risk, flashy but we explicity want FWI
##
## ----------------------------------------------------------------------
## General Functions
## ----------------------------------------------------------------------
## - log(log_string, color="OK") - Prints info in Log format
##
## - logo() - Does what you would guess it does, it prints a logo
##
## - HTTP_request_csv(ip, filename) 
##                        - Sends a GET request to a HTTP server for CSV file
##
## - csv_file_collect() - Collects CSV file from HTTP to download as a local file or an existing local file, 
##                        then checks if CSV file is present locally before returning path
##
## - csv_file_prep(my_df) - Asks for headers to use within whole program, 
##                          then cleans file and adds needed rows for FWI
##
## - subplot_graph_df(my_df0,my_df1,my_df2,my_df3,my_columns,my_title,my_filename)
##                      - Plots 4 dataframes based on columns list as argument
##                        If DSR in dataframe, graphs the DSR beside each dataframe to compare
##                        Used for What-If Scenarios
##
## - graph_df(my_df,my_headers,my_columns,my_title,my_xaxis_title,my_yaxis_title,my_filename)
##                      - Plots one graph for a specific dataframe and specific columns
##                        Used for initial plot of original data


## ----------------------------------------------------------------------
## Fire Season Check Function
## ----------------------------------------------------------------------
def fire_season_check(my_df,my_headers):

    ## We need to find the start of the potential fire season
    ## Fire season starts if it hasn't rained for at least 3 days (< 0.5mm) AND the temperature is at least 6deg
    ## Returns the Year/Month/Day of the fire season start, or None/None/None if we can't find any

    # Make sure data is sorted chronolically
    my_df.sort_values([ my_headers["year"], my_headers["month"], my_headers["day"] ], inplace = True)

    streak = 0
    
    # Go though the data chronologically
    for index, row in my_df.iterrows():
        curr_temp = row[my_headers["temp"]]
        curr_rain = row[my_headers["rain"]]
        
        # Check if criteria are met
        if (curr_rain < 0.5 and curr_temp >= 6):
            streak += 1
        else:
            streak = 0   # reset the streak
        
        # if we've had three days of good data, return our start date    
        if streak >= 3:
            log(f"FWI SYSTEM : for {int(row[my_headers["year"]])} using {int(row[my_headers["year"]])},{int(row[my_headers["month"]])},{int(row[my_headers["day"]])} for season start date","OK")
            return ( int(row[my_headers["year"]]), int(row[my_headers["month"]]), int(row[my_headers["day"]]) )

    # If we found no start date, we find the first date in the CSV as a fallback (not ideal, but it will fix itself over a few weeks of data as it is history based)
    first_row = my_df.iloc[0]

    # Return the very first date as the fallback
    log(f"FWI SYSTEM : No start for fire season found, using start of dataframe","INFO")
    return (int(first_row[my_headers["year"]]),int(first_row[my_headers["month"]]),int(first_row[my_headers["day"]]))
    
## ----------------------------------------------------------------------
## Startup FWI variables Function - Vital for FWI system initialisation
## ----------------------------------------------------------------------
def startup_FWI_sys(my_df, my_year, my_month, my_day, my_headers):
    ## We need history for FFMC, DMC and DC in order to compute in the FWI system
    ## To solve this issue, we call to this function to get the official values to start up

    log(f"FWI SYSTEM : Calculations for {my_year} started - FWI Startup Process","OK")

    # Default startup values (According to Canadian Government Agencies)
    FFMC0 = 85
    DMC0 = 6
    DC0 = 15 # Could use overwintering, but too complicated for this project

    row_to_update = (my_df[my_headers["year"]] == my_year) & (my_df[my_headers["month"]] == my_month) & (my_df[my_headers["day"]] == my_day)
    
    my_df.loc[row_to_update, my_headers["FFMC"]] = FFMC0
    my_df.loc[row_to_update, my_headers["DMC"]] = DMC0
    my_df.loc[row_to_update, my_headers["DC"]] = DC0
    
    return my_df

## ----------------------------------------------------------------------
## Full FWI workflow function
##  - fully_calculate_fwi() calls compute_fwi_variables() by passing in 1 year of a given dataframe
##  - compute_fwi_variables() computes all the FWI variables for each row in a 1 year dataframe
## ----------------------------------------------------------------------

def fully_calculate_fwi(my_df, my_headers):

    # Make a copy of the dataframe to calculate FWI on
    df = my_df.copy()
    # Create a list for each years FWI calculations
    all_years_output = []
    # Find each unique year value in the dataframe
    years = df[my_headers["year"]].unique()

    # Calculates the FWI values for each year
    for yr in sorted(years):
        df_year = df[df[my_headers["year"]] == yr].copy()
        # Check for fire season start
        start_year, start_month, start_day = fire_season_check(df_year, my_headers)
        # Startup FWI system
        df_year = startup_FWI_sys(df_year, start_year, start_month, start_day, my_headers)
        # Compute the FWI variables for the year
        df_year = compute_FWI_variables(df_year, start_year, start_month, start_day, my_headers)
        # Append the year to the list we will use to make a final dataframe
        all_years_output.append(df_year)

    # Combine all years info one dataframe to output
    final_df = pd.concat(all_years_output)

    # Sort the final dataframe before returning
    final_df.sort_values([my_headers["year"], my_headers["month"], my_headers["day"]],inplace=True)

    return final_df

def compute_FWI_variables(my_df, my_year, my_month, my_day, my_headers):
    try:
        # Make sure data is sorted chronolically
        my_df.sort_values([ my_headers["year"], my_headers["month"], my_headers["day"] ], inplace = True)
        
        # Initial values until fire season start
        in_fire_season = False
        last_FFMC = None
        last_DMC = None
        last_DC = None
        
        day_length = 9 # Mean day length factor, required by DMC and DC, found in original FWI system documents 1985
        
        ## Go though the data chronologically
        for index, row in my_df.iterrows():
                
            ## If start of fire season, set values to proper numbers. This only happens once in the program (When the row is the season start date)
            if (row[my_headers["year"]] == my_year) and (row[my_headers["month"]] == my_month) and (row[my_headers["day"]] == my_day):
                in_fire_season = True
                last_FFMC = row[my_headers["FFMC"]]
                last_DMC  = row[my_headers["DMC"]]
                last_DC   = row[my_headers["DC"]] 

                if all(FWI_var is not None for FWI_var in [last_FFMC, last_DMC, last_DC]):
                    curr_temp = row[my_headers["temp"]]
                    curr_wind = row[my_headers["wind"]]
                    curr_hum = row[my_headers["hum"]]
                    curr_rain = row[my_headers["rain"]]

                    curr_ISI = compute_ISI(last_FFMC, curr_wind)
                    curr_BUI = compute_BUI(last_DMC, last_DC)
                    curr_FWI = compute_FWI(curr_ISI, curr_BUI)
                    curr_DSR = compute_DSR(curr_FWI)

                    my_df.loc[index, my_headers["ISI"]] = curr_ISI
                    my_df.loc[index, my_headers["BUI"]] = curr_BUI
                    my_df.loc[index, my_headers["FWI"]] = curr_FWI
                    my_df.loc[index, my_headers["DSR"]] = curr_DSR
                continue
        
            if (in_fire_season):
                ## Get todays (this rows) sensor data
                curr_temp = row[my_headers["temp"]]
                curr_wind = row[my_headers["wind"]]
                curr_hum  = row[my_headers["hum"]]
                curr_rain = row[my_headers["rain"]]  
                
                ## Calculate the new moisture codes and fire indexes with this sensor data
                ## Moisture Codes limited to ensure no data runaway
                curr_FFMC = min(compute_FFMC(curr_temp, curr_hum, curr_rain, curr_wind, last_FFMC) , 95)
                curr_DMC  = min(compute_DMC(curr_temp, curr_hum, curr_rain, day_length, last_DMC) , 250)
                curr_DC   = min(compute_DC(curr_temp, curr_rain, day_length, last_DC) , 1500)
                curr_ISI  = compute_ISI(curr_FFMC,curr_wind)
                curr_BUI  = compute_BUI(curr_DMC,curr_DC)
                curr_FWI  = compute_FWI(curr_ISI,curr_BUI)
                curr_DSR  = compute_DSR(curr_FWI)
                
                ## Update the current dataframe row
                my_df.loc[index, my_headers["FFMC"]] = curr_FFMC
                my_df.loc[index, my_headers["DMC"]]  = curr_DMC
                my_df.loc[index, my_headers["DC"]]   = curr_DC
                my_df.loc[index, my_headers["ISI"]]  = curr_ISI
                my_df.loc[index, my_headers["BUI"]]  = curr_BUI
                my_df.loc[index, my_headers["FWI"]]  = curr_FWI
                my_df.loc[index, my_headers["DSR"]]  = curr_DSR
                
                ## Save todays moisture codes for use in next iteration
                last_FFMC = curr_FFMC
                last_DMC  = curr_DMC
                last_DC   = curr_DC 
                
            else:
                continue

        log(f"FWI SYSTEM : Calculations for {my_year} finished - Compute FWI Variables Process","OK")
        ## return the final complete DataFrame
        return my_df
    except Exception as e:
        log(f"FWI SYSTEM : Calculations for {my_year} failed - Compute FWI Variables Process : {e}","OK")

## ----------------------------------------------------------------------
## Computation of FWI variables
##  - Calculations are (mostly) from the original Canadian Forest Fire Weather Index System
##    or from the Updated source code
##
## Original source code and system publication by Gov. of Canada (1985)
## - https://ostrnrcan-dostrncan.canada.ca/handle/1845/228362
## Updated source code PDF (2015)
## - https://publications.gc.ca/collections/collection_2016/rncan-nrcan/Fo133-1-424-eng.pdf
##
## NONE OF THIS CODE WAS DIRECTLY COPIED FROM THE SOURCE CODE
## I USED THE FORMULAS FROM THE 1985 PUBLICATION FOR THE MAJORITY OF MY WORK
## ----------------------------------------------------------------------

def compute_FFMC(temp,humidity,rainfall,wind,FFMC_0):

    # Step 1 - Previous Days FFMC becomes FFMC_0 (done by function argument)
    # Step 2 - Calculate M0 from FFMC_0
    M0 = (147.2*(101-FFMC_0))/(59.5+FFMC_0) # Calculate M0 from FFMC_0

    # Step 3 - Calculate Mr with Rainfall taken into account if needed
    if rainfall > 0.5:
        Rf = rainfall - 0.5 # Effective Rainfall
        if M0 <= 150:
            Mr = M0 + 42.5 * Rf * (math.exp(-100/(251-M0))) * (1-math.exp(-6.93/Rf))
        elif M0 > 150:
            Mr = M0 + 42.5 * Rf * (math.exp(-100/(251-M0))) * (1-math.exp(-6.93/Rf)) + (0.0015*(M0-150)**2)*(Rf**0.5)
        Mr = min(Mr,250)
    else:
        Mr = M0

    # Step 4 - Compute Drying and wettinf equilibrium
    Ed = 0.942 * (humidity**0.679) + (11*math.exp((humidity-100)/10)) + 0.18*(21.1-temp) * (1-math.exp(-0.115*humidity))
    Ew = 0.618 + (humidity**0.753) + (10*math.exp((humidity-100)/10)) + 0.18*(21.1-temp) * (1-math.exp(-0.115*humidity))

    # Step 5 - Drying and Wetting rate
    if Mr > Ed:
        K0 = 0.424*(1-(humidity/100)**1.7) + ((0.0694*wind)**0.5) * (1-(humidity/100)**8)
        Kd = K0 * 0.581*math.exp(0.0365*temp)
        M = Ed + (Mr-Ed) * 10**-Kd
    elif Mr < Ew:
        K0 = 0.424*(1-((100-humidity)/100)**1.7) + ((0.0694*wind)**0.5) * (1-((100-humidity)/100)**8)
        Kw = K0 * 0.581 * math.exp(0.0365*temp)
        M = Ew - (Ew-Mr) * 10**-Kw
    elif Ed >= Mr >= Ew:
        M = Mr

    # Step 6 - Convert back to FFMC
    FFMC = (59.5*(250-M))/(147.2+M) 

    return FFMC

def compute_DMC(temp,humidity,rainfall,L,DMC_0):   

    # Step 1 - Convert DMC to Moisture Content
    P0 = DMC_0
    
    # Step 2 - Adjust for rainfall
    if rainfall > 1.5:
        # Calculate Effetive Rainfall
        Re = 0.92*rainfall - 1.27

        # Calculate M0 from past DMC
        M0 = 20 + math.exp((5.6348 - P0)/43.43)

        # Calculate b depending on past DMC (P0)
        if P0 <= 33:
            b = 100/(0.5 + 0.3*P0)
        elif P0 >33 and P0 <=65:
            b = 14 - 1.3*math.log(P0)
        elif P0 > 65:
            b = 6.2*math.log(P0) - 17.2
        
        # Calculate Mr
        Mr = M0 + (1000*Re)/(48.77 + b*Re)

        # Convert Mr to Pr
        Pr = 244.72 - 43.43*math.log(Mr - 20)
    else:
        Pr = P0

    # Calculate K
    K = 1.894*(temp+1.1)*(100-humidity)*L*(10**-6)

    # Convert back to DMC
    DMC = Pr + 100*K

    return DMC

def compute_DC(temp,rainfall,L,DC_0):
    # Step 1 - Convert Last Days DC to D0 for calculations
    D0 = DC_0

    # Step 2 - Rainfall Adjustments
    if rainfall >= 2.8:
        Re = 0.83*(rainfall) - 1.27
        Qr = 800-(800-D0)*math.exp(-Re/400)
    else:
        Qr = D0
    
    # Step 3 - Drying due to temperature
    K = 0.36*(temp+2.8) + L

    # Step 4 - Update DC
    DC = Qr + K

    return DC 

def compute_ISI(FFMC,wind):
    # Step 1 - Compute moisture effect on spread
    m = (147.2*(101-FFMC))/(59.5+FFMC)

    # Step 2 - Computer factor of wind
    Fw = math.exp(0.05039*wind)

    # Step 3 - Compute rate of spread
    Ff = 91.1*math.exp(-0.1386*m)*(1+(m**5.31)/(4.93 * 10**7))

    # Step 4 - Compute ISI
    ISI = 0.208*Fw*Ff

    return ISI

def compute_BUI(DMC,DC):
    # Step 1 - Calculate BUI based on DMC
    if DMC <= 0.4*DC:
        BUI = (0.8*DC*DMC)/(DMC+0.4*DC)
    else:
        BUI = (DMC-(1-0.8*DC))/((DMC+0.4*DC)*(0.92+(0.0114*DMC)**1.7))
    return BUI

def compute_FWI(ISI,BUI):
    # Step 1 - Computate Fd based on BUI
    if BUI <= 80:
        Fd = 0.626*BUI**0.809+2
    else:
        Fd = 1000/(25+108.64*math.exp(-0.023*BUI))
    
    # Step 2 - Compute B (Combined index before adjustment)
    B = 0.1 * ISI * Fd

    # Step 3 - Compute FWI
    if B > 1:
        FWI = math.exp(2.72*((0.434*math.log(B))**0.647))
    else:
        FWI = B

    return FWI

def compute_DSR(FWI):
    DSR = 0.0272*(FWI)**1.77
    return DSR

## ----------------------------------------------------------------------
## Function to write data in Log Format, and new function to make an input in log format
## ----------------------------------------------------------------------
def log(log_string, color="OK"):
    match color.upper():
        case "WARN":
            print(f"\033[31m[{time.strftime('%H:%M:%S')}] {log_string} \033[0m")
        case "INFO":
            print(f"\033[33m[{time.strftime('%H:%M:%S')}] {log_string} \033[0m")
        case _:
            print(f"\033[32m[{time.strftime('%H:%M:%S')}] {log_string} \033[0m")

## ----------------------------------------------------------------------
## Function to print super cool FWI logo
## ----------------------------------------------------------------------=
def logo():
    log("")
    log(r"    ______________  ______   _       ___________  ________  ____________     _____   ______  _______  __    ____  _________ __ __    __  _______  ____  ________    __    _____   ________")
    log(r"   / ____/  _/ __ \/ ____/  | |     / / ____/   |/_  __/ / / / ____/ __ \   /  _/ | / / __ \/ ____/ |/ /   / __ \/  _/ ___// //_/   /  |/  / __ \/ __ \/ ____/ /   / /   /  _/ | / / ____/")
    log(r"  / /_   / // /_/ / __/     | | /| / / __/ / /| | / / / /_/ / __/ / /_/ /   / //  |/ / / / / __/  |   /   / /_/ // / \__ \/ ,<     / /|_/ / / / / / / / __/ / /   / /    / //  |/ / / __  ")
    log(r" / __/ _/ // _, _/ /___     | |/ |/ / /___/ ___ |/ / / __  / /___/ _, _/  _/ // /|  / /_/ / /___ /   |   / _, _// / ___/ / /| |   / /  / / /_/ / /_/ / /___/ /___/ /____/ // /|  / /_/ /  ")
    log(r"/_/   /___/_/ |_/_____/     |__/|__/_____/_/  |_/_/ /_/ /_/_____/_/ |_|  /___/_/ |_/_____/_____//_/|_|  /_/ |_/___//____/_/ |_|  /_/  /_/\____/_____/_____/_____/_____/___/_/ |_/\____/   ")
    log("")


## ----------------------------------------------------------------------
## Function to send a get HTTP request to a given HTTP server
## ----------------------------------------------------------------------
def HTTP_request_csv(ip, filename):
    try:
        url = f"http://{ip}" # URL to request from
        
        response = requests.get(url) # send HTTP GET request
        response.raise_for_status() # If the status code is good (e.g. 200), automatically continues
        
        f = open(filename, "wb") # Save to working directory
        f.write(response.content) # Write to file
        f.close() # Close and save the file
        log(f"HTTP REQUEST : Successfully called to http://{ip}","WARN")
        return filename
    
    except Exception as e:
        log(f"HTTP REQUEST : Could not successfully call to http://{ip}","WARN")
        return None

## ----------------------------------------------------------------------
## Function to prepare then return filepath for a user selected CSV file
## ----------------------------------------------------------------------
def csv_file_collect():  
    no_csv = True
    while no_csv == True:
        try:
            logo()
            log(" ---------- CSV INPUT ---------- ","INFO")
            data_input_choice = input("Input data via Local CSV or HTTP remotely (local/http - Default: local) : ") or "local"

            if data_input_choice.lower() == "local":
                try:
                    filename = input("Enter the file path of the CSV file (Default: canadian_6_year_data): ") or "canadian_6_year_data"
                    filename = os.path.normpath(filename.strip().strip('"'))
                except Exception as e:
                    log(e,"WARN")
            elif data_input_choice.lower() == "http":
                try:
                    ip = input("Enter the accessible IP address for the HTTP server : ")
                    filename_requested = input("Enter name for the csv file? (default : data.csv): ") or "data.csv"
                    filename = HTTP_request_csv(ip, filename_requested)
                except Exception as e:
                    log(e,"WARN")
            
            if os.path.isfile(filename):
                no_csv = False
                log("CSV COLLECT : CSV collection success, continuing","OK")
            else:
                no_csv = True
                print("")
                print("")
                print("")
                print("")
                log("CSV COLLECT : CSV collection failed (no CSV present?), restarting","WARN")
        
        except Exception as e:
            log("","WARN")
            log("","WARN")
            log("","WARN")
            log("","WARN")
            log(f"CSV COLLECT : Error during CSV collection : {e}","WARN")
            pass
            
    return filename

## ----------------------------------------------------------------------
## Function to prepare the CSV file for FWI calculations
## ----------------------------------------------------------------------
def csv_file_prep(my_df):

    # Step 1 - Ask user to enter the headers to use for the dataframe
    log(list(my_df.columns), "INFO")
    
    # Make a dict to store the headers from the CSV I want to keep/use]
    headers_to_keep = {}
   
    ## Get the names of the CSV headers from the user - defaults to the headers used in the sample Canadian data
    headers_to_keep["year"]  = input("Enter the header label that matches year (default=Year) : ") or "Year"
    headers_to_keep["month"] = input("Enter the header label that matches month (default=Month) : ") or "Month"
    headers_to_keep["day"]   = input("Enter the header label that matches day (default=Day) : ") or "Day"
    headers_to_keep["wind"]  = input("Enter the header label that matches wind speed (default=Wind Spd (km/h)) : ") or "Wind Spd (km/h)"
    headers_to_keep["temp"]  = input("Enter the header label that matches temperature (default=Temp (°C)) : ") or "Temp (°C)"
    headers_to_keep["hum"]   = input("Enter the header label that matches humidity (default=Rel Hum (%)) : ") or "Rel Hum (%)"
    headers_to_keep["rain"]  = input("Enter the header label that matches rainfall (default=Precip. Amount (mm)) : ") or "Precip. Amount (mm)"


    for col in [headers_to_keep["temp"],headers_to_keep["hum"],headers_to_keep["wind"],headers_to_keep["rain"]]:
        my_df[col] = pd.to_numeric(my_df[col], errors="coerce")

    # Replace any wind and rain NaN values with 0
    my_df[headers_to_keep["wind"]] = my_df[headers_to_keep["wind"]].fillna(0)   # Assume no wind
    my_df[headers_to_keep["rain"]] = my_df[headers_to_keep["rain"]].fillna(0)   # Assume no rain

    my_df[headers_to_keep["hum"]] = my_df[headers_to_keep["hum"]].fillna(65)    # Average Humidity in BC yearly
    my_df[headers_to_keep["temp"]] = my_df[headers_to_keep["temp"]].fillna(10)  # Average Temp in BC

    vars_to_average = [ headers_to_keep["wind"], headers_to_keep["temp"], headers_to_keep["hum"], headers_to_keep["rain"] ]

    summary_df = my_df.groupby([ headers_to_keep["year"], headers_to_keep["month"], headers_to_keep["day"] ])[vars_to_average].mean().reset_index()
      
    ## Also add extra headers for data that doesnt exist in the CSV, but that we will calculate later 
    for h_name in [ "FFMC", "DMC", "DC", "ISI", "BUI", "FWI", "DSR" ]:
        headers_to_keep[h_name] = h_name 
    
    # Step 2 - Add new columns to the dataframe if thay dont already exist (my new extra headers)
    for column in headers_to_keep.values():
        if column not in summary_df.columns:
            summary_df[column] = None

    summary_df = summary_df.sort_values([headers_to_keep["year"], headers_to_keep["month"], headers_to_keep["day"]]).reset_index(drop=True)
    print("")

    return summary_df,headers_to_keep

## ----------------------------------------------------------------------
## Function for graphing the dataframe
## ----------------------------------------------------------------------
def subplot_graph_df(my_df0,my_df1,my_df2,my_df3,my_columns,my_title,my_filename):
    graphed = False
    while graphed != True:
        for df in [my_df0,my_df1,my_df2,my_df3]:
            df[my_columns] = (df[my_columns].replace(r'^\s*$', None, regex=True).apply(pd.to_numeric, errors="coerce"))

        fig = make_subplots(rows=4,cols=2,subplot_titles=("Temperature +2°C","DSR","Rain 20% Increase","DSR","Humidity 10% Increase","DSR","Wind Double"))
        # Create the subplots for the What-If Graphs, including all columns in my_cloumns
        dfs = [my_df0,my_df1,my_df2,my_df3]
        positions = [(1,1),(2,1),(3,1),(4,1)]

        # For each subplot (given by posotion)
        for df,(row,col) in zip(dfs,positions):
            # For each column in the list of columns to graph
            for column in my_columns:
                if column == headers['DSR']:
                    fig.add_trace(go.Scatter(x=df["Date"],y=df[column],name=column,showlegend=(row==1 and col==1)),row=row,col=2) # Creates each trace based on positions (easily changable in future) and columns
                else:
                    fig.add_trace(go.Scatter(x=df["Date"],y=df[column],name=column,showlegend=(row==1 and col==1)),row=row,col=col)
        
        # Make the Y axis a fixed range from 0 to 100
        fig.update_yaxes(range=[0, 100])

        # Update the layout of the Subplot graph
        fig.update_layout(height=4000,width=1400,title_text=my_title,template='plotly_white')
        
        # Show the graph
        log(f"MULTI-GRAPH PLOTTING : {my_title} graph starting","INFO")
        time.sleep(1)
        pio.write_html(fig, my_filename)
        my_filename = os.path.normpath(my_filename.strip().strip('"'))
        webbrowser.open(my_filename)

        user_response = input(f"\033[33m[{time.strftime('%H:%M:%S')}] MULTI-GRAPH PLOTTING : Has the graph loaded? y/n (n) : \033[0m") or "n"
        if user_response.lower() == "y":
            graphed == True
            print("")
            print("")
            print("")
            print("")
            print("")
            print("")
            return
        elif user_response.lower() == "n":
            log("MULTI-GRAPH PLOTTING : Reloading Graph...","INFO")
            log("...","INFO")
            log("...","INFO")
            log("...","INFO")
    
def graph_df(my_df,my_headers,my_columns,my_title,my_xaxis_title,my_yaxis_title,my_filename):
    graphed = False
    while graphed != True:
        # Create a proper datetime column
        my_df['Date'] = pd.to_datetime(my_df[[my_headers["year"], my_headers["month"], my_headers["day"]]],errors="coerce")

        # Makes sure dataframe is numeric and wont cause any errors with graphing
        my_df[my_columns] = (my_df[my_columns].replace(r'^\s*$', None, regex=True).apply(pd.to_numeric, errors="coerce"))

        # Melt the dataframe so Plotly can plot multiple lines easily
        df_melted = my_df.melt(id_vars='Date', value_vars=my_columns, var_name='Index', value_name='Value')

        # Plot the graph
        fig = px.line(df_melted,x='Date',y='Value',color='Index',render_mode='webgl')
        
        # Update graph with titles and templates
        fig.update_layout(xaxis_title=my_xaxis_title,yaxis_title=my_yaxis_title,template='plotly_white',legend_title_text=my_title)

        log(f"GRAPH PLOTTING : {my_title} graph starting","INFO")
        time.sleep(1)
        pio.write_html(fig, my_filename)
        my_filename = os.path.normpath(my_filename.strip().strip('"'))
        webbrowser.open(my_filename)


        user_response = input(f"\033[33m[{time.strftime('%H:%M:%S')}] GRAPH PLOTTING : Has the graph loaded? y/n (n) : \033[0m") or "n"
        if user_response.lower() == "y":
            graphed == True
            print("")
            print("")
            print("")
            print("")
            print("")
            print("")
            return
        elif user_response.lower() == "n":
            log("GRAPH PLOTTING : Reloading Graph...","INFO")
            log("...","INFO")
            log("...","INFO")
            log("...","INFO")

"""
## ----------------------------------------------------------------------
## Check the CSV file for missing rows after all processes - <<<<< DEBUG ONLY, REMOVE FOR FINAL >>>>>
## ----------------------------------------------------------------------
def check_missing_days(my_df, my_headers):

    # create real datetime column
    my_df["DATE"] = pd.to_datetime(my_df[[my_headers["year"], my_headers["month"], my_headers["day"]]])

    # remove duplicate dates if they exist
    my_df = my_df.drop_duplicates(subset="DATE")

    # sort chronologically
    my_df = my_df.sort_values("DATE")

    # generate full expected date range
    full_range = pd.date_range(start=my_df["DATE"].min(),end=my_df["DATE"].max(),freq="D")

    # compare with actual dates
    missing = full_range.difference(my_df["DATE"])

    if len(missing) == 0:
        log("CHECK MISSING DAYS : No missing days detected","INFO")
    else:
        log(f"CHECK MISSING DAYS : Missing {len(missing)} days:\n","INFO")
        for d in missing:
            log(d.date(),"INFO")

    return missing
""" 

## ----------------------------------------------------------------------
## Main Code
## ----------------------------------------------------------------------
## AR1 - Disaster Risk Modelling 
##
## - The main code is a computational model based on the Canadian Forest Fire Weather Index System (Est. 1985)
## - This models the risk of wildfires through the input of temperature, humidity, rain and windspeed variables
##
## - Open source information is from official Canadian Weather Data, specifically the data linked below, recorded at ASHCROFT, BRITISH COLUMBIA hourly between June 2010 to February 2026
##   https://climate.weather.gc.ca/climate_data/hourly_data_e.html?hlyRange=2010-06-16%7C2026-02-14&dlyRange=2010-06-16%7C2026-02-14&mlyRange=%7C&StationID=48708&Prov=BC
##
## - In the file provided, there should be a 5 year snippet from Jan 1 2011 to Dec 31 2016 included
##
## - My Weather Station (Embedded System) creates weather data with the exact same headers as the weather data csv files linked, so this program interacts properly with both.
## ----------------------------------------------------------------------


# Print Logo, then loop trying to collect CSV file locally or through HTTP remotely until file is usable
filename = csv_file_collect() 

# Initialise dataframe from CSV with pandas
df = pd.read_csv(filename)

# Get the dict of header names, add the extra (empty) the dataframes columns and save as a prepped file
daily_df,headers = csv_file_prep(df)

# Compute the original dataframe
final_df_original = fully_calculate_fwi(daily_df, headers)

# DEBUG - Used to check dataframe is okay and whether theres any missing days when I was testing with varying size of data
#print(final_df_standard)
#check_missing_days(final_df_standard, headers)

# Inform end-user of next plotting process
print("")
log(" --- PLOTLY GRAPHING WARNING --- ","WARN")
log("Program will now attempt to graph this original dataframe using plotly","INFO")
log("For many reasons, Plotly can decide to not load the graph.","INFO")
log("If this happens, close your browser window, return to the program and ask to reload the graph","INFO")
input("Press enter to continue for Original Results (AR1)")
print("")

# Graph the original df before going onto What If scenarios
final_df_original_columns = headers['DSR'] # Only Plot DSR for now, will plot weather data on What-If Scenarios
graph_df(final_df_original,headers,final_df_original_columns,"Original Dataframe and DSR value","Time","DSR","original_dataframe.html")

## ----------------------------------------------------------------------
## What If scenarios
## ----------------------------------------------------------------------

# Inform end-user of the What If scenarios I intend on doing, and that I will plot them now
print("")
log(" --- WHAT IF SCENARIOS INFORMATION --- ","WARN")
log("This program will now graph 4 subgraphs for each What-If scenario","INFO")
log("(1) Scientists predict global temperature will increase by 2 degrees by 2100, how will that affect wildfires?","INFO")
log("(2) How would wildfires be affected if the rain increased in this area?","INFO")
log("(3) How much does humidity actually affect the Fire Weather Index variables?","INFO")
log("(4) How much worse would wildfires be if the wind doubled?","INFO")
log("Each subgraph will be labelled accordingly","INFO")
log("Once again, if the graph failes to load, close the browser window and reload the graph","INFO")
input("Press enter to continue onto What-If Scenarios (AR2)")
print("")

# Create copies of the dataframes to make What-If scenarios with
df_temp_increase = final_df_original.copy()         # Relates to predicted global temperature in 2100
df_rain_increase = final_df_original.copy()         # What if rain increased in this area
df_humidity_increase = final_df_original.copy()     # What if humidity increased? 
df_wind_double = final_df_original.copy()           # What if wind doubled? How would other variables react

# Manipulate the What-If variables
df_temp_increase[headers['temp']] += 2 # Increase temperature by 2 degrees celcius

df_rain_increase[headers['rain']] *= 1.2 # Increase the rain by 20 percent

df_humidity_increase[headers['hum']] += 10 # Increase humidity by 10, make sure it doesnt go over 100
df_humidity_increase[headers['hum']] = df_humidity_increase[headers['hum']].clip(upper=100)

df_wind_double[headers['wind']] *= 2 # Double the wind values

# What-If columns for each graph
final_df_what_if_columns = [headers['wind'], headers['temp'], headers['hum'], headers['rain'], headers['DSR']]

# Calculate FWI for each What-If scenario
final_temp_increase = fully_calculate_fwi(df_temp_increase, headers)
final_rain_increase = fully_calculate_fwi(df_rain_increase, headers)
final_humidity_increase = fully_calculate_fwi(df_humidity_increase, headers)
final_wind_double = fully_calculate_fwi(df_wind_double, headers)

# Display the What-If graph
print("")
subplot_graph_df(final_temp_increase,final_rain_increase,final_humidity_increase,final_wind_double,final_df_what_if_columns,"What If Scenario's effect with Sensor Values and DSR","what_if_scenarios.html")