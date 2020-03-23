# encoding: utf-8

###########################################################################################################
#
#
#	Reporter Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Reporter
#
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals
from math import atan2, sqrt, pi, degrees, cos, sin
import objc
from AppKit import NSColor
from GlyphsApp import *
from GlyphsApp.plugins import *

def get_normed_vector(x, y):
	length = sqrt(x**2 + y**2)
	return x / length, y / length


def get_angle_from_points(x1, y1, x2, y2):
	dX, dY = x2 - x1, y2 - y1

	dX_norm, dY_norm = get_normed_vector(dX, dY)

	return degrees(atan2(dY_norm, dX_norm)) % 180

def get_rotated_vector(x, y, angle=3*pi/2):
	return cos(angle)*x - sin(angle)*y, sin(angle)*x + cos(angle)*y


def get_intermediate_from_points(x1, y1, x2, y2, t=0.5):
	return t * (x2 - x1) + x1, t * (y2 - y1) + y1

def get_points_from_line(segment):
	start, end = segment
	return start.x, start.y, end.x, end.y

class AllAngles(ReporterPlugin):

	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({'en': u'All Angles'})
		self.generalContextMenus = [
			{'name': Glyphs.localize({'en': u'Show angles for all straight line segments on the layer.', 'de': u'Tu etwas'}) },
		]

	@objc.python_method
	def foreground(self, layer):
		for path in layer.paths:
			for segment in filter(lambda s: len(s) == 2 , path.segments):
				x1, y1, x2, y2 = get_points_from_line(segment)
				angle = get_angle_from_points(x1, y1, x2, y2)
				prettyAngle = u"%s°" % str(round(angle, 1))

				offset_scale = 4
				x_mid, y_mid = get_intermediate_from_points(x1, y1, x2, y2)
				x_norm, y_norm = get_normed_vector(x2 - x1, y2 - y1)
				x_orth, y_orth = get_rotated_vector(x_norm, y_norm)
				x_mid_offset, y_mid_offset = x_mid+offset_scale*x_orth, y_mid+offset_scale*y_orth

				color = NSColor.colorWithCalibratedRed_green_blue_alpha_( 52/256, 235/256, 203/256, 1 )

				color.set()
				self.draw_indicator((x_mid, y_mid), (x_mid_offset, y_mid_offset))
				self.drawTextAtPoint(prettyAngle, NSPoint(x_mid_offset, y_mid_offset), fontColor=color )

	@objc.python_method
	def draw_indicator(self, start, end):
		linePath = NSBezierPath.bezierPath()
		linePath.moveToPoint_(start)
		linePath.lineToPoint_(end)
		linePath.setLineWidth_(1/self.getScale())
		linePath.stroke()





	# @objc.python_method
	# def inactiveLayer(self, layer):
	# 	NSColor.redColor().set()
	# 	if layer.paths:
	# 		layer.bezierPath.fill()
	# 	if layer.components:
	# 		for component in layer.components:
	# 			component.bezierPath.fill()

	# @objc.python_method
	# def preview(self, layer):
	# 	NSColor.blueColor().set()
	# 	if layer.paths:
	# 		layer.bezierPath.fill()
	# 	if layer.components:
	# 		for component in layer.components:
	# 			component.bezierPath.fill()

	# @objc.python_method
	# def conditionalContextMenus(self):
	#
	# 	# Empty list of context menu items
	# 	contextMenus = []
	#
	# 	# Execute only if layers are actually selected
	# 	if Glyphs.font.selectedLayers:
	# 		layer = Glyphs.font.selectedLayers[0]
	#
	# 		# Exactly one object is selected and it’s an anchor
	# 		if len(layer.selection) == 1 and type(layer.selection[0]) == GSAnchor:
	#
	# 			# Add context menu item
	# 			contextMenus.append({'name': Glyphs.localize({'en': u'Do something else', 'de': u'Tu etwas anderes'}), 'action': self.doSomethingElse})
	#
	# 	# Return list of context menu items
	# 	return contextMenus

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
