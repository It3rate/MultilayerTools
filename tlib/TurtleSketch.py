
import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from collections.abc import Iterable
from functools import cmp_to_key
from .TurtleUtils import TurtleUtils
from .TurtlePath import TurtlePath
from .TurtleParams import TurtleParams

f:adsk.fusion
core:adsk.core
f,core,app,ui = TurtleUtils.initGlobals()

class TurtleSketch:
    def __init__(self, sketchTarget:f.Sketch):
        self.sketch:f.Sketch = sketchTarget
        self.name = self.sketch.name
        self.params = TurtleParams.instance()
        self.referencePlane = sketchTarget.referencePlane
        self.component = sketchTarget.parentComponent
        self.constraints:f.GeometricConstraints = sketchTarget.geometricConstraints
        self.dimensions:f.SketchDimensions = sketchTarget.sketchDimensions
        self.sketchPoints:f.SketchPoints = sketchTarget.sketchPoints
        self.sketchLines:f.SketchLines = sketchTarget.sketchCurves.sketchLines
        self.profiles:f.Profiles = sketchTarget.profiles
        self.path:TurtlePath = TurtlePath(self.sketch)
        

    @classmethod
    def createWithSketch(cls, sketch:f.Sketch):
        return cls(sketch)
        
    @classmethod
    def createWithPlane(cls, component:f.Component, planarEntity):
        sketch = component.sketches.add(planarEntity)
        return cls(sketch)

    @property
    def name(self):
        return self.sketch.name    
    @name.setter
    def name(self, val):
        self.sketch.name = val

    @property
    def lastAddedConstraint(self):
        return self.constraints.item(self.constraints.count - 1) if self.constraints.count > 0 else None
    @property
    def lastAddedParameter(self):
        return self.component.modelParameters[self.component.modelParameters.count - 1] if self.component.modelParameters.count > 0 else None


    def draw(self, line:f.SketchLine, *data:str):
        data = " ".join(data)
        self.sketch.isComputeDeferred = True
        result = self.path.draw(line, data, False)
        self.sketch.isComputeDeferred = False
        return result

    def drawClosed(self, line:f.SketchLine, *data:str):
        data = " ".join(data)
        self.sketch.isComputeDeferred = True
        result = self.path.draw(line, data, True)
        self.sketch.isComputeDeferred = False
        return result

    def constrain(self, constraintList):
        self.sketch.isComputeDeferred = True
        self.path.setConstraints(constraintList)
        self.sketch.isComputeDeferred = False

    def setDistances(self, lines, indexValues):
        self.sketch.isComputeDeferred = True
        for pair in indexValues:
             self.addLineLength(lines[pair[0]], pair[1])
        self.sketch.isComputeDeferred = False

    def makeVertHorz(self, lines, indexes):
        for index in indexes:
            sp = lines[index].startSketchPoint.geometry
            ep = lines[index].endSketchPoint.geometry
            if(abs(sp.x - ep.x) < abs(sp.y - ep.y)):
                self.constraints.addVertical(lines[index])
            else:
                self.constraints.addHorizontal(lines[index])

    def makeEqual(self, curves, pairIndexes):
        for pair in pairIndexes:
            self.constraints.addEqual(curves[pair[0]], curves[pair[1]])

    def makeParallel(self, lines, pairIndexes):
        for pair in pairIndexes:
            self.constraints.addParallel(lines[pair[0]], lines[pair[1]])
            
    def makePerpendicular(self, lines, pairIndexes):
        for pair in pairIndexes:
            self.constraints.addPerpendicular(lines[pair[0]], lines[pair[1]])

    def makeCollinear(self, lines, pairIndexes):
        for pair in pairIndexes:
            self.constraints.addCollinear(lines[pair[0]], lines[pair[1]])

    def addLineLength(self, line:f.SketchLine, expr):
        dim = self.dimensions.addDistanceDimension(line.startSketchPoint, line.endSketchPoint, \
            f.DimensionOrientations.AlignedDimensionOrientation, line.startSketchPoint.geometry)
        dim.parameter.expression = expr

    def addTwoPointsDist(self, p0:f.SketchPoint, p1:f.SketchPoint, expr):
        dim = self.dimensions.addDistanceDimension(p0, p1, \
            f.DimensionOrientations.AlignedDimensionOrientation, p0.geometry)
        dim.parameter.expression = expr

    def addTwoLinesDist(self, line0:f.SketchLine, line1:f.SketchLine, expr):
        dim = self.dimensions.addOffsetDimension(line0, line1, line1.startSketchPoint.geometry)
        dim.parameter.expression = expr

    def projectList(self, lst, makeConstruction = False):
        result = []#core.ObjectCollection.create()
        for ent in lst:
            proj = self.sketch.project(ent)
            result.append(*proj)
            if makeConstruction:
                if isinstance(proj, Iterable):
                    for p in proj:
                         p.isConstruction = True
                else:
                    proj.isConstruction = True
        return result

    def projectLine(self, line:f.SketchLine, makeConstruction = False):
        pp0 = self.sketch.project(line.startSketchPoint)
        pp1 = self.sketch.project(line.endSketchPoint)
        line = self.sketchLines.addByTwoPoints(pp0[0], pp1[0])
        if makeConstruction:
            line.isConstruction = True
        return line

    def offset(self, elements, direction:core.Point3D, distanceExpr:str, makeConstruction = False):
        if not isinstance(elements, core.ObjectCollection):
            lst = core.ObjectCollection.create()
            for e in elements:
                lst.add(e)
        else:
            lst = elements
            
        offsetElements = self.sketch.offset(lst, direction, .01)
        offsetConstraint = self.lastAddedConstraint
        lastParameter = self.lastAddedParameter
        lastParameter.expression = distanceExpr
        if makeConstruction:
            for oe in offsetElements:
                oe.isConstruction = True
        # The order of offsets is random and varies per run.
        # Need to sort elements tip to tail and clockwise. Allow for broken chains.
        pointChain = self.getRectPointChain(offsetElements)
        return (pointChain, offsetConstraint)

    def addMidpointConstructionLine(self, linex, lengthExpr=None, toLeft=True):
        baseLine:f.SketchLine = self.path.fromLineOrIndex(linex)
        constraints = self.constraints
        path = "XM50LF50X" if toLeft else "XM50RF50X"
        lines = self.path.draw(baseLine, path)
        construction = lines[0]
        constraints.addPerpendicular(construction, baseLine)
        constraints.addMidPoint(construction.startSketchPoint, baseLine)
        if lengthExpr:
            self.addLineLength(construction, lengthExpr)
        else:
            constraints.addEqual(construction, baseLine)
        return lines[0]

    def duplicateLine(self, line:f.SketchLine):
        return self.sketchLines.addByTwoPoints(line.startSketchPoint, line.endSketchPoint)

    def addParallelLine(self, line:f.SketchLine, direction=1):
        p0 = line.startSketchPoint.geometry
        p1 = line.endSketchPoint.geometry
        rpx = (p1.y - p0.y) * direction # rotate to get perpendicular point to ensure direction
        rpy = (p1.x - p0.x) * -direction
        pp0 = core.Point3D.create(p0.x + rpx, p0.y + rpy, 0)
        pp1 = core.Point3D.create(p1.x + rpx, p1.y + rpy, 0)
        line2 = self.sketchLines.addByTwoPoints(pp0, pp1)
        return line2


    def getProfileAt(self, index:int):
        return self.sketch.profiles.item(index)

    def combineProfiles(self):
        result = core.ObjectCollection.create()
        for p in self.profiles:
            result.add(p)
        return result
        
    def findOuterProfile(self, profiles:core.ObjectCollection = None):
        collection = self.profiles if profiles == None else profiles
        index = 0
        largestArea = 0
        for i in range(collection.count):
            profile = collection.item(i)
            area = TurtleUtils.bbArea(profile.boundingBox)
            if area > largestArea:
                largestArea = area
                index = i
        return collection.item(index)

    def allButOuterProfile(self):
        profiles = core.ObjectCollection.create()
        for profile in self.sketch.profiles:
            profiles.add(profile)
        outer = self.findOuterProfile(profiles)   
        profiles.removeByItem(outer)
        return profiles

    def findLargestProfile(self, profiles:core.ObjectCollection = None):
        collection = self.profiles if profiles == None else profiles
        index = 0
        largestArea = 0
        for i in range(collection.count):
            areaProps = collection.item(i).areaProperties(f.CalculationAccuracy.MediumCalculationAccuracy)
            if areaProps.area > largestArea:
                largestArea = areaProps.area
                index = i
        return collection.item(index)

    def findSmallestProfile(self, profiles:core.ObjectCollection = None):
        collection = self.profiles if profiles == None else profiles
        index = 0
        smallestArea = float('inf')
        for i in range(collection.count):
            areaProps = collection.item(i).areaProperties(f.CalculationAccuracy.MediumCalculationAccuracy)
            if areaProps.area < smallestArea:
                smallestArea = areaProps.area
                index = i
        return collection.item(index)

    def removeLargestProfile(self, profiles:core.ObjectCollection = None):
        collection = self.profiles if profiles == None else profiles
        result = self.findLargestProfile(collection)   
        collection.removeByItem(result)
        return result

    def removeSmallestProfile(self, profiles:core.ObjectCollection = None):
        collection = self.profiles if profiles == None else profiles
        result = self.findSmallestProfile(collection)   
        collection.removeByItem(result)
        return result

    def findPointAt(self, target:core.Point3D):
        result = None
        for i in range(self.sketchPoints.count):
            pt:f.SketchPoint = self.sketchPoints.item(i)
            if target.isEqualTo(pt.geometry):
                result = pt
                break
        return result

    def getSingleLines(self):
        lines = []
        touched = []
        for gc in self.constraints:
            if isinstance(gc, f.CoincidentConstraint) and gc.point.connectedEntities:
                for con in gc.point.connectedEntities:
                    if isinstance(con, f.SketchLine):
                        touched.append(con) 
                if isinstance(gc.entity, f.SketchLine):
                    touched.append(gc.entity) # bug: enity reference doesn't seem to be the same object as original

        for line in self.sketch.sketchCurves.sketchLines:
            if not line.isConstruction:
                continue
            if line.startSketchPoint.connectedEntities.count > 1:
                continue
            if line.endSketchPoint.connectedEntities.count > 1:
                continue

            lines.append(line)

        result = []
        for line in lines:
            isTouched = False
            for t in touched:
                if TurtlePath.isEquivalentCurve(t, line):
                    isTouched = True
                    break
            if not isTouched:
                result.append(line)

        return result
    
    def getSingleConstructionLine(self):
        result = None
        for line in self.sketch.sketchCurves.sketchLines:
            if line.isConstruction:
                result = line
                break
        return result

    
    def createOffsetPlane(self, offset, destinationComponent:f.Component = None, name:str = None):
        comp = destinationComponent if destinationComponent else self.component
        comp.isConstructionFolderLightBulbOn = True
        planeInput:f.ConstructionPlaneInput = comp.constructionPlanes.createInput()
        dist = self.params.createValue(offset)
        planeInput.setByOffset(self.referencePlane, dist)
        result = comp.constructionPlanes.add(planeInput)
        if name:
            result.name = name
        return result

    def createOrthoganalPlane(self, line:f.SketchLine, destinationComponent:f.Component = None):
        comp = destinationComponent if destinationComponent else self.component
        planeInput = comp.constructionPlanes.createInput()
        planeInput.setByAngle(line, adsk.core.ValueInput.createByReal(-math.pi/2.0), self.referencePlane)
        result = comp.constructionPlanes.add(planeInput)
        return result
    
    def drawLine(self, startPoint:f.SketchPoint, endPoint:f.SketchPoint) -> f.SketchLine:
        return self.sketchLines.addByTwoPoints(startPoint, endPoint)

    def drawLines(self, pointPairs:list[tuple[f.SketchPoint, f.SketchPoint]]) -> list[f.SketchLine]:
        result = []
        for pp in pointPairs:
            result.append(self.drawLine(pp[0], pp[1]))
        return result

    def drawPolyLine(self, points:list[f.SketchPoint]) -> list[f.SketchLine]:
        result = []
        if len(points) > 0:
            startPt = None
            for pt in points:
                if startPt:
                    result.append(self.drawLine(startPt, pt))
                startPt = pt
        return result




    @classmethod
    def getCWPointPairs(cls, loop:f.BRepLoop) -> list[core.Point3D]:
        result = []
        for coEdge in loop.coEdges:
            result.append(cls.coEdgeToPoints(coEdge))
        return result

    def coEdgeToPoints(self, coEdge:f.BRepCoEdge) -> tuple[core.Point3D, core.Point3D]:
        sp = coEdge.edge.startVertex.geometry
        ep = coEdge.edge.endVertex.geometry
        return (self.sketch.modelToSketchSpace(sp), self.sketch.modelToSketchSpace(ep))

    def getRectPointChain(self, lines:list[f.SketchLine], makeCW:bool=True)->list[tuple[core.Point3D, core.Point3D]]:
        ptPairs = []
        # allow lines or existing pointPairs to be sorted here
        normList = []
        for line in lines:
            if isinstance(line, tuple): # assumes list[p0, p1]
                normList.append((line[0], line[1]))
            elif line.length > 0.000001:
                normList.append((line.startSketchPoint, line.endSketchPoint))
        
        if len(normList) == 2: # special case where rect is defined by left and right side, or top and bottom
            l0 = self.sortedSketchPointsMinToMax(normList[0][0], normList[0][1])
            l1 = self.sortedSketchPointsMinToMax(normList[1][0], normList[1][1])
            ptPairs.append((l0[0], l0[1]))
            ptPairs.append((l0[1], l1[1]))
            ptPairs.append((l1[1], l1[0]))
            ptPairs.append((l1[0], l0[0]))
        else: #normal rect or even polyline
            ptPairs = normList

        curPair = ptPairs.pop(0)
        chain = [curPair[0], curPair[1]]
        firstPt = curPair[0]
        lastPt = curPair[1]
        minPt = self.minSketchPoint(firstPt, lastPt)
        pairLen = len(ptPairs)
        for i in range(pairLen):
            match = None
            for pair in ptPairs:
                if pair[0].geometry.isEqualTo(lastPt.geometry):
                    lastPt = pair[1]
                    chain.append(lastPt)
                    match = (pair, 1)
                elif pair[1].geometry.isEqualTo(lastPt.geometry):
                    lastPt = pair[0]
                    chain.append(lastPt)
                    match = (pair, 0)
                elif pair[0].geometry.isEqualTo(firstPt.geometry):
                    firstPt = pair[1]
                    chain.insert(0, firstPt)
                    match = (pair, 1)
                elif pair[1].geometry.isEqualTo(firstPt.geometry):
                    firstPt = pair[0]
                    chain.insert(0, firstPt)
                    match = (pair, 0)
                    
                if(match):
                    matchPair = match[0]
                    matchIndex = match[1]
                    minPt = self.minSketchPoint(minPt, matchPair[matchIndex])
                    ptPairs.pop(ptPairs.index(matchPair))
                    break
        #start at min
        #todo: min point needs to account for xDirection and yDirection
        minIndex = chain.index(minPt)
        chain = chain[minIndex:] + chain[:minIndex]

        # ensure clockwise or ccw
        if len(chain) > 2:
            isCw = self.areSketchPointsClockwise(chain[0], chain[1], chain[2])
            if(makeCW and not isCw) or (not makeCW and isCw):
                chain.reverse()

        # turn points into pairs
        result = []
        for ptIndex in range(1, len(chain)): # start at one as we are reaching back
            result.append((chain[ptIndex - 1], chain[ptIndex]))
        result.append((chain[len(chain) - 1], chain[0])) # and wrap around
        return result

    def areSketchPointsClockwise(self, a:core.Point3D, b:core.Point3D, c:core.Point3D, isFlipped:bool = False)->bool:
        return self.arePointsClockwise(a.geometry, b.geometry, c.geometry, self.isSketchCWFlipped())
    def areSketchPointsCounterClockwise(self, a:core.Point3D, b:core.Point3D, c:core.Point3D, isFlipped:bool = False)->bool:
        return self.arePointsCounterClockwise(a.geometry, b.geometry, c.geometry, self.isSketchCWFlipped())
    def areSketchPointsColinear(self, a:core.Point3D, b:core.Point3D, c:core.Point3D)->bool:
        return self.arePointsColinear(a.geometry, b.geometry, c.geometry)
    def isSketchCWFlipped(self)->bool:
        return self.isCWFlipped(self.sketch)

    @classmethod
    def sortPointsMinToMax(cls, lst:list[core.Point3D])->None:
        return list.sort(key=cls.comparePoints)
    @classmethod
    def sortedPoint3DsMinToMax(cls, *args)->list[core.Point3D]:
        result = list(args)
        sorted(result, key=cmp_to_key(TurtleSketch.comparePoints), reverse=False)
        return result

    @classmethod
    def sortedSketchPointsMinToMax(cls, *args)->list[f.SketchPoint]:
        result = list(args)
        result=sorted(result, key=cmp_to_key(TurtleSketch.compareSketchPoints), reverse=False)
        return result

    @classmethod
    def comparePoints(cls, p0:core.Point3D, p1:core.Point3D):
        result = 1
        tolerance = 0.000001
        if p0.x - p1.x < -tolerance:
            result = -1
        elif abs(p0.x - p1.x) < tolerance and p0.y - p1.y < -tolerance:
            result = -1
        elif abs(p0.x - p1.x) < tolerance and abs(p0.y - p1.y) < tolerance:
            result = 0
        return result

    @classmethod
    def compareSketchPoints(cls, sp0:f.SketchPoint, sp1:f.SketchPoint):
        return cls.comparePoints(sp0.geometry, sp1.geometry)

    @classmethod
    def minPoint(cls, p0:core.Point3D, p1:core.Point3D)->core.Point3D:
        result = p1
        tolerance = 0.000001
        if (p0.x - p1.x) < -tolerance:
            result = p0
        elif abs(p0.x - p1.x) < tolerance and (p0.y - p1.y) < -tolerance:
            result = p0
        return result

    @classmethod
    def minSketchPoint(cls, p0:f.SketchPoint, p1:f.SketchPoint)->f.SketchPoint:
        return p0 if cls.minPoint(p0.geometry, p1.geometry).isEqualTo(p0.geometry) else p1
    
    @classmethod
    def arePointsClockwise(cls, a:core.Point3D, b:core.Point3D, c:core.Point3D, isFlipped:bool = False)->bool:
        #return (float(b.y - a.y) * (c.x - b.x)) - (float(b.x - a.x) * (c.y - b.y)) > 0.000001
        result = (b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y) < -0.000001
        return not result if isFlipped else result
    @classmethod
    def arePointsCounterClockwise(cls, a:core.Point3D, b:core.Point3D, c:core.Point3D, isFlipped:bool = False)->bool:
        #return (float(b.y - a.y) * (c.x - b.x)) - (float(b.x - a.x) * (c.y - b.y)) < -0.000001
        result = (b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y) > 0.000001
        return not result if isFlipped else result
    @classmethod
    def arePointsColinear(cls, a:core.Point3D, b:core.Point3D, c:core.Point3D)->bool:
        return abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) < 0.000001

    @classmethod
    def isCWFlipped(cls, sketch:f.Sketch)->bool:
        result = 1
        if sketch.xDirection.x < 0:
            result *= -1
        if sketch.yDirection.y < 0:
            result *= -1
        return result < 0

    @classmethod
    def createCenteredTabs(cls, startPoint:core.Point3D, endPoint:core.Point3D, tabWidth:float, tabSpacing:float, count:int = -1):
        lineLen = startPoint.distanceTo(endPoint)
        tabTotalLen = tabSpacing + tabWidth
        lineWorking = (lineLen - tabSpacing)
        slotCount = math.floor(lineWorking / tabTotalLen) if count < 0 else count
        offset = (lineLen - (slotCount * tabTotalLen + tabSpacing)) / 2.0
        result = []
        curLen = offset + tabSpacing
        for i in range(slotCount): # each side of center, plus center
            pt0 = cls.pointAlongLine(startPoint, endPoint, curLen)
            curLen += tabWidth
            pt1 = cls.pointAlongLine(startPoint, endPoint, curLen)
            curLen += tabSpacing
            result.append((pt0, pt1))
        return result
    
    # @classmethod
    # def createCenteredTabsAuto(cls, startPoint:core.Point3D, endPoint:core.Point3D, tabWidth:float, tabSpacing:float):
    #     lineLen = startPoint.distanceTo(endPoint)
    #     tabTotalLen = tabSpacing + tabWidth
    #     lineWorking = (lineLen - tabSpacing)
    #     slotCount = math.floor(lineWorking / tabTotalLen)
    #     offset = (lineLen - (slotCount * tabTotalLen + tabSpacing)) / 2.0
    #     result = []
    #     curLen = offset + tabSpacing
    #     for i in range(slotCount): # each side of center, plus center
    #         pt0 = cls.pointAlongLine(startPoint, endPoint, curLen)
    #         curLen += tabWidth
    #         pt1 = cls.pointAlongLine(startPoint, endPoint, curLen)
    #         curLen += tabSpacing
    #         result.append((pt0, pt1))
    #     return result
    
    @classmethod
    def pointAlongLine(self, startPoint:core.Point3D, endPoint:core.Point3D, length:float):
        lineVec = startPoint.vectorTo(endPoint)
        lineLen = lineVec.length
        ratio = length / lineLen
        lineVec.scaleBy(ratio)
        result = startPoint.copy()
        result.translateBy(lineVec)
        return result

    @classmethod
    def getMidpoint(cls, curve:f.SketchCurve):
        ev = curve.geometry.evaluator
        pe = ev.getParameterExtents()
        return ev.getPointAtParameter((pe[2] - pe[1]) * 0.5)[1]
        
    @classmethod
    def isLineFlipped(cls, line:f.SketchLine):
        sp = line.startSketchPoint.geometry
        ep = line.endSketchPoint.geometry
        isFlippedX = sp.x > ep.x
        isFlippedY = abs(sp.x - ep.x) < 0.0001 and sp.y > ep.y
        return isFlippedX or isFlippedY
        
    @classmethod
    def naturalPointOrder(cls, line:f.SketchLine):
        sp = line.startSketchPoint.geometry
        ep = line.endSketchPoint.geometry
        return (sp, ep) if not TurtleSketch.isLineFlipped(line) else (ep, sp)

    @classmethod    
    def veryOuterPoint(cls):
        return core.Point3D.create(-9999,-9999,-9999)





    def printSketchDir(self):
        self.printPoint3D(self.sketch.xDirection)
        self.printPoint3D(self.sketch.yDirection)

    def printPointPairs(self, pointPairs:list):
        for pp in pointPairs:
            self.printSketchPoints(*pp)
            print(" ")
        print(' ')

    def printSketchPoint(self, pt):
        self.printPoint3D(pt.geometry)

    def printSketchPoints(self, *args):
        if isinstance(args[0], core.ObjectCollection) or isinstance(args[0], list):
            for pt in args[0]:
                self.printPoint3D(pt.geometry)
        else:
            for pt in args:
                self.printPoint3D(pt.geometry)

    def printSketchLines(self, *args):
        if isinstance(args[0], core.ObjectCollection) or isinstance(args[0], list):
            for ln in args[0]:
                self.printLine3D(ln.geometry)
                print(' ')
        else:
            for ln in args:
                self.printLine3D(ln.geometry)
                print(' ')
        print(' ')

    def printPoint3Ds(self, *args):
        for pt in args:
            self.printPoint3D(pt)
    def printPoint3D(self, pt):
        print("(",round(pt.x, 2),",",round(pt.y, 2),",",round(pt.z, 2),") ", end = '')

    def printLine3D(self, line):
        print('[', end='')
        self.printPoint3D(line.startPoint)
        print(' - ', end='')
        self.printPoint3D(line.endPoint)
        print(']', end='')
