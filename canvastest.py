import pygame
import sys
import math

# constants

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
GREY = (175, 175, 175)

class ScreenObject:
    ID = 0
class Line(ScreenObject):
    def __init__(self, start, end, color):
        self.id = ScreenObject.ID 
        self.start = start
        self.end = end
        self.endpoints = start, end
        self.color = color

        self.setColor(self.color)
        
        self.computePoints()

        ScreenObject.ID += 1

    def displace(self, disp_x, disp_y):
        self.start = self.start[0] + disp_x, self.start[1] + disp_y
        self.end = self.end[0] + disp_x, self.end[1] + disp_y

        self.computePoints()

    def setColor(self,color):
        self.activeColor = color
    def setSelected(self, selected):
        if selected:
            self.activeColor = GREY
        else:
            self.activeColor = self.color
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

    def __eq__(self, other):
        if isinstance(other, Line):
            return other.start == self.start and other.end == self.end

    def __contains__(self, point):
        return point in self.points


def cls(sc):
    sc.fill(WHITE)

def drawScreen(sc, obj):
    cls(sc)
    for path in obj['paths']:
        drawLine(sc, path)

    pygame.display.flip()

def drawLine(sc, l):
    for p in l.points:
        sc.set_at(p, l.activeColor)
# init pygame
pygame.init()

screen_width = 700
screen_height = 400
screen = pygame.display.set_mode([screen_width, screen_height])
screen.fill(WHITE)

clock = pygame.time.Clock()
mousedown = False

screenObjects = {'paths':[], 'shapes':[]}
state = 'draw'
selection = []

while True:
    clock.tick(30)
    # check for events
    
    drawScreen(screen, screenObjects)


    # if the mouse is currently down    
    if state == 'draw':    
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONUP:
                print "start:", start, "end:", end
                line = Line(start, end, BLACK)
                screenObjects['paths'].append(line)
                mousedown = False

                start, end = 0, 0
                drawScreen(screen, screenObjects)
                state = 'selection'
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mousedown = True
                start = pygame.mouse.get_pos()


        if mousedown:
            end = pygame.mouse.get_pos()
            pygame.draw.line(screen, BLACK, start, end)
            pygame.display.flip()

    elif state == 'move':
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # find line to move
                mousedown = True
                init_pos = pygame.mouse.get_pos()
                thisline = None
                print selection
                if not selection:
                    # attempt to select one object
                    for line in screenObjects['paths']:
                        # check around the radius
                        for i in range(4):
                            for j in range(4):
                                if (init_pos[0]+i, init_pos[1]+j) in line:
                                    thisline = line
                    if thisline:
                        selection.append(thisline)
                        thisline.setSelected(True)

                last_pos = init_pos

            elif event.type == pygame.MOUSEBUTTONUP:
                # finished moving
                mousedown = False
                if selection:
                    for line in selection:
                        line.setSelected(False)
                state = 'draw'

        if mousedown:
            current_pos = pygame.mouse.get_pos()
            displacement = current_pos[0]-last_pos[0], current_pos[1] - last_pos[1]
            if selection:
                for line in selection:
                    line.displace(*displacement)
            last_pos = current_pos

    elif state == 'selection':
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # clear previous selection
                for i in selection:
                    i.setSelected(False)
                selection = []

                # selection started
                start_pos = pygame.mouse.get_pos()
                mousedown = True
            elif event.type == pygame.MOUSEBUTTONUP:
                # finished moving

                mousedown = False
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

                selection_area = pygame.Rect(start_pos, (abs(width), abs(height)))

                selection = []
                # check selected path
                for line in screenObjects['paths']:
                    print selection_area
                    print selection_area.collidepoint(line.start)
                    if selection_area.collidepoint(line.start) and selection_area.collidepoint(line.end):
                        line.setSelected(True)
                        selection.append(line)

                # check selected shapes
                pass
                for scobject in selection:
                    scobject.setSelected(True)
                state = 'move'

        if mousedown:
            end_pos = pygame.mouse.get_pos()
            width = end_pos[0] - start_pos[0]
            height = end_pos[1] - start_pos[1]

            pygame.draw.line(screen, BLACK, start_pos, (start_pos[0], start_pos[1]+height))
            pygame.draw.line(screen, BLACK, start_pos, (start_pos[0]+width, start_pos[1]))
            pygame.draw.line(screen, BLACK, (start_pos[0]+width, start_pos[1]), 
                                            (start_pos[0]+width, start_pos[1]+height))
            pygame.draw.line(screen, BLACK, (start_pos[0], start_pos[1]+height), 
                                            (start_pos[0]+width, start_pos[1]+height))
            pygame.display.flip()



