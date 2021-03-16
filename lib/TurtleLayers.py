
import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from .TurtleUtils import TurtleUtils
from .TurtleParams import TurtleParams

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class TurtleLayers(list):
    # pass lists, or optionally single elements if specifying layerCount. layerCount should match list sizes if one is passed.
    def __init__(self, tcomponent:'TurtleComponent'):
        self.tcomponent = tcomponent
        self.component = tcomponent.component
        self.parameters = TurtleParams.instance()
        self.layers = []
        self.layerCount = 0

    @classmethod
    def createFromExisting(cls, tcomponent:'TurtleComponent'):
        result = cls(tcomponent)
        attrCount = tcomponent.component.attributes.itemByName("Turtle", "layerCount")
        if attrCount:
            for i in range(int(attrCount)):
                self.layers.append([])

            for body in tcomponent.component.bodies:
                bodyData = LayerBodyData.createWithExisting(body)
                self.layers[bodyData.layerIndex].append(bodyData)
        else:
            print("Mapped layers with non TurtleLayer component (layers will be empty).")
        return result

    @classmethod
    def createFromProfiles(cls, tcomponent:'TurtleComponent', profiles:list, thicknesses:list, layerCount:int = -1, isFlipped = False, appearanceList = []):
        result = cls(tcomponent)

        isListProfiles = isinstance(profiles, list)
        isListThickness = isinstance(thicknesses, list)
        profileCount = len(profiles) if isListProfiles else 1
        thicknessCount = len(thicknesses) if isListThickness else 1
        newLayerCount = layerCount if layerCount > 0 else max(profileCount, thicknessCount)
        result.profiles = profiles if isListProfiles else [profiles] * self.layerCount
        result.thicknesses = thicknesses if isListThickness else [thicknesses] * self.layerCount
        result.isFlipped = isFlipped
        result.appearanceList = appearanceList
        
        result.extrudes = result._extrudeAllLayers(newLayerCount)
        result.extend(result.extrudes)

        countAttr = result.component.attributes.itemByName("Turtle", "layerCount")
        count = int(countAttr) if countAttr else 0
        result.component.attributes.add("Turtle", "layerCount", str(self.layerCount + count))

        return result


    def _extrudeAllLayers(self, newLayerCount:int):
        for i in range(newLayerCount):
            self.layers.append([])

        extrudes = []
        startFace = None # zero distance from profile plane is default, startFrom is not set
        bodyCount = self.component.bRepBodies.count
        for i in range(newLayerCount):
            profileIndex = i if len(self.profiles) > i else len(self.profiles) - 1
            thicknessIndex = i if len(self.thicknesses) > i else len(self.thicknesses) - 1
            layerProfiles = TurtleUtils.ensureObjectCollection(self.profiles[profileIndex])
            extruded:f.ExtrudeFeature = self.tcomponent.extrude(layerProfiles, startFace, self.thicknesses[thicknessIndex], self.isFlipped)

            if len(self.appearanceList) > i:
                self.tcomponent.colorExtrudedBodiesByIndex(extruded, self.appearanceList[i])
            else:
                self.tcomponent.colorExtrudedBodiesByThickness(extruded, self.thicknesses[thicknessIndex])

            # mark layers with extrude index and body map
            start:f.BRepFace = startFace if startFace else extruded.startFaces[0]
            for body in extruded.bodies:
                bodyData = LayerBodyData.createNew(body, self.layerCount + i, bodyCount, start.entityToken, self.thicknesses[thicknessIndex], self.isFlipped)
                self.layers[bodyData.layerIndex].append(bodyData)
                bodyCount += 1

            extrudes.append(extruded)
            startFace = extruded.endFaces[0]
        self.layerCount += newLayerCount
        return extrudes

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



class LayerBodyData:
    def __init__(self, body:f.BRepBody):
        self.body = body
        self.layerIndex, self.bodyIndex, self.startFaceToken, self.thickness, self.isFlipped = self._getBodyAttributes(body)
        self.startFace = design.findEntityByToken(self.startFaceToken)

    @classmethod
    def createWithExisting(cls, body:f.BRepBody):
        return cls(body)

    @classmethod
    def createNew(cls, body:f.BRepBody, layerIndex:int, bodyIndex:int, startFaceToken:str, thickness, isFlipped:bool):
        cls._setBodyAttributes(body, layerIndex, bodyIndex, startFaceToken, thickness, isFlipped)
        return cls(body)

    @classmethod
    def _getBodyAttributes(cls, body:f.BRepBody):
        attrs = body.attributes
        attr = attrs.itemByName("Turtle", "layerIndex")
        layerIndex = int(attr.value) if attr else -1
        attr = attrs.itemByName("Turtle", "bodyIndex")
        bodyIndex = int(attr.value) if attr else -1
        attr = attrs.itemByName("Turtle", "startFace")
        startFaceToken = attr.value if attr else ""
        attr = attrs.itemByName("Turtle", "thickness")
        thickness = attr.value if attr else "0"
        attr = attrs.itemByName("Turtle", "isFlipped")
        isFlipped = bool(attr.value) if attr else False
        return layerIndex, bodyIndex, startFaceToken, thickness, isFlipped

    @classmethod
    def _setBodyAttributes(cls, body:f.BRepBody, layerIndex:int, bodyIndex:int, startFaceToken:str, thickness, isFlipped:bool):
        body.attributes.add("Turtle", "layerIndex", str(layerIndex))
        body.attributes.add("Turtle", "bodyIndex", str(bodyIndex))
        body.attributes.add("Turtle", "startFace", startFaceToken)
        body.attributes.add("Turtle", "thickness", str(thickness))
        body.attributes.add("Turtle", "isFlipped", str(isFlipped))