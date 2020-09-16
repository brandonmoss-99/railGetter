from zeep import Client
from zeep import xsd
from zeep.plugins import HistoryPlugin
import sys, getopt


def getHelp():
	print("\nList of Parameters:\n\n"+
		"(s)tation to fetch train times from [3 letter station code]\n"+
		"(t)oken to use for connection [token]\n"+
		"max (n)umber of next trains to fetch [1-20], default=5\n"+
		"\nExample of usage:\n\n"+
		"rail.py -s PAD -t aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee -n 10\nGets next 10 trains from London Paddington")
	sys.exit(0)

def getNextTrains(stationToCheck, LDB_TOKEN, numberNextTrains):

	#current WSDL version. Available from https://lite.realtime.nationalrail.co.uk/OpenLDBWS/
	WSDL = 'https://lite.realtime.nationalrail.co.uk/OpenLDBWS/wsdl.aspx?ver=2017-10-01'

	history = HistoryPlugin()

	client = Client(wsdl=WSDL, plugins=[history])

	header = xsd.Element(
	    '{http://thalesgroup.com/RTTI/2013-11-28/Token/types}AccessToken',
	    xsd.ComplexType([
	        xsd.Element(
	            '{http://thalesgroup.com/RTTI/2013-11-28/Token/types}TokenValue',
	            xsd.String()),
	    ])
	)
	header_value = header(TokenValue=LDB_TOKEN)

	try:
		res = client.service.GetDepBoardWithDetails(numRows=numberNextTrains, crs=stationToCheck, _soapheaders=[header_value])
	except:
		print("Error fetching train times! Check your token is correct!")
		sys.exit(1)

	print("Next " + str(numberNextTrains) + " trains at " + res.locationName + "\nLast Updated:", res.generatedAt)
	print("===============================================================================")


	try:
		services = res.trainServices.service

		i = 0
		while i < len(services):
			callingPoints = services[i].subsequentCallingPoints.callingPointList
			print("\n" + services[i].std, "to", services[i].destination.location[0].locationName, "     ")
			if isinstance(services[i].platform, str):
				print("Plat " + services[i].platform, end=" ")
			else:
				print("Plat -", end=" ")
			if services[i].etd != "On time":
				print("Exp:", end=" ")
			print(services[i].etd)

			if services[i].etd == "Cancelled":
				print("This was a", services[i].operator, "service.\n")
			else:
				print("This is a", services[i].operator, "service.")
				print("Calling at:", end = " ")
				x = 0
				if len(callingPoints[0].callingPoint) > 1: #if more than 1 station
					while x < len(callingPoints[0].callingPoint)-1:
						print(callingPoints[0].callingPoint[x].locationName + ", ", end="")
						x = x + 1
				print(callingPoints[0].callingPoint[-1].locationName + ".\n")

			i += 1
	except AttributeError:
		print("There are no trains running at this station!")


LDB_TOKEN = None #National Rail OpenLDBWS token
stationToCheck = None #which station to check
numberNextTrains = 5 #fetch 5 next trains by default

argv = sys.argv[1:]

#try getting supported parameters and args from command line
try:
	opts, args = getopt.getopt(argv, "s:t:n:", ["station=", "token=", "next=", "help"])
except:
	print("Error parsing options")
	getHelp()

#assign variables based on command line parameters and args
for opt, arg in opts:
	if opt in ['-s', '--station']:
		try:
			stationToCheck = str(arg).upper()
		except:
			print("Error parsing station name!")
			getHelp()

	if opt in ['-t', '--token']:
		LDB_TOKEN = arg
	if opt in ['-n', '--next']:
		try:
			numberNextTrains = int(arg)
		except:
			print("Error converting number of next trains to an integer!")
	if opt in ['--help']:
		getHelp()


#make sure the number of trains to fetch isn't abusing any OpenLDBWS limits
if numberNextTrains < 1:
	numberNextTrains = 1
elif numberNextTrains > 20:
	numberNextTrains = 20

if stationToCheck is not None and LDB_TOKEN is not None:
	getNextTrains(stationToCheck, LDB_TOKEN, numberNextTrains)
elif LDB_TOKEN is None:
    print("Token not given!")
else:
	print("Station code not given!")
