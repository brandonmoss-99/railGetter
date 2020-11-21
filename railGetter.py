from zeep import Client
from zeep import xsd
from zeep.plugins import HistoryPlugin
from multiprocessing import Pipe, Process
import sys, getopt, time, textwrap, re

# Made railGetter a class to simplify multhreading, 
# program still runs as normal
class railGetter:

	def __init__(self, token, station, pipe, trains_n = 5, delay=20):
		self.res = None
		self.token = token
		self.station = station
		self.pipe = pipe
		self.train_n = trains_n
		self.delay = delay

	def getNextTrains(self, stationToCheck, LDB_TOKEN, numberNextTrains):

		# current WSDL version. Available from 
		# https://lite.realtime.nationalrail.co.uk/OpenLDBWS/
		WSDL = ('https://lite.realtime.nationalrail.co.uk/'
			'OpenLDBWS/wsdl.aspx?ver=2017-10-01')

		history = HistoryPlugin()

		client = Client(wsdl=WSDL, plugins=[history])

		header = xsd.Element(
			'{http://thalesgroup.com/RTTI/2013-11-28/Token/types}AccessToken',
			xsd.ComplexType([
				xsd.Element(
					'{http://thalesgroup.com/'
					'RTTI/2013-11-28/Token/types}TokenValue',
					xsd.String()),
			])
		)
		header_value = header(TokenValue=LDB_TOKEN)

		# attempt connection to the API, return the API response on success,
		# otherwise return an error message and exit program with error status
		try:
			res = (client.service.GetDepBoardWithDetails(
				numRows=numberNextTrains,
				crs=stationToCheck, _soapheaders=[header_value]))
		except:
			print("Error fetching train times! Check your token is correct!")
			sys.exit(1)

		return res

	# This is the thread that we want to run, it gets the updates from
	# national rail and sends them to the main thread
	def run(self):
		while True:
			self.res = (self.getNextTrains(self.station,
				self.token, self.train_n))
			self.pipe.send(self.res)
			time.sleep(self.delay)


def printScreen(res, wrapwidth):

	# try to output all of the train information, or output a message
	# if there is an attribute warning (no info/no trains running)
	if res is not None:
		try:
			# get the list of train services
			services = res.trainServices.service

			# for each service, get the calling points list and print
			# the platform, time and status (on-time/delayed), train
			# operator and the stations along the service
			for i in range(0, len(services)):
				callingPoints = (services[i].subsequentCallingPoints.
					callingPointList)
				print("\n" + services[i].std, "to",
					services[i].destination.location[0].locationName, end=" ")
				if isinstance(services[i].destination.location[0].via, str):
					print(services[i].destination.location[0].via, end=" ")

				# if the platform number is a string, print it, otherwise just
				# print '-' to represent N/A, unknown or other
				if isinstance(services[i].platform, str):
					print("\nPlat " + services[i].platform, end=" ")
				else:
					print("\nPlat -", end=" ")
				if services[i].etd != "On time":
					print("Exp:", end=" ")
				print(services[i].etd)

				# check if service is cancelled and output cancelled if so,
				# otherwise print the train operator and the service stations
				if services[i].etd == "Cancelled":
					print("This was a", services[i].operator, "service.\n")
				else:
					print("This is a", services[i].operator, "service.")
					toPrint = "Calling at: "
					x = 0
					# if more than 1 station, append each but the last to
					# a string to be wrapped at the end
					if len(callingPoints[0].callingPoint) > 1:
						for x in range(0,
							len(callingPoints[0].callingPoint)-1):
								toPrint += (callingPoints[0].callingPoint[x].
									locationName) + ", "
					# append the last/only service station to the string
					toPrint += (callingPoints[0].callingPoint[-1].
						locationName) + ".\n"

					# wrap the string to a max number of characters. Returns a
					# list of strings representing each line's output to print
					wrappedText = textwrap.wrap(toPrint, wrapwidth)
					for line in wrappedText:
						print(line)

					# get the number of coaches for each train service, 
					# if available
					if isinstance(
						services[i].length,str) and services[i].length > 0:
						print("This train has", services[i].length,
						"coaches.\n")
		except AttributeError:
			print("There are no trains running at this station!")


def printMessages(res, wrapwidth):
	if res is not None:
		try:
			# get the list of important departure board messages
			messages = res.nrccMessages.message
			print("\n")

			for message in messages:
				# get the message text
				messageText = message._value_1

				# replace any HTML p tags with newlines, as per OpenLDBWS's
				# guidelines
				messageText = messageText.replace("<P>", "\n")
				messageText = messageText.replace("</P>", "\n")

				# use regex to strip any opening HTML a tags with blanks,
				# as per OpenLDBWS's guidelines
				messageText = re.sub(
					r'<A\s+(?:[^>]*?\s+)?href=(["\'])(.*?)\1>',
					"", messageText)
				messageText = messageText.replace("</A>", "")

				msgPadding = 10
				wrappedText = textwrap.wrap(messageText, wrapwidth-msgPadding)
				for line in wrappedText:
					print(" "*msgPadding + line.lstrip(' '))
				print("\n")
		except:
			print("Error printing station messages!")


def checkIfMessages(res):
	# check if there are station messages to display, returns True or False
	if res is not None:
		try:
			return True if len(res.nrccMessages.message) > 0 else False
		except:
			return False


def resetScreen(t, wrapwidth, res, colon):
	stationNameLength = len(res.locationName)

	# get character spaces left to pad with '=' by removing length of the
	# station name/time and the other characters also displayed on the line
	freeSpaceStation = wrapwidth - stationNameLength - 15
	freeSpaceTime = wrapwidth - 10

	print("\u001b[H", end="") # move cursor to top left (1,1)
	print("\u001b[0J", end="") # clear screen after cursor (whole screen)

	# try to print so the title and time are centered, but if not possible
	# then print the extra character on the right side of the line
	if freeSpaceStation % 2 == 0:
		print("="*int(freeSpaceStation/2), "RAILGETTER -",
			res.locationName.upper(),"="*int(freeSpaceStation/2))
	else:
		print("="*int((freeSpaceStation-1)/2), "RAILGETTER -",
			res.locationName.upper(),"="*int((freeSpaceStation+1)/2))
	if freeSpaceTime % 2 == 0:
		if colon:
			print("="*int(freeSpaceTime/2), time.strftime("%H:%M:%S", t),
			"="*int(freeSpaceTime/2))
		else:
			print("="*int(freeSpaceTime/2), time.strftime("%H:%M %S", t),
			"="*int(freeSpaceTime/2))
	else:
		if colon:
			print("="*int((freeSpaceTime-1)/2), time.strftime("%H:%M:%S", t),
			"="*int((freeSpaceTime+1)/2))
		else:
			print("="*int((freeSpaceTime-1)/2), time.strftime("%H:%M %S", t),
			"="*int((freeSpaceTime+1)/2))


def getHelp():
		# print help information, then quit
		print("\nList of options:\n\n"+
			"(s)tation to fetch train times from [3 letter station code]\n"+
			"(t)oken to use for connection [token]\n"+
			"max (n)umber of next trains to fetch [1-10], default=5\n"+
			"\nExample of usage:\n\n"+
			"rail.py -s PAD -t aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee -n 10\n"+
			"Gets next 10 trains from London Paddington")
		sys.exit(0)


if __name__ == '__main__':
	LDB_TOKEN = None # National Rail OpenLDBWS token
	stationToCheck = None # which station to check
	numberNextTrains = 5 # fetch 5 next trains by default
	wrapwidth = 80 # how many characters wide to print text before wrapping
	timesDisplayDuration = 20 # duration to display train times (seconds)
	msgDisplayDuration = 10 # duration to display messages (seconds)
	updateDelay = 20 # how long to keep data before re-requesting (seconds)
	argv = sys.argv[1:]

	# try getting supported parameters and args from command line
	try:
		opts, args = getopt.getopt(argv, "s:t:n:",
			["station=", "token=", "next=", "help"])
	except:
		print("Error parsing options")
		getHelp()

	# assign variables based on command line parameters and args
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

	# make sure the no. trains to fetch isn't abusing any OpenLDBWS limits
	if numberNextTrains < 1:
		numberNextTrains = 1
	elif numberNextTrains > 10:
		numberNextTrains = 10

	if stationToCheck is not None and LDB_TOKEN is not None:
		# create a pipe, to send stuff between threads
		pipe1, pipe2 = Pipe()
		# create an instance of the class
		R_getter = railGetter(LDB_TOKEN, stationToCheck, pipe2, 
			trains_n = numberNextTrains, delay = updateDelay)
		# Create a process with target being the function we want to run
		# in the thread
		p = Process(target=R_getter.run, args=())
		p.start() # start the thread

		# wait x seconds when the program is started until the first info
		# is displayed, to make sure some data has been recieved before trying
		# to process and display the data response. 
		safeWaitTime = 5
		print("Waiting", safeWaitTime, 
			"seconds for an initial data response...")
		time.sleep(safeWaitTime)

		t = time.localtime()
		colon = True # should be colon be shown in the time display

		# loop until program is manually quit. Every x seconds, fetch the next
		# train times from API. For x seconds, print the last requested API
		# data along with the current time, updating every second, until x
		# seconds has passed & another API request is made to update the info
		
		while True:
			for i in range(0,timesDisplayDuration):
				t = time.localtime()

				# Check if there is something to receive from the pipe
				if pipe1.poll():
					res = pipe1.recv() # Get the results from the pipe

				# alternate the colon display each refresh
				if colon:
					resetScreen(t, wrapwidth, res, colon)
					colon = False
				else:
					resetScreen(t, wrapwidth, res, colon)
					colon = True

				printScreen(res, wrapwidth)
				time.sleep(1)

			if checkIfMessages(res):
				for i in range(0, msgDisplayDuration):
					t = time.localtime()

					# Check if there is something to receive from the pipe
					if pipe1.poll():
						res = pipe1.recv() # Get the results from the pipe

					# alternate the colon display each refresh
					if colon:
						resetScreen(t, wrapwidth, res, colon)
						colon = False
					else:
						resetScreen(t, wrapwidth, res, colon)
						colon = True
					printMessages(res, wrapwidth)
					time.sleep(1)
				
	elif LDB_TOKEN is None:
		print("Token not given!")
	else:
		print("Station code not given!")
