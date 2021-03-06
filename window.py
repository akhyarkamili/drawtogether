'''
DRAWTOGETHER - CANVAS
By Akhyar I. Kamili
November 2016

This module consists of a CanvasWindow class which
manages a window in the drawing application. It's a
container for a canvas, and it handles all events happening
both from network and from canvas.

Threading hack is attributed to Ismir Kamili's msglib library.
'''

import pygame
import sys
import socket as so
import msglib as mc
import helper
import tools
import shapes
import pickle
import random
import ctypes

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
GREY  = (175, 175, 175)
RED   = pygame.Color(255, 0, 0)
BLUE  = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (0, 150, 150)
BROWN = (120, 120, 0)

USERCOLORS = [GREY, RED, BLUE, GREEN, YELLOW, BROWN]

def incomingMsgHandler(self, msg):
    myEvent = pygame.event.Event(pygame.USEREVENT+4, message=msg) # create pygame event here
    pygame.event.post(myEvent)

class CanvasWindow:
    def __init__(self, userdict):
        '''
        Accepts a session, a connection, a project string
        that will be converted to the canvas, and a 
        list of user dictionaries that is in the session.
        '''
        # connector to server
        self.connector = mc.connector('localhost', 15112, 'BL2')
        mc.channel.logMessage = incomingMsgHandler
        self.connector.connect()
        self.bg = WHITE

        self.userID = userdict['owner']
        self.userdict = self.initializeUsers(userdict['users'])

        self.drawTools = {'circle':tools.drawCircle, 
                          'polygon':tools.drawPolygon, 
                          'line':tools.drawLine,
                          'path':tools.drawPath
                         }
        self.selectTools = {'fill': tools.fill,
                            'rotate': tools.rotate,
                            'scale': tools.scale
                           }
        self.screenItems = []

        self.clock = pygame.time.Clock()

        pygame.init()
        pygame.display.set_caption(self.userID)
        # in case of full screen
        user32 = ctypes.windll.user32
        self.screenSize =  user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

        self.width = 700
        self.height = 400
        self.screen = pygame.display.set_mode([self.width, self.height])

        self.requestProject()
        self.listen()
    ##
    def listen(self):
        '''
        Listens to all kind of events and react accordingly
        '''
        # define events
        events = {'click':pygame.USEREVENT+1,
                'drag':pygame.USEREVENT+2,
                'drop':pygame.USEREVENT+3,
                'update':pygame.USEREVENT+5,
                'tool_change':pygame.USEREVENT+6
            }
        server = pygame.USEREVENT+4

        mousedown = False
        mousedrag = False
        clock = pygame.time.Clock()
        pygame.time.set_timer(events['update'], 500)

        wheel = pygame.image.load('colorspectrum.png').convert()

        # Reactor loop
        while True:
            self.clock.tick(30)
            self.screen.fill(WHITE)
            self.drawScreen() 

            dest = [20, 350]
            self.screen.blit(wheel, dest)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    press_pos = pygame.mouse.get_pos()
                    mousedown = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    mousedown = False
                    if not mousedrag:
                        # mouse was clicked
                        e = pygame.event.Event(events['click'], etype='click', pos=pos, source=self.userID)
                        pygame.event.post(e)
                    else:
                        # mouse is dropped from drag
                        e = pygame.event.Event(events['drop'], etype='drop', pos=pos, 
                                    origin=press_pos, rel=relative, source=self.userID)
                        pygame.event.post(e)
                        mousedrag = False
                elif event.type == pygame.KEYUP:
                    if event.key == 27:
                        self.quit()
                    e = pygame.event.Event(events['tool_change'], etype='tool_change', source=self.userID, key=event.key)
                    pygame.event.post(e)
                elif event.type == events['tool_change']:
                    if event.source == self.userID:
                        self.sendEvent(event)
                    self.toolHandler(event)
                elif event.type == events['click']:
                    if event.source==self.userID:
                        self.sendEvent(event)
                    self.clickHandler(event)
                    mousedown = False
                elif event.type == events['drag']:
                    mousedrag = True
                    if event.source==self.userID:
                        self.sendEvent(event)
                    self.dragHandler(event)
                elif event.type == events['drop']:
                    mousedrag = False
                    if event.source==self.userID:
                        self.sendEvent(event)
                    self.dropHandler(event)
                elif event.type == events['update']:
                    self.broadcastState()
                    pygame.time.set_timer(events['update'], 500)
                elif event.type == server:
                    # msg is a dictionary
                    head = event.message[:20].strip()
                    if head == 'EVENT':
                        mainmsg = pickle.loads(event.message[20:])
                        msg = mainmsg['body']
                        if mainmsg['source'] != self.userID:
                            e = pygame.event.Event(events[msg['type']], **msg['event'])
                            pygame.event.post(e)
                    elif head == 'STATE_UPDATE':
                        mainmsg = pickle.loads(event.message[20:])
                        msg = mainmsg['body']
                        source = msg['source']
                        user = self.userdict[source]
                        for key in msg:
                            user[key] = msg[key]
                    elif head == 'BC_UPDATE':
                        # updates all others based on the canvas
                        d = 'RESP_UPDATE'.ljust(20) + self.save()
                        self.connector.send(d)
                    elif head == 'RESP_UPDATE':
                        # received an update
                        if event.message[-4:] == 'NONE':
                            # no existing canvas
                            pass
                        else:
                            # there is an existing canvas
                            self.load(event.message)


            # trigger drag
            if mousedown:
                pos = pygame.mouse.get_pos()
                if not helper.isNear(pos, press_pos):
                    # mouse is still down, 
                    # but has moved considerably
                    relative = (pos[0]-last_pos[0],pos[1]-last_pos[1])
                    e = pygame.event.Event(events['drag'], etype='drag', pos=pos, 
                                origin=press_pos, rel=relative, source=self.userID)
                    pygame.event.post(e)
                last_pos = pos

            pygame.display.flip()
    ##

    def initializeUsers(self, ul):
        userdict = {}

        for u in ul:
            sc = random.choice(USERCOLORS)
            d = {'state':'draw', 
                 'activeTool':'polygon', 
                 'bordercolor':BLACK,
                 'borderwidth': 1,
                 'fillcolor': WHITE,
                 'selection': [],
                 'tempObj': None,
                 'polygonSides':5,
                 'selectionRect': pygame.Rect((0,0), (0,0)),
                 'selectColor':sc
                 }

            userdict[u['id']] = d
            USERCOLORS.remove(sc)
        return userdict
    ##
    def drawScreen(self):
        self.screen.fill(self.bg)
        for obj in self.screenItems:
            obj.draw(self.screen)
    ##
    def sendEvent(self, event):
        ''' construct event message
            A dictionary object containing:
            type: click, drag, drop

            sends to all other users
        '''
        print event
        msg = {}

        msg['type'] = event.etype
        msg['event'] = {}
        for k, v in event.__dict__.items():
            msg['event'][k] = v
        print msg

        mainmsg = {'body':msg, 'source':self.userID}
        d = 'EVENT'.ljust(20) + pickle.dumps(mainmsg)
        self.connector.send(d)
    ##
    def broadcastState(self):
        # broadcasts state of user
        # to all other users
        me = self.userdict[self.userID]
        msg = {}

        msg['source'] = self.userID
        msg['state'] = me['state']
        msg['activeTool'] = me['activeTool']
        msg['bordercolor'] = me['bordercolor']
        msg['fillcolor'] = me['fillcolor']
        msg['borderwidth'] = me['borderwidth']
        msg['polygonSides'] = me['polygonSides']

        mainmsg = {'body':msg, 'source':self.userID}
        d = 'STATE_UPDATE'.ljust(20) + pickle.dumps(mainmsg)
        self.connector.send(d)
    ##
    def requestProject(self):
        self.connector.send('RQ_UPDATE'.ljust(20))
        print 'request sent!'
    def toolHandler(self, event):
        user = self.userdict[event.source]

        if event.key == 108:
            user['state'] = 'draw'
            user['activeTool'] = 'line'
        elif event.key == 112:
            user['state'] = 'draw'
            user['activeTool'] = 'polygon'
        elif event.key in range(49, 58):
            user['polygonSides'] = event.key - 48 
        elif event.key == 100:
            user['state'] = 'draw'
        elif event.key == 99:
            user['state'] = 'draw'
            user['activeTool'] = 'circle'
        elif event.key == 115:
            user['state'] = 'select'
        elif event.key == 102:
            user['state'] = 'draw'
            user['activeTool'] = 'path'
        elif event.key == 127:
            # delete button was pressed
            self.deleteSelection(user)

    def clickHandler(self, event):
        print 'event coming from:', event.source
        user = self.userdict[event.source]     

        state = user['state']
        selection = user['selection']
        screenItems = self.screenItems 

        pos = event.pos
        if 20 < pos[0] < 680 and 330 < pos[1] < 400:
            thiscolor = self.screen.get_at(pos)
            if state == 'select':
                for obj in selection:
                    user['bordercolor'] = thiscolor
                    obj.setColor(thiscolor)
        else:
            outside = True # measure the amount of change occured
            # check if any of the object is clicked
            for obj in screenItems:
                if obj not in selection:
                    if pos in obj:
                        # the click is in a ScreenObject
                        self.clearSelection(user)                    
                        outside = False
                        if state == 'select':
                            obj.toggleSelected(user['selectColor'])
                            if not obj in selection:
                                user['selection'] = helper.listPush(user['selection'], obj)
                        break
                else:
                    if pos in obj:
                        outside = False
            if outside: 
                # clicked outside of any object
                self.clearSelection(user)
    ##
    def dragHandler(self, event):
        print 'event coming from:', event.source
        user = self.userdict[event.source]     

        state = user['state']
        selection = user['selection']
        activeTool = user['activeTool']

        screenItems = self.screenItems 


        if state == 'select':
            pygame.draw.rect(self.screen, RED, user['selectionRect'], 1)
            if selection:
                # selection is not empty
                # dragging means moving
                for obj in selection:
                    obj.displace(*event.rel)
            else:
                # selection is empty 
                # do area selection
                user['selectionRect'] = self.createSelectionArea(event.origin, event.pos)
        elif state == 'draw':
            start, end = event.origin, event.pos
            if not user['tempObj']:
                user['tempObj'] = self.drawTools[activeTool](start, end, 
                                    user['fillcolor'], user['bordercolor'], user['borderwidth'], n=user['polygonSides'], sColor=user['selectColor'])
            else:
                # adjust the object to follow mouse handler
                self.drawTools[activeTool](start, end, user['fillcolor'], 
                                      user['bordercolor'], user['borderwidth'], user['tempObj'], n=user['polygonSides'], sColor=user['selectColor'])
            user['tempObj'].draw(self.screen)
    ##
    def dropHandler(self, event):
        print 'event coming from:', event.source

        user = self.userdict[event.source]     

        state = user['state']
        selection = user['selection']
        activeTool = user['activeTool']

        if state == 'select':
            area = user['selectionRect']
            tools.selectArea(self.screenItems, area, selection, user)

            # capture selection, remove rectangle
            user['selectionRect'] = pygame.Rect((0,0), (0,0))
        elif state == 'draw':
            self.clearSelection(user)
            self.screenItems.append(user['tempObj'])
            user['selection'] = helper.listPush(user['selection'], user['tempObj'])
            print event.source, user['selection']
            user['tempObj'] = None

    def createSelectionArea(self, start_pos, end_pos):
        end_pos, start_pos = helper.adjust(end_pos, start_pos)
        width = end_pos[0] - start_pos[0]
        height = end_pos[1] - start_pos[1]
        screen = self.screen

        rect = pygame.Rect(start_pos, (width, height))

        # manually create lines
        # pygame.draw.line(screen, BLACK, start_pos, (start_pos[0], start_pos[1]+height))
        # pygame.draw.line(screen, BLACK, start_pos, (start_pos[0]+width, start_pos[1]))
        # pygame.draw.line(screen, BLACK, (start_pos[0]+width, start_pos[1]), 
        #                                 (start_pos[0]+width, start_pos[1]+height))
        # pygame.draw.line(screen, BLACK, (start_pos[0], start_pos[1]+height), 
        #                                 (start_pos[0]+width, start_pos[1]+height))

        return rect
    ##
    def clearSelection(self, user):
        # clearing
        for obj in user['selection']:
            obj.selected = True
            obj.toggleSelected(user['selectColor'])

        user['selection'] = []
    ##
    def deleteSelection(self, user):
        for obj in user['selection']:
            self.screenItems.remove(obj)
        user['selection'] = []

    def createControls(self):
        # assigns the controls to the window
        pass
    ##
    def save(self):
        itemDump = []
        for obj in self.screenItems:
            itemDump.append(obj.save())
        return pickle.dumps(itemDump)
    ##
    def load(self, project):
        types = {'LINE': shapes.Line,
                 'POLYGON': shapes.Polygon,
                 'PATH': shapes.Path
                }
        print "project:", project
        self.screenItems = []
        if project[20:]:
            dumps = pickle.loads(project[20:])
            for d in dumps:
                obj_type = types[d[:20].strip()]
                keyargs = pickle.loads(d[20:])
                self.screenItems.append(obj_type(**keyargs))
    ##
    def quit(self):
        d = 'RESP_UPDATE'.ljust(20) + self.save()
        self.connector.send(d)
        self.connector.disconnect()
        pygame.quit()
        sys.exit()


# if __name__ == '__main__':
#     conn = mc.connector('localhost', 15112, 'BL2')
#     userlist = []
#     for ID in sys.argv[1:]:
#         userlist.append({'id':ID})
#     window = CanvasWindow()

