
import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from .TurtleUtils import TurtleUtils
from .TurtleParams import TurtleParams

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class TurtleLayers(list):
    # pass lists, or optionally single elements if specifying layerCount. layerCount should match list sizes if one is passed.
    def __init__(self, tcomponent:'TurtleComponent', profiles:list, thicknesses:list, layerCount:int = 1):
        self.tcomponent = tcomponent
        self.component = tcomponent.component
        self.parameters = TurtleParams.instance()

        isListProfiles = isinstance(profiles, list)
        isListThickness = isinstance(thicknesses, list)
        self.layerCount = len(profiles) if isListProfiles else len(thicknesses) if isListThickness else layerCount
        self.profiles = profiles if isListProfiles else [profiles] * self.layerCount
        self.thicknesses = thicknesses if isListThickness else [thicknesses] * self.layerCount

        self.extrudes = self._extrudeAllLayers()
        self.extend(self.extrudes)

    def _extrudeAllLayers(self):
        extrudes = []
        startFace = 0
        for i in range(self.layerCount):
            extruded = self.tcomponent.extrude(self.profiles[i], startFace, self.thicknesses[i])
            extrudes.append(extruded)
            startFace = extruded.endFaces.item(0)
        return extrudes

    def __getitem__(self, item) -> f.ExtrudeFeature:
        return self.extrudes.__getitem__(item)

    def bodyAt(self, extrudeIndex:int, bodyIndex:int = 0) -> f.BRepBody:
        return self[extrudeIndex].bodies.item(bodyIndex)

    def allLayerBodies(self):
        return self.getBodiesFrom(*range(self.layerCount))

    def getBodiesFrom(self, *extrudeIndexes:int):
        result = []
        for index in extrudeIndexes:
            for body in self[index].bodies:
                result.append(body)
        return result

    def startFaceAt(self, extrudeIndex:int) -> f.BRepFace:
        return self[extrudeIndex].startFaces.item(0)

    def endFaceAt(self, extrudeIndex:int) -> f.BRepFace:
        return self[extrudeIndex].endFaces.item(0)

    def cutWithProfiles(self, profiles):
        self.cutBodiesWithProfiles(profiles, *range(self.layerCount))

    def cutBodiesWithProfiles(self, profiles, *bodyIndexes:int):
        profiles = profiles if isinstance(profiles, list) else [profiles] * len(bodyIndexes)
        for i in range(len(bodyIndexes)):
            bodies = self.getBodiesFrom(bodyIndexes[i])
            pindex = min(i, len(profiles) - 1)
            for body in bodies:
                self.tcomponent.cutBodyWithProfile(profiles[pindex], body)

    def mirrorLayers(self, plane:f.ConstructionPlane, isJoined:bool = False):
        mirrorFeatures = self.component.features.mirrorFeatures
        inputEntites = core.ObjectCollection.create()
        for body in self.allLayerBodies():
            inputEntites.add(body)
        mirrorInput:f.MirrorFeatureInput = mirrorFeatures.createInput(inputEntites, plane)
        mirrorInput.isCombine = isJoined
        mirrorFeature = mirrorFeatures.add(mirrorInput)
        return mirrorFeature
