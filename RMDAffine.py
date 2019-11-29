"""
    Scratch sheet for Calculating Skew Corrections in Gcode

    Written By Chad A. Woitas for RMD Engineering
    November 2019
"""

import math as mt
import statistics as stat
from matplotlib import pyplot as plt
from typing import List, Any, Union

from matplotlib import pyplot as plt
import time

# Globals
MINLINELIMIT = 0.25
ERRORMIN = 0.0001


# Functions to keep our code clean
class Point:
    def __init__(self,x,y):
        self.x = x
        self.y = y

    def __str__(self):
        return "({},{})".format(self.x, self.y)

    def distanceTo(self, p):
        x2 = mt.pow((self.x - p.x), 2)
        y2 = mt.pow((self.y - p.y), 2)
        return mt.sqrt(x2 + y2)


class Line:
    def __init__(self, p1, p2):
        self.st = p1
        self.en = p2
    
    def __str__(self):
        return "[{},{}]".format(self.st, self.en)

    def split(self):
        xMid = (self.st.x + self.en.x) / 2
        yMid = (self.st.y + self.en.y) / 2
        l1 = Line(self.st, Point(xMid, yMid))
        l2 = Line(Point(xMid, yMid), self.en)
        return l1, l2

    def length(self):
        return self.st.distanceTo(self.en)


# Functions for skewing
def MarkCoefficients(desired, actual):
    """:returns list of Coefficients from the marks"""
    shear_co: List[Point] = []
    for item in range(len(desired)):
        hx = desired[item].x - actual[item].x
        hy = desired[item].y - actual[item].y
        shear_co.append(Point(hx, hy))

    return shear_co


def LineCoefficients(ln, desired):
    """:returns a list of coefficients from line to the mark"""
    line_co_e: List[float] = []
    line_co_s: List[float] = []
    for item in range(len(desired)):
        coeff = ln.en.distanceTo(desired[item])
        line_co_e.append(coeff)
        coeff = ln.st.distanceTo(desired[item])
        line_co_s.append(coeff)
    AVG = stat.median(line_co_e)
    mx = max(line_co_e)
    line_co_s = [mx - xi/ AVG for xi in line_co_s]
    AVG = stat.median(line_co_s)
    mx = max(line_co_s)
    line_co_e = [mx - xi / AVG for xi in line_co_e]
    return line_co_s, line_co_e


def affine(pt, mco, lco):
    """:returns a point shifted by Shear affine matrix"""
    return Point(pt.x + mco.x*lco, pt.y + mco.y*lco)


def skewLine(line, mcoL, lco_s, lco_e):
    """
    :param line: Line Object
    :param mcoL: Mark Coeffiecients
    :param lco_s: Line Start Point Coefficients
    :param lco_e: Line End Point Coefficients 
    :returns a line skewed by all marks"""
    starts = []
    ends = []
    for item in range(len(mcoL)):
        # Get the skew from each mark
        starts.append(affine(line.st, mcoL[item], lco_s[item]))
        ends.append(affine(line.en, mcoL[item], lco_e[item]))
    xaveS = 0
    yaveS = 0
    xaveE = 0
    yaveE = 0
    for item in starts:
        # average the total skew
        xaveS = xaveS + item.x
        yaveS = yaveS + item.y
    xaveS = xaveS/len(starts)
    yaveS = yaveS/len(starts)
    for item in ends:
        # average the total skew
        xaveE = xaveE + item.x
        yaveE = yaveE + item.y
    xaveE = xaveE/len(ends)
    yaveE = yaveE/len(ends)
    return Line(Point(xaveS,yaveS), Point(xaveE, yaveE))


def skewList(lines, markco, desired):
    """
    :rtype: List[Line]
    :param lines: List of lines to Skew
    :param markco: list of Mark Coordinates
    :param desired: list of Desired points
    :return: list of skewed lines
    """
    out: List[Line] = []
    for line in lines:
        lcs, lce = LineCoefficients(line, desired)
        out.append(skewLine(line, markco, lcs, lce))
    return out


# MAIN TESTING

# GLOBALS COMING FROM SOMEWHERE ELSE EVENTUALLY
# Desired
dp = [Point(1, 1), Point(4, 1), Point(4, 4), Point(40, 4)]
# Actual
ap = [Point(1.5, 1), Point(4, 1), Point(4, 4), Point(39.5, 4)]

# Create Variables
xs = [10, 20, 30, 20, 20, 30, 20, 10]
ys = [10, 20, 10, 20, 30, 20, 30, 20]
pts = []
lns = []
for i in range(len(xs)):
    pts.append(Point(xs[i], ys[i]))
for i in range(len(pts)-1):
    lns.append(Line(pts[i], pts[i+1]))

mc = MarkCoefficients(dp, ap)
for i in mc:
    print(i)
# Test Functions
skewed = skewList(lns, mc, dp)


# Plot Data

for i in lns:
    plt.plot([i.st.x, i.en.x], [i.st.y, i.en.y], "r")

for i in skewed:
    plt.plot([i.st.x, i.en.x], [i.st.y, i.en.y], "g--")


plt.show()

