
import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from .TurtleUtils import TurtleUtils

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class TurtlePath:

    def __init__(self, sketch:f.Sketch):
        self.sketch:f.Sketch = sketch
        self.dimensions = sketch.sketchDimensions
        self.constraints:f.GeometricConstraints = self.sketch.geometricConstraints
        self.unitsManager:f.UnitsManager = design.unitsManager
        
    # Command letters must be uppercase
    # units is the data portion should be lowercase (in, mm, fl_oz, %). Some fusion units have uppercase, if this becomes an issue just rework the regex.
    def draw(self, constructionLine:f.SketchLine, path:str, isClosed=False, makeCurrent=True):
        self.contructionLine:f.SketchLine = constructionLine
        cmds = re.findall("[#FLRMXU][0-9\-\.a-z_%]*", path) #lazy number
        startPt = self.contructionLine.startSketchPoint.geometry
        endPt = self.contructionLine.endSketchPoint.geometry
        difX = endPt.x - startPt.x
        difY = endPt.y - startPt.y
        distance = math.sqrt(difX * difX + difY * difY)
        angle = math.atan2(difY,difX) + math.pi * 4.0
        curPt:f.SketchPoint = self.contructionLine.startSketchPoint
        lastLine:f.SketchLine = self.contructionLine
        lines = []
        cmd:str
        num:float
        units:str = "rel"
        for cmd in cmds:
            if cmd.startswith('U'):
                units = cmd[1:]
                continue
            
            data = cmd[1:]
            num = float(data) if len(cmd) > 1 else 90
            if cmd.startswith('D'):
                distance = num
            elif cmd.startswith('F'):
                dist = self.parseDistance(units, data, distance) 
                p2 = self.getEndPoint(curPt.geometry, angle, dist)
                lastLine = self.sketch.sketchCurves.sketchLines.addByTwoPoints(curPt, p2)
                lines.append(lastLine)
                curPt = lastLine.endSketchPoint
            elif cmd.startswith('L'):
                angle -= num/180.0 * math.pi
            elif cmd.startswith('R'):
                angle += num/180.0 * math.pi
            elif cmd.startswith('M'):
                dist = self.parseDistance(units, data, distance)
                curPt = self.sketch.sketchPoints.add(self.getEndPoint(curPt.geometry, angle, dist))
            elif cmd.startswith('X'):
                lastLine.isConstruction = True
            elif cmd.startswith('#'):
                pass # comment number

        if isClosed:
            lines[0].startSketchPoint.merge(lines[len(lines) - 1].endSketchPoint)
        if makeCurrent:
            self.curLines = lines
        return lines

    def parseDistance(self, units:str, data:str, measure:float):
        if not data.isnumeric():
            result = data
        elif units == 'rel':
            result = (float(data) / 100.0) * measure
        elif units == 'mm':
            result = float(data) + 'mm'
        elif units == 'in':
            result = float(data) + 'in'
        else:
            result = data
        return result

    # VH PA PE EQ CO SY LL ME MI PD
    # Contraints lines are indexes or actual lines.
    # Constraint points are actual Points,  or a Line and [0|1] indicating start or end points of the line.
    # Expressions are strings.
    def setConstraints(self, constraintList):
        # consts = [
        #     "ME", [0,0,13,1, 9,0,14,1],
        #     "PA", [baseLine, 0],
        #     "EQ", [baseLine, 4],
        #     "CO", [0,8, 2,6],
        #     "PA", [0,4, 1,7, 3,5, 9,13, 11,13, 12,10],
        #     "SY", [9,13,construction, 1,7,construction, 3,5,construction],
        #     "PE", [2,3, 9,10]
        pairs = [constraintList[i:i + 2] for i in range(0, len(constraintList), 2)]

        for pair in pairs:
            cmd:str = pair[0].upper()
            data = pair[1]

            if cmd.startswith('VH'): # VERTICAL HORIZONTAL
                for dataIndex in range(0, len(data), 1):
                    lines = self.grabLines(data, dataIndex, 1)
                    self.makeVertHorz(lines[0], lines[1])

            elif cmd.startswith('PA'): # PARALLEL
                for dataIndex in range(0, len(data), 2):
                    lines = self.grabLines(data, dataIndex, 2)
                    self.makeParallel(lines[0], lines[1])

            elif cmd.startswith('PE'): # PERPENDICULAR
                for dataIndex in range(0, len(data), 2):
                    lines = self.grabLines(data, dataIndex, 2)
                    self.makePerpendicular(lines[0], lines[1])
                    
            elif cmd.startswith('EQ'): # EQUAL
                for dataIndex in range(0, len(data), 2):
                    lines = self.grabLines(data, dataIndex, 2)
                    self.makeEqual(lines[0], lines[1])

            elif cmd.startswith('CL'): # COLLINEAR
                for dataIndex in range(0, len(data), 2):
                    lines = self.grabLines(data, dataIndex, 2)
                    self.makeCollinear(lines[0], lines[1])

            elif cmd.startswith('CO'): # COINCIDENT
                for dataIndex in range(0, len(data), 2):
                    lines = self.grabLines(data, dataIndex, 2)
                    self.makeCoincident(lines[0], lines[1])

            elif cmd.startswith('SY'): # SYMETRIC
                for dataIndex in range(0, len(data), 3):
                    lines = self.grabLines(data, dataIndex, 3)
                    self.makeSymetric(lines[0], lines[1], lines[2])

            elif cmd.startswith('LL'): # LINE LENGTH
                for dataIndex in range(0, len(data), 2):
                    lines = self.grabLines(data, dataIndex, 1)
                    expr = data[dataIndex + 1]
                    self.setLineLength(lines[0], expr)
                    
            elif cmd.startswith('LD'): # LINES DISTANCE
                for dataIndex in range(0, len(data), 3):
                    lines = self.grabLines(data, dataIndex, 2)
                    expr = data[dataIndex + 2]
                    self.setTwoLinesDist(lines[0], lines[1], expr)

            elif cmd.startswith('ME'): # MERGE
                dataIndex = 0
                while dataIndex < len(data):
                    pts, dataIndex = self.grabPoints(data, dataIndex, 2)
                    self.mergePoints(pts[0], pts[1])

            elif cmd.startswith('MI'): # MIDPOINT
                dataIndex = 0
                while dataIndex < len(data):
                    pts, dataIndex = self.grabPoints(data, dataIndex, 1)
                    lines = self.grabLines(data, dataIndex, 1)
                    dataIndex += 1
                    self.makeMidpoint(pts[0], lines[0])

            elif cmd.startswith('PD'): # POINTS DISTANCE
                dataIndex = 0
                while dataIndex < len(data):
                    pts, dataIndex = self.grabPoints(data, dataIndex, 2)
                    expr = data[dataIndex]
                    dataIndex += 1
                    self.setTwoPointsDist(pts[0], pts[1], expr)
                    


    def grabPoints(self, data, start:int, pointCount:int):
        result = []
        index = start
        for i in range(pointCount):
            if isinstance(type(data[index]), f.SketchPoint):
                result.append(data[index])
                index += 1
            else:
                val = data[index]
                line = self.curLines[val] if (type(val) == int)  else val # else is a line
                p0:SketchPoint = line.startSketchPoint if data[index + 1] == 0 else line.endSketchPoint
                result.append(p0)
                index += 2
        return result, index


    def grabLines(self, data, start:int, count:int):
        result = []
        for i in range(0, count):
            val = data[start + i]
            line = self.fromLineOrIndex(val)
            result.append(line)
        return result

    # Returns a line whether linex is an index or actual line
    def fromLineOrIndex(self, linex):
        return self.curLines[linex] if (type(linex) == int) else linex 



    def mergePoints(self, p0:f.SketchPoint, p1:f.SketchPoint):
        p0.merge(p1)
    
    def makeVertHorz(self, a:f.SketchLine):
        sp = self.curLines[index].startSketchPoint.geometry
        ep = self.curLines[index].endSketchPoint.geometry
        if(abs(sp.x - ep.x) < abs(sp.y - ep.y)):
            self.constraints.addVertical(self.curLines[index])
        else:
            self.constraints.addHorizontal(self.curLines[index])

    def makeParallel(self, a:f.SketchLine, b:f.SketchLine):
        self.constraints.addParallel(a, b)
            
    def makePerpendicular(self, a:f.SketchLine, b:f.SketchLine):
        self.constraints.addPerpendicular(a, b)

    def makeCollinear(self,  a:f.SketchLine, b:f.SketchLine):
        self.constraints.addCollinear(a, b)

    def makeCoincident(self,  point:f.SketchPoint, line:f.SketchLine):
        self.constraints.addCoincident(point, line)

    def makeEqual(self, a:f.SketchLine, b:f.SketchLine):
        self.constraints.addEqual(a, b)
        
    def makeSymetric(self, left:f.SketchLine, right:f.SketchLine, center:f.SketchLine):
        self.constraints.addSymmetry(left, right, center)

    def makeMidpoint(self, point:f.SketchPoint, line:f.SketchLine):
        self.constraints.addMidPoint(point, line)

    def setLineLength(self, line:f.SketchLine, expr:str):
        dim = self.dimensions.addDistanceDimension(line.startSketchPoint, line.endSketchPoint, \
            f.DimensionOrientations.AlignedDimensionOrientation, line.startSketchPoint.geometry)
        dim.parameter.expression = expr

    def setTwoLinesDist(self, line0:f.SketchLine, line1:f.SketchLine, expr):
        dim = self.dimensions.addOffsetDimension(line0, line1, line1.startSketchPoint.geometry)
        dim.parameter.expression = expr

    def setTwoPointsDist(self, p0:f.SketchPoint, p1:f.SketchPoint, expr):
        dim = self.dimensions.addDistanceDimension(p0, p1, \
            f.DimensionOrientations.AlignedDimensionOrientation, p0.geometry)
        dim.parameter.expression = expr



    def addMidpointConstructionLine(self, baseLine:f.SketchLine, lengthExpr, toLeft=True):
        path = "XM1L90F1X" if toLeft else "XM1R90F1X"
        lines = self.draw(baseLine, path, False)
        construction = lines[0]
        self.constraints.addMidPoint(construction.startSketchPoint, baseLine)
        self.setLineLength(self.sketch, construction, lengthExpr)
        return lines[0]
        
    def duplicateLine(self, line:f.SketchLine):
        line = self.sketchLines.addByTwoPoints(line.startSketchPoint, line.endSketchPoint)
        return line

    def addParallelLine(self, line:f.SketchLine, direction=1):
        p0 = line.startSketchPoint.geometry
        p1 = line.endSketchPoint.geometry
        rpx = (p1.y - p0.y) * direction # rotate to get perpendicular point to ensure direction
        rpy = (p1.x - p0.x) * -direction
        pp0 = core.Point3D.create(p0.x + rpx, p0.y + rpy, 0)
        pp1 = core.Point3D.create(p1.x + rpx, p1.y + rpy, 0)
        line2 = self.sketchLines.addByTwoPoints(pp0, pp1)
        return line2
    
    # returns double value of expression evaluated to current units
    @classmethod
    def evaluate(cls, expr):
        result = 0
        if type(expr) == float or type(expr) == int:
            result = expr
        else:
            result = self.unitsManager.evaluateExpression(expr)
        return result
        
    @classmethod
    def getEndPoint(cls, start:core.Point3D, angle:float, dist):
        distance = cls.evaluate(dist)
        x = start.x + distance * math.cos(angle)
        y = start.y + distance * math.sin(angle) 
        return core.Point3D.create(x, y, 0)

    @classmethod
    def isOnLine(cls, a:core.Point3D, line:f.SketchLine):
        b = line.startSketchPoint.geometry
        c = line.endSketchPoint.geometry
        cross = (c.y - a.y) * (b.x - a.x) - (c.x - a.x) * (b.y - a.y)
        return abs(cross) < 0.0001

    @classmethod
    def distanceToLine(cls, a:core.Point3D, line:f.SketchLine):
        b = line.startSketchPoint.geometry
        c = line.endSketchPoint.geometry
        x_diff = c.x - b.x
        y_diff = c.y - b.y
        num = abs(y_diff * a.x - x_diff * a.y + c.x*b.y - c.y*b.x)
        den = math.sqrt(y_diff**2 + x_diff**2)
        return num / den

    @classmethod
    def isEquivalentCurve(cls, a:f.SketchCurve, b:f.SketchCurve, maxDist = 0):
        if type(a) == f.SketchCircle:
            result = abs(a.geometry.center.x - b.geometry.center.x) <= maxDist and \
                abs(a.geometry.center.y - b.geometry.center.y) <= maxDist and \
                abs(a.geometry.radius - b.geometry.radius) <= maxDist 
        else:            
            result = abs(a.geometry.startPoint.x - b.geometry.startPoint.x) <= maxDist and \
                abs(a.geometry.startPoint.y - b.geometry.startPoint.y) <= maxDist and \
                abs(a.geometry.endPoint.x - b.geometry.endPoint.x) <= maxDist and \
                abs(a.geometry.endPoint.y - b.geometry.endPoint.y) <= maxDist
        return result

        
    @classmethod
    def printLines(self, lines, newLine="\n"):
        spc = "Line: "
        for line in lines:
            print(spc, end="")
            self.printLine(line, "")
            spc=", "
        print("",end=newLine)

    @classmethod
    def printLine(self, line:f.SketchLine, newLine="\n"):
        print("[",end="")
        self.printPoint(line.startSketchPoint)
        print(", ",end="")
        self.printPoint(line.endSketchPoint)
        print("("+ TurtleUtils.round(line.length) + ")", end="")
        print("]", end=newLine)

    @classmethod
    def printPoints(self, points:f.SketchPoint, newLine="\n"):
        spc = "Points: "
        for point in points:
            print(spc, end="")
            print("(",end="")
            self.printPoint(point)
            print(")",end="")
            spc=", "
        print("",end=newLine)

    @classmethod
    def printPoint(self, pt:f.SketchPoint):
        print(TurtleUtils.round(pt.geometry.y) +", " + TurtleUtils.round(pt.geometry.y),end="")
