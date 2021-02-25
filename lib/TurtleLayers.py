
import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from .TurtleUtils import TurtleUtils
from .TurtleParams import TurtleParams

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class TurtleLayers(list):
    # pass lists, or optionally single elements if specifying layerCount. layerCount should match list sizes if one is passed.
    def __init__(self, tcomponent:'TurtleComponent', profiles:list, thicknesses:list, layerCount:int = -1, isFlipped = False):
        self.tcomponent = tcomponent
        self.component = tcomponent.component
        self.parameters = TurtleParams.instance()
        self.sketch = None

        isListProfiles = isinstance(profiles, list)
        isListThickness = isinstance(thicknesses, list)
        profileCount = len(profiles) if isListProfiles else 1
        thicknessCount = len(thicknesses) if isListThickness else 1
        self.layerCount = layerCount if layerCount > 0 else max(profileCount, thicknessCount)
        self.profiles = profiles if isListProfiles else [profiles] * self.layerCount
        self.thicknesses = thicknesses if isListThickness else [thicknesses] * self.layerCount
        self.isFlipped = isFlipped
        
        self.extrudes = self._extrudeAllLayers()
        self.extend(self.extrudes)

    def _extrudeAllLayers(self):
        extrudes = []
        startFace = 0
        for i in range(self.layerCount):
            profileIndex = i if len(self.profiles) > i else len(self.profiles) - 1
            thicknessIndex = i if len(self.thicknesses) > i else len(self.thicknesses) - 1
            layerProfiles = TurtleUtils.ensureObjectCollection(self.profiles[profileIndex])
            self.sketch = layerProfiles[0].parentSketch
            extruded = self.tcomponent.extrude(layerProfiles, startFace, self.thicknesses[thicknessIndex], self.isFlipped)
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
