
import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from .TurtleUtils import TurtleUtils
from .TurtlePath import TurtlePath
from .TurtleParams import TurtleParams

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class TurtleSketch:
    def __init__(self, sketchTarget:f.Sketch):
        self.sketch:f.Sketch = sketchTarget
        self.name = self.sketch.name
        self.parameters = TurtleParams.instance()
        self.referencePlane = sketchTarget.referencePlane
        self.component = sketchTarget.parentComponent
        self.constraints:f.GeometricConstraints = sketchTarget.geometricConstraints
        self.dimensions:f.SketchDimensions = sketchTarget.sketchDimensions
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

    def draw(self, line:f.SketchLine, *data:str):
        data = " ".join(data)
        return self.path.draw(line, data, False)

    def drawClosed(self, line:f.SketchLine, *data:str):
        data = " ".join(data)
        return self.path.draw(line, data, True)

    def constrain(self, constraintList):
        self.path.setConstraints(constraintList)



    def setDistances(self, lines, indexValues):
        for pair in indexValues:
             self.addLineLength(self.sketch, lines[pair[0]], pair[1])

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



    def projectLine(self, line:f.SketchLine, makeConstruction = False):
        pp0 = self.sketch.project(line.startSketchPoint)
        pp1 = self.sketch.project(line.endSketchPoint)
        line = self.sketchLines.addByTwoPoints(pp0[0], pp1[0])
        if makeConstruction:
            line.isConstruction = True
        return line

    def addMidpointConstructionLine(self, linex, lengthExpr=None, toLeft=True):
        baseLine:f.SketchLine = self.path.fromLineOrIndex(linex)
        constraints = self.sketch.geometricConstraints
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

    def getSingleLines(self):
        lines = []
        touched = []
        for gc in self.sketch.geometricConstraints:
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
        dist = self.parameters.createValue(offset)
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
    def getMidpoint(cls, curve:f.SketchCurve):
        ev = curve.geometry.evaluator
        pe = ev.getParameterExtents()
        return ev.getPointAtParameter((pe[2] - pe[1]) * 0.5)[1]
