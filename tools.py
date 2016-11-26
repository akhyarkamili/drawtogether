# Akhyar I. Kamili
# akamili@andrew.cmu.edu
#
# This module contains functions which transform
# drag and drop motions into drawing shapes

from shapes import *
import helper
import pygame

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
GREY = (175, 175, 175)
RED = pygame.Color(255, 0, 0)

def drawCircle(start, end, fillcolor, bordercolor, borderwidth, temp=None, n=0):
	pass
def drawLine(start, end, fillcolor, bordercolor, borderwidth, temp=None, n=0):
	if not temp:
		return Line(start, end, bordercolor)
	temp.change(start, end)

def drawPath(start, end, fillcolor, bordercolor, borderwidth, temp=None, n=0):
	pass
def drawPolygon(start, end, fillcolor, bordercolor, borderwidth, temp=None, n=0):
	end, start = helper.adjust(end, start)
	rad = (end[0]-start[0])/2
	if not temp:
		return Polygon(list(start), rad, n)
	temp.resize(list(start), end)

def fill():
	pass
def transform():
	pass
def selectArea(objects, area, selection):
	# selection is always emptied before selecting an area
	for obj in objects:
		if obj.inbound(area):
			# object is within bounds
			# toggle and add to selection
			obj.toggleSelected()
			selection.append(obj)

