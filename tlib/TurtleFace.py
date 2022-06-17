from __future__ import annotations
import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from .TurtleUtils import TurtleUtils
from .TurtleParams import TurtleParams
from .TurtleSketch import TurtleSketch

f,core,app,ui = TurtleUtils.initGlobals()

class TurtleFace:
    def __init__(self, face:f.BRepFace):
        self.face:f.BRepFace = face
        self.parameters = TurtleParams.instance()
        self.body = face.body
        self.component = face.body.parentComponent

    @classmethod
    def createWithFace(cls, face:f.BRepFace):
        return cls(face)
        
    @property
    def area(self)->float:
        return self.face.area
        
    @property
    def normal(self)->core.Vector3D:
        return self.face.geometry.normal
    @property
    def isParamReversed(self)->bool:
        return self.face.isParamReversed
    @property
    def edges(self)->f.BRepEdges:
        return self.face.edges
    @property
    def loops(self)->f.BRepLoops:
        return self.face.loops
    @property
    def outerLoop(self)->f.BRepLoop:
        return next((loop for loop in self.face.loops if loop.isOuter) , None)
    @property
    def centroid(self)->core.Point3D:
        return self.face.centroid
    @property
    def vertices(self)->f.BRepVertices:
        return self.face.vertices
    def vertexAt(self, index:int)->f.BRepVertex:
        return self.vertices.item(index) if self.vertices.count > index else None

    @property
    def minPoint(self)->core.Point3D:
        minPt = self.face.boundingBox.minPoint
        return next((vertex for vertex in self.face.vertices if vertex.geometry.isEqualTo(minPt)) , None)
    @property
    def maxPoint(self)->core.Point3D:
        maxPt = self.face.boudingBox.minPoint
        return next((vertex for vertex in self.face.vertices if vertex.geometry.isEqualTo(maxPt)) , None)

    def reverseNormal(self)->core.Vector3D:
        return TurtleUtils.reverseVector(self.normal)

    def isNormalEqualTo(self, normal:core.Vector3D) -> bool:
        (success, ownNormal) = self.face.evaluator.getNormalAtPoint(self.face.pointOnFace)
        return ownNormal.isEqualTo(normal) if success else False

    def isNormalSame(self, tface:TurtleFace) -> bool:
        return self.isNormalEqualTo(tface.normal)

    def reverseNormal(self) -> adsk.core.Vector3D:
        return TurtleUtils.reverseVector(self.normal)

    def minDistanceTo(self, otherFace:f.BRepBody)->float:
        tempBR = f.TemporaryBRepManager.get()
        body1 = tempBR.copy(self.face)
        body2 = tempBR.copy(otherFace)
        dist = app.measureManager.measureMinimumDistance(body1, body2)
        self.thicknessVal = dist.value
        self.thicknessExpr = f'{dist.value} cm'
        
    def createSketchAtPoint(self, origin:core.Point3D, name:str = None):
        self.component.isConstructionFolderLightBulbOn = True
        planeInput:f.ConstructionPlaneInput = self.component.constructionPlanes.createInput()
        planeInput.setByTangentAtPoint(self.face, origin)
        plane = self.component.constructionPlanes.add(planeInput)
        result = TurtleSketch.createWithPlane(self.component, plane)
        if name:
            result.name = name
        return result