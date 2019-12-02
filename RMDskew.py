"""
    Scratch sheet for Calculating Skew Corrections in Gcode

    Written By Chad A. Woitas for RMD Engineering
    November 2019
"""
import math as mt
from matplotlib import pyplot as plt
import time

# Constants that will eventually come from registration marks
line = [(0, 0), (10, 10)]
MA = (5, 5.125)     # Desired Point
ME = (5, 5)  # Measured Point

desiredPoints = [(1.125, 1), (4.125, 1), (1.0625, 4), (4, 4)]
actualPoints =  [(1, 1), (4, 1), (1, 4), (4, 4)]


# Constants for Skew
X = 0
Y = 1
MINLINELIMIT = 0.25
ERRORMIN = 0.0001

DEBUGGING = False

# Functions for calculating
class Skew():
    def point2PointDistance(self, p1, p2):
        """Returns the absolute distance between two points"""
        return mt.sqrt(mt.pow((p2[X]-p1[X]), 2) + mt.pow((p2[Y]-p1[Y]), 2))

    def splitLine(self, l):
        """Returns two segments of equal length from the input"""
        xMid = (l[0][X] + l[1][X])/2
        yMid = (l[0][Y] + l[1][Y])/2
        line1 = [l[0], (xMid, yMid)]
        line2 = [(xMid, yMid), l[1]]
        return line1, line2

    def joinLine(self, l1, l2):
        return [l1[0], l2[1]]

    def detectErrors(self, line, ma, me):
        out = []
        toCompute = [line]
        avgdistance = 0.0
        avgCount=0
        for l in toCompute:
            r1a = self.point2PointDistance(l[0], ma)
            r1e = self.point2PointDistance(l[0], me)
            r2a = self.point2PointDistance(l[1], ma)
            r2e = self.point2PointDistance(l[1], me)

            avgdistance = avgdistance + r2a
            avgCount = avgCount + 1
            if (r2e-r2a) - (r1e-r1a) > ERRORMIN:
                if self.point2PointDistance(l[0], l[1]) > MINLINELIMIT:
                    l1, l2 = self.splitLine(l)
                    toCompute.append(l1)
                    toCompute.append(l2)
                else:
                    out.append([l, r2e-r2a])
            else:
                # Don't fix what aint broke
                out.append([l, 0])

        return out

    # Not currently used
    def pointCompass(self, p1, p2):
        """Returns quadrant of p2 with respect to p1"""
        if p1[X] > p2[X]:
            if p1[Y] > p2[Y]:
                return 3
            elif p1[Y] < p2[Y]:
                return 2
            else:
                return "Y-"
        elif p1[X] < p2[X]:
            if p1[Y] > p2[Y]:
                return 4
            elif p1[Y] < p2[Y]:
                return 1
            else:
                return "Y+"
        elif p1[X] == p2[X]:
            if p1[Y] > p2[Y]:
                return "X-"
            elif p1[Y] < p2[Y]:
                return "X+"
            else:
                return 0

    def openGCode(self):
        gcode = []
        try:
            f = open('bob.ngc', 'r')
            lines = f.readlines()
            for l in lines:
                gcode.append(l)
            f.close()
        except OSError:
            pass
        out = []
        for l in gcode:
            l = l.replace("\n", "")
            l = l.replace("\r", "")
            l = l.replace(" ",  "")
            if l.startswith('G'):
                l = l.replace("G0", "")
                l = l.replace("G1", "")
                l = l.replace("G2", "")
                l = l.replace("G3", "")
            if l.count('X')==1:
                if l.count('Y')==1:
                    l = l.replace('X', "(")
                    l = l.replace('Y', ",")
                    if l.count('Z')>0:
                        l, trash = l.split('Z')
                    if l.count('F')>0:
                        l, trash = l.split('F')
            else:
                l = "(" + l
            l = l+")"
            out.append(eval(l))
        return out

    def parseGArc(self, prevPos, gString):
        gString = gString.replace('G', '')
        gString = gString.replace(' ', '')
        if gString.startsWith('2'):
            gString = gString.replace('2', '')
            Xstart, Ystart = prevPos
            iOff = gString.find('I')
            jOff = gString.find('J')
            Center = (Xstart + iOff, Ystart + jOff)
            radius = self.point2PointDistance(prevPos, Center)
        elif gString.startsWith('3'):
            gString = gString.replace('2', '')
            Xstart, Ystart = prevPos
            iOff = gString.find('I')
            jOff = gString.find('J')
            Center = (Xstart + iOff, Ystart + jOff)
            radius = self.point2PointDistance(prevPos, Center)
        else:
            return -1

    def correctErrors(self, inp, me):
        """Returns a list of skewed points"""
        # [[(xi,yi),(xf,yf)], corrected value]
        # Handle End point
        out = []
        endp = inp[0][0][0]
        d1 = self.point2PointDistance(endp, me)
        d2 = inp[0][1] / d1
        endpX = endp[X] + d2 * (me[X] - endp[X])
        endpY = endp[Y] + d2 * (me[Y] - endp[Y])
        out.append((endpX,endpY))
        for i in inp:
            l = i[0]
            d1 = self.point2PointDistance(l[1], me)
            d2 = i[1] / d1
            newXf = l[1][X] + d2 * (me[X] - l[1][X])
            newYf = l[1][Y] + d2 * (me[Y] - l[1][Y])
            out.append((newXf, newYf))

        return out


""" BEGIN MAIN """

# Declare Variables
s = Skew()
g = s.openGCode()

# Plotting functions
plt.style.use('dark_background')
plt.subplot(221)
t = time.time()
fixG = []
fixG1 = []
fixG2 = []
fixG3 = []
for ind in range(len(g)-1):
    p1 = g[ind]
    p2 = g[ind+1]
    error = s.detectErrors([p1, p2], MA, ME)
    correct = s.correctErrors(error, ME)
    for thing in correct:
        fixG.append(thing)
    plt.plot([p1[X], p2[X]], [p1[Y], p2[Y]], 'b')
    xvals = []
    yvals = []
    for point in correct:
        xvals.append(point[X])
        yvals.append(point[Y])
    plt.plot(xvals, yvals, 'r--')
print(time.time()-t)

print("000000000000000000000000000000000000000000000000000000")

plt.subplot(222)
t = time.time()
for ind in range(len(fixG)-1):
    p1 = fixG[ind]
    p2 = fixG[ind+1]
    error = s.detectErrors([p1, p2], desiredPoints[0], actualPoints[0])
    correct = s.correctErrors(error, desiredPoints[0])
    for thing in correct:
        fixG1.append(thing)
        print(thing)
    plt.plot([p1[X], p2[X]], [p1[Y], p2[Y]], 'b')
    xvals = []
    yvals = []
    for point in correct:
        xvals.append(point[X])
        yvals.append(point[Y])
    plt.plot(xvals, yvals, 'r--')
print(time.time()-t)
print(len(fixG1))
print("1111111111111111111111111111111111111111111111111111111")

plt.subplot(223)
t = time.time()
for ind in range(len(fixG1)-1):
    p1 = fixG1[ind]
    p2 = fixG1[ind+1]
    error = s.detectErrors([p1, p2], desiredPoints[1], actualPoints[1])
    correct = s.correctErrors(error, desiredPoints[1])
    for thing in correct:
        fixG2.append(thing)
        print(thing)
    plt.plot([p1[X], p2[X]], [p1[Y], p2[Y]], 'b')
    xvals = []
    yvals = []
    for point in correct:
        xvals.append(point[X])
        yvals.append(point[Y])
    plt.plot(xvals, yvals, 'r--')
print(time.time()-t)
print(len(fixG2))
# plt.subplot(224)
# t = time.time()
# for ind in range(len(fixG2)-1):
#     p1 = fixG2[ind]
#     p2 = fixG2[ind+1]
#     error = s.detectErrors([p1, p2], desiredPoints[2], actualPoints[2])
#     correct = s.correctErrors(error, desiredPoints[2])
#     for thing in correct:
#         fixG3.append(thing)
#     plt.plot([p1[X], p2[X]], [p1[Y], p2[Y]], 'b')
#     xvals = []
#     yvals = []
#     for point in correct:
#         xvals.append(point[X])
#         yvals.append(point[Y])
#     plt.plot(xvals, yvals, 'r--')
# print(time.time()-t)
plt.show()

