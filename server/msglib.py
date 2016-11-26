# msglib.py
# a module to be loaded to python IDE or interpreter
# to perform messaging functions
# created by Ismir Kamili 2016
import os
import sys
import socket as socklib
import collections
import threading
import time
# from OpenSSL import SSL

if sys.platform in ('darwin', 'linux', 'linux2'):
    LOG_FOLDER = '~/msglogs'.replace('~/', os.environ['HOME'] + '/')    # where to store logs
elif sys.platform == 'win32':
    LOG_FOLDER = 'c:\\logs\\atmlog'
else:
    raise Exception, 'Undefined platform value %s' % sys.platform
if not os.access(LOG_FOLDER, os.F_OK):
    os.makedirs(LOG_FOLDER)

SOCK_TIMEOUT = 1            # periodic check for socket data
CHANNEL_COUNTER = 1

def getNextChannelCounter():
    global CHANNEL_COUNTER
    CHANNEL_COUNTER += 1
    return CHANNEL_COUNTER

def verify_cb(conn, cert, errnum, depth, ok):
    # This obviously has to be updated
    o = cert.get_subject()
    print 'Certificate depth %d from: %s' % (depth, o.commonName)
    #print cert.get_issuer()
    return ok

class connector:
    def __init__(self, host, port, adapterSetting = None):
        # valid values for adapterSetting:
        #   BLn: binary length with n bytes of exclusive length indicator. if n is not specified assumed n = 2
        #   BExxyy (not supported yet): begin-end, where xx and yy are hex digits representing ASCII character for header and trailer, respectively
        #   LF: line-feed. Every line feed is considered a new message. CR character will be automatically stripped from end of line
        self.adapterSetting = adapterSetting
        self.host = host
        self.port = port
        self.socket = None
        self.channel = None
        self.logEncoding = None
        self.isSSL = False
        self.sslContext = None
        self.sslRawSocket = None
    #-- def
    
    def connect(self):
        if self.channel != None:
            raise Exception, 'Already connected (channel active)'
        self.socket = socklib.socket(socklib.AF_INET, socklib.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.isSSL = False
        self.createAndRunChannel()
        pass
    #--

    def createAndRunChannel(self):
        channel_id = '%08x' % os.getpid()
        print 'Connected to %s. channel id = %s' % (self.host + ':' + str(self.port), channel_id)
        self.channel = channel(self.socket, self.host + ':' + str(self.port), channel_id, 
                               {
                                   'adapterSetting': self.adapterSetting, 
                                   'owner': self, 
                                   'sharedMessageLog': self,
                                   'logEncoding': self.logEncoding
                               }
                        )
        self.channel.runReader()

    def secureConnect(self, rootCAPEMFile = None, CAStorePath = None):
        #import rpdb2; rpdb2.start_embedded_debugger('000')
        ctx = SSL.Context(SSL.TLSv1_METHOD)
        ctx.set_verify(SSL.VERIFY_PEER|SSL.VERIFY_FAIL_IF_NO_PEER_CERT, verify_cb) 
        if rootCAPEMFile is None and CAStorePath is not None:
            ctx.load_verify_locations(None, CAStorePath)
        elif rootCAPEMFile is not None and CAStorePath is None:
            ctx.load_verify_locations(rootCAPEMFile)
        else:
            raise Exception, 'Either root CA PEM file or CA store path must be selected'
        self.isSSL = True
        self.sslContext = ctx
        self.sslRawSocket = socklib.socket(socklib.AF_INET, socklib.SOCK_STREAM)
        self.createAndRunChannel()
    
    def notifyChannelTermination(self, channel, isError):
        self.channel = None
        self.socket = None
    
    def __checkChannel(self):
        if self.channel is None:
            raise Exception, 'Channel not connected'
        
    def send(self, aMessage):
        self.__checkChannel()
        self.channel.send(aMessage)
    
    def disconnect(self):
        self.__checkChannel()
        self.channel.disconnect()
        pass
        

    def writeLog(self, sLog):
        print sLog
    
class listener:
    def __init__(self, port, adapterSetting = None):
        self.adapterSetting = adapterSetting
        self.port = port
        self.socket = None
        self.listenThread = None
        self.lockChannels = threading.Lock()
        self.lockLog = threading.Lock()
        self.channels = [] # members are channels from incoming connections
        self.logEncoding = None
        self.sharedLogFileName = LOG_FOLDER + os.sep + 'msg-listen-%d.log' % port
        if os.access(self.sharedLogFileName, os.F_OK):
            self.sharedLogFile = file(self.sharedLogFileName, 'a+b')
        else:
            self.sharedLogFile = file(self.sharedLogFileName, 'wb')
    
    def __del__(self):
        self.sharedLogFile.close()
        
    def listen(self):
        if self.listenThread is not None:
            raise Exception, 'Still in listening state. Pls call listener.stopListen() first'
        
        self.socket = socklib.socket(socklib.AF_INET, socklib.SOCK_STREAM)
        self.socket.bind(('', self.port))
        self.socket.listen(10)
        try:
            self.listenThread = listenThread(self)
            self.listenThread.start()
            print 'Listening @port %d started. Message pool log file is %s' % (self.port, self.sharedLogFileName)
        except:
            self.listenThread = None
            raise
        #-- except
        
        pass
    #-- def listen
    
    def killChannels(self):
        self.lockChannels.acquire()
        try:
            for channel in self.channels:
                channelID = channel.channelID
                try:
                    channel.disconnect()
                except:
                    excStr = str(sys.exc_info()[0]) + '.' + str(sys.exc_info()[1])
                    print 'Closing channel %s: %s' % (channelID, excStr)
            self.channels = {}
        finally:
            self.lockChannels.release()
    #-- def 
        
    def notifyListenThreadTermination(self, isError): # interface function required by class listenThread
        self.listenThread = None
        self.killChannels()
    
    def notifyChannelTermination(self, channel, isError):
        channels = self.channels
        self.lockChannels.acquire()
        try:
            if channel in channels:
                channels.remove(channel)
        finally:
            self.lockChannels.release()
        pass 
    
    def writeLog(self, sLog): # interface function required by class channel
        self.lockLog.acquire()
        try:
            self.sharedLogFile.write('%s|%s\n' % (time.asctime(), sLog))
            self.sharedLogFile.flush()
        finally:
            self.lockLog.release()
        pass
    
    def sendFirst(self, msg):
        self.lockChannels.acquire()
        try:
            if len(self.channels) == 0:
                raise Exception, 'No channel is connected'
            self.channel[0].send(msg)
        finally:
            self.lockChannels.release()
        pass
        
    def stopListen(self, maxTimeOut = 10):
        if self.listenThread is None:
            return
        
        self.killChannels()
        listenThread = self.listenThread
        listenThread.requestedTermination = True
        
        self.listenThread = None
        
        time.sleep(1)
        self.socket.close()
        
        t0 = time.time(); t1 = time.time()
        while listenThread.isAlive() and (t1 - t0) < maxTimeOut:
            print 'Wait listener thread termination'
            time.sleep(1)
            t1 = time.time()
        #-- while
        
        if listenThread.isAlive():
            print 'Timeout waiting listener thread'
        else:
            print 'Listener thread terminated successfully'
        pass
    
    def createChannel(self, parameters): # virtual method to be overriden for custom channel
        soConn = parameters['socket']
        remoteAddr = parameters['remoteAddress']
        channel_id = parameters['channelID']
        otherSettings = parameters['otherSettings']
        aChannel = channel(soConn, remoteAddr, channel_id, otherSettings)
        return aChannel;
    
    def notifyNewConnection(self, soConn, remoteAddr):
        channel_id = '%x-%d' % (os.getpid(), getNextChannelCounter())
        aChannel = self.createChannel({
            'socket': soConn,
            'remoteAddress': remoteAddr,
            'channelID': channel_id,
            'otherSettings': {
                   'owner': self,
                   'adapterSetting': self.adapterSetting, 
                   'sharedMessageLog': self,
                   'logEncoding': self.logEncoding
                }
        })
        aChannel.runReader()
        print 'New connection was accepted. Channel id = %s' % channel_id
        self.lockChannels.acquire()
        try:
            self.channels.append(aChannel)
        finally:
            self.lockChannels.release()
        pass
    #--
    
    def listChannels(self):
        print 'channels:'
        print '----------+--------------------+-----+----------+---------------+---------------+'
        print '   ID     |    ADDRESS         |PORT | ADAPTER  |LOG.ENCODING   |      CLASS    |'
        print '----------+--------------------+-----+----------+---------------+---------------+'
        for c in self.channels:
            print '%10s|%20s|%5d|%10s|%15s|%15s|' % (c.channelID[:10], c.remoteAddr[0][:20], c.remoteAddr[1], c.adapterSetting or '', (c.logEncoding or '')[:15], c.channelClassName)
        print '----------+--------------------+-----+----------+---------------+---------------+'
        print
        
        pass
    
    # method aliases (shortcuts)
    lc = listChannels # alias
    sendDefault = sendFirst
    sd = sendFirst # alias
    stop = stopListen # alias
    
    pass
#-- class
                             
class channel:
    def __init__(self, socket, remoteAddr, channel_id, otherSettings = {}):
        # keys for otherSettings:
        #   'adapterSetting', 'sharedMesssageLog', 'owner', 'logEncoding'
        
        adapterSetting = otherSettings.get('adapterSetting', None)
        # valid values for adapterSetting:
        #   BLn: binary length with n bytes of exclusive length indicator. if n is not specified assumed n = 2
        #   BExxyy (not supported yet): begin-end, where xx and yy are hex digits representing ASCII character for header and trailer, respectively
        #   LF: line-feed. Every line feed is considered a new message. CR character will be automatically stripped from end of line

        sharedMessageLog = otherSettings.get('sharedMessageLog', None)
        # standard intf functions for sharedMessageLog:
        #    def writeLog(s)
        
        self.owner = otherSettings.get('owner', None)
        # standard intf functions for owner:
        #    def notifyChannelTermination()
        
        self.logEncoding = otherSettings.get('logEncoding', None)
        
        self.channelClassName = 'standard'
        self.remoteAddr = remoteAddr
        self.channelID = channel_id
        self.sharedMessageLog = sharedMessageLog
        self.adapterSetting = adapterSetting if adapterSetting is not None else 'BL2'
        self.isSSL = False
        self.sslContext = None
        self.sslRawSocket = None
        adapterSetting = self.adapterSetting
        if adapterSetting[:2] == 'BL':
            nLen = int(adapterSetting[2:])
            self.adapter = asyncBLMsgReader(self, nLen)
        elif adapterSetting == 'LF':
            self.adapter = asyncLFMsgReader(self)
        elif adapterSetting == 'RAW':
            self.adapter = asyncRawMsgReader(self)
        else:
            raise Exception, 'Unknown adapter setting'
        if isinstance(self.owner, connector) and self.owner.isSSL:
            self.socket = None # socket must be created in thread during SSL_Connect() process
            self.isSSL = True
            self.sslContext = self.owner.sslContext
            self.sslRawSocket = self.owner.sslRawSocket
        else:
            self.socket = socket
            self.isSSL = False
        self.logFileName = LOG_FOLDER + os.sep + 'msg-%s.log' % channel_id
        self.rawLogFileName = LOG_FOLDER + os.sep + 'raw-%s.log' % channel_id
        
        self.log = file(self.logFileName, 'wb' if os.access(self.logFileName, os.F_OK) else 'a+b')
        self.raw = file(self.rawLogFileName, 'wb' if os.access(self.rawLogFileName, os.F_OK) else 'a+b')
        self.readThread = None
    #-- def
    
    def __del__(self):
        self.log.close()
        self.raw.close()
        
    def logMessage(self, msg):
        if self.logEncoding is not None:
            msg = msg.encode(self.logEncoding)
        sText = '%s - incoming message received @%s\n%s\n' % (time.asctime(), self.channelID, msg)
        if self.sharedMessageLog != None:
            self.sharedMessageLog.writeLog(sText)
        self.log.write(sText)
        self.log.flush()
        pass
    
    def logRawData(self, msg):
        self.raw.write(msg)
        self.raw.flush()
        pass
    
    def send(self, aMessage):
        self.adapter.sendData(aMessage)
    
    def disconnect(self):
        self.readThread.requestedTermination = True
        self.readThread = None
        try:
            self.socket.shutdown(socklib.SHUT_RDWR)
        except:
            pass
        
        try:
            self.socket.close()
        except:
            pass
        
        self.notifyTermination(False)
        pass
    
    def notifyTermination(self, isError):
        self.readThread = None
        print 'channel %s terminated. %s' % (self.channelID, 'status=normal' if not isError else 'status=error/disconnection')
        if self.owner != None:
            self.owner.notifyChannelTermination(self, isError)
    
    def runReader(self):
        if self.readThread is not None:
            self.stopReader()
            pass
        #-- if
        self.readThread = readThread(self)
        self.readThread.start()
        print 'channel %s started' % self.channelID
        pass
    
    def stopReader(self, bWait = True):
        try:
            self.socket.shutdown(socklib.SHUT_RDWR)
        except:
            pass
        
        try:
            self.socket.close()
        except:
            pass
        
        self.readThread.requestedTermination = True; time.sleep(1)
        
        readThread = self.readThread
        self.readThread = None
        if bWait:
            waitTry = 0
            while readThread.isAlive() and waitTry < 5:
                print 'Wait reader thread termination'
                time.sleep(1)
                waitTry += 1
            #-- while
            if readThread.isAlive():
                print 'Timeout waiting reader thread'
            else:
                print 'Reader thread terminated successfully'
            #--
            pass
        #-- if bWait
        pass
    #-- def stopReader

class readThread(threading.Thread):
    def __init__(self, channel):
        threading.Thread.__init__(self)
        self.channel = channel
        if not channel.isSSL:
            self.channel.socket.settimeout(SOCK_TIMEOUT)
            self.socket = self.channel.socket
        else:
            self.socket = None
        self.adapter = self.channel.adapter
        self.requestedTermination = False
    
    def run(self):
        threading.Thread.run(self)
        channel = self.channel
        if channel.isSSL:
            self.socket = SSL.Connection(channel.sslContext, channel.sslRawSocket)
            channel.socket = self.socket
            channel.owner.socket = self.socket
            self.socket.connect((channel.owner.host, channel.owner.port))

        while not self.requestedTermination:
            try:
                sData = self.socket.recv(1024)
                if sData is not None and len(sData) > 0:
                    self.channel.logRawData(sData)
                    self.adapter.feedData(sData)
                    if self.adapter.hasMessage():
                        msg = self.adapter.fetchMessage()
                        while msg is not None:
                            self.channel.logMessage(msg)
                            msg = self.adapter.fetchMessage()
                        #-- while
                        pass
                    #-- if hasMessage
                    pass
                elif sData == '': # network error / disconnected
                    raise Exception, 'Network read error'
                #-- if sData != None
            except:
                exc_type = sys.exc_info()[0]
                if exc_type != socklib.timeout:
                    self.channel.notifyTermination(True) # make sure that reference to this thread is removed
                    raise
                #--
                pass
            #-- except
            pass
        #-- while
        self.channel.notifyTermination(False) # make sure that reference to this thread is removed
        pass
    #-- def run()

class listenThread(threading.Thread):
    def __init__(self, listener):
        threading.Thread.__init__(self)
        self.listener = listener
        self.socket = listener.socket
        self.socket.settimeout(SOCK_TIMEOUT)
        self.requestedTermination = False
        
    def run(self):
        threading.Thread.run(self)
        while not self.requestedTermination:
            try:
                soConn, remoteAddr = self.socket.accept()
                self.listener.notifyNewConnection(soConn, remoteAddr)
                #-- if sData != None
            except:
                exc_type = sys.exc_info()[0]
                if exc_type != socklib.timeout:
                    self.listener.notifyListenThreadTermination(True)
                    raise
                #--
                pass
            #-- except
            pass
        #-- while
        self.listener.notifyListenThreadTermination(False)
        pass
        
        
        
class asyncReader:
    def __init__(self, channel):
        self.messages = collections.deque()
        self.channel = channel
        
    def fetchMessage(self):
        if len(self.messages) > 0:
            return self.messages.popleft()
        else:
            return None
        pass
    #-- def
    
    def hasMessage(self):
        return len(self.messages) > 0
    
    def feedData(self, data): pass # virtual to replace
    def sendData(self, data): pass # virtual to replace

class asyncRawMsgReader(asyncReader):
    def __init__(self, channel):
        asyncReader.__init__(self, channel)
    
    def feedData(self, data):
        self.messages.append(data)
        
    def sendData(self, data):
        self.channel.socket.send(data)
    
class asyncLFMsgReader(asyncReader):
    def __init__(self, channel):
        asyncReader.__init__(self, channel)
        self.currentLine = ''
    
    def feedData(self, data):
        while len(data) > 0:
            i = data.find('\n')
            if i >= 0:
                msg = self.currentLine + data[:i]
                if msg[-1:] == '\r':
                    msg = msg[:-1]
                self.messages.append(msg)
                self.currentLine = ''
                data = data[i + 1:]
            else:
                self.currentLine += data
                data = ''
            #--
            pass
        #-- while
        pass
    #-- def
    
    def sendData(self, data):
        self.channel.socket.send(data + '\n')
        

class asyncBLMsgReader(asyncReader):
    def __init__(self, channel, nLenBytes = 2):
        asyncReader.__init__(self, channel)
        self.lenBytes = nLenBytes
        self.resetReadMessage()
        self.MAX_MESSAGE_LENGTH = (0x100 ** nLenBytes) - 1
        
    def resetReadMessage(self):
        self.__readState = 0
        # readState can be: 
        #   0 <= rs < lenBytes -> stating reading header position, with rs denotes how many bytes has been read
        #   lenBytes -> stating header position has been completely read and now reading bytes
        self.__msgLenBytes = ''
        self.__msgLen = 0
        self.__msgBytesRead = 0
        self.__msgData = ''
        
    def feedData(self, data):
        while len(data) > 0:
            if self.__readState < self.lenBytes:
                self.__msgLenBytes += data[:self.lenBytes - self.__readState]
                data = data[self.lenBytes - self.__readState:]
                self.__readState = len(self.__msgLenBytes)
                if self.__readState == self.lenBytes:
                    l = 0
                    for cc in self.__msgLenBytes:
                        l = (l * 0x100) + ord(cc)
                    self.__msgLen = l
                    self.__msgData = ''
                #-- if
                pass
            #--if
            if self.__readState == self.lenBytes:
                nRead = min(len(data), self.__msgLen - self.__msgBytesRead)
                self.__msgData += data[:nRead]
                self.__msgBytesRead += nRead
                data = data[nRead:]

                if self.__msgBytesRead == self.__msgLen:
                    self.messages.append(self.__msgData)
                    self.resetReadMessage()
                #-- if msgbytesread
                pass
            #-- if readstate
            pass
        #-- while
    #-- def
    
    def sendData(self, data):
        ldata = len(data)
        if ldata > self.MAX_MESSAGE_LENGTH:
            raise Exception, 'Message length overflow'
        sLen = ''
        for i in range(self.lenBytes):
            sLen = chr(ldata % 0x100) + sLen
            ldata = ldata / 0x100
        #--
        self.channel.socket.send(sLen + data)
    #-- def
    
