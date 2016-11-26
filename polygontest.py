import pygame
import math as m
import sys
import time
from uuid import uuid1 as ID_GEN

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
GREY = (175, 175, 175)


class CanvasObject(object):
    def __init__(self):
        self.id = ID_GEN()

class Shape(CanvasObject):
    def __init__(self, topleft, fillcolor, bordercolor, borderwidth):
        self.id = ID_GEN()
    def getRect(self):
        return self.rect

class Line(CanvasObject):
    def __init__(self, start, end, color):
        super(Line, self).__init__()
        self.start = start
        self.end = end
        self.color = color

        # when a line is created,
        # it should be in a selected state 
        self.activeColor = GREY
        self.selected = True

        self.setColor(self.activeColor)
        
        self.computePoints()

    def displace(self, disp_x, disp_y):
        self.start = self.start[0] + disp_x, self.start[1] + disp_y
        self.end = self.end[0] + disp_x, self.end[1] + disp_y

        self.computePoints()

    def setColor(self, color):
        self.activeColor = color

    def getColor(self):
        return self.activeColor

    def toggleSelected(self):
        if not self.selected:
            # temporarily turn to grey 
            # until selected = False
            self.activeColor = GREY
        else:
            self.activeColor = self.color
        # toggle selected
        self.selected = not self.selected

    def change(self, start, end):
        self.end, self.start = end, start
        self.computePoints()

    def computePoints(self):
        self.points = []
        x0, y0 = self.start
        x1, y1 = self.end

        # BRESENHAM'S LINE ALGORITHM
        # CODE BY BRIAN WILL

        rise = y1-y0
        run = x1-x0

        if not run:
            # vertical line
            if y1 < y0:
                y1, y0 = y0, y1
            for y in range(y0, y1):
                self.points.append((x0, y))
        else:
            m = float(rise)/run
            adjust = 1 if m >=0 else -1
            offset = 0
            threshold = abs(run)
            thresholdInc = abs(run) * 2
            if abs(m) < 1:
                y = y0
                if x1 < x0:
                    # swap
                    x1, x0 = x0, x1
                    y = y1
                for x in range(x0, x1+1):
                    self.points.append((x, y))
                    offset += abs(rise) * 2

                    if offset >= threshold:
                        y += adjust
                        threshold += thresholdInc
            else:
                x = x0
                threshold = abs(rise)
                thresholdInc = abs(rise) * 2
                if y1 < y0:
                    # swap
                    y1, y0 = y0, y1
                    x = x1

                for y in range(y0, y1+1):
                    self.points.append((x, y))
                    offset += abs(run)*2
                    if offset >= threshold:
                        x += adjust
                        threshold += thresholdInc

    def draw(self, sc):
        for p in self.points:
            sc.set_at(p, self.activeColor)

    def __eq__(self, other):
        if isinstance(other, Line):
            return other.start == self.start and other.end == self.end

    def __contains__(self, point):
        return point in self.points

class Polygon(Shape):
    def __init__(self, topleft, radius, n, fillcolor=WHITE, bordercolor=BLACK, borderwidth=1):
        self.n = n
        self.topleft = topleft
        self.radius = radius
        self.image = None
        self.fillcolor = fillcolor
        self.rotation = 0

        self.borderwidth = borderwidth
        self.bordercolor = bordercolor
        self.selected = True

        self.edges = [] # Fill with line objects
        for _ in range(n):
            edge = Line((0,0), (0,0), bordercolor)
            self.edges.append(edge)

        self.computeEdges()

    def resize(self, start, end):
        # drag and drop resize
        end, start = adjust(end, start)
        self.topleft = start
        self.radius = (end[0] - start[0])/2 # (end[0] - start[0])/2, (end[1] - start[1])/2 
        self.computeEdges()

    def getCenter(self):
        rad = self.radius
        tl = self.topleft
        return (tl[0] + rad, tl[1]+rad)
    ##
    def computeEdges(self):
        # find the location of vertices based on center point x, y
        r = self.radius
        n = self.n
        edges = self.edges
        x, y = self.getCenter()

        angle = 0
        offset = 2*m.pi/n
        for i in range(n):
            edge = edges[i]
            # start x, start y
            sy = y + int(r*m.sin(angle))
            sx = x + int(r*m.cos(angle))

            angle += offset
            # end x, end y
            ey = y + int(r*m.sin(angle))
            ex = x + int(r*m.cos(angle))

            edge.change((sx, sy),(ex, ey))
    ##
    def displace(self, dx, dy):
        self.topleft[0] += dx
        self.topleft[1] += dy
        self.computeEdges()
    ##
    def draw(self, sc):
        for edge in self.edges:
            edge.draw(sc)
    ##
    def inRect(self, p):
        # check if x or y is in the rough rectangle
        tl = self.topleft
        r = self.radius
        x, y = p
        if x <= tl[0] or x >= tl[0]+2*r:
            return False
        if y <= tl[1] or y >= tl[1]+2*r:
            return False
        return True
    def toggleSelected(self):
        self.selected = not self.selected
        for e in self.edges:
            e.toggleSelected()
    def __contains__(self, p):
        ''' 
        Check if a point lies inside a polygon.
        Scans a horizontal line from the topleft[0] to the point.
        If the number of edges it crosses is 
        odd, the point is inside.
        '''
        tl = self.topleft
        r = self.radius

        if not self.inRect(p):
            return False

        x, y = p
        inside = False
        for e in self.edges:
            inEdge = False
            for i in range(tl[0], x):
                if (i, y) in e and not inEdge:
                    inEdge = True
                    inside = not inside
        return inside


def adjust(end_pos, start_pos):
    if end_pos[1] < start_pos[1]:
        if end_pos[0] < start_pos[0]:
            start_pos, end_pos = end_pos, start_pos
        else:
            temp = end_pos
            end_pos = end_pos[0], start_pos[1]
            start_pos = start_pos[0], temp[1]
    else:
        if end_pos[0] < start_pos[0]:
            temp = end_pos
            end_pos = start_pos[0], end_pos[1]
            start_pos = temp[0], start_pos[1]
    return end_pos, start_pos

def drawScreen(screen, screenObjects , bg):
    screen.fill(bg)
    for obj in screenObjects:
        obj.draw(screen)

def clearSelection(selection):
    # clearing
    for i in range(len(selection)):
        selection[i].toggleSelected()

def isNear(p1, p2):
    # check if two points are near each other
    # uses pythagorean theorem
    dx = p2[0]-p1[0]
    dy = p2[1]-p1[1]
    if dx**2 + dy**2 < 8:
        return True
    return False

def drawSelectionArea(start_pos, end_pos):
    width = end_pos[0] - start_pos[0]
    height = end_pos[1] - start_pos[1]

    pygame.draw.line(screen, BLACK, start_pos, (start_pos[0], start_pos[1]+height))
    pygame.draw.line(screen, BLACK, start_pos, (start_pos[0]+width, start_pos[1]))
    pygame.draw.line(screen, BLACK, (start_pos[0]+width, start_pos[1]), 
                                    (start_pos[0]+width, start_pos[1]+height))
    pygame.draw.line(screen, BLACK, (start_pos[0], start_pos[1]+height), 
                                    (start_pos[0]+width, start_pos[1]+height))

if __name__ == '__main__':
    print 'running..'
    # init pygame
    pygame.init()

    screen_width = 700
    screen_height = 400
    screen = pygame.display.set_mode([screen_width, screen_height])
    screen.fill(WHITE)

    clock = pygame.time.Clock()
    mousedown = False

    pol = Polygon([100, 100], 25, 3)
    screenObjects = [pol]
    state = 'select'
    activeTool = 'move'
    selection = [pol]

    # define events
    click = pygame.USEREVENT+1
    drag = pygame.USEREVENT+2
    drop = pygame.USEREVENT+3

    while True:
        clock.tick(30)
        # check for events
        drawScreen(screen, screenObjects, WHITE)  
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                press_pos = pygame.mouse.get_pos()
                mousedown = True

            elif event.type == pygame.MOUSEBUTTONUP:
                mousedown = False
                if isNear(pos, press_pos):
                    # probably a click
                    e = pygame.event.Event(click, pos=pos)
                    pygame.event.post(e)

            elif event.type == click:
                if state == 'select':
                    sel = str(selection)
                    # check if any of the object is clicked
                    for obj in screenObjects:
                        if not obj in selection:
                            if pos in obj:
                                obj.toggleSelected()
                                selection.append(obj)
                    if str(selection) == sel: 
                        # clicked outside of any object
                        # selection is cleared
                        clearSelection(selection)
                        selection = []
            elif event.type == drag:
                if state == 'select':
                    if selection:
                        # selection is not empty
                        if activeTool == 'move':
                            for obj in selection:
                                obj.displace(*event.rel)
                    else:
                        # selection is empty 
                        # do area selection
                        drawSelectionArea(press_pos, event.pos)
                elif state == 'draw':
                    pass

        # handle custom events
        if mousedown:
            pos = pygame.mouse.get_pos()
            if not isNear(pos, press_pos):
                # mouse is still down, 
                # but has moved considerably
                relative = (pos[0]-last_pos[0],pos[1]-last_pos[1])
                e = pygame.event.Event(drag, pos=pos, rel=relative)
                pygame.event.post(e)
            last_pos = pos

        pygame.display.flip()