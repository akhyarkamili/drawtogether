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

    def broadcast(self, msg):
        for channel in self.owner.channels:
            channel.send(msg)
    def authenticate(self, msg):
        with open('users.data', 'r') as filedata:
            users = pickle.loads(filedata)
        content = pickle.loads(msg[20:])
        source = content['source']

        success = content['body']['password'] == users[source]['password']

        if success:
            # authentication successful
            self.send('SUCCESS'.ljust(20))
            if not PROJECT_OPENED:
                PROJECT_OPENED = True
            else:
                # project is already open
                existing = self.owner.channels[0]
                # request for latest version broadcast
                self.requestUpdate(existing)
        else:
            self.send('FAIL'.ljust(20))

    def requestUpdate(self, ch):
        ch.send('RQ_UPDATE'.ljust(20))

class CustomListener(msglib.listener):
    def createChannel(self, parameters): # override standard method
        soConn = parameters['socket']
        remoteAddr = parameters['remoteAddress']
        channel_id = parameters['channelID']
        otherSettings = parameters['otherSettings']
        aChannel = MyChannel(soConn, remoteAddr, channel_id, otherSettings) # refer to MyChannel class instead of msglib.channel standard class
        return aChannel;

def main():
    # create listener
    PORT_NUMBER = 15112
    aListener = CustomListener(PORT_NUMBER, 'BL2')
    aListener.listen()

main()
