import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from enum import Enum

from .TurtleSketch import TurtleSketch
from .TurtleUtils import TurtleUtils
from .data.SketchData import Sketches

f:adsk.fusion
core:adsk.core
f,core,app,ui = TurtleUtils.initGlobals()

class SlotKind(Enum):
    none = 0
    hole = 10
    holeEdge = 11
    holeLock = 12
    finger = 20
    fingerEdge = 21
    fingerLock = 22
    fingerPokeLock = 23

class WallKind(Enum):
    none = 0
    topInner= 10
    topCenter = 11
    topOuter = 12
    topHole = 13
    bottomInner= 20
    bottomCenter = 21
    bottomOuter = 22
    frontInner= 30
    frontCenter = 31
    frontOuter = 32
    backInner= 40
    backCenter = 41
    backOuter = 42
    leftInner= 50
    leftCenter = 51
    leftOuter = 52
    rightInner= 60
    rightCenter = 61
    rightOuter = 62
    holeInner= 70
    holeCenter= 71
    holeOuter= 72

    def isLeftRight(self):
        return int(self.value) >= 50 and int(self.value) < 70

    def isTopBottom(self):
        return self.isKindTopBottom(self)
    def isFrontBack(self):
        return self.isKindFrontBack(self)
    def isLeftRight(self):
        return self.isKindLeftRight(self)
    def isHole(self):
        return self.isKindHole(self)
    def isInner(self):
        return self.isKindInner(self)
    def isCenter(self):
        return self.isKindCenter(self)
    def isOuter(self):
        return self.isKindOuter(self)
    def oppositeWall(self):
        return self.kindOppositeWall(self)

    @property
    def colorIndex(self):
        result = 0
        if self == WallKind.bottomInner:
            result = 3
        elif self.isLeftRight():
            result = 1
        elif self.isFrontBack():
            result = 2
        return result

    @classmethod
    def isKindTopBottom(cls, wallKind):
        return int(wallKind.value) > 0 and int(wallKind.value) < 30
    @classmethod
    def isKindFrontBack(cls, wallKind):
        return int(wallKind.value) >= 30 and int(wallKind.value) < 50
    @classmethod
    def isKindLeftRight(cls, wallKind):
        return int(wallKind.value) >= 50 and int(wallKind.value) < 70
    @classmethod
    def isKindHole(cls, wallKind):
        return int(wallKind.value) >= 70 and int(wallKind.value) < 80
    @classmethod
    def isKindInner(cls, wallKind):
        return int(wallKind.value) % 10 == 0
    @classmethod
    def isKindCenter(cls, wallKind):
        return int(wallKind.value) % 10 == 1
    @classmethod
    def isKindOuter(cls, wallKind):
        return int(wallKind.value) % 10 == 2
    @classmethod
    def edgesToOffsetForKind(cls, wallKind)->tuple[list[int], bool]: # cw from bottom left
        result = []
        isNeg = False
        if cls.isTopBottom(wallKind):
            isNeg = False
            result = [] if cls.isInner(wallKind) else [0,1,2,3] # expand all lid, none for floor
        elif cls.isLeftRight(wallKind):
            isNeg = True
            result = [0,2,3] if cls.isInner(wallKind) else [] # contract sides, and floor line if inner
        elif cls.isFrontBack(wallKind):
            isNeg = True
            result = [3] if cls.isInner(wallKind) else [0,2] # contract floor line if inner
        elif cls.isHole(wallKind):
            isNeg = True
            result = [0,1,2,3] # expand all the top hole edges inward to make room for slot holes on wall line
        return (result, isNeg)
    @classmethod
    def getSlotKinds(cls, wallKind)->list[int]:
        result = []
        if cls.isTopBottom(wallKind):
            result = [SlotKind.hole, SlotKind.hole, SlotKind.hole, SlotKind.hole] 
        elif cls.isLeftRight(wallKind):
            result =[SlotKind.finger, SlotKind.holeLock, SlotKind.finger, SlotKind.holeLock] 
        elif cls.isFrontBack(wallKind):
            result =[SlotKind.finger, SlotKind.fingerLock, SlotKind.finger, SlotKind.fingerLock] 
        elif cls.isHole(wallKind):
            result = [SlotKind.hole, SlotKind.hole, SlotKind.hole, SlotKind.hole] 

    @classmethod
    def kindOppositeWall(cls, wallKind):
        result = WallKind.none
        if wallKind == WallKind.topInner:
            result = WallKind.bottomInner
        elif wallKind == WallKind.topCenter :
            result = WallKind.bottomCenter
        elif wallKind == WallKind.topOuter :
            result = WallKind.bottomOuter
        elif wallKind == WallKind.bottomInner:
            result = WallKind.topInner
        elif wallKind == WallKind.bottomCenter :
            result = WallKind.topCenter
        elif wallKind == WallKind.bottomOuter :
            result = WallKind.topOuter
        elif wallKind == WallKind.frontInner:
            result = WallKind.backInner
        elif wallKind == WallKind.frontCenter :
            result = WallKind.backCenter
        elif wallKind == WallKind.frontOuter :
            result = WallKind.backOuter
        elif wallKind == WallKind.backInner:
            result = WallKind.frontInner
        elif wallKind == WallKind.backCenter :
            result = WallKind.frontCenter
        elif wallKind == WallKind.backOuter :
            result = WallKind.frontOuter
        elif wallKind == WallKind.leftInner:
            result = WallKind.rightInner
        elif wallKind == WallKind.leftCenter :
            result = WallKind.rightCenter
        elif wallKind == WallKind.leftOuter :
            result = WallKind.rightOuter
        elif wallKind == WallKind.rightInner:
            result = WallKind.leftInner
        elif wallKind == WallKind.rightCenter :
            result = WallKind.leftCenter
        elif wallKind == WallKind.rightOuter :
            result = WallKind.leftOuter
        return result

class WallData:
    def __init__(self, slotKind:Sketches, slotCount:int, mirrorInvert:bool, midPlane:core.Plane) -> None:
        self.slotKind:Sketches = slotKind
        self.slotCount:int = slotCount
        self.mirrorInvert = mirrorInvert
        self.midPlane = midPlane

        self.tSketch:TurtleSketch = None
        self.edgeLines:tuple(f.SketchLine, f.SketchLine) = None
        self.isMirror = False
        self.reflectSlots:bool = True
    @classmethod
    def create(cls, slotKind:Sketches, slotCount:int, mirrored:bool, midPlane:core.Plane):
        return cls( slotKind, slotCount, mirrored, midPlane)

