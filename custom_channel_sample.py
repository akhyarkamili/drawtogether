# custom channel sample

import os
import sys
import msglib
import threading

class MyChannel(msglib.channel):
    def logMessage(self, msg): # override standard method
        print 'CUSTOM msghandler: ' + msg
        print 'Channels available: %d' % len(self.owner.channels)
        pass # note: use self.owner to access listener object
        pass # note: use self.owner.channels to access all channels
        pass # because of multi-thread environment, make sure that access to channels array are guarded against race condition !
        pass # use threading.Lock objects for this purpose

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

#main()
