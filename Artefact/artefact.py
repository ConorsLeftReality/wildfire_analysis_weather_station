 ## ----------------------------------------------------------------------
##
##    CompSci Higher Level 
##  - Leaving Cert Artefact -
##       
##       Class of 2026
##
## ----------------------------------------------------------------------
##
##      Conor Masterson
##   School Roll No. REDACTED
##    Candidate No. REDACTED
##
## ----------------------------------------------------------------------
##
## Packages Used:
##
## make a list here using requirements.txt that pip can make
## 
## ----------------------------------------------------------------------


## ----------------------------------------------------------------------
## Modules Imported
## ----------------------------------------------------------------------

# I2C LCD modules
from RPLCD.i2c import CharLCD

# I2C ADC modules
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

# Sensor Loop specific modules
import datetime # Used to get the day, month and year from unixtime in sensor writing
import math # For Voltage to Temp
import RPi.GPIO as GPIO # Used to collect ticks from rainfalls reed switch

# General Modules
import time # Sleep
import os # For IP Collect and post for debug
import socket # For IP Collection
import sys # For program exit() if nessicary components fail to initialise

# HTTP Modules
from http.server import BaseHTTPRequestHandler, HTTPServer

# Threading (in order to run HTTP server and Sensor Code on seperate threads simultaneously without 2 python code files)
import threading

# Alert Email Modules
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

## ----------------------------------------------------------------------
## Classes
## - NullLCD (Subsitutuion for the LCD class in RPLCD.i2c Module if no LCD detected)
## - WeatherHandler (HTTP Request Handler, makes sure only .csv file accessed)
## ----------------------------------------------------------------------

## Class is for use if no LCD present
## Means I can have code for the LCD in my program, and the code wont crash if there isnt an actual LCD
class NullLCD:
    def clear(self):
        pass

    def write_string(self, text):
        pass

    def cursor_pos(self, row, col):
        pass


## Custom HTTP handler
## Controls which files can be accessed by people accessing HTTP server, basic cybersecurity
class WeatherHandler(BaseHTTPRequestHandler):
    def do_GET(self): # When someone sends a GET HTTP request
        # We only send back CSV, regardless of path
        self.send_response(200) # OK ACK
        self.send_header("Content-Type", "text/csv") # Content Type Headers for client
        self.end_headers() # Headers end for client

        weather_data = open(csv_file, "rb") # Reads CSV file in binary (required for HTTP)
        self.wfile.write(weather_data.read()) # Sends Data to client
        weather_data.close() # Closes CSV file, transfer is complete


## ----------------------------------------------------------------------
## Functions
## ----------------------------------------------------------------------
## - init_lcd() (Initialises the LCD screen onboard)
## - lcd_write() (Writes 2 given lines to a specified class)
## - log() 
## - init_adc() (Initialises the ADC Board for sensors)
## - init_pins() (Tests if pins output data)
## - get_ip() (Gets the current IP using sockets, multi-OS compatible)
## - logo() (Prints the Logo)
## - init_all() (Calls all init functions)
## - send_email() (Sends email via met.node.alerts@gmail.com)
## ----------------------------------------------------------------------

## ----------------------------------------------------------------------
## Function to initialise LCD
## ----------------------------------------------------------------------
def init_lcd():
    print(f"[{time.strftime('%H:%M:%S')}] Initialising the onboard I2C LCD: ",end="") # printed to indicate function started
    
    # Attempt to initialise the physical LCD
    try:
        lcd          = CharLCD(
        i2c_expander ='PCF8574',
        address      =0x27,
        port         =1,
        cols         =16,
        rows         =2,
        dotsize      =8
        )
        lcd.clear()
        print("Done") # success!
        return lcd # use the LCD class in RPLCD.i2c

    # If physical LCD doesnt initialise / fails. Doesn't need init_status here as its not nessicary
    except Exception as e:
        log(f"LCD Initialization failed : {e}","WARN")
        log("Continuing with NullLCD Class instead")
        return NullLCD() # use NullLCD class we made instead


## ----------------------------------------------------------------------
## Function to write 2 lines to the LCD
## ----------------------------------------------------------------------
def lcd_write(line1,line2,c_lcd):
    c_lcd.clear()
    c_lcd.cursor_pos = (0,0)  
    c_lcd.write_string(line1)
    c_lcd.cursor_pos = (1,0)
    c_lcd.write_string(line2)
    time.sleep(1)


## ----------------------------------------------------------------------
## Function to write data in Log Format
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
## Function to initialise ADC
## ----------------------------------------------------------------------
def init_adc():
    try:
        # Globaled to use throughout full program
        # Yes, globalling is bad, but I cant even process how to pass these variables around anymore
        global i2c, ads, chan0, chan1, chan2, chan3

        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS1115(i2c)

        # Channels for Sensors Initialised 
        chan0 = AnalogIn(ads, 0)
        chan1 = AnalogIn (ads, 1)
        chan2 = AnalogIn (ads, 2)
        chan3 = AnalogIn (ads, 3)
        
        return True,"" 
    except Exception as e:
        return False,e
    

## ----------------------------------------------------------------------
## Function to initialise ADC Pins
## ----------------------------------------------------------------------
def init_pins():
    try:
        # Testing whether pin 0 is giving voltage, will fail if it isn't
        ads.gain = 1
        variable_to_test_adc_readings = chan0.voltage

        return True,""
    except Exception as e:
        return False,e


## ----------------------------------------------------------------------
## Gets the current IP address using sockets
## Needed to access the HTTP Server
## ----------------------------------------------------------------------
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # IP specified in socket doesn't have to be reachable
        # Just needs to send a request to get this machines IP
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    # At end, must close socket
    s.close()
    return IP


## ----------------------------------------------------------------------
## Logo Print Function
## ----------------------------------------------------------------------

def logo():
    log("")
    log(r"    ____        __           __")
    log(r"   / __ \____ _/ /_____ _   / /   ____  ____ _____ ____  _____")
    log(r"  / / / / __ `/ __/ __ `/  / /   / __ \/ __ `/ __ `/ _ \/ ___/")
    log(r" / /_/ / /_/ / /_/ /_/ /  / /___/ /_/ / /_/ / /_/ /  __/ /")
    log(r"/_____/\__,_/\__/\__,_/  /_____/\____/\__, /\__, /\___/_/")
    log(r"                                     /____//____/")
    log("")


## ----------------------------------------------------------------------
## Function that runs all init functions and all_OK checks
## Debulks main code
## ----------------------------------------------------------------------

def init_all(examiner):

    # STEP 1 - INIT ADC 
    log("Initializing ADC board")
    
    result_adc,error = init_adc() 
 
    if (result_adc):
        log("ADC board OK")
    else:
        log(f"ADC board FAIL: {error}", "WARN")

    # STEP 2 - INITIALISE RAIN GAUGE
    log("Initialising Rain Gauge")

    try:
        RAIN_PIN = reed_switch_setup()
        log("Rain Gauge OK")
    except Exception as e:
        log(f"Rain Gauge FAIL: {e}","WARN")

    # STEP 3 - TEST IF PINS RECIEVE DATA
    log("Attempting to initialize Pins...")
    
    result_pins,error = init_pins() 
 
    if (result_pins):
        log("Pins initialized OK")
    else:
        log(f"Pins failed: {error}", "WARN")
    
    # STEP 4 - CHECK IF READY TO START
    if (result_pins and result_adc == True and examiner == False):
        log("INIT OK, starting program")
        return RAIN_PIN
    else:
        log("Initialization failed, exiting program","WARN")
        sys.exit(1)

def send_email(my_station_name,my_climate_ID,subject,my_alert_type,recipient=None,my_alerts=None):
    if recipient == None:
        recipient = os.getenv("GMAIL_ALERT_GROUP")
    if my_alert_type=="Weather Alert":
        body = (
            f"\nAlert from device [{my_station_name} STATION - ClimateID={my_climate_ID}]"
            +f"\nAlert Type: {my_alert_type}"
            +f"\nTimestamp: {time.strftime('%Y-%m-%d %H:%M')}"
            +f"\n\nWeather Warnings:\n\n"
            +f"\n".join(my_alerts)
            +f"\n\nAlert sent to {recipient}"
            )
    else:
        body = (
            f"\nAlert from device [{my_station_name} STATION - ClimateID={my_climate_ID}]"
            +f"\nAlert Type: {my_alert_type}"
            +f"\nTimestamp: {time.strftime('%Y-%m-%d %H:%M')}"
            +f"\n\nAlert sent to {recipient}"
            )
    
    msg = MIMEText(body)
    msg["Subject"] = f"[{subject}] - {time.strftime('%Y-%m-%d %H:%M')} - {my_station_name}({my_climate_ID})"
    msg["From"] = os.getenv("SMTP_LOGIN_EMAIL")
    msg["To"] = recipient

    # Variables stored in .env for security
    with smtplib.SMTP_SSL((os.getenv("SMTP_SERVER")), 465) as server:
        server.login(str(os.getenv("SMTP_LOGIN_EMAIL")), str(os.getenv("GMAIL_APP_PASSWORD")))
        server.send_message(msg)

        log(f"Alert [{subject}] sent via Gmail SMTP")
    
    return


## ----------------------------------------------------------------------
## Sensor Maths Functions
## ----------------------------------------------------------------------
def voltage_to_wind(voltage):
    try:
        return voltage * 28.4210526316 # Given 108km/h at 3.8V
    except Exception as e:
        log(f"Error converting volt to humidity: {e}", "WARN")
        return 0.0

def voltage_to_temp(voltage):
    try:
        return (voltage - 0.5) * 100 # From arduino forum
    except Exception as e:
        log(f"Error converting volt to temp: {e}","WARN")
        return 0.0

def voltage_to_humidity(voltage):
    try:
        return voltage / 0.03 # From datasheet
    except Exception as e:
        log(f"Error converting volt to humidity: {e}", "WARN")
        return 0.0

## ----------------------------------------------------------------------
## GPIO Setup for Rain Gauge's reed switch
## ----------------------------------------------------------------------

def reed_switch_setup():
    RAIN_PIN = 17  # GPIO pin connected to reed switch
    
    # Set up GPIO to read from this pin
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RAIN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    return RAIN_PIN # Pass the pin to sensor_loop for creation of event


# ----------------------------------------------------------------------
# Rain callback used by the GPIO add_event_detect code
# ----------------------------------------------------------------------

def rain_callback(channel):
    rain_counter += 1  # Add 1 to rain counter for every tip


## ----------------------------------------------------------------------
## Function to be read sensor data, then write to CSV every hour
## ----------------------------------------------------------------------

def sensor_loop(lcd,ip,csv_file,RAIN_PIN):
    # Initial Variables for use in Sensor Loop
    buffer = []
    write_interval = 60 * 60            # In Minutes - 1 in testing, 60 in production
    read_interval  = 4                  # In Seconds - 5 in production only due to weather station positioning 
                                        #  not being exposed enough

    last_write     = time.monotonic()   # Initial Time using monotonic

    # Station Specific Variables
    latitude  = 53.12
    longitude = -6.74
    station_name = "Kilcullen"
    climate_ID = "100000"

    
    # Setup GPIO event for rain_counter
    GPIO.add_event_detect(RAIN_PIN, GPIO.FALLING, callback=rain_callback, bouncetime=200)
    

    log("==================================================================")

    # Main Loop for Sensors, loops every (read_interval) seconds
    while True:
        # Writes to LCD to overwrite CSV writing message if it has just written
        lcd_write(ip,"ACTIVE",lcd)

        # Try collect values from sensors to add to the buffer
        try:
            wind_speed  = abs(round(voltage_to_wind(chan0.voltage), 2))
            temperature = round(voltage_to_temp(chan1.voltage),2)
            humidity    = round(voltage_to_humidity(chan2.voltage),2)

            buffer.append((wind_speed,temperature,humidity))
            log("TEMP-WRITE: Sensor Data appended to Buffer")

        # Could not read values, ADC failure, buffer failure, variable failure, log failure?
        except Exception as e:
            log(f"FAIL: Data failed to append to Buffer: {e}", "WARN")

        # Check the time of last write vs present, and compare to the write interval (converted to seconds)
        if (time.monotonic() - last_write) >= (write_interval):
            
            # Try to write to CSV
            try:
                # Tell end users
                lcd_write(ip, "DATA WRITING", lcd)
                log(f"NOTICE: Writing to {csv_file}, do not stop the program","INFO")

                ## STEP 1 - OPEN FILE AND CHECK IF EXISTS
                # Check if file exists then open/create file
                file_exists = os.path.isfile(csv_file)
                weather_data = open(csv_file, "a")

                # If file doesn't exist, write headers to new file (based on weather data headers from Ashcroft Station, BC, Canada)
                # https://climate.weather.gc.ca/climate_data/hourly_data_e.html?hlyRange=2010-06-16%7C2026-02-14&dlyRange=2010-06-16%7C2026-02-14&mlyRange=%7C&StationID=48708&Prov=BC
                if not file_exists:
                    log(f"NOTICE: No CSV file present in working directory, creating {csv_file} at {csv_file}","WARN")
                    weather_data.write("Longitude (x),Latitude (y),Station Name,Climate ID,Date/Time (LST),Year,Month,Day,Time (LST),Flag,Temp (°C),Temp Flag,Dew Point Temp (°C),Dew Point Temp Flag,Rel Hum (%),Rel Hum Flag,Precip. Amount (mm),Precip. Amount Flag,Wind Dir (10s deg),Wind Dir Flag,Wind Spd (km/h),Wind Spd Flag,Visibility (km),Visibility Flag,Stn Press (kPa),Stn Press Flag,Hmdx,Hmdx Flag,Wind Chill,Wind Chill Flag,Weather\n")

                ## STEP 2 - TIME PARSING FROM UNIX TIME
                # Find unixtime to convert into Human Readable format
                timestamp = int(time.time())
                dt = datetime.datetime.fromtimestamp(timestamp)

                # Force 2 decimals for day and month, year will always be 4 regardless
                hour  = f"{dt.hour:02d}"
                day   = f"{dt.day:02d}"
                month = f"{dt.month:02d}"
                year  = dt.year

                
                ## STEP 3 - COLLECT RAINWATER VALUE
                # Literally only issue in the code is here, if the switch flips while this is read, the reading from that flip would be lost
                rainfall = rain_counter * 0.5503 # Get rain counter and multiply by the volume per flip (0.5503mm for my rain gauge)
                rain_counter = 0
                
                rainfall = 0

                ## STEP 4 - WEATHER VARIABLE AVERAGING
                # Get averages for each variable being written
                if buffer:
                    wind_speed_entrys  = []
                    temperature_entrys = []
                    humidity_entrys    = []

                    for entry in buffer:
                        # Assign each variable in entry to *_var variables
                        wind_speed_var,temperature_var,humidity_var = entry

                        # Append these *_var variables to the entrys list
                        wind_speed_entrys.append(wind_speed_var)
                        temperature_entrys.append(temperature_var)
                        humidity_entrys.append(humidity_var)
                    
                    # Calculate averages from the entrys lists
                    wind_speed_average  = sum(wind_speed_entrys)/len(wind_speed_entrys)
                    temperature_average = sum(temperature_entrys)/len(temperature_entrys)
                    humidity_average    = sum(humidity_entrys)/len(humidity_entrys)
                else:
                    wind_speed_average = temperature_average = humidity_average = 0.0

                ## STEP 5 - ADD ROW TO CSV
                # Add a row to CSV file with averages over the hour
                weather_data.write(f'"{latitude}","{longitude}","{station_name}","{int(climate_ID)}","{year}-{month}-{day} {hour}:00","{year}","{month}","{day}","{hour}:00","","{temperature_average:.2f}","","","","{humidity_average:.2f}","","{rainfall:.3f}","","","","{wind_speed_average:.2f}","","","","","","","","","",""\n')

                ## STEP 6 - FILE CLOSE AND RESET VARIABLES NEEDING RESET
                weather_data.close() # Close File
                buffer.clear() # Clear Buffer
                last_write = time.monotonic() # Update Last Write time
                
                ## STEP 7 - BR3 Compliance, "Sim Result"
                if temperature_average >= 50:
                    log(f"BR3 Sim Result - FATAL temperature warning","WARN")
                    lcd_write(ip,"FATAL TEMP", lcd)
                elif temperature_average < 50 and temperature_average >= 30:
                    log(f"BR3 Sim Result - Extreme temperature warning","WARN")
                    lcd_write(ip,"EXTREME TEMP", lcd)
                elif temperature_average < 30 and temperature_average >= 15:
                    log(f"BR3 Sim Result - Warm temperature","INFO")
                    lcd_write(ip,"WARM TEMP", lcd)
                elif temperature_average < 15 and temperature_average >= 10:
                    log(f"BR3 Sim Result - Safe/Cold temperature","INFO")
                    lcd_write(ip,"SAFE TEMP", lcd)
                elif temperature_average < 10 and temperature_average >= -5:
                    log(f"BR3 Sim Result - Cold temperature","INFO")
                    lcd_write(ip,"COLD TEMP", lcd)
                elif temperature_average < -5:
                    log(f"BR3 Sim Result - Extreme Cold temperature warning","INFO")
                    lcd_write(ip,"EXTREME COLD", lcd)

                ## STEP 8 - CHECK IF ALERT EMAIL SHOULD BE SENT
                alerts = [] # Box for alerts to be collected in before email is composed
                try:
                    # Variable Limits for the Warning System
                    LIMITS = {"Temperature":30,"Wind":50,"Humidity":90,"Rainfall":10}
                    UNITS = {"Temperature": "°C","Wind": "km/h","Humidity": "%","Rainfall": "mm"}
                    values = {"Temperature": temperature_average,"Wind": wind_speed_average,"Humidity": humidity_average,"Rainfall": rainfall}
                    for name in values:
                        if values[name] > LIMITS[name]:
                            alerts.append(f"{name} HIGH: {values[name]} {UNITS[name]}")
        
                    if alerts:
                        log("Extreme Weather Detected, sending email alert","WARN")
                        send_email(station_name,climate_ID,"WEATHER WARNING","Weather Alert",alerts)

                except Exception as e:
                    log(f"FAIL: Failed to send email via Gmail SMTP : {e}","WARN")
                # Tell user data is done writing
                log(f"WRITE: {csv_file} updated in persistant storage")
                lcd_write(ip,"DATA WRITTEN", lcd)

            # For any failure during CSV write
            except Exception as e:
                log(f"FAIL: Failed to write Buffer to {csv_file} in persistant storage : {e}","WARN")

        time.sleep(read_interval)

def run_server(lcd,ip,csv_file):
    # Tell user HTTP server is starting then start server
    try:
        server = HTTPServer(("0.0.0.0", 8000), WeatherHandler) # 0.0.0.0 is this machine, port is 8000 and uses WeatherHandler as the HTTP handler
        log(f"HTTP Server starting on http://{ip}:8000/") # Says that the HTTP Server is running
        lcd_write(ip, "HTTP OK",lcd)
        server.serve_forever() # Starts Server

    # On Failure, tell end user
    except Exception as e:
        log(f"HTTP Server failed to start: {e}", "WARN") # Says that the HTTP Server crashed
        lcd_write(ip,"HTTP FAIL",lcd)
    

########## Main Code ##########


# CSV File Path
csv_file = "/srv/weather_station/weather_data.csv" # or data.csv when working on simulation program locally

# Load .env
load_dotenv()

# Rain Counter initialised for Rain Gauge
rain_counter = 0

# Logo displayed in CLI
logo()

# Get the IP via socket, needed for HTTP server later
ip = get_ip()

# Initialise LCD
lcd = init_lcd()

# Setup Sensors and ADC
RAIN_PIN = init_all()

# If hardware is all good, we start logging data
lcd_write(ip,"SYSTEM OK",lcd)
log("Data Logger Ready, starting sensor process in background")
send_email("Kilcullen","100000","SYSTEM START","Start-Up Alert")

## Spawn a thread to run sensor_loop
## Its a daemon thread, which means it ends when the main program's thread ends
threading.Thread(target=sensor_loop, args=(lcd,ip,csv_file,RAIN_PIN), daemon=True).start()

## Run the HTTP server - *this* is the main program's thread
## This runs until the service/program is stopped
run_server(lcd,ip,csv_file)