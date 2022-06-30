import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from enum import Enum
from collections.abc import Iterable

from .TurtleSketch import TurtleSketch
from .TurtleUtils import *
from .TurtlePath import TurtlePath
from .TurtleParams import TurtleParams
from .TurtleParams import TurtleParams
from .data.SketchData import BuiltInDrawing, SketchData

f:adsk.fusion
core:adsk.core
f,core,app,ui = TurtleUtils.initGlobals()

class TurtleWall:
    def __init__(self, face:f.BRepFace, wallKind:SurfaceKind):
        self.face:f.BRepFace = face
        self.tSketch:TurtleSketch = None
        self.wallKind:SurfaceKind = wallKind

    @property
    def sketch(self)->f.Sketch:
        return self.tSketch.sketch
    
    def getXVector(self)->core.Vector3D:
        return self.sketch.xDirection
    def getYVector(self)->core.Vector3D:
        return self.sketch.yDirection
        
    def getOrientationForVector(self, vec:core.Vector3D)->Orientation:
        return self.sketch.yDirection

    def getSlotCountForEdge(self, orientation:Orientation)->int:
        pass
    
    def getLineByGlobalOrientation(self, orientation:Orientation)->f.SketchLine:
        pass

    def offsetLines(self, lines, orientations:list[Orientation], extrudeDistance)->list[f.SketchLine]:
        pass

    def addSlotsToLine(self, lines, orientations:Orientation, count:int):
        pass

    def mirrorEdge(self, orientations:Orientation):
        pass

    def extrude(self, profiles:list[f.Profile], extrudeDistance):
        pass

    def patternFeature(self):
        pass


class SketchPointPair:
    def __init__(self, p0:f.SketchPoint, p1:f.SketchPoint):
        self.p0:f.SketchPoint = p0
        self.p1:f.SketchPoint = p1

class PointPair:
    def __init__(self, p0:core.Point3D, p1:core.Point3D):
        self.p0:f.Point3D = p0
        self.p1:f.Point3D = p1

class WallData:
    def __init__(self, wallKind:SurfaceKind, face:f.BRepFace, extrudeDistance, ):
        self.wallKind:SurfaceKind = wallKind
        self.face:f.BRepFace = face
        self.sketchKinds:list[BuiltInDrawing]
        self.extrudeDistance = extrudeDistance
        self.extrudeLineIndexes: list[int]
            
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
