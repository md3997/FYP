import matplotlib.pyplot as plt
import pandas as pd
import re
import sys
from datetime import datetime
import os.path

try:
	c = int(input("1 --> Departure Delay Error Calcutaion\n2 --> Arrival Delay Error Calcutaion\nEnter Choice: "))
	if c not in [1, 2]:
		print("Invalid Choice!!")
		sys.exit(0)
except:
	print("Invalid Choice!!")
	sys.exit(0)

d = input("Enter Date(DD/MM/YYYY): ")

if not re.match("^\d{2}/\d{2}/\d{4}$", d):
	print("Invalid Date Format!!")
	sys.exit(0)

dd, mm, yyyy = map(int, d.split("/"))

try:
	d = datetime(yyyy, mm, dd)
except:
	print("Wrong Date!!")
	sys.exit(0)

if c == 1:
	filePath = "Departure/" + d.strftime("%d_%m_%Y") + ".csv"
else:
	filePath = "Arrival/" + d.strftime("%d_%m_%Y") + ".csv"

if not os.path.exists(filePath):
	print("Log does NOT exist for specified date!!")
	sys.exit(0)

data = pd.read_csv(filePath)

def plotGraph():
	flightId=data['FlightIdentifier']
	predicted=data['Predicted']
	actual=data['Actual']
	error = data['Error']
	plt.plot(flightId,actual,color='orange',label='Actual', linewidth = 0.5)
	plt.plot(flightId,predicted,color='green',label='Predicted', linewidth = 0.5)
	plt.plot(flightId,error,color='black',label='Error', linewidth = 0.7)
	
	if c == 1:
		plt.title('Departure Delay Plot')
		plt.ylabel('Departure Delay (mins)')
	else:
		plt.title('Arrival Delay Plot')
		plt.ylabel('Arrival Delay (mins)')

	plt.xlabel('Flight Identifier')
	
	#plt.xticks(rotation='vertical',fontsize=2)

	plt.xticks([])
	
	plt.legend()
	plt.show()

def findAbsError(row):
	return pd.Series([abs(row['Actual'] - row['Predicted'])])

def findError(row):
	return pd.Series([row['Actual'] - row['Predicted']])
	
data[['AbsoluteError']] = data.apply(findAbsError, axis = 1)
data[['Error']] = data.apply(findError, axis = 1)

tArr = data['AbsoluteError'].values

MAE = sum(tArr) / len(tArr)

print("Mean Absolute Error: {0:.2f}".format(MAE))
plotGraph()