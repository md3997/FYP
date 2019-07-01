import numpy as np
import pickle
import json
import csv
import datetime
import pytz

pickle_in_departure_delay_regressor = open("Data/Pickles/departure_delay_regressor.pickle","rb")
departure_delay_regressor = pickle.load(pickle_in_departure_delay_regressor)

pickle_in_sc_X_departure = open("Data/Pickles/sc_X_departure.pickle","rb")
sc_X_departure = pickle.load(pickle_in_sc_X_departure)

pickle_in_sc_y_departure = open("Data/Pickles/sc_y_departure.pickle","rb")
sc_y_departure = pickle.load(pickle_in_sc_y_departure)

with open('Data/zones.csv') as f:
    reader = csv.reader(f, skipinitialspace=True)
    timeZones = dict(reader)
    
timeZones = dict((k,v) for k,v in timeZones.items())

def timeInMinutes(x):
	x = str(x).zfill(4)
	h = int(x[:2])
	m = int(x[2:])
	
	return h * 60 + m

def predictCompulsaryDelay(origin, interval, prev_arrival_delay, scheduled_departure_epoch):
    if interval - prev_arrival_delay >= 0:
        interval = interval - prev_arrival_delay
        prev_arrival_delay = 0
    else:
        prev_arrival_delay = prev_arrival_delay - interval
        interval = 0
	
    scheduled_departure_epoch = scheduled_departure_epoch + prev_arrival_delay
    tz = pytz.timezone(timeZones[origin])
    date_scheduled_departure = datetime.datetime.fromtimestamp(scheduled_departure_epoch*60, tz)
    month = date_scheduled_departure.month
    weekday = date_scheduled_departure.weekday() + 1
    scheduled_departure = str(date_scheduled_departure.hour).zfill(2) + str(date_scheduled_departure.minute).zfill(2)
    
    return (month, weekday, scheduled_departure, interval, prev_arrival_delay)

def predictDepartureDelay(month, dayOfWeek, scheduledDeparture, distance, interval):
	minutes_in_day = 24*60
	scheduledDepartureMinutes = timeInMinutes(scheduledDeparture)
	sin_scheduledDepartureMinutes = np.sin(2 * np.pi * scheduledDepartureMinutes / minutes_in_day)
	cos_scheduledDepartureMinutes = np.cos(2 * np.pi * scheduledDepartureMinutes / minutes_in_day)
	
	sin_month = np.sin(2 * np.pi * (month - 1) / 11)
	cos_month = np.cos(2 * np.pi * (month - 1) / 11)
	
	X = [dayOfWeek, distance, interval, sin_scheduledDepartureMinutes, cos_scheduledDepartureMinutes, sin_month, cos_month]
	
	y = departure_delay_regressor.predict(sc_X_departure.transform([X]))
	y = sc_y_departure.inverse_transform(y)
	
	return y[0]