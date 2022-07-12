import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from enum import Enum
from collections.abc import Iterable

from .data.SketchData import BuiltInDrawing, SketchData
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
    def __init__(self, tFace:TurtleFace, wallKind:WallKind, crossData:WallSlotData, outwardData:WallSlotData, colorIndex:int = 0):
        self.tFace:TurtleFace = tFace
        self.wallKind:WallKind = wallKind
        self.crossData:WallSlotData = crossData
        self.outwardData:WallSlotData = outwardData
        self.colorIndex:int = colorIndex

        self.face:f.BRepFace = self.tFace.face

        self.tComponent = None
        self.tSketch:TurtleSketch = None


        self.baseFeature:f.ExtrudeFeature = None
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
    def create(cls, face:f.BRepFace, wallKind:WallKind,):
        result = cls(face, wallKind, None, None) 
        result.run()
        return result

    def run(self):
        self.projectFaceEdges()
        linesToOffest, isNeg = WallKind.edgesToOffsetForKind(self.wallKind)
        distExpr = self.negWallThicknessExpr if isNeg else self.wallThicknessExpr
        self.offsetEdges(linesToOffest, distExpr)

    def projectFaceEdges(self, projectLoopIndex:int = 0, asConstruction:bool = True) -> \
                tuple[f.Component, f.Sketch, list[f.SketchLine]]:
        self.tSketch = self.tFace.createSketchAtPoint(self.face.centroid)
        self.tComponent = TurtleComponent.createFromSketch(self.tSketch.sketch)
        if projectLoopIndex < self.face.loops.count:
            loop = self.face.loops[projectLoopIndex]
            self.projectedLines = self.tSketch.projectList(loop.edges, asConstruction)

    def offsetEdges(self, edgeIndexes:list[int], expression:str)-> list[f.BRepEdges]:
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
            pass
        ptPairs = self.tSketch.getRectPointChain(linesForCorners, True)
        self.boundryLines = self.tSketch.drawLines(ptPairs)
        self.baseFeature = self.tComponent.extrudeLargestProfile(self.tSketch, self.wallThicknessExpr, 1)


    def createInnerFrontAndBack(self, isPreview:bool):
        projectedList = self.sketchFromFace(self.backInnerFace, 0, True)
        # shrink bottom only, make holes in the sides, fingers in the bottom and top
        offsetLines = self.tSketch.offset([projectedList[3]], self.backInnerFace.centroid, '-' + self.wallThicknessExpr, True)[0]
        topLine = projectedList[1]
        bottomLine = offsetLines[0]
        # ptPairs = \
        #   self.getSortedRectSegments(topLine.startSketchPoint, bottomLine.startSketchPoint, bottomLine.endSketchPoint, topLine.endSketchPoint)
        ptPairs = self.tSketch.getRectPointChain([topLine, bottomLine], True)
        boundryLines = self.tSketch.drawLines(ptPairs)
        # main rect extrude
        rectFeature = self.tComponent.extrudeLargestProfile(self.tSketch, self.wallThicknessExpr, 1)

        bottomTop = self.tComponent.getLinesByAxis(self.xAxis, self.zAxis, boundryLines)
        leftRight = self.tComponent.getLinesByAxis(self.zAxis, self.xAxis, boundryLines)
        btMidPlane = self.midPlaneOnLine(leftRight[0])
        lrMidPlane = self.midPlaneOnLine(bottomTop[0])
        self.createMirroredFeatures(bottomTop, btMidPlane, BuiltInDrawing.edgeFilletFinger, 8, rectFeature, f.FeatureOperations.JoinFeatureOperation)# self.slotCountHeight)
        self.createMirroredFeatures(leftRight, lrMidPlane, BuiltInDrawing.edgeFilletHole, 4, rectFeature, f.FeatureOperations.CutFeatureOperation)# self.slotCountHeight)

        # Set the data for second direction
        #rectangularPatternInput.setDirectionTwo(yAxis, quantityTwo, distanceTwo)
        
        # Create the rectangular pattern
        # rectangularFeature = rectangularPatterns.add(rectangularPatternInput)
        return

    # def createMirroredFeatures(self, lines:tuple[f.SketchLine,f.SketchLine], midPlane:f.ConstructionPlane,\
    #                  slotKind:BuiltInDrawing, count:int)->f.SketchLine:
    #     op = BuiltInDrawing.normalOperationForDrawing(slotKind)
    #     projLines = self.sketchFromFaceAndLines(face, lines)
    #     startLine = projLines[0]
    #     endLine = projLines[1]
    #     tabPts = self.tSketch.createFirstTabPoints(startLine.startSketchPoint, startLine.endSketchPoint,\
    #          self.slotLengthVal, self.slotSpaceVal, count)
    #     drawData = SketchData.createFromBuiltIn(slotKind)
    #     decoder = TurtleDecoder.createWithPoints(drawData, self.tSketch.sketch, tabPts)
    #     slotFeature = self.tComponent.extrudeAllProfiles(self.tSketch, self.wallThicknessExpr, 1)

    #     if self.baseFeature:
    #         if op == f.FeatureOperations.CutFeatureOperation:
    #             TurtleLayers.changeExtrudeOperation(slotFeature, self.baseFeature.bodies, op)
    #         elif op == f.FeatureOperations.JoinFeatureOperation:
    #             TurtleLayers.changeExtrudeOperation(slotFeature, self.baseFeature.bodies, op)
    #         elif op == f.FeatureOperations.IntersectFeatureOperation:
    #             TurtleLayers.changeExtrudeOperation(slotFeature, self.baseFeature.bodies, op)
        
    #     rectangularPatterns = self.component.features.rectangularPatternFeatures
    #     features = core.ObjectCollection.create()
    #     features.add(slotFeature)

    #     axis, lineDir, negation = self.tComponent.getAxisOfLine(startLine)
    #     quantity = self.parameters.createValue(str(count))
    #     dist = self.parameters.createValue(str(self.slotLengthVal + self.slotSpaceVal) + "*" + str(negation) + "cm")
    #     rectangularPatternInput = rectangularPatterns.createInput(features, axis, quantity, dist, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)

    #     axis2 = self.yAxis if axis != self.yAxis else self.zAxis
    #     quantity2 = self.parameters.createValue('1')
    #     dist2 = self.parameters.createValue('0cm')
    #     rectangularPatternInput.setDirectionTwo(axis2, quantity2, dist2)
        
    #     rectangularPatternInput.patternComputeOption = f.PatternComputeOptions.IdenticalPatternCompute
    #     rectangularFeature = rectangularPatterns.add(rectangularPatternInput)

    #     if midPlane:
    #         self.tComponent.mirrorFeaturesWithPlane(midPlane, slotFeature, rectangularFeature)
    #     return (slotFeature, rectangularFeature)
        

    # def createMirroredFeaturesX(self, lines:tuple[f.SketchLine,f.SketchLine], midPlane:f.ConstructionPlane, slotKind:BuiltInDrawing, count:int, \
    #                  targetFeature:f.Feature = None, op:f.FeatureOperations = f.FeatureOperations.JoinFeatureOperation)->f.SketchLine:
    #     projLines = self.sketchFromFaceAndLines(self.backInnerFace, lines)
    #     startLine = projLines[0]
    #     endLine = projLines[1]
    #     tabPts = self.tSketch.createFirstTabPoints(startLine.startSketchPoint, startLine.endSketchPoint,\
    #          self.slotLengthVal, self.slotSpaceVal, count)
    #     drawData = SketchData.createFromBuiltIn(slotKind)
    #     decoder = TurtleDecoder.createWithPoints(drawData, self.tSketch.sketch, tabPts)
    #     slotFeature = self.tComponent.extrudeAllProfiles(self.tSketch, self.wallThicknessExpr, 1)

    #     if targetFeature:
    #         if op == f.FeatureOperations.CutFeatureOperation:
    #             TurtleLayers.changeExtrudeOperation(slotFeature, targetFeature.bodies, op)
    #         elif op == f.FeatureOperations.JoinFeatureOperation:
    #             TurtleLayers.changeExtrudeOperation(slotFeature, targetFeature.bodies, op)
    #         elif op == f.FeatureOperations.IntersectFeatureOperation:
    #             TurtleLayers.changeExtrudeOperation(slotFeature, targetFeature.bodies, op)
        
    #     rectangularPatterns = self.component.features.rectangularPatternFeatures
    #     features = core.ObjectCollection.create()
    #     features.add(slotFeature)

    #     axis, lineDir, negation = self.tComponent.getAxisOfLine(startLine)
    #     quantity = self.parameters.createValue(str(count))
    #     dist = self.parameters.createValue(str(self.slotLengthVal + self.slotSpaceVal) + "*" + str(negation) + "cm")
    #     rectangularPatternInput = rectangularPatterns.createInput(features, axis, quantity, dist, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)

    #     axis2 = self.yAxis if axis != self.yAxis else self.zAxis
    #     quantity2 = self.parameters.createValue('1')
    #     dist2 = self.parameters.createValue('0cm')
    #     rectangularPatternInput.setDirectionTwo(axis2, quantity2, dist2)
        
    #     rectangularPatternInput.patternComputeOption = f.PatternComputeOptions.IdenticalPatternCompute
    #     rectangularFeature = rectangularPatterns.add(rectangularPatternInput)

    #     if midPlane:
    #         self.tComponent.mirrorFeaturesWithPlane(midPlane, slotFeature, rectangularFeature)
    #     return (slotFeature, rectangularFeature)
        
#     def oppositeLineIndex(sourceIndex:int)->int:
#         result = (sourceIndex + 2) % 4

#     def getLineByGlobalOrientation(self, orientation:Orientation)->f.SketchLine:
#         pass
    
#     def getXVector(self)->core.Vector3D:
#         return self.sketch.xDirection
#     def getYVector(self)->core.Vector3D:
#         return self.sketch.yDirection
        
#     def getOrientationForVector(self, vec:core.Vector3D)->Orientation:
#         return self.sketch.yDirection

#     def getSlotCountForEdge(self, orientation:Orientation)->int:
#         pass
    

#     def offsetLines(self, lines, orientations:list[Orientation], extrudeDistance)->list[f.SketchLine]:
#         pass

#     def addSlotsToLine(self, lines, orientations:Orientation, count:int):
#         pass

#     def mirrorEdge(self, orientations:Orientation):
#         pass

#     def extrude(self, profiles:list[f.Profile], extrudeDistance):
#         pass

#     def patternFeature(self):
#         pass


# class SketchPointPair:
#     def __init__(self, p0:f.SketchPoint, p1:f.SketchPoint):
#         self.p0:f.SketchPoint = p0
#         self.p1:f.SketchPoint = p1

# class PointPair:
#     def __init__(self, p0:core.Point3D, p1:core.Point3D):
#         self.p0:f.Point3D = p0
#         self.p1:f.Point3D = p1

# class WallData:
#     def __init__(self, wallKind:SurfaceKind, face:f.BRepFace, extrudeDistance, ):
#         self.wallKind:SurfaceKind = wallKind
#         self.face:f.BRepFace = face
#         self.sketchKinds:list[BuiltInDrawing]
#         self.extrudeDistance = extrudeDistance
#         self.extrudeLineIndexes: list[int]
            
    # kind # outerFront, innerLeft etc 
    # faceRef # BRepFace
    # extrude distance
    # slotKind # drawing to paste
    # wallThickness # default from table
    # slotCount # default from table
    # isMirrored # default no,or drawings all consistant?
    # isNegated # default no, or drawings all consistant?
    # profileKind # default outer, largest, [index list]
    # extrudeKind # default new, cut, join, intersect
    # makeSymetricCopy # always true?
    # name # optional body/component name
    # colorIndex # optional color

    # global:
    # wallThickness # list, or one value - interior from model, exteriors all same
    # slotcounts[] #width, depth, height (inner is one less?) 
    # slotLength
    # lipLength
    # slotSpacingPercent?
    
    
    # # project face, offset lines, make ring, draw slots (type, count, mirror/neg - per edge), 
    # # find profile, extrude/cut, offset to other wall, name, color
