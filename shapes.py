from helper import *
from uuid import uuid1 as ID_GEN
import math as m
import pickle

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
GREY = (175, 175, 175)

class CanvasObject(object):
    def __init__(self):
        self.id = ID_GEN()
##
class Line(CanvasObject):
    def __init__(self, start, end, color, sColor=GREY):
        super(Line, self).__init__()
        self.start = start
        self.end = end
        self.color = color

        # when a line is created,
        # it should be in a selected state 
        self.activeColor = sColor
        self.selected = True
        
        self.computePoints()

    def displace(self, disp_x, disp_y):
        self.start = self.start[0] + disp_x, self.start[1] + disp_y
        self.end = self.end[0] + disp_x, self.end[1] + disp_y

        self.computePoints()
    ##
    def setColor(self, color):
        # changes permanent color
        self.color = color
    ##
    def getColor(self):
        return self.activeColor
    ##
    def getEndPoints(self):
        return self.start, self.end
    ##
    def toggleSelected(self, sColor):
        if self.selected:
            # release the select
            self.activeColor = self.color
        else:
            # temporarily turn to selected color 
            # until selected = False
            self.activeColor = sColor
        # toggle selected
        self.selected = not self.selected
    ##
    def inbound(self, rect):
        return rect.collidepoint(self.start) and rect.collidepoint(self.end)
    ##
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
    ##
    def __contains__(self, point):
        return point in self.points
    ##
    def dump(self):
        d = {}

        d['start'] = self.start
        d['end'] = self.end
        d['color'] = self.color

        return 'LINE'.ljust(10) + pickle.dumps(d)

##

class Path(CanvasObject):
    def __init__(self, start, color, sColor=GREY):
        self.points = [start]
        self.selected = True
        self.selectedColor = sColor
        self.color = color

        self.activeColor = sColor
    def toggleSelected(self, sColor):
        if self.selected:
            # unselect
            self.activeColor = self.color
            self.selected = False
        else:
            self.activeColor = sColor
            self.selected = True

    def add(self, point):
        self.points.append(point)

    def displace(self, dx, dy):
        for i in range(len(self.points)):
            self.points[i] = self.points[i][0] + dx, self.points[i][1] + dy 

    def inbound(self, rect):
        return all(rect.collidepoint(p) for p in self.points)

    def draw(self, sc):
        for p in self.points:
            for i in range(3):
                point = (p[0]-1) + i, (p[1]-1) + i
                sc.set_at(point, self.activeColor)

    def __contains__(self, p):
        return p in self.points

    def dump(self):
        d = {}
        d['points'] = self.points
        d['color'] = self.color
        return 'PATH'.ljust(10) + pickle.dumps(d)
##

class Shape(CanvasObject):
    def __init__(self, topleft, fillcolor, bordercolor, borderwidth):
        pass
    def getRect(self):
        return self.rect
##

class Circle(Shape):
    def __init__(self, topleft, radius):
        pass
    def draw(self, canvas):
        center = topleft[0]+self.radius/2, topleft[1]+self.radius/2
        self.image = pygame.draw.circle(surface, self.color, center, self.radius, self.borderwidth)
##

class Polygon(Shape):
    def __init__(self, topleft, radius, n, sColor=GREY, fillcolor=WHITE, bordercolor=BLACK, borderwidth=1):
        self.n = n
        self.topleft = topleft
        self.radius = radius
        self.image = None
        self.fillcolor = fillcolor
        self.rotation = 0

        self.borderwidth = borderwidth
        # permanent color
        self.bordercolor = bordercolor
        self.selected = True
        # temporary color
        self.activeBorderColor = sColor

        self.edges = [] # Fill with line objects
        for _ in range(n):
            edge = Line((0,0), (0,0), self.bordercolor, self.activeBorderColor)
            self.edges.append(edge)

        self.computeEdges()

    def resize(self, start, end):
        # drag and drop resize
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
    def pointInRect(self, p):
        # check if x or y is in the rough rectangle
        tl = self.topleft
        r = self.radius
        x, y = p
        if x <= tl[0] or x >= tl[0]+2*r:
            return False
        if y <= tl[1] or y >= tl[1]+2*r:
            return False
        return True
    ##
    def inbound(self, rect):
        '''
        Accepts a pygame.Rect object
        and checks whether this object
        is contained within the rectangle
        '''
        outbound = False
        for e in self.edges:
            s, e = e.getEndPoints()
            if not (rect.collidepoint(s) or rect.collidepoint(e)):
                outbound = True
        return not outbound
    ##
    def toggleSelected(self, sColor):
        if self.selected:
            self.activeBorderColor = self.bordercolor
        else:
            self.activeBorderColor = sColor
        # toggle line selection
        for e in self.edges:
            e.toggleSelected(self.activeBorderColor)
        self.selected = not self.selected
    ##
    def setColor(self, color):
        for edge in self.edges:
            edge.color = color
            edge.setColor(color)
    def __contains__(self, p):
        ''' 
        Check if a point lies inside a polygon.
        Scans a horizontal line from the topleft[0] to the point.
        If the number of edges it crosses is 
        odd, the point is inside.
        '''
        tl = self.topleft
        r = self.radius

        if not self.pointInRect(p):
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

    def draw(self, sc):
        for edge in self.edges:
            edge.draw(sc)
    ##
    def save(self):
        d = {}
        d['topleft'] = self.topleft
        d['radius'] = self.radius
        d['n'] = self.n
        d['fillcolor'] = self.fillcolor
        d['bordercolor'] = self.bordercolor
        d['borderwidth'] = self.borderwidth

        return 'POLYGON'.ljust(10) + pickle.dumps(d)

##
