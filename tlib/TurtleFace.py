
import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from .TurtleUtils import TurtleUtils
from .TurtleParams import TurtleParams

f,core,app,ui = TurtleUtils.initGlobals()

class TurtleFace:
    def __init__(self, face:f.BRepFace):
        self.face:f.BRepFace = face
        self.parameters = TurtleParams.instance()
        self.body = face.body
        self.component = face.body.parentComponent
        
    @property
    def normal(self):
        return self.face.geometry.normal

    def reverseNormal(self) -> adsk.core.Vector3D:
        return TurtleUtils.reverseVector(self.normal)

    def minDistanceTo(self, otherFace:f.BRepBody)->float:
        tempBR = f.TemporaryBRepManager.get()
        body1 = tempBR.copy(self.face)
        body2 = tempBR.copy(otherFace)
        dist = app.measureManager.measureMinimumDistance(body1, body2)
        self.thicknessVal = dist.value
        self.thicknessExpr = f'{dist.value} cm'