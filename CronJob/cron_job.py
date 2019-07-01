import os
import sys 

# Add /Modules to sys path so that program has access to the files in the Modules folder
sys.path.append(os.getcwd() + '/Modules')

import time
import mysql.connector
import numpy as np
import pandas as pd
import json
from datetime import datetime
import os.path
import csv
from DepartureDelay import predictCompulsaryDelay
from DepartureDelay import predictDepartureDelay
from ArrivalDelay import predictArrivalDelay
from WeatherDelay import predictWeatherDelay
from WeatherDelay import findNearest

# Connect to Database

flightdb = mysql.connector.connect(
	host="localhost",
	user="root",
	passwd="",
	database="flights"
)

# Constant MIN_PREP_TIME for setting minimum preperation time (Use same value as that used while training)

MIN_PREP_TIME = 30

def getLatestInfo(tailNum):
	''' 
		Returns tuple with info about last Occurance of flight with particular tail number
		Parameters: tailNumber (string)
		Returns: tuple (Destination Airport, Scheduled Arrival Epoch, Arrival Delay)
	'''
	
	dbnewcursor = flightdb.cursor()
	
	# Fetch the flight with passed Tail number present in FlightInfo having the highest Scheduled Departure Epoch (Latest)
	
	sqlst = "SELECT FlightIdentifier, SchArrEpoch, DestinationAirport, HasDeparted FROM FlightInfo WHERE SchDepEpoch = (SELECT MAX(SchDepEpoch) FROM FlightInfo WHERE TailNumber = '" + tailNum + "') AND TailNumber = '" + tailNum + "'"
	dbnewcursor.execute(sqlst)
	
	# Maximum one flight will be returned (We can use fetchone() but it will raise error in case length of cursor is 0)
	
	tl = dbnewcursor.fetchall()
	
	# If length of result is not 0 then flight is present in either InAir or Scheduled (whose Info is in FlightInfo)
	# Get Arrival Delay of this flight (Predicted) and return all values.
	
	if len(tl) != 0:
		fi, sae, da, hd = tl[0]
		
		if hd == 'Y':
			dbnewcursor.reset()
			sqlst = "SELECT ArrivalDelay FROM InAir WHERE FlightIdentifier = '" + fi + "'"
			dbnewcursor.execute(sqlst)
			ad = dbnewcursor.fetchone()[0]
		else:
			dbnewcursor.reset()
			sqlst = "SELECT ArrivalDelay FROM Scheduled WHERE FlightIdentifier = '" + fi + "'"
			dbnewcursor.execute(sqlst)
			ad = dbnewcursor.fetchone()[0]
		
		dbnewcursor.close()
		
		return (da, sae, ad)
	
	# If length of result is 0 then no flight is present in InAir or Scheduled with given tail number
	# Search for flight in LastLanding and return values if found
	
	sqlst = "SELECT LastLandingLocation, ArrivalDelay, ScheduledArrivalEpoch FROM LastLanding WHERE TailNumber = '" + tailNum + "'"
	dbnewcursor.execute(sqlst)
	tl = dbnewcursor.fetchall()
	
	dbnewcursor.close()
	
	if len(tl) != 0:
		lll, ad, sae = tl[0]
		
		return(lll, sae, ad)
	
	# If no flight with given tail number is found
	
	return ('UNKNOWN', -1, -1)

# Open log.json file and read the value (integer)
# log.json file contains the CE of previous exucution of cron job
# LUE = Last Update Epoch

with open("log.json", "r") as read_file:
	LUE = json.load(read_file)

# ToDo: Change to system utc epoch while deployment
# CE = Current Epoch

# Windows Testing
# CE = LUE + 5

# LinuxDeployment
CE = int(int(time.time())/60)

# When running for the first time with empty database
# log.json --> 23667020
# CE = 23668465

# Edited will hold the tail numbers of all the flights that will be updated

Edited = list()

dbcursor = flightdb.cursor()

# ************* SECTION TO HANDLE LANDED FLIGHTS *************

# Each row in Data_Jan/Actual_Arrival.csv contains Flight Identifier, Actual Arrival Epoch and Actual Arrival Delay
# Read the CSV
# Make a dataframe that contains only the flights which landed after Last Update epoch (LUE) and till Current Epoch (CE) (Including CE)

actual_arrival = pd.read_csv('Data_Jan/Actual_Arrival.csv')
actual_arrival = actual_arrival[(actual_arrival.ARRIVAL_EPOCH > LUE) & (actual_arrival.ARRIVAL_EPOCH <= CE)]

arrival_log = []

if len(actual_arrival) != 0:
	flights_landed_mat = actual_arrival[['FLIGHT_IDENTIFIER', 'ARRIVAL_DELAY']].values
	
	# Will contain Flight Identifiers
	
	flights_landed = list()
	
	# Will store mapping flight Identifier -> Arrival Delay and will be while updating LastLanding
	
	flights_landed_dict = dict()
		
	for fi, ad in flights_landed_mat:
		flights_landed.append(fi)
		flights_landed_dict[fi] = int(ad)
	
	# arrival_log will store the Predicted Arrival Delays before removing the entry to store in Log
	
	dbcursor.execute("SELECT FlightIdentifier, ArrivalDelay FROM InAir WHERE FlightIdentifier IN " + str(tuple(flights_landed) + ('Junk','More_Junk')))
	arrival_log = dbcursor.fetchall()

	# Delete entries of landed flights from InAir, WeatherInfo, PrevFlightInfo
	
	sqlst = "DELETE FROM InAir WHERE FlightIdentifier IN " + str(tuple(flights_landed) + ('Junk','More_Junk'))
	dbcursor.execute(sqlst)
	flightdb.commit()
	
	sqlst = "DELETE FROM WeatherInfo WHERE FlightIdentifier IN " + str(tuple(flights_landed) + ('Junk','More_Junk'))
	dbcursor.execute(sqlst)
	flightdb.commit()

	sqlst = "DELETE FROM PrevFlightInfo WHERE FlightIdentifier IN " + str(tuple(flights_landed) + ('Junk','More_Junk'))
	dbcursor.execute(sqlst)
	flightdb.commit()
	
	# Update the Destination Airport, Scheduled Arrival Epoch and Arrival Delay for landed Tail Numbers
	
	dbcursor.execute("SELECT FlightIdentifier, TailNumber, DestinationAirport, SchArrEpoch FROM FlightInfo WHERE FlightIdentifier IN " + str(tuple(flights_landed)  + ('Junk','More_Junk')))
	result = dbcursor.fetchall()
	
	templist = list()
	
	for fi, tn, da, sae in result:
		t = (tn, da, flights_landed_dict[fi], sae)
		templist.append(t)
		
		# Add Tail Number to Edited
		Edited.append(tn)
	
	sqlst = "REPLACE INTO LastLanding VALUES (%s, %s, %s, %s)"
	dbcursor.executemany(sqlst, templist)
	flightdb.commit()
	
	# Delete entries of landed flights from FlightInfo
	
	sqlst = "DELETE FROM FlightInfo WHERE FlightIdentifier IN " + str(tuple(flights_landed) + ('Junk','More_Junk'))
	dbcursor.execute(sqlst)
	flightdb.commit()

# Variables from sections that will be used later too: Edited, arrival_log, actual_arrival

# ************* SECTION TO HANDLE FLIGHTS THAT TOOK OFF or GOT CANCELLED *************

# Each row in Data_Jan/Actual_Departure.csv contains Flight Identifier, Actual Departure Epoch and Actual Departure Delay
# Read the CSV
# Make a dataframe that contains only the flights which took off after Last Update epoch (LUE) and till Current Epoch (CE) (Including CE)

actual_departure = pd.read_csv('Data_Jan/Actual_Departure.csv')
actual_departure = actual_departure[(actual_departure.DEPARTURE_EPOCH > LUE) & (actual_departure.DEPARTURE_EPOCH <= CE)]

# Add Tail Numbers to Edited

for fi in actual_departure['FLIGHT_IDENTIFIER'].values:
	sqlst = "SELECT TailNumber FROM FlightInfo WHERE FlightIdentifier = '" + fi + "'"
	dbcursor.execute(sqlst)
	tn = dbcursor.fetchone()[0]
	Edited.append(tn)

# Departure_log will store the Predicted Departure Delays before transfering flights from Scheduled to InAir

dbcursor.execute("SELECT FlightIdentifier, DepartureDelay FROM Scheduled WHERE FlightIdentifier IN " + str(tuple(actual_departure['FLIGHT_IDENTIFIER'].values) + ('Junk','More_Junk')))
departure_log = dbcursor.fetchall()

# Delete entries of flights that took off from FlightInfo

sqlst = "DELETE FROM Scheduled WHERE FlightIdentifier IN " + str(tuple(actual_departure['FLIGHT_IDENTIFIER'].values) + ('Junk','More_Junk'))
dbcursor.execute(sqlst)
flightdb.commit()

if len(actual_departure) != 0:

	# 	actual_departure.CANCELLED can be equal to:
	#		0 -> Not Cancelled
	#		1 -> Cancelled, But didn't take off only
	#		2 -> Diverted to unknown location and then cancelled (Basically we don't know the landing location of these flights)
	# departure_cancelled is a dataframe that contains flights that are cancelled
	# actual_departure now contains only flights that were not cancelled and landed successfully in future
	
	departure_cancelled = actual_departure[(actual_departure.CANCELLED != 0)]
	actual_departure = actual_departure[(actual_departure.CANCELLED == 0)]
	
	if len(actual_departure) != 0:
		flights_departed_mat = actual_departure[['FLIGHT_IDENTIFIER', 'DEPARTURE_EPOCH', 'DEPARTURE_DELAY']].values
		
		# For all the flights that took off predict the Arrival Delay with and INSERT the entry in InAir with each row in InAir containing:
		# 	Flight Identifier, Actual Departure Delay, Predicted Arrival Delay, Wrong(Default Zero)
		# 'Wrong' is used later
		# Also update HasDeparted in FlightInfo to 'Y' and the LastUpdateEpoch which is used to check if flight was updated in WebApp while implementing automatic refresh
		
		for fi, de, dd in flights_departed_mat:
			sqlst = "SELECT OriginAirport, ScheduledTime, ScheduledArrival FROM FlightInfo WHERE FlightIdentifier = '" + fi + "'"
			dbcursor.execute(sqlst)
			oa, st, sa = dbcursor.fetchone()
			
			ad = predictArrivalDelay(st, sa, dd)
			t = (fi, int(dd), int(ad), 0)
			
			sqlst = "INSERT INTO InAir VALUES " + str(t)
			dbcursor.execute(sqlst)
			flightdb.commit()
			
			sqlst = "UPDATE FlightInfo SET HasDeparted = 'Y', LastUpdateEpoch = " + str(CE) + " WHERE FlightIdentifier = '" + fi + "'"
			dbcursor.execute(sqlst)
			flightdb.commit()
			
			# Update WeatherInfo with the closest point to actual departure epoch in weather information available
			
			cP = findNearest(oa, int(de))
			
			if cP == None:
				cP = -1
			else:
				cP = cP['valid_time_gmt']
			
			sqlst = "UPDATE WeatherInfo SET WeatherDelay = -1, WeatherPointEpoch = " +  str(int(cP)) + " WHERE FlightIdentifier = '" + fi + "'"
			dbcursor.execute(sqlst)
			flightdb.commit()
	
	if len(departure_cancelled) != 0:
		
		# For all the flights that were cancelled:
		# 	if departure_cancelled.CANCELLED == 1:
		#		Don't do anything as the LastLanding already contains the info of last successful landing
		# 	if departure_cancelled.CANCELLED == 2:
		# 		Delete entry from Last Landing for that tail number as the information becomes invalid
		# 	Delete entries of flights that were cancelled from WeatherInfo, PrevFlightInfo, FlightInfo
		
		if len(departure_cancelled[departure_cancelled.CANCELLED == 2]) != 0:
			location_unknown = departure_cancelled[departure_cancelled.CANCELLED == 2]['FLIGHT_IDENTIFIER'].values
			
			dbcursor.execute("SELECT TailNumber FROM FlightInfo WHERE FlightIdentifier IN " + str(tuple(location_unknown)  + ('Junk','More_Junk')))
			t = dbcursor.fetchone()[0]
			print(t)
			sqlst = "DELETE FROM  LastLanding WHERE TailNumber IN " + str(tuple(t) + ('Junk', 'More_Junk'))
			dbcursor.execute(sqlst)
			flightdb.commit()
		
		sqlst = "DELETE FROM WeatherInfo WHERE FlightIdentifier IN " + str(tuple(departure_cancelled['FLIGHT_IDENTIFIER'].values) + ('Junk','More_Junk'))
		dbcursor.execute(sqlst)
		flightdb.commit()
	
		sqlst = "DELETE FROM PrevFlightInfo WHERE FlightIdentifier IN " + str(tuple(departure_cancelled['FLIGHT_IDENTIFIER'].values) + ('Junk','More_Junk'))
		dbcursor.execute(sqlst)
		flightdb.commit()
		
		sqlst = "DELETE FROM FlightInfo WHERE FlightIdentifier IN " + str(tuple(departure_cancelled['FLIGHT_IDENTIFIER'].values) + ('Junk','More_Junk'))
		dbcursor.execute(sqlst)
		flightdb.commit()

# Variables from sections that will be used later too: Edited, departure_log, actual_departure

# ************* SECTION TO UPDATE FLIGHTS IN SCHEDULED WHERE TAIL NUMBER IS PRESENT IN Edited *************

# Check Edited for Duplicate Entries

Edited = list(set(Edited))

# SELECT information required for predicting Departure Delay of flights with tail numbers as that in Edited which are present in InAir
# Means that the update is required because the flight with the same tail number took off
# Store result of Select query to tail_changed1
# Also remove the found tail numbers from Edited

sqlst = "SELECT FlightInfo.TailNumber, FlightInfo.DestinationAirport, FlightInfo.SchArrEpoch, InAir.ArrivalDelay FROM FlightInfo INNER JOIN InAir ON FlightInfo.FlightIdentifier = InAir.FlightIdentifier WHERE FlightInfo.TailNumber IN " + str(tuple(Edited) + ('Junk', 'More_Junk'))
dbcursor.execute(sqlst)
tail_changed1 = dbcursor.fetchall()

for t in tail_changed1:
	Edited.remove(t[0])

# SELECT information required for predicting Departure Delay of flights with tail numbers as that in Edited which are present in LastLanding
# Means that the update is required because the flight with the same tail number Landed
# Store result of Select query to tail_changed2
# Also remove the found tail numbers from Edited

sqlst = "SELECT TailNumber, LastLandingLocation, ScheduledArrivalEpoch, ArrivalDelay FROM LastLanding WHERE TailNumber IN " + str(tuple(Edited) + ('Junk', 'More_Junk'))
dbcursor.execute(sqlst)
tail_changed2 = dbcursor.fetchall()

for t in tail_changed2:
	Edited.remove(t[0])

# Add lists tail_changed1, tail_changed2

tail_changed = tail_changed1 + tail_changed2

# Now only remaining tail numbers in Edited are of flights which departed but were diverted and never reached the destination

for tailNum in Edited:
	t = (tailNum, 'UNKNOWN', -1, -1)
	tail_changed.append(t)

# Now all entries in this list tail_changed contains a tupple:
# 	(Tail Number, Current Know Location, Previous flights Scheduled Arrival Epoch, Previous flights Scheduled Arrival Delay)
# Which will be used to predict departure delay for next flight

for tailNum, currLoc, prevSchArrEpoch, prevArrDelay in tail_changed:

	# Select all flights with tail number in Scheduled
	# These flights need to be updated
	
	sqlst = "SELECT FlightIdentifier, Month, DayOfWeek, Distance, OriginAirport, DestinationAirport, SchDepEpoch, SchArrEpoch, ScheduledTime, ScheduledArrival FROM FlightInfo WHERE TailNumber = '" + tailNum + "' AND HasDeparted = 'N' ORDER BY SchDepEpoch"
	dbcursor.execute(sqlst)
	flights_scheduled = dbcursor.fetchall()
	
	# Iteratively predict departure and arrival delay and store predictions
	
	for fi, m, dOW, d, oA, dA, sDE, sAE, sT, sA in flights_scheduled:	
		
		# interval = Scheduled Departure Epoch of current flight - Scheduled Arrival Epoch of prev Flight
		# Store the prevArrDelay and interval in PrevFlightInfo to display in WebApp Later
		# Check if Origin Airport of current flight is same as destination of previous
		
		if currLoc == oA:
			interval = sDE - prevSchArrEpoch
			sqlst = "UPDATE PrevFlightInfo SET PrevArrivalDelay = " + str(int(prevArrDelay)) + ", PrepTime = " +  str(interval) + " WHERE FlightIdentifier = '" + fi + "'"
			dbcursor.execute(sqlst)
			flightdb.commit()
		
		else:
			interval = MIN_PREP_TIME
			prevArrDelay = 0
			sqlst = "UPDATE PrevFlightInfo SET PrevArrivalDelay = -999, PrepTime = -999 WHERE FlightIdentifier = '" + fi + "'"
			dbcursor.execute(sqlst)
			flightdb.commit()
		
		m, dOW, sD, interval, compulsaryDelay = predictCompulsaryDelay(oA, interval, prevArrDelay, sDE)
		dd = int(predictDepartureDelay(m, dOW, sD, d, interval) + compulsaryDelay)
		wd, cP = predictWeatherDelay(oA, sDE, dd)
		ad = int(predictArrivalDelay(sT, sA, dd + wd))
		
		# Update Scheduled
		
		sqlst = "UPDATE Scheduled SET DepartureDelay = " + str(int(dd + wd)) + ", ArrivalDelay = " +  str(ad) + " WHERE FlightIdentifier = '" + fi + "'"
		dbcursor.execute(sqlst)
		flightdb.commit()
		
		# Update WeatherInfo with new calculated Weather Delay and Closest Point Found(To be used to display weather info in WebApp)
		
		sqlst = "UPDATE WeatherInfo SET WeatherDelay = " + str(int(wd)) + ", WeatherPointEpoch = " +  str(int(cP)) + " WHERE FlightIdentifier = '" + fi + "'"
		dbcursor.execute(sqlst)
		flightdb.commit()
		
		# Update LastUpdateEpoch
		
		sqlst = "UPDATE flightinfo SET LastUpdateEpoch = " + str(CE) + " WHERE FlightIdentifier = '" + fi + "'"
		dbcursor.execute(sqlst)
		flightdb.commit()
		
		# Find out currLoc, prevSchArrEpoch, predictArrivalDelay which will be used for next flight in the chain
		
		currLoc = dA
		prevSchArrEpoch = sAE
		prevArrDelay = ad

# ************* SECTION TO ADD NEW FLIGHTS TO SCHEDULED *************

# Each row in Data_Jan/Schedule.csv contains Flights information that we know beforehand
# Read the CSV
# Scheduled table in database contains flights scheduled for next day from LUE
# Add flights of 'n' mins after that
# Make a dataframe that contains only the flights which are scheduled 'n' mins between 'LUE + 1 day' and 'CE + 1 day'
# n = interval of running cronjob

flights_new = pd.read_csv('Data_Jan/Schedule.csv')
flights_new = flights_new[(flights_new.SCH_DEP_EPOCH > LUE + 1440) & (flights_new.SCH_DEP_EPOCH <= CE + 1440)]

flights_new_identifier = flights_new["FLIGHT_IDENTIFIER"].values
flights_new_tail = flights_new["TAIL_NUMBER"].values

LatestInfo = dict()

# Get last occurance of flight with same tail number as that to be added to schedule
# Dictionary mapping Tail Number -> Tuple of Latest Flights Info

for tn in flights_new_tail:
	LatestInfo[tn] = getLatestInfo(tn)


# INSERT information into FlightInfo for each flight with Last Update Epoch as Current Epoch

flights_new["HAS_DEPARTED"] = "N"
flights_new["LastUpdateEpoch"] = CE
flights_new.SCH_DEP_EPOCH = flights_new.SCH_DEP_EPOCH.astype(int)
flights_new.SCH_ARR_EPOCH = flights_new.SCH_ARR_EPOCH.astype(int)
flights_new.FLIGHT_NUMBER = flights_new.FLIGHT_NUMBER.astype(str)

tuples = [tuple(x) for x in flights_new.values]

sqlst = "INSERT INTO FlightInfo VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
dbcursor.executemany(sqlst, tuples)
flightdb.commit()

# Predict Departure and Arrival Delays for flights and store in Scheduled
# Also INSERT in PrevFlightInfo, WeatherInfo
# This operation is similar to that done previously of predicting delays and storing

for fi in flights_new_identifier:
	sqlst = "SELECT TailNumber FROM FlightInfo WHERE FlightIdentifier = '" + fi + "'" 
	dbcursor.execute(sqlst)
	tailNum = dbcursor.fetchone()[0]
	
	currLoc, prevSchArrEpoch, prevArrDelay = LatestInfo[tailNum]
	
	sqlst = "SELECT Month, DayOfWeek, Distance, OriginAirport, DestinationAirport, SchDepEpoch, SchArrEpoch, ScheduledTime, ScheduledArrival FROM FlightInfo WHERE FlightIdentifier = '" + fi + "'"
	dbcursor.execute(sqlst)
	m, dOW, d, oA, dA, sDE, sAE, sT, sA = dbcursor.fetchone()
	
	if currLoc == oA:
		interval = sDE - prevSchArrEpoch
		
		t = (fi, int(prevArrDelay), int(interval))
	
		sqlst = "INSERT INTO PrevFlightInfo VALUES " + str(t)
		dbcursor.execute(sqlst)
		flightdb.commit()
	
	else:
		interval = MIN_PREP_TIME
		prevArrDelay = 0
		
		t = (fi, -999, -999)
		
		sqlst = "INSERT INTO PrevFlightInfo VALUES " + str(t)
		dbcursor.execute(sqlst)
		flightdb.commit()
	
	m, dOW, sD, interval, compulsaryDelay = predictCompulsaryDelay(oA, interval, prevArrDelay, sDE)
	dd = int(predictDepartureDelay(m, dOW, sD, d, interval) + compulsaryDelay)
	wd, cP = predictWeatherDelay(oA, sDE, dd)
	ad = int(predictArrivalDelay(sT, sA, dd + wd))
	
	t = (fi, int(dd + wd), int(ad), 0)
	
	sqlst = "INSERT INTO Scheduled VALUES " + str(t)
	dbcursor.execute(sqlst)
	flightdb.commit()
	
	t = (fi, int(wd), int(cP))
	
	sqlst = "INSERT INTO WeatherInfo VALUES " + str(t)
	dbcursor.execute(sqlst)
	flightdb.commit()

# ************* SECTION FOR HANDLING WRONG DELAY PROPOGATION*************

# Select all flights for which --> Scheduled Arrival Epoch + Predicted Arrival Delay > Current Epoch

sqlst = "SELECT FlightInfo.FlightIdentifier, FlightInfo.HasDeparted, FlightInfo.TailNumber, FlightInfo.DestinationAirport, FlightInfo.SchArrEpoch, InAir.Wrong FROM Flightinfo INNER JOIN InAir ON Flightinfo.FlightIdentifier = InAir.FlightIdentifier WHERE FlightInfo.SchArrEpoch + InAir.ArrivalDelay <= " + str(CE) + ";"
dbcursor.execute(sqlst)
flights_wrong_arr_pred = dbcursor.fetchall()

# Select all flights for which --> Scheduled Departure Epoch + Predicted Departure Delay > Current Epoch

sqlst = "SELECT FlightInfo.FlightIdentifier, FlightInfo.HasDeparted, FlightInfo.TailNumber, FlightInfo.DestinationAirport, FlightInfo.SchArrEpoch, Scheduled.Wrong FROM Flightinfo INNER JOIN Scheduled ON Flightinfo.FlightIdentifier = Scheduled.FlightIdentifier WHERE FlightInfo.SchDepEpoch + Scheduled.DepartureDelay <= " + str(CE) + ";"
dbcursor.execute(sqlst)
flights_wrong_dep_pred = dbcursor.fetchall()

flights_wrong_pred = flights_wrong_arr_pred + flights_wrong_dep_pred

for fliId, hasDep, tailNum, currLoc, prevSchArrEpoch, wrong in flights_wrong_pred:
	
	# Check if Arrival is Predicted Wrong(hasDep == 'Y') or Departure(hasDep == 'N')
	
	if hasDep == 'Y':
		
		# Update InAir.Wrong and FlightInfo.LastUpdateEpoch if needed
		# Calculate prevArrDelay (i.e Predict new Arrival Delay of the flight DON'T STORE) so that it can be used for further flights correction
		
		if wrong == 0:
			sqlst = "UPDATE InAir SET Wrong = 1 WHERE FlightIdentifier = '" + fliId + "'"
			dbcursor.execute(sqlst)
			flightdb.commit()
			
			sqlst = "UPDATE flightinfo SET LastUpdateEpoch = " + str(CE) + " WHERE FlightIdentifier = '" + fliId + "'"
			dbcursor.execute(sqlst)
			flightdb.commit()
		
		prevArrDelay = CE - prevSchArrEpoch
	else:
		
		# Update InAir.Wrong and FlightInfo.LastUpdateEpoch if needed
		
		if wrong == 0:
			sqlst = "UPDATE Scheduled SET Wrong = 1 WHERE FlightIdentifier = '" + fliId + "'"
			dbcursor.execute(sqlst)
			flightdb.commit()
			
			sqlst = "UPDATE flightinfo SET LastUpdateEpoch = " + str(CE) + " WHERE FlightIdentifier = '" + fliId + "'"
			dbcursor.execute(sqlst)
			flightdb.commit()

		sqlst = "SELECT SchDepEpoch, ScheduledTime, ScheduledArrival FROM FlightInfo WHERE FlightIdentifier = '" + fliId + "'"
		dbcursor.execute(sqlst)
		schDepEp, schTime, schArr = dbcursor.fetchone()
		
		depDelay = 	CE - schDepEp
		prevArrDelay = int(predictArrivalDelay(schTime, schArr, depDelay))
	
	# Update the Departure and Arrival Delay of next flights in the chain (Same operations as done previously)
	
	sqlst = "SELECT FlightIdentifier, Month, DayOfWeek, Distance, OriginAirport, DestinationAirport, SchDepEpoch, SchArrEpoch, ScheduledTime, ScheduledArrival FROM FlightInfo WHERE TailNumber = '" + tailNum + "' AND HasDeparted = 'N' AND SchDepEpoch > " + str(prevSchArrEpoch) + " ORDER BY SchDepEpoch"
	dbcursor.execute(sqlst)
	flights_scheduled = dbcursor.fetchall()
	
	for fi, m, dOW, d, oA, dA, sDE, sAE, sT, sA in flights_scheduled:	
		
		if currLoc == oA:
			interval = sDE - prevSchArrEpoch
			
			sqlst = "UPDATE PrevFlightInfo SET PrevArrivalDelay = " + str(int(prevArrDelay)) + ", PrepTime = " +  str(interval) + " WHERE FlightIdentifier = '" + fi + "'"
			dbcursor.execute(sqlst)
			flightdb.commit()
		
		else:
			interval = MIN_PREP_TIME
			prevArrDelay = 0
			
			sqlst = "UPDATE PrevFlightInfo SET PrevArrivalDelay = -999, PrepTime = -999 WHERE FlightIdentifier = '" + fi + "'"
			dbcursor.execute(sqlst)
			flightdb.commit()
		
		m, dOW, sD, interval, compulsaryDelay = predictCompulsaryDelay(oA, interval, prevArrDelay, sDE)
		dd = int(predictDepartureDelay(m, dOW, sD, d, interval) + compulsaryDelay)
		wd, cP = predictWeatherDelay(oA, sDE, dd)
		
		ad = int(predictArrivalDelay(sT, sA, dd + wd))
		
		sqlst = "UPDATE Scheduled SET DepartureDelay = " + str(int(dd + wd)) + ", ArrivalDelay = " +  str(ad) + " WHERE FlightIdentifier = '" + fi + "'"
		dbcursor.execute(sqlst)
		flightdb.commit()
		
		sqlst = "UPDATE WeatherInfo SET WeatherDelay = " + str(int(wd)) + ", WeatherPointEpoch = " +  str(int(cP)) + " WHERE FlightIdentifier = '" + fi + "'"
		dbcursor.execute(sqlst)
		flightdb.commit()
		
		sqlst = "UPDATE flightinfo SET LastUpdateEpoch = " + str(CE) + " WHERE FlightIdentifier = '" + fi + "'"
		dbcursor.execute(sqlst)
		flightdb.commit()
		
		currLoc = dA
		prevSchArrEpoch = sAE
		prevArrDelay = ad


# All operations were succussful
# Now update the log.json file with current epoch

with open("log.json", "w") as write_file:
	json.dump(CE, write_file)

dbcursor.close()
flightdb.close()

# Write Log according to date

fileDeparturePath = "Logs/Departure/" + datetime.utcnow().strftime("%d_%m_%Y") + ".csv"
fileArrivalPath = "Logs/Arrival/" + datetime.utcnow().strftime("%d_%m_%Y") + ".csv"

with open (fileDeparturePath, 'a', newline='') as log:
	csv_out=csv.writer(log)
	if os.stat(fileDeparturePath).st_size == 0:
		csv_out.writerow(['FlightIdentifier','Predicted', 'Actual'])
	for fI, pDD in departure_log:
		if actual_departure[actual_departure.FLIGHT_IDENTIFIER == fI].shape[0] != 0:
			aDD = actual_departure[actual_departure.FLIGHT_IDENTIFIER == fI]['DEPARTURE_DELAY'].iloc[0]
			tempTup = (fI, pDD, int(aDD))
			csv_out.writerow(tempTup)

with open (fileArrivalPath, 'a', newline='') as log:
	csv_out=csv.writer(log)
	if os.stat(fileArrivalPath).st_size == 0:
		csv_out.writerow(['FlightIdentifier','Predicted', 'Actual'])
	for fI, pAD in arrival_log:
		aAD = actual_arrival[actual_arrival.FLIGHT_IDENTIFIER == fI]['ARRIVAL_DELAY'].iloc[0]
		tempTup = (fI, pAD, int(aAD))
		csv_out.writerow(tempTup)

#ToDo: Implement flock while deploying on Linux
