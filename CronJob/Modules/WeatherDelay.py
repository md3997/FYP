import pickle
import json
import csv
import datetime
import pytz
import re

pickle_in_weather_delay_classifier = open("Data/Pickles/weather_delay_classifier.pickle","rb")
weather_delay_classifier = pickle.load(pickle_in_weather_delay_classifier)

pickle_in_sc_X_weather = open("Data/Pickles/sc_X_weather.pickle","rb")
sc_X_weather = pickle.load(pickle_in_sc_X_weather)

with open('Data/zones.csv') as f:
    reader = csv.reader(f, skipinitialspace=True)
    timeZones = dict(reader)
    
timeZones = dict((k,v) for k,v in timeZones.items())

METAR = {'CLR': 0, 'FEW': 1, 'SCT': 2, 'BKN': 3, 'OVC': 4}

mapping = {}

with open('Data/mapping.json', 'r') as f:
    mapping = json.load(f)
	
with open('Data_Jan/Weather_WN_JAN_2015.json', 'r') as f:
    weather = json.load(f)

def makeCols(wx_phrase):
    conditions = re.split(' with | and | \/ ', wx_phrase)
    obj = {}
    
    for key in mapping.keys():
        obj[key] = 0

    for token in conditions:
        for key, value in mapping.items():
            if token in mapping[key].keys():
                obj[key] = mapping[key][token]
                continue

    return list(obj.values())

def findNearest(origin, epoch_point):
    
    epoch_point = epoch_point * 60
    
    lower_limit = epoch_point - 30 * 60
    upper_limit = epoch_point + 30 * 60
    
    tz = pytz.timezone(timeZones[origin])
    
    date_ll = datetime.datetime.fromtimestamp(lower_limit, tz)
    date_hl = datetime.datetime.fromtimestamp(upper_limit, tz)
    
    searchList = list()
    
    month_ll = str(date_ll.month)
    day_ll = str(date_ll.day)
    
    if month_ll in weather[origin]:
        if day_ll in weather[origin][month_ll]:
            searchList = searchList + weather[origin][str(month_ll)][str(day_ll)]

    if date_hl.strftime('%dd/%mm/%YYYY') != date_ll.strftime('%dd/%mm/%YYYY'):
        month_hl = str(date_hl.month)
        day_hl = str(date_hl.day)
        
        if month_hl in weather[origin]:
            if day_hl in weather[origin][month_hl]:
                searchList  = searchList + weather[origin][str(month_hl)][str(day_hl)]

    searchList = sorted(searchList, key  = lambda x: x['valid_time_gmt'])
    
    lower = upper = -1
    
    for i, obj in enumerate(searchList):
        if obj['valid_time_gmt'] >= epoch_point:
            upper = i
            break
        else:
            lower = i
    
    if lower == -1 and upper == -1:
        return None
    elif lower == -1:
        if searchList[upper]['valid_time_gmt'] - epoch_point <= 30 * 60:
            return searchList[upper]
        else:
            return None
    elif upper == -1:
        if epoch_point - searchList[lower]['valid_time_gmt'] <= 30 * 60:
            return searchList[upper]
        else:
            return None
    else:
        diffUpper = searchList[upper]['valid_time_gmt'] - epoch_point
        diffLower = epoch_point - searchList[lower]['valid_time_gmt']
        
        if diffUpper <= diffLower:
            select = upper
        else:
            select = lower
        
        if searchList[select]['valid_time_gmt'] - epoch_point <= 30 * 60:
            return searchList[select]
        else:
            return None

def PredictDeparture(obj):
    
    if None in obj.values():
        return -1
    
    addL = makeCols(obj['wx_phrase'])
    #X = [[obj['temp'], obj['dewPt'], obj['rh'], obj['pressure'], obj['wspd'], METAR[obj['clds']], obj['vis']] + addL]
    X = [[obj['wspd'], METAR[obj['clds']], obj['vis']] + addL]
    y_pred = weather_delay_classifier.predict(sc_X_weather.transform(X))
    return y_pred[0]

def predictWeatherDelay(origin, scheduled_dep_epoch, regular_dep_delay):
    
    weather_delay = 0
    initial_epoch = ep = scheduled_dep_epoch + regular_dep_delay
    
    while(True):
        closestPoint = findNearest(origin, ep)
        
        if closestPoint == None:
            return (0, -1)
        
        res = PredictDeparture(closestPoint)
        
        if res == -1:
            return (0, -1)
        
        if res == 1:
            return (ep - initial_epoch, findNearest(origin, initial_epoch)['valid_time_gmt'])
        else:
            ep = ep + 20
