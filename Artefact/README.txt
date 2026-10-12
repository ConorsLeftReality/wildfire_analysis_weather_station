
===================================

CompSci 2026 LC FINAL PROJECT
Weather Station Embedded System - Ubuntu 24.04 - Raspberry Pi 3B+
Powered by Python 3
System Administrator's Documentation

===================================
INDEXING 
===================================

- File Organisation
	- File Paths
	- Program Requirements
- Service Details
	- Service Name + Description
	- Journalctl command
	- Restart command
- Backups
	- Local Backups
	- SCP backup procedure
- Development / Debug
	- Source CMD for venv
	- Abstract Program Workflow
	- Sensors + Hardware Used
	- CSV file expected output
	- HTTP Server 

===================================
FILE ORGANISATION
===================================
- File Paths
	/srv/venv
	     |
	     v
	artefact.py
	README.txt
	weather_data.csv
	/backup
	/testing

- Program Requirements
	The Program requires artefact.py and for the dependancies in requirements.txt
	If there is no requirements.txt, list of dependancies can be found in artefact.py above modules

===================================
SERVICE DETAILS
===================================
- Service Name + Description
	DataLogger.service runs artefact.py as root automatically on boot-up

- Journalctl command
	To view logs: 
	journalctl -u DataLogger -f -o cat --no-pager 

	To view status, use systemctl (as usual)

- Restart Command
	To restart on the next hour:
	systemd-run --on-calendar="$(date -d 'next hour' '+%Y-%m-%d %H:00:00')" systemctl restart DataLogger.service

===================================
BACKUPS
===================================
- Local Backups
	Local Backups are made in /testing
	For every version and change to artefact.py, the developer should copy the
	previous version to /backups with the following name format:

	artefact.py.dd_mm_yyyy

- SCP Backup Procedure
	1) Log onto external device (such as laptop)

	2) Run following scp command as sudo
	   scp -rv ~/venv cmasterson@current-IP:"C:\Users\cmasterson\Desktop\venv_backupDD_MM_YY"

	Note: You can find current-IP for the weather station through Tailscale GUI or IPCONFIG

===================================
Development / Debug
===================================
- Source CMD
	In order to interact with venv and exteral dependancies,
	run 'source /srv/venv/bin/activate'

- Abstract Program Workflow
	jkasgdpjaghjdhgasd

- Sensors / Hardware Used
	Embedded System - Raspberry Pi 3B+ with 16Gb MicroSD card
	LCD - Generic 16x2 I2C LCD Board, used for program data output
	ADC Board - ADAFRUIT ADS1115 - Used to measure Voltages on sensors
	
	Sensors - Temperature Sensor - TMP36 Voltage Thermometer
		- Humidity Sensor - AM1011A Humidity and Temperature Sensor 
			(Not using Temperature sensor as it is a thermister)
		- Rainfall Sensor - Reed Switch in a 3D printed Rain Gauge
		- Windspeed Sensor - Generic Voltage Anemometer w/ linear readings from 0-3.3V

- Troubleshoot I2C
	Firstly, check the wires are in the GPIO slots correctly	
	Then, check 'i2cdetect -y 1' to see if theres any addresses for I2C detected,
	if there arent, check it the cables are backwards.
	Expect 2 addresses if LCD and ADC are present, one if only one present

- CSV File Expected Output
	Time is seconds since 1 Jan 1970, also known as Unix Time, found via int(time.time())

	Format for Data:
	Longitude (x),Latitude (y),Station Name,Climate ID,Date/Time (LST),Year,Month,Day,Time (LST),Flag,Temp (°C),Temp Flag,Dew Point Temp (°C),Dew Point Temp Flag,Rel Hum (%),Rel Hum Flag,Precip. Amount (mm),Precip. Amount Flag,Wind Dir (10s deg),Wind Dir Flag,Wind Spd (km/h),Wind Spd Flag,Visibility (km),Visibility Flag,Stn Press (kPa),Stn Press Flag,Hmdx,Hmdx Flag,Wind Chill,Wind Chill Flag,Weather
	
	We measure Lon, Lat, Station Name, Climate ID=100000, Date Variables, Time (LST), Temp (°C), Rel Hum (%), Precip. Amount (mm) and Wind Spd (km/h)

- HTTP Server
	When running artefact, .csv file will be made in the venv repository.
	To keep data consistent, change the output for production to /srv/venv and testing to /srv/venv/testing

	To access file, visit current_ip:8000/weather_data.csv

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

NOTE: READ THIS IN VI, DOESNT SHOW FULLY WITH CAT ANYMORE

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
