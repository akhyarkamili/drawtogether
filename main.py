import pygame
import math
from uuid import uuid1 as ID_GEN
import socket as so

IPADDRESS = '127.0.0.1'
PORTNUMBER = 15112

class DrawingApp():
	def __init__(self):
		self.socket = self.StartConnection()
		self.state = 0
		username, password = self.getLogin()
		self.uname = username

		while not self.authenticate (socket, username, password):
			username, password = self.getLogin(True)

	def StartConnection (self):
	    connection = so.socket(so.AF_INET, so.SOCK_STREAM)
	    connection.connect((IPADDRESS, PORTNUMBER))

	    return connection

	def getLogin(failed=False):
	    wnd = Tkinter.Tk()
	    wnd.geometry("250x200")
	    wnd.title("Welcome to DrawTogether! Login")
	    if failed:
	        wnd.title("Wrong username/password")


	    # control variables
	    uname = Tkinter.StringVar()
	    pwd = Tkinter.StringVar()

	    # graphical elements
	    ulabel = Tkinter.Label(wnd, text="username")
	    plabel = Tkinter.Label(wnd, text="password")
	    uentry = Tkinter.Entry(wnd, textvariable=uname)
	    pentry = Tkinter.Entry(wnd, show='*', textvariable=pwd)
	    sbutton = Tkinter.Button(wnd, text="Login", command=wnd.destroy)

	    # pack the elements
	    ulabel.pack()
	    uentry.pack()
	    plabel.pack()
	    pentry.pack()
	    sbutton.pack()	

	    # bind pull event
	    mw.after(5000, callback=self.update)

	    wnd.mainloop()

	    return uname.get(), pwd.get()

	def authenticate(self, socket, uname, pwd):
		pass


	def startApp(self, logindetails):
		pass