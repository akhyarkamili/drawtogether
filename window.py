import pygame
import math as m
import sys
import time
from uuid import uuid1 as ID_GEN

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
GREY = (175, 175, 175)

class CanvasWindow:
    def __init__(self, sessionID, conn, project):
        self.ID = sessionID
        self.conn = conn

        pygame.init()
        self.width = 700
        self.height = 400
        self.screen = pygame.display.set_mode([self.width, self.height])

        self.createControls()
        self.load(project)
        self.listen()

        self.items = []

    def load(self, project):
        # loads the image into canvas
        pass

    def createControls(self):
        # assigns the controls to the window
        pass

    def listen(self):
        print "listening..."

class ScreenObject(object):
    def __init__(self):
        self.id = ID_GEN()


class Line(ScreenObject):
    def __init__(self, start, end, color):
        super(Line, self).__init__()
        self.start = start
        self.end = end
        self.color = color

        self.setColor(self.color)
        
        self.computePoints()

    def displace(self, disp_x, disp_y):
        self.start = self.start[0] + disp_x, self.start[1] + disp_y
        self.end = self.end[0] + disp_x, self.end[1] + disp_y

        self.computePoints()

    def setColor(self,color):
        self.activeColor = color

    def getColor(self):
        return self.activeColor

    def setSelected(self, selected):
        if selected:
            self.activeColor = GREY
        else:
            self.activeColor = self.color
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

class Shape():
    def __init__(self, topleft, fillcolor, bordercolor, borderwidth):
        pass
    def getRect(self):
        return self.rect

class Circle(Shape):
    def __init__(self, topleft, radius):
        pass
    def draw(self, canvas):
        center = topleft[0]+self.radius/2, topleft[1]+self.radius/2
        self.image = pygame.draw.circle(surface, self.color, center, self.radius, self.borderwidth)

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

        self.edges = [] # Fill with line objects
        for _ in range(n):
            edge = Line((0,0), (0,0), bordercolor)
            self.edges.append(edge)
        center = self.getCenter()
        self.computeEdges(*center)

    def resize(self, start, end):
        # drag and drop resize
        end, start = adjust(end, start)
        x, y = (end[0] - start[0])/2, (end[1] - start[1])/2 
        self.updateEdges(x, y)
        self.draw()

    def getCenter(self):
        rad = self.radius
        tl = self.topleft
        return (tl[0] + rad, tl[1]+rad)

    def computeEdges(self, x, y):
        # find the location of vertices based on center point x, y
        r = self.radius
        n = self.n
        edges = self.edges
        center = self.getCenter()

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

        print ""

    def draw(self, sc):
        for edge in self.edges:
            edge.draw(sc)

# helper functions
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

if __name__ == '__main__':
    conn = None
    sessionID = '000'
    window = CanvasWindow(sessionID, conn, None)
    while True:
        window.screen.fill(WHITE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        pol = Polygon((250, 100), 50, 9)
        pol.draw(window.screen) 
        for i in range(3):
            for j in range(3):
                window.screen.set_at((300+i, 150+j), BLACK)
        time.sleep(0.5)
        pygame.display.flip()
