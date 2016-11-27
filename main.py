import pickle
import socket as so
import msglib as mc
import window
import Tkinter

IPADDRESS = '127.0.0.1'
PORTNUMBER = 15112

app = None

def authMessageHandler(self, msg):
    print 'rcvd:', msg
    if app:
        app.check(msg)

class DrawingApp(object):
    def __init__(self):
        self.conn = self.startConnection()
        self.username, password = self.getLogin()
        self.login = False
        self.authenticate(self.username, password)

    def startConnection(self):
        # conn = so.socket(so.AF_INET, so.SOCK_STREAM)
        # conn.connect((IPADDRESS, PORTNUMBER))

        conn = mc.connector('localhost', 15112, 'BL2')
        mc.channel.logMessage = authMessageHandler
        conn.connect()
        return conn

    def getLogin(self, failed=False):
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

        wnd.mainloop()

        return uname.get(), pwd.get()

    def authenticate(self, uname, pwd):
        user = (uname, pwd)
        d = pickle.dumps(user)
        msg = 'AUTH'.ljust(20) + d
        self.conn.send(msg)


    def check(self, resp):
        if resp[:20].strip() == 'SUCCESS':
            self.conn.disconnect()
            self.login = True
            self.startApp()
        else:
            quit()

    def startApp(self):        
        userdict = {}
        userdict['owner'] = self.username
        userdict['users'] = [{'id':'saquibr'}, {'id':'akhyarkamili'}, {'id':'kemalo'}, {'id':'khaledh'}]
        self.canvas = window.CanvasWindow(userdict)


if __name__ == '__main__':
    app = DrawingApp()


