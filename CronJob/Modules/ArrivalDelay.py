import numpy as np
import pickle

pickle_in_arrival_delay_regressor = open("Data/Pickles/arrival_delay_regressor.pickle","rb")
arrival_delay_regressor = pickle.load(pickle_in_arrival_delay_regressor)

pickle_in_sc_X_arrival = open("Data/Pickles/sc_X_arrival.pickle","rb")
sc_X_arrival = pickle.load(pickle_in_sc_X_arrival)

pickle_in_sc_y_arrival = open("Data/Pickles/sc_y_arrival.pickle","rb")
sc_y_arrival = pickle.load(pickle_in_sc_y_arrival)

def timeInMinutes(x):
	x = str(x).zfill(4)
	h = int(x[:2])
	m = int(x[2:])
	
	return h * 60 + m

def predictArrivalDelay(scheduledTime, scheduledArrival, departureDelay):
	minutes_in_day = 24*60
	scheduledArrivalMinutes = timeInMinutes(scheduledArrival) + departureDelay
	
	if scheduledArrivalMinutes > 1439:
		scheduledArrivalMinutes = scheduledArrivalMinutes - 1440
	
	sin_scheduledArrivalMinutes = np.sin(2*np.pi*scheduledArrivalMinutes/minutes_in_day)
	cos_scheduledArrivalMinutes = np.cos(2*np.pi*scheduledArrivalMinutes/minutes_in_day)
	
	X = [scheduledTime, departureDelay, sin_scheduledArrivalMinutes, cos_scheduledArrivalMinutes]
	
	y = arrival_delay_regressor.predict(sc_X_arrival.transform([X]))
	y = sc_y_arrival.inverse_transform(y)
	
	return (y[0] - scheduledTime + departureDelay)