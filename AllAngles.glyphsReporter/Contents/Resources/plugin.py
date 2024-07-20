# encoding: utf-8
from __future__ import division, print_function, unicode_literals

###########################################################################################################
#
# AllAngles Reporter Plugin
#
# This reporter shows the angle from the horizontal of all straight lines in the active
# layer in the Glyphs edit view. This includes straight line segments, and the handles of
# of curves. Angles are given to .1 degree of precision. All indicators can be toggled
# on and off in the context menu, while the reporter is active.
#
#   Developed by Nic Schumann for Occupant Fonts.
#   Copyright 2020, Occupant Fonts
#
###########################################################################################################

from math import atan2, sqrt, pi, degrees, cos, sin
import objc
from Cocoa import NSColor, NSPoint, NSBezierPath, NSBundle
from GlyphsApp import Glyphs, GSFont
from GlyphsApp.plugins import ReporterPlugin

# =======
# Constants:
#  - Colors to use when rendering line and handle indicators.
#  - Number of significant digits beyond the decimal to account for
#    When printing angles.
# =======

LINE_COLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(56 / 256, 217 / 256, 137 / 256, 1)
HANDLE_COLOR = NSColor.colorWithCalibratedRed_green_blue_alpha_(217 / 256, 56 / 256, 107 / 256, 1)
PRECISION = 1


# =======
# Mini 2d vector manipulation library. All methods take vectors 2d vectors
# as a list of components, and return components (or angles in degrees).
# =======
def get_unit_vector(x, y):
	"""Given 2d vector components x and y as floats,
	returns the unit vector in the same direction
	as the given vector (x, y).
	"""
	length = sqrt(x**2 + y**2)
	return x / length, y / length


def get_vector_angle(x, y):
	"""Given 2d vector components x and y as floats,
	returns the degrees from the horizontal of that vector.
	The return value is clamped into the range [0, 180), so that
	angles in the bottom two quadrants of the unit circle are
	translated into the top two.

	example: an angle of 240 degrees is clamped to 60 degrees.
	"""
	x_norm, y_norm = get_unit_vector(x, y)
	return degrees(atan2(x_norm, y_norm)) % 180


def get_rotated_vector(x, y, angle=3 * pi / 2):
	"""Given 2d vector components x and y as floats,
	rotate that vector by "angle" degrees, and return
	the components of the rotated vector.
	"""
	return cos(angle) * x - sin(angle) * y, sin(angle) * x + cos(angle) * y


def get_intermediate_from_points(x1, y1, x2, y2, t=0.5):
	"""Given a line defined by two vectors as component floats,
	return a point interpolated along the line between the two vectors,
	as given by a parameter "t".
	"""
	return t * (x2 - x1) + x1, t * (y2 - y1) + y1


def determine_quadrant(x1, y1, x2, y2):
	# Calculate the differences
	dx = x2 - x1
	dy = y2 - y1

	# Calculate the angle in degrees
	angle = atan2(dy, dx) * 180 / pi
	angle += 90
	# Normalize the angle to [0, 360)
	if angle < 0:
		angle += 360

	# Determine the quadrant
	if angle >= 337.5 or angle < 22.5:
		return "right"
	elif angle >= 22.5 and angle < 67.5:
		return "topright"
	elif angle >= 67.5 and angle < 112.5:
		return "topcenter"
	elif angle >= 112.5 and angle < 157.5:
		return "topleft"
	elif angle >= 157.5 and angle < 202.5:
		return "left"
	elif angle >= 202.5 and angle < 247.5:
		return "bottomleft"
	elif angle >= 247.5 and angle < 292.5:
		return "bottomcenter"
	else:
		return "bottomright"


bundle = NSBundle.bundleForClass_(GSFont)
objc.loadBundleFunctions(bundle, globals(), [("GSFloatToStringWithPrecisionLocalized", b'@di')])

Glyphs.registerDefault("AllAnglesShowLineAngles", True)


# =======
# Reporter Plugin Class.
# All UI and User-dependent state is managed in this class.
# =======
class AllAngles(ReporterPlugin):

	@objc.python_method
	def settings(self):
		"""Registers basic settings and default context menus.
		"""
		self.menuName = Glyphs.localize({'en': 'All Angles'})
		self.update_context_menu()

	@objc.python_method
	def update_context_menu(self):
		self.generalContextMenus = [
			{'name': Glyphs.localize({'en': 'Show Line Angles'}), 'action': self.toggleLines, 'state': self.show_lines},
			{'name': Glyphs.localize({'en': 'Show Handle Angles'}), 'action': self.toggleHandles, 'state': self.show_handles}
		]

	@objc.python_method
	def refresh_view(self):
		"""The refresh view function forces a repaint of the EditView,
		even the user has not interacted. useful for updating views based on
		settings changes or external events.
		"""
		try:
			current_tab_view = Glyphs.font.currentTab
			if current_tab_view:
				current_tab_view.redraw()
		except:
			pass

	@objc.python_method
	def foreground(self, layer):
		"""Called whenever the Editview is updated through a UI interaction.
		Receives the active layer as a parameter. This method is responsible for
		drawing the angles on lines and handles, given the current visibility of
		line indicators and handle indicators.
		"""
		show_lines = self.show_lines
		show_handles = self.show_handles
		for path in layer.paths:
			for segment in path.segments:
				if len(segment) == 2 and show_lines:
					self.render_indicator_for_line(segment[0], segment[1], draw_color=LINE_COLOR)
				elif len(segment) == 4 and show_handles:
					self.render_indicator_for_line(segment[0], segment[1], draw_color=HANDLE_COLOR)
					self.render_indicator_for_line(segment[2], segment[3], draw_color=HANDLE_COLOR)

	@objc.python_method
	def render_indicator_for_line(self, p1, p2, draw_color=LINE_COLOR):
		"""Given a segment from glyphs (a list of two NSPoints), draw an indicator
		showing the angle of that segment with respect to the horizontal in the given "draw_color".
		"""
		# 1.0 Get the angle from the segment
		x1, y1 = p1.x, p1.y
		x2, y2 = p2.x, p2.y

		dx, dy = x2 - x1, y2 - y1
		theta = get_vector_angle(dx, dy)

		# 1.1 Prettyprint the Angle with the degree sign,
		# to the desired precision
		pretty_angle = GSFloatToStringWithPrecisionLocalized(theta, PRECISION) + "°"

		# 2.0 Generate the off-curve endpoint of the indicator pointing from the
		# Angle to the curve it describes.
		offset_scale = 14 / self.getScale()
		x_mid, y_mid = get_intermediate_from_points(x1, y1, x2, y2)
		x_norm, y_norm = get_unit_vector(x2 - x1, y2 - y1)
		x_orth, y_orth = get_rotated_vector(x_norm, y_norm)
		x_mid_offset, y_mid_offset = x_mid + offset_scale * x_orth, y_mid + offset_scale * y_orth

		# 3.0 Generate the anchor for the text so that it's positioned more or less
		# Appropriately relative to the indicator line.
		align = determine_quadrant(x1, y1, x2, y2)

		# 4.0 Draw everything to the canvas.
		draw_color.set()
		self.draw_indicator((x_mid, y_mid), (x_mid_offset, y_mid_offset))
		self.drawTextAtPoint(pretty_angle, NSPoint(x_mid_offset, y_mid_offset), fontColor=draw_color, align=align)

	def toggleLines(self):
		"""Toggles whether or not to show line angles in the canvas. Also
		refreshes the name of the menu item so that it makes sense.

		TODO: This does not immediately refresh the view, only when the view
		is interacted with. Can we fix this?
		"""
		self.show_lines = not self.show_lines
		self.refresh_view()
		self.update_context_menu()

	def toggleHandles(self):
		"""Toggles whether or not to show handle angles in the canvas. Also
		refreshes the name of the menu item so that it makes sense.

		TODO: This does not immediately refresh the view, only when the view
		is interacted with. Can we fix this?
		"""
		self.show_handles = not self.show_handles
		self.refresh_view()
		self.update_context_menu()

	@property
	def show_lines(self):
		return Glyphs.boolDefaults["AllAnglesShowLineAngles"]

	@show_lines.setter
	def show_lines(self, value):
		Glyphs.boolDefaults["AllAnglesShowLineAngles"] = value

	@property
	def show_handles(self):
		return Glyphs.boolDefaults["AllAnglesShowHandleAngles"]

	@show_handles.setter
	def show_handles(self, value):
		Glyphs.boolDefaults["AllAnglesShowHandleAngles"] = value

	@objc.python_method
	def draw_indicator(self, start, end):
		"""Given a starting point and and ending point as a list of floats,
		Draws a line to the canvas from start to end.
		"""
		linePath = NSBezierPath.bezierPath()
		linePath.moveToPoint_(start)
		linePath.lineToPoint_(end)
		linePath.setLineWidth_(0.8 / self.getScale())
		linePath.stroke()

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
