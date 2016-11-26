# custom channel sample

import os
import sys
import msglib
import threading
import pickle

class WatchChannel(msglib.channel):
    def logMessage(self, msg): # override standard method
        '''
        Process messages from the client
        '''
    def broadcast(self, msg):
        for channel in self.owner.channels:
            channel.send(msg)

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
