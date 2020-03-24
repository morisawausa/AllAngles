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

LINE_COLOR=(56/256, 217/256, 137/256, 1)
QUAD_COLOR=(217/256, 56/256, 107/256, 1)

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

	show_lines = True
	show_quads = False

	@objc.python_method
	def settings(self):
		self.menuName = Glyphs.localize({'en': u'All Angles'})
		self.generalContextMenus = [
			{'name': Glyphs.localize({'en': 'Hide Line Angles '}), 'action': self.toggle_lines},
			{'name': Glyphs.localize({'en': 'Show Handle Angles'}), 'action': self.toggle_quads}
		]

	@objc.python_method
	def foreground(self, layer):
		for path in layer.paths:
			for segment in path.segments:
				if len(segment) == 2 and self.show_lines:
					self.render_indicator_for_line_segment(segment, draw_color=LINE_COLOR)
				elif len(segment) == 4 and self.show_quads:
					p1, p2, p3, p4 = segment
					quad_segment_1 = (p1, p2)
					quad_segment_2 = (p3, p4)
					self.render_indicator_for_line_segment(quad_segment_1, draw_color=QUAD_COLOR)
					self.render_indicator_for_line_segment(quad_segment_2, draw_color=QUAD_COLOR)


	def render_indicator_for_line_segment(self, segment, draw_color=LINE_COLOR):
		x1, y1, x2, y2 = get_points_from_line(segment)
		angle = get_angle_from_points(x1, y1, x2, y2)
		prettyAngle = u"%s°" % str(round(angle, 1))

		offset_scale = 14/self.getScale()
		x_mid, y_mid = get_intermediate_from_points(x1, y1, x2, y2)
		x_norm, y_norm = get_normed_vector(x2 - x1, y2 - y1)
		x_orth, y_orth = get_rotated_vector(x_norm, y_norm)
		x_mid_offset, y_mid_offset = x_mid+offset_scale*x_orth, y_mid+offset_scale*y_orth

		color = NSColor.colorWithCalibratedRed_green_blue_alpha_(*draw_color)

		x_text_anchor, y_text_anchor = self.get_text_anchor(prettyAngle, x_mid, y_mid, x_mid_offset, y_mid_offset)

		color.set()
		self.draw_indicator((x_mid, y_mid), (x_mid_offset, y_mid_offset))
		self.drawTextAtPoint(prettyAngle, NSPoint(x_text_anchor, y_text_anchor), fontColor=color )


	@objc.python_method
	def toggle_lines(self):
		self.show_lines = not self.show_lines
		menuName = 'Hide Line Angles' if self.show_lines else 'Show Line Angles'
		self.generalContextMenus[0] = {'name': Glyphs.localize({'en': menuName}), 'action': self.toggle_lines}


	@objc.python_method
	def toggle_quads(self):
		self.show_quads = not self.show_quads
		menuName = 'Hide Handle Angles' if self.show_quads else 'Show Handle Angles'
		self.generalContextMenus[1] = {'name': Glyphs.localize({'en': menuName}), 'action': self.toggle_lines}


	@objc.python_method
	def draw_indicator(self, start, end):
		linePath = NSBezierPath.bezierPath()
		linePath.moveToPoint_(start)
		linePath.lineToPoint_(end)
		linePath.setLineWidth_(1/self.getScale())
		linePath.stroke()


	@objc.python_method
	def get_text_anchor(self, text, x1, y1, x2, y2):

		CHARWIDTH=6 # Magic number for approximating the width of a drawn character
		CHARHEIGHT=12 # Magic number for approximating the height of a drawn character

		o_x = len(text)/self.getScale()
		o_y = 1/self.getScale()
		buffer = 8/self.getScale()

		x_anchor, y_anchor = x2, y2


		if x2 < x1:
			x_anchor -= CHARWIDTH * o_x
		elif x2 == x1:
			x_anchor -= CHARWIDTH * o_x / 3
			y_anchor += buffer if y2 > y1 else -buffer*0.8
		# else:
		# 	x_anchor = x_anchor  # + CHARWIDTH * o_x / 2

		if y2 < y1:
			y_anchor -= CHARHEIGHT * o_y
		elif y2 == y1:
			y_anchor -= (CHARHEIGHT/2) * o_y
			x_anchor += buffer if x2 > x1 else -buffer
		else:
			y_anchor -= (CHARHEIGHT/2) * o_y

		return x_anchor, y_anchor

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
