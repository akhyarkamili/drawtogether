import pygame
import sys
import socket as so
import msglib as mc
import helper
import tools
import shapes
import pickle

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
GREY  = (175, 175, 175)
RED   = pygame.Color(255, 0, 0)

def incomingMsgHandler(self, msg):
    myEvent = pygame.event.Event(pygame.USEREVENT+4, message=msg) # create pygame event here
    pygame.event.post(myEvent)

class CanvasWindow:
    def __init__(self, sessionID, conn, project, userlist):
        '''
        Accepts a session, a connection, a project string
        that will be converted to the canvas, and a 
        list of user dictionaries that is in the session.
        '''
        self.sessionID = sessionID
        self.userID = userlist[0]['id']
        self.conn = conn
        self.userlist = userlist

        self.drawTools = {'circle':tools.drawCircle, 
                          'polygon':tools.drawPolygon, 
                          'line':tools.drawLine,
                          'path':tools.drawPath
                         }
        self.selectTools = {'fill': tools.fill,
                            'transform': tools.transform,
                           }

        self.state = 'draw'
        self.activeTool = 'polygon'
        self.screenItems = []
        self.selection = []

        self.clock = pygame.time.Clock()

        pygame.init()
        self.width = 700
        self.height = 400
        self.screen = pygame.display.set_mode([self.width, self.height])
        self.createControls()

        # project-related
        self.name = ''
        self.background = ''
        self.load(project)

        self.bordercolor = BLACK
        self.borderwidth = 1
        self.fillcolor = WHITE

        # connector to server
        self.connector = conn
        mc.channel.logMessage = incomingMsgHandler
        self.connector.connect()


        # test vars
        self.count = 0 
        pol = shapes.Polygon([100, 100], 25, 3)
        self.screenItems.append(pol)
        self.selection.append(pol)

        self.listen()
    ##
    def listen(self):
        '''
        Listens to all kind of events and react accordingly
        '''
        # define events
        events = {'click':pygame.USEREVENT+1,
                'drag':pygame.USEREVENT+2,
                'drop':pygame.USEREVENT+3
            }
        server = pygame.USEREVENT+4

        mousedown = False
        mousedrag = False
        clock = pygame.time.Clock()

        self.selectionRect = pygame.Rect((0,0), (0,0))
        self.tempObj = None
        self.polygonSides = 4
        # Reactor loop
        while True:
            self.clock.tick(30)
            self.screen.fill(WHITE)
            self.drawScreen() 

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.connector.disconnect()
                    pygame.quit()
                    sys.exit()
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
                    self.sendEvent(event)
                    self.dropHandler(event)
                elif event.type == pygame.KEYUP:
                    print event.key
                    if event.key == 108:
                        self.state = 'draw'
                        self.activeTool = 'line'
                    elif event.key == 112:
                        self.state = 'draw'
                        self.activeTool = 'polygon'
                    elif event.key == 115:
                        self.state = 'select'
                        self.activeTool = 'move'
                    elif event.key in range(49, 58):
                        self.polygonSides = event.key - 48 
                    elif event.key == 99:
                        self.state = 'draw'
                        self.activeTool = 'circle'

                elif event.type == server:
                    # msg is a dictionary
                    msg = pickle.loads(event.message)
                    if msg['source'] != self.userID:
                        e = pygame.event.Event(events[msg['type']], **msg['event'])
                        pygame.event.post(e)

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

            if mousedrag:
                pygame.draw.rect(self.screen, RED, self.selectionRect, 1)

            pygame.display.flip()
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
        '''
        print event
        msg = {}

        msg['type'] = event.etype
        msg['event'] = {}
        for k, v in event.__dict__.items():
            msg['event'][k] = v
        msg['source'] = self.userID

        print msg
        d = pickle.dumps(msg)
        self.connector.send(d)
    ##
    def clickHandler(self, event):
        print 'event coming from:', event.source        
        state = self.state
        selection = self.selection
        screenItems = self.screenItems 

        pos = event.pos
        outside = True # measure the amount of change occured
        # check if any of the object is clicked
        for obj in screenItems:
            if obj not in selection:
                if pos in obj:
                    # the click is in a ScreenObject
                    self.clearSelection()                    
                    outside = False
                    if state == 'select':
                        obj.toggleSelected()
                        if not obj in selection:
                                self.selection.append(obj)
                    break
            else:
                if pos in obj:
                    outside = False
        if outside: 
            # clicked outside of any obje
            self.clearSelection()
    ##
    def dragHandler(self, event):
        print 'event coming from:', event.source
        state = self.state
        selection = self.selection
        activeTool = self.activeTool

        if state == 'select':
            if selection:
                # selection is not empty
                # dragging means moving
                if activeTool == 'move':
                    for obj in selection:
                        obj.displace(*event.rel)
            else:
                # selection is empty 
                # do area selection
                self.selectionRect = self.createSelectionArea(event.origin, event.pos)
        elif state == 'draw':
            start, end = event.origin, event.pos
            if not self.tempObj:
                self.tempObj = self.drawTools[activeTool](start, end, 
                                    self.fillcolor, self.bordercolor, self.borderwidth, n=self.polygonSides)
            else:
                # adjust the object to follow mouse handler
                self.drawTools[activeTool](start, end, self.fillcolor, 
                                      self.bordercolor, self.borderwidth, self.tempObj, n=self.polygonSides)
            self.tempObj.draw(self.screen)
    ##
    def dropHandler(self, event):
        print 'event coming from:', event.source
        state = self.state
        if state == 'select':
            area = self.selectionRect
            tools.selectArea(self.screenItems, area, self.selection)

            # capture selection, remove rectangle
            mousedrag = False
            self.selectionRect = pygame.Rect((0,0), (0,0))
        elif state == 'draw':
            self.clearSelection()
            self.screenItems.append(self.tempObj)
            self.selection.append(self.tempObj)
            self.tempObj = None

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
    def clearSelection(self):           
        # clearing
        for obj in self.selection:
            obj.selected = True
            obj.toggleSelected()

        self.selection = []
    ##
    def load(self, project):
        # loads the image into canvas
        self.bg = WHITE
    ##
    def createControls(self):
        # assigns the controls to the window
        pass
    ##
    def save(self):
        pass


if __name__ == '__main__':
    conn = mc.connector('localhost', 15112, 'BL2')
    ID = sys.argv[1]
    sessionID = '000'
    window = CanvasWindow(sessionID, conn, None, [{'id':ID}])

