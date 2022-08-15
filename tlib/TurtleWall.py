import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from enum import Enum
from collections.abc import Iterable

from .data.SketchData import Sketches, SketchData
from .TurtleComponent import TurtleComponent
from .TurtleSketch import TurtleSketch
from .TurtleDecoder import TurtleDecoder
from .TurtleUtils import TurtleUtils, Orientation
from .TurtleLayers import TurtleLayers
from .TurtleFace import TurtleFace
from .TurtleParams import TurtleParams
from .WallData import *

f:adsk.fusion
core:adsk.core
f,core,app,ui = TurtleUtils.initGlobals()

class TurtleWall:
    def __init__(self, tFace:TurtleFace, wallKind:WallKind, crossData:WallData, outwardData:WallData, useOuterLoop:bool):
        self.tFace:TurtleFace = tFace
        self.wallKind:WallKind = wallKind
        self.crossData:WallData = crossData
        self.outwardData:WallData = outwardData
        self.useOuterLoop = useOuterLoop
        self.colorIndex:int = wallKind.colorIndex

        self.parameters = TurtleParams.instance()
        self.slotLengthVal = self.parameters.getParamValueOrDefault('slotLength', 1.0)
        self.slotSpaceVal = self.parameters.getParamValueOrDefault('slotSpacing', 1.5)

        self.face:f.BRepFace = self.tFace.face

        self.rootComponent = TurtleComponent(TurtleUtils.activeRoot())
        self.tComponent = None
        self.tSketch:TurtleSketch = None

        self.baseFeature:f.ExtrudeFeature = None
        self.mainBody:f.BRepBody = None
        self.projectedLines:list[f.SketchLine] = []
        self.boundryLines:list[f.SketchLine] = []

        self.mirrorFeature:f.MirrorFeature = None
        self.wallThicknessExpr = "wallThickness"
        self.negWallThicknessExpr = "-"+self.wallThicknessExpr

        
        self.edgeLine:f.SketchLine = None
        self.oppEdgeLine:f.SketchLine = None
        self.midPlane:f.ConstructionPlane = None
        self.slotType:str = None
        self.op:f.FeatureOperations = None
        self.firstFeature:f.ExtrudeFeature = None
        self.patternFeature:f.RectangularPatternFeature = None
        

    @classmethod
    def create(cls, face:f.BRepFace, wallKind:WallKind, crossData:WallData, outwardData:WallData, useOuterLoop:bool = True):
        result = cls(face, wallKind, crossData, outwardData, useOuterLoop) 
        result.run()
        return result

    @property
    def sketch(self):
        return self.tSketch.sketch
        
    @property
    def component(self):
        return self.tComponent.component

    def run(self):
        self.addFeatures(self.crossData, self.outwardData, self.useOuterLoop)

    def addFeatures(self, crossData:WallData, outwardData:WallData, useOuterLoop:bool = True):
        self.crossData = crossData
        self.outwardData = outwardData
        self.useOuterLoop = useOuterLoop
        self.tSketch = self.projectFaceEdges()
        linesToOffest, isNeg = WallKind.edgesToOffsetForKind(self.wallKind)
        distExpr = self.negWallThicknessExpr if isNeg else self.wallThicknessExpr
        self.makeOffsetBoundry(linesToOffest, distExpr)
        if not self.baseFeature:
            self.baseFeature = self.tComponent.extrudeLargestProfile(self.tSketch, self.wallThicknessExpr, self.colorIndex)
            self.mainBody = self.baseFeature.bodies[0]

        if self.wallKind.isTopBottom() and self.wallKind.isOuter():
            self.addLip(self.boundryLines)

        crossLines, crossMirror = self.tComponent.getLinesByAxis(self.primaryAxis, self.secondaryAxis, self.boundryLines)
        outwardLines, outwardMirror = self.tComponent.getLinesByAxis(self.secondaryAxis, self.primaryAxis, self.boundryLines)
        if self.crossData:
            self.crossData.edgeLines = crossLines
            self.crossData.isMirror = crossMirror
            self.createMirroredSlots(self.crossData)
        if self.outwardData:
            self.outwardData.edgeLines = outwardLines
            self.outwardData.isMirror = outwardMirror
            self.createMirroredSlots(self.outwardData)
            
    @property
    def primaryAxis(self):
        return self.yAxis if self.wallKind.isLeftRight() else self.xAxis
    @property
    def secondaryAxis(self):
        return self.yAxis if self.wallKind.isTopBottom() else self.zAxis
        
    @property
    def xAxis(self):
        return self.tComponent.xAxis if self.tComponent else self.rootComponent.component.xConstructionAxis
    @property
    def yAxis(self):
        return self.tComponent.yAxis if self.tComponent else self.rootComponent.component.yConstructionAxis   
    @property
    def zAxis(self):
        return self.tComponent.zAxis if self.tComponent else self.rootComponent.component.zConstructionAxis    


    def projectFaceEdges(self, asConstruction:bool = True)->f.Sketch:
        tSketch = self.tFace.createSketchAtPoint(self.face.centroid)
        self.tComponent = TurtleComponent.createFromSketch(tSketch.sketch)
        for lp in self.face.loops:
            if lp.isOuter == self.useOuterLoop:
                loop = lp
                break
        self.projectedLines = tSketch.projectList(loop.edges, asConstruction)
        return tSketch

    def sketchFromFaceAndLines(self, lines:list[f.SketchLine])-> tuple[list[f.SketchLine], f.Sketch]:       
        sketch = self.tFace.createSketchAtPoint(self.tFace.centroid)
        projectedLines = sketch.projectList(lines, False)
        return (projectedLines, sketch)

    def addLip(self, boundryLines:list[f.SketchLine]):
        isCW = self.tSketch.areSketchLinesClockwise(boundryLines)
        flipDirection = isCW if self.useOuterLoop else not isCW
        negStr = "-" if flipDirection else ""
        self.tSketch.offset(boundryLines, self.face.centroid, negStr + "lipWidth", False)
        if self.useOuterLoop:
            lipFeature = self.tComponent.extrudeOuterProfile(self.tSketch, self.wallThicknessExpr, self.colorIndex)
            TurtleLayers.changeExtrudeOperation(lipFeature, self.baseFeature.bodies, f.FeatureOperations.JoinFeatureOperation)
        else: # hole
            lipFeature = self.tComponent.extrudeAllButOuterProfile(self.tSketch, self.wallThicknessExpr, self.colorIndex)
            TurtleLayers.changeExtrudeOperation(lipFeature, self.baseFeature.bodies, f.FeatureOperations.CutFeatureOperation)
        return lipFeature

    def makeOffsetBoundry(self, edgeIndexes:list[int], expression:str):
        if len(edgeIndexes) > 0:
            linesToOffset = []
            for index in edgeIndexes:
                linesToOffset.append(self.projectedLines[index])
            offsetLines = self.tSketch.offset(linesToOffset, self.face.centroid, expression, True)[0]
        linesForCorners = []
        if len(edgeIndexes) == 0:
            linesForCorners.append(self.projectedLines[0])
            linesForCorners.append(self.projectedLines[2])
        elif len(edgeIndexes) == 1:
            oppIndex = self.oppositeLineIndex(edgeIndexes[0])
            linesForCorners.append(self.projectedLines[oppIndex])
            linesForCorners.append(offsetLines[0])
        elif len(edgeIndexes) == 2:
            linesForCorners.append(offsetLines[0])
            linesForCorners.append(offsetLines[2])
        elif len(edgeIndexes) == 3:
            linesForCorners.append(offsetLines[0])
            linesForCorners.append(offsetLines[2])
        elif len(edgeIndexes) == 4:
            linesForCorners.append(offsetLines[0])
            linesForCorners.append(offsetLines[2])
        ptPairs = self.tSketch.getRectPointChain(linesForCorners, True)
        self.boundryLines = self.tSketch.drawLines(ptPairs)

    def createMirroredSlots(self, wallData:WallData)->list[tuple[f.ExtrudeFeature, f.RectangularPatternFeature]]:
        result = []
        mirrorNewFeatures = len(wallData.slotKinds) < 2
        passCount = 0
        for slotKind in wallData.slotKinds:
            op = Sketches.normalOperationForDrawing(slotKind)
            projLines, wallData.tSketch = self.sketchFromFaceAndLines(wallData.edgeLines)
            startLine = projLines[passCount]
            passCount += 1
            #self.tSketch.printSketchLines([wallData.edgeLines[0], startLine])
            tabPts = self.tSketch.createFirstTabPoints(startLine.startSketchPoint, startLine.endSketchPoint,\
                self.slotLengthVal, self.slotSpaceVal, wallData.slotCount)
            drawData = SketchData.createFromBuiltIn(slotKind)
            mirror = not wallData.isMirror if wallData.mirrorInvert else wallData.isMirror
            decoder = TurtleDecoder.createWithPoints(drawData, wallData.tSketch, tabPts, False, mirror)
            slotFeature = self.tComponent.extrudeOuterProfile(wallData.tSketch, self.wallThicknessExpr, 1)

            if self.baseFeature:
                if op == f.FeatureOperations.CutFeatureOperation:
                    TurtleLayers.changeExtrudeOperation(slotFeature, self.baseFeature.bodies, op)
                elif op == f.FeatureOperations.JoinFeatureOperation:
                    TurtleLayers.changeExtrudeOperation(slotFeature, self.baseFeature.bodies, op)
                elif op == f.FeatureOperations.IntersectFeatureOperation:
                    TurtleLayers.changeExtrudeOperation(slotFeature, self.baseFeature.bodies, op)
            rectangularFeature = None
            if wallData.slotCount > 1:
                rectangularPatterns = self.component.features.rectangularPatternFeatures
                features = core.ObjectCollection.create()
                features.add(slotFeature)

                axis, lineDir, negation = self.tComponent.getAxisOfLine(startLine)
                quantity = self.parameters.createValue(str(wallData.slotCount))
                dist = self.parameters.createValue(str(self.slotLengthVal + self.slotSpaceVal) + "*" + str(negation) + "cm")
                #dist = self.parameters.createValue(str("slotLength + slotSpacing") + "*" + str(negation) + "cm")
                rectangularPatternInput = rectangularPatterns.createInput(features, axis, quantity, dist, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)

                axis2 = self.yAxis if axis != self.yAxis else self.zAxis
                quantity2 = self.parameters.createValue('1')
                dist2 = self.parameters.createValue('0cm')
                rectangularPatternInput.setDirectionTwo(axis2, quantity2, dist2)
                
                rectangularPatternInput.patternComputeOption = f.PatternComputeOptions.IdenticalPatternCompute
                rectangularFeature = rectangularPatterns.add(rectangularPatternInput)

            if mirrorNewFeatures and wallData.midPlane:
                self.tComponent.mirrorFeaturesWithPlane(wallData.midPlane, slotFeature, rectangularFeature)
            result.append((slotFeature, rectangularFeature))
        return result
        
    def oppositeLineIndex(self, sourceIndex:int)->int:
        result = (sourceIndex + 2) % 4
        return result
        