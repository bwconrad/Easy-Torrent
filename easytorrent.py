import libtorrent as lt
import time
import sys
import os
import string
import tkinter as tk
from tkinter import filedialog
import _thread






# Select torent file to download
def chooseTorrent():
	#Create Tk window
	root = tk.Tk()
	root.withdraw()
		
	#Choose torrent file
	path = filedialog.askopenfilename(title = "Select Torrent File", filetypes = (("torrent files", "*.torrent"),\
	("all files", "*.*")), initialdir = ".")
		
	#Check if file is .torrent 
	while not path.endswith('.torrent'): 
		print("Please Select a .torrent File")
		path = chooseTorrent(save_path)

	root.destroy()
	return path

# Create a new session
def createSession():
	session = lt.session()
	session.listen_on(6881,6891)
	return session

# Add torrent file to download
def addTorrent(path, session, s_path):
	e = lt.bdecode(open(path, 'rb').read())
	info = lt.torrent_info(e)

	par = { 'save_path': s_path, \
		'storage_mode': lt.storage_mode_t.storage_mode_sparse, \
		'ti': info }
	h = session.add_torrent(par)
	return h

# Add magnet link to download
def addMagnet(link, session, s_path):
	par = { 'save_path': s_path, \
		'storage_mode': lt.storage_mode_t.storage_mode_sparse}
	h = lt.add_magnet_uri(session, link, par)

	os.system("clear")
	timeout = time.time() + 60 # 60s timer
	while(not h.has_metadata()):
		if(time.time() > timeout):
			print("Metadata download has timed out")
			print("Possible bad magnet link URI used")
			sys.exit()
		print("Downloading Metadata", end="\r")
		time.sleep(1)

	return h

# Start downloading file
def startDownTorrent(tor):
	os.system('clear') # Clear the screen
	s = tor.status() # Get DL information

	list = []
	_thread.start_new_thread(input_thread, (list,)) # Start a listening thread for pause input

	print('~~~Press ENTER to Pause or Quit Download~~~')
	length = 0 # White space printing variable
	# While downloading update the status and display
	while( not s.is_seeding):
		if(list):
			list = paused(tor,list)	# If resuming clear list
			print('~~~Press ENTER to Pause or Quit Download~~~')
			_thread.start_new_thread(input_thread, (list,)) # Start another listening thread

		s = tor.status()
		state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']

		down, dl_size = rateConvert(byte_rate = s.download_rate)
		up, up_size = rateConvert(byte_rate = s.upload_rate)

		p = '%s: %.2f%% complete (down: %.1f %s up: %.1f %s peers: %d)' %(state_str[s.state].upper(), s.progress * 100, down, \
			dl_size, up, up_size, s.num_peers)

		space = max(0, length-len(p)) * ' ' #White space to print so no leftover characters when proceding line is shorter than privious
		print(p + space, end="\r") # Print dynamic status line
		length = len(p)		
		time.sleep(.2)

	# Ask if user wants to seed torrent after download
	tor.pause() 
	print("\n\nDownload Complete")
	print("Press ENTER to continue")
	choice = input("Would you like to continue seeding? (y/n): ")
	if(choice in ['yes', 'y', 'Yes', 'Y']):
		seed(tor)
	return

# Convert byte rate into kB and MB
def rateConvert(byte_rate):
	# Display in kB
	if( byte_rate<1000000.0): 
		rate = byte_rate / 1000 
		size = "kB/s"

	# Display in MB
	else: 
		rate = byte_rate / 1000000 
		size = "MB/s"

	return rate, size

# Not given an input on startup
def noInputStart():
	print("What Would You Like to Add?")
	choice = input("Torrent File (1) or Magnet Link (2)?: ")
	while(choice != '1'):
		while(choice != '2'):
			print("Please Make a Correct Input")
			choice = input("Torrent File (1) or Magnet Link (2)?: ")
		break

	# Adding a Torrent File
	if(choice == '1'): 
		t_path = chooseTorrent()
		save_path = destination() 
		session = createSession()
		h = addTorrent(t_path, session, save_path)
		d = startDownTorrent(h)
		return

	# Adding a Magnet Link
	elif(choice == '2'):
		link = input("Magnet Link URI: ")
		save_path = destination() 
		session = createSession()
		h = addMagnet(link, session, save_path)
		d = startDownTorrent(h)
		return

# Given an input on startup
def inputStart(file):
	choice = input("Do you want to use " + file + " ? (y/n): ")
	if(choice in ['yes', 'y', 'Yes', 'Y']):
		t_path = file
		save_path = destination() 
		session = createSession()
		h = addTorrent(t_path, session, save_path)
		d = startDownTorrent(h)
		
	else:
		noInputStart()
	
	return

# Pause input thread during download
def input_thread(list):
	input()
	list.append(1)

# While download is paused
def paused(tor,list):
	tor.pause()
	print("\nPaused")
	choice = input("Continue (1) or Quit (2): ")

	while(not(choice in ['1','2'])):
		print("Please make a correct input")
		choice = input("Continue (1) or Quit (2): ")

	# Continue download
	if(choice == '1'):
		list = [] # Clear list
	
	# Exiting the program
	elif(choice == '2'):
		sys.exit()
		
	os.system('clear') # Clear the screen
	tor.resume()
	return list

def seed(tor):
	os.system('clear') # Clear the screen	
	tor.resume()
	s = tor.status() # Get DL information

	list = []
	_thread.start_new_thread(input_thread, (list,)) # Start a listening thread for pause input
	length = 0
	print('~~~Press ENTER to Pause or Quit Seeding~~~')
	# While seeding update the status and display
	while(1):
		if(list):
			list = paused(tor,list)	# If resuming clear list
			print('~~~Press ENTER to Pause or Quit Seeding~~~')
			_thread.start_new_thread(input_thread, (list,)) # Start another listening thread

		s = tor.status()
		state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']

		down, dl_size = rateConvert(byte_rate = s.download_rate)
		up, up_size = rateConvert(byte_rate = s.upload_rate)

		p = '%s: %.2f%% complete (down: %.1f %s up: %.1f %s peers: %d)' %(state_str[s.state].upper(), s.progress * 100, down, \
			dl_size, up, up_size, s.num_peers)

		space = max(0, length-len(p)) * ' ' #White space to print so no leftover characters when proceding line is shorter than privious
		print(p + space, end="\r") # Print dynamic status line
		length = len(p)
				
		time.sleep(.2)

def destination():
	print("\nWould you like to specify the download location?")
	choice = input("Specify (1) Default Directory (2): ")
	if(choice == '1'):
		#Create Tk window
		root = tk.Tk()
		root.withdraw()
			
		#Choose destination directory
		save_path = filedialog.askdirectory(title = "Select Torrent File", initialdir = "/home")

		root.destroy()
	
	else:
		save_path = '.'

	return save_path

def main():
	os.system('clear')
	# Kill if too many inputs were given
	if(len(sys.argv) > 2):
		print("Too Many Inputs Given")
		return

	# If no input is given ask user
	elif(len(sys.argv) == 1):
		noInputStart()
		
	# If input given use it as the path
	elif(len(sys.argv) == 2):
		inputStart(sys.argv[1])
		
	return

if __name__ == '__main__':
	main()











	





