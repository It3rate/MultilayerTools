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

class WallData:
    def __init__(self, slotKind:Sketches, slotCount:int, mirrorInvert:bool = False) -> None:
        self.slotKind:Sketches = slotKind
        self.slotCount:int = slotCount
        self.mirrorInvert = mirrorInvert

        self.tSketch:TurtleSketch = None
        self.edgeLines:tuple(f.SketchLine, f.SketchLine) = None
        self.isMirror = False
        self.midPlane:core.Plane = None
        self.reflectSlots:bool = True
    @classmethod
    def create(cls, slotKind:Sketches, slotCount:int, mirrored:bool = False):
        return cls( slotKind, slotCount, mirrored)

