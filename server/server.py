'''
SERVER FOR DRAWTOGETHER
By Akhyar I. Kamili
November 2016

The asynchronous server 
is built upon msglib's listener class.
'''
import os
import sys
import msglib
import threading
import pickle

PROJECT_OPENED = False

class ClientChannel(msglib.channel):
    def logMessage(self, msg): # override standard log method
        '''
        Process messages from the client
        '''
        header = msg[:20].strip()
        if header in ('EVENT', 'STATE_UPDATE', 'RESP_UPDATE'):
            self.broadcast(msg)
        elif header == 'AUTH':
            self.authenticate(msg)
        elif header == 'RQ_UPDATE':
            self.requestUpdate(msg)

    def broadcast(self, msg):
        header = msg[:20].strip()
        if header == 'RESP_UPDATE':
            self.save(msg)
        for channel in self.owner.channels:
            channel.send(msg)

    def authenticate(self, msg):
        global PROJECT_OPENED

        with open('users.data', 'r') as filedata:
            users = pickle.load(filedata)
        content = pickle.loads(msg[20:]) # tuple of uname, pwd
        success = content[1] == users[content[0]]

        if success:
            # authentication successful
            self.send('SUCCESS'.ljust(20))
        else:
            self.send('FAIL'.ljust(20))

    def requestUpdate(self):
        if len(self.owner.channels) == 1:
            old = pickle.load('project.data')
            self.send('RQ_UPDATE'.ljust(20)+"NONE")
        else:
            self.owner.channels[0].send('BC_UPDATE'.ljust(20))

    def save(self, sav):
        pickle.dump(sav, 'project.data')



class CustomListener(msglib.listener):
    def createChannel(self, parameters): # override standard method
        soConn = parameters['socket']
        remoteAddr = parameters['remoteAddress']
        channel_id = parameters['channelID']
        otherSettings = parameters['otherSettings']
        aChannel = ClientChannel(soConn, remoteAddr, channel_id, otherSettings) # refer to MyChannel class instead of msglib.channel standard class
        return aChannel;

def main():
    # create listener
    PORT_NUMBER = 15112
    aListener = CustomListener(PORT_NUMBER, 'BL2')
    aListener.listen()

main()
