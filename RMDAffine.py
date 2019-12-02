"""
    Scratch sheet for Calculating Skew Corrections in Gcode

    Written By Chad A. Woitas for RMD Engineering
    November 2019
"""

import math as mt
import statistics as stat
from matplotlib import pyplot as plt
from typing import List, Any, Union
from copy import deepcopy
import random

from matplotlib import pyplot as plt
import time

# Globals
MINLINELIMIT = 1
ERRORMIN = 0.0001


# Functions to keep our code clean
class Point:
    def __init__(self,x,y):
        self.x = x
        self.y = y

    def __str__(self):
        return "({},{})".format(self.x, self.y)

    def __repr__(self):
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

    def __repr__(self):
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
# Coefficients +++++++++++++++++++++++++++
def MarkCoefficients(desired, actual):
    """:returns list of Coefficients from the marks"""
    shear_co: List[Point] = []
    for item in range(len(desired)):
        hx = desired[item].x - actual[item].x
        hy = desired[item].y - actual[item].y
        shear_co.append(Point(hx, hy))

    return shear_co


def LineCoefficients(ln, desired):
    """:returns a list of coefficients from line endpoints to the mark"""
    # CONSTANT COEFF
    avgCoeff = 1
    distCoeff = 0.75

    # List of Coefficients for start and end point
    line_co_e: List[float] = []
    line_co_s: List[float] = []
    for item in desired:
        d = ln.en.distanceTo(item)
        if d == 0:
            coeff = 1
        else:
            coeff = distCoeff/(d+0.001)  # Divide by zero handling
        line_co_e.append(coeff)
        d = ln.st.distanceTo(item)
        if d == 0:
            coeff = 1
        else:
            coeff = distCoeff/(d+0.001)
        line_co_s.append(coeff)
    # AVG = stat.median(line_co_e)
    mx = max(line_co_e)
    line_co_s = [xi/mx for xi in line_co_s]
    # AVG = stat.median(line_co_s)
    mx = max(line_co_s)
    line_co_e = [xi/mx for xi in line_co_e]
    return line_co_s, line_co_e


# Point Functions ++++++++++++++++++++++++
def affine(pt, mco, lco):
    """:returns a point shifted by Shear affine matrix"""
    return Point(pt.x + mco.x*lco, pt.y + mco.y*lco)


# Single Line Functions ++++++++++++++++++
def skewLine(line, mcoL, lco_s, lco_e):
    """
    :param line: Line Object
    :param mcoL: Mark Coefficients
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
    return Line(Point(xaveS, yaveS), Point(xaveE, yaveE))


def segmentLine(line):
    """
    :param line: Line object
    :return: List of Line segments
    """
    # Number of times to segment line
    numSplits = int(line.length() / MINLINELIMIT)
    # Only need to split it once for two lines
    numSplits = int(numSplits / 2 + 1)
    # Start the list with one line
    toSplit = [line]
    out = [line]
    while numSplits > 0:
        # Split each line and remove it
        toSplit = deepcopy(out)
        out = []
        for ln in toSplit:
            l1, l2 = ln.split()

            out.append(l1)
            out.append(l2)
        numSplits = numSplits - 1
    return out


# Group Functions
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
        leng = line.length()
        if leng >= MINLINELIMIT:
            segs = segmentLine(line)
            middleOut = skewList(segs, markco, desired)
            for i2 in range(len(middleOut)-1):
                smoothLine(middleOut[i2], middleOut[i2+1])
            for x in middleOut:
                out.append(x)
        else:
            lcs, lce = LineCoefficients(line, desired)
            out.append(skewLine(line, markco, lcs, lce))
    return out


def smoothLine(l1, l2):
    """
    :param l1: Line with an Endpoint X% away from L2 Start Point
    :param l2: line with a Start point X% away from L1 End Point
    :return: Lines with an averaged point between them
    """
    xAve = (l2.st.x + l2.st.x) / 2
    yAve = (l2.st.y + l2.st.y) / 2
    l1.en = Point(xAve, yAve)
    l2.st = Point(xAve, yAve)
    return l1, l2


# MAIN TESTING

# GLOBALS COMING FROM SOMEWHERE ELSE EVENTUALLY
numPoints = 10
dp = []  # Desired Points
ap = []  # Actual points
for i in range(numPoints):
    x = random.randint(1, 40)
    y = random.randint(1, 40)
    dp.append(Point(x, y))
    ap.append(Point(x + random.randint(-5, 5)/5, y + random.randint(-5, 5)/5))

# dp = [Point(1, 1),  Point(32, 20), Point(10, 30), Point(40, 4)]
# # Actual
# ap = [Point(1, 1), Point(31, 20), Point(11, 30), Point(39, 4)]

# Create Variables (Fake Gcode)
xs = [10, 20, 30, 20, 20, 30, 20, 10]
ys = [10, 20, 10, 20, 30, 20, 30, 20]
pts = []
lns = []

# Change Gcode into out data structures
for i in range(len(xs)):
    pts.append(Point(xs[i], ys[i]))
for i in range(len(pts)-1):
    lns.append(Line(pts[i], pts[i+1]))

# Calculate Offsets from mark registration
mc = MarkCoefficients(dp, ap)
for i in mc:
    print(i)
# Test Functions
t = time.time()
skewed = skewList(deepcopy(lns), mc, dp)
print(time.time() - t, "for", len(skewed), "Data points. Started with", len(lns))
for x in skewed:
    print(x)

# Plot Data

for i in lns:
    plt.plot([i.st.x, i.en.x], [i.st.y, i.en.y], "r")

for i in skewed:
    plt.plot([i.st.x, i.en.x], [i.st.y, i.en.y], "g--")

for p in ap:
    plt.plot(p.x, p.y, "ro")
for p in dp:
    plt.plot(p.x, p.y, "go")

plt.text(1, 1, "Green - Desired/Output \n Red - Actual/input")
plt.show()

