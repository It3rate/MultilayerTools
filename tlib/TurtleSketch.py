
import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from collections.abc import Iterable
from functools import cmp_to_key
from .TurtleUtils import TurtleUtils
from .TurtlePath import TurtlePath
from .TurtleParams import TurtleParams

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
    @property
    def lastAddedConstraint(self):
        return self.constraints.item(self.constraints.count - 1) if self.constraints.count > 0 else None
    @property
    def lastAddedParameter(self):
        return self.component.modelParameters[self.component.modelParameters.count - 1] if self.component.modelParameters.count > 0 else None
    @name.setter
    def name(self, val):
        self.sketch.name = val

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
             self.addLineLength(self.sketch, lines[pair[0]], pair[1])
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
            
        offsetElements = self.sketch.offset(lst, direction, .2)
        offsetConstraint = self.lastAddedConstraint
        lastParameter = self.lastAddedParameter
        lastParameter.expression = distanceExpr
        if makeConstruction:
            for oe in offsetElements:
                oe.isConstruction = True
        return (offsetElements, offsetConstraint)

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

    @classmethod
    def getCWPointPairs(cls, loop:f.BRepLoop) -> list[core.Point3D]:
        result = []
        for coEdge in loop.coEdges:
            result.append(cls.coEdgeToPoints(coEdge))
        return result

    @classmethod
    def coEdgeToPoints(cls, coEdge:f.BRepCoEdge) -> tuple[core.Point3D, core.Point3D]:
        sp = coEdge.edge.startVertex.geometry
        ep = coEdge.edge.endVertex.geometry
        #print('{:0.2f},{:0.2f}  {:0.2f},{:0.2f}'.format(sp.x, sp.y, ep.x, ep.y))
        return (cls.sketch.modelToSketchSpace(sp), cls.sketch.modelToSketchSpace(ep))

    @classmethod
    def getPointChain(cls, lines:list[f.SketchLine], makeCW:bool=True)->tuple[core.Point3D, core.Point3D]:
        ptPairs = []
        for line in lines:
            ptPairs.append((line.startSketchPoint.geometry, line.endSketchPoint.geometry))

        curPair = ptPairs.pop(0)
        chain = [curPair[1]]
        minPt = curPair[1]
        lastPt = curPair[1]
        pairLen = len(ptPairs)
        for i in range(pairLen):
            resultIndex = -1
            for pair in ptPairs:
                if pair[0].isEqualTo(lastPt):
                    chain.append(pair[1])
                    resultIndex = ptPairs.index(pair)
                elif pair[1].isEqualTo(lastPt):
                    chain.append(pair[0])
                    resultIndex = ptPairs.index(pair)
                if(resultIndex > -1):
                    lastPt = chain[len(chain)-1]
                    minPt = cls.minPoint(minPt, chain[len(chain) - 1])
                    ptPairs.pop(resultIndex)
                    break
        #start at min
        minIndex = chain.index(minPt)
        chain = chain[minIndex:] + chain[:minIndex]

        # ensure clockwise or ccw
        if len(chain) > 2:
            isCw = cls.arePointsClockwise(chain[0], chain[1], chain[2])
            if(makeCW and not isCw) or (not makeCW and isCw):
                chain.reverse()

        result = []
        for ptIndex in range(1, len(chain)):
            result.append((chain[ptIndex - 1], chain[ptIndex]))
        result.append((chain[len(chain) - 1], chain[0]))
        return result

    @classmethod
    def sortPointsMinToMax(cls, lst:list[core.Point3D])->None:
        return list.sort(key=cls.comparePoints)

    @classmethod
    def comparePoints(cls, p0:core.Point3D, p1:core.Point3D):
        result = 1
        if(p0.x < p1.x):
            result = -1
        elif(p0.x == p1.x and p0.y < p1.y):
            result = -1
        elif(p0.x == p1.x and p0.y == p1.y and p0.z < p1.z):
            result = -1
        return result

    @classmethod
    def sortedPointsMinToMax(cls, *args)->list[core.Point3D]:
        result = list(args)
        sorted(result, key=cmp_to_key(TurtleSketch.comparePoints), reverse=True)
        return result

    @classmethod
    def minPoint(cls, p0:core.Point3D, p1:core.Point3D)->core.Point3D:
        result = p1
        if(p0.x < p1.x):
            result = p0
        elif(p0.x == p1.x and p0.y < p1.y):
            result = p0
        elif(p0.x == p1.x and p0.y == p1.y and p0.z < p1.z):
            result = p0
        return result
    
    
    @classmethod
    def arePointsClockwise(cls, a:core.Point3D, b:core.Point3D, c:core.Point3D):
        return (b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y) < 0
    @classmethod
    def arePointsCounterClockwise(cls, a:core.Point3D, b:core.Point3D, c:core.Point3D):
        return (b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y) > 0
    @classmethod
    def arePointsColinear(cls, a:core.Point3D, b:core.Point3D, c:core.Point3D):
        return abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) < 0.000001
    
    @classmethod
    def createCenteredTabs(cls, startPoint:core.Point3D, endPoint:core.Point3D, tabWidth:float, tabSpacing:float):
        lineLen = startPoint.distanceTo(endPoint)
        tabTotalLen = tabSpacing + tabWidth
        lineWorking = (lineLen - tabSpacing)
        slotCount = math.floor(lineWorking / tabTotalLen)
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