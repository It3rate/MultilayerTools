
import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from .TurtleUtils import TurtleUtils
from .TurtleParams import TurtleParams

f,core,app,ui = TurtleUtils.initGlobals()

class TurtleLayers:
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
            for i in range(int(attrCount.value)):
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
        # make extrude new bodies public and pass profiles, return extrudes.
        profiles = profiles if isListProfiles else [profiles] * newLayerCount
        thicknesses = thicknesses if isListThickness else [thicknesses] * newLayerCount
        
        result.extrudes = result._extrudeNewBodies(newLayerCount, profiles, thicknesses, isFlipped, appearanceList)

        countAttr = result.component.attributes.itemByName("Turtle", "layerCount")
        count = int(countAttr.value) if countAttr else 0
        result.component.attributes.add("Turtle", "layerCount", str(newLayerCount + count))

        return result


    def _extrudeNewBodies(self, newLayerCount:int, profiles:list, thicknesses:list, isFlipped:bool, appearanceList = []):
        for i in range(newLayerCount):
            self.layers.append([])

        extrudes = []
        startFace = None # zero distance from profile plane is default, startFrom is not set
        totalBodyCount = self.component.bRepBodies.count
        for i in range(newLayerCount):
            profileIndex = i if len(profiles) > i else len(profiles) - 1
            thicknessIndex = i if len(thicknesses) > i else len(thicknesses) - 1
            layerProfiles = TurtleUtils.ensureObjectCollection(profiles[profileIndex])
            extruded:f.ExtrudeFeature = self.tcomponent.extrude(layerProfiles, startFace, thicknesses[thicknessIndex], isFlipped)

            if len(appearanceList) > i:
                self.tcomponent.colorExtrudedBodiesByIndex(extruded, appearanceList[i])
            else:
                self.tcomponent.colorExtrudedBodiesByThickness(extruded, thicknesses[thicknessIndex])

            # mark layers with extrude index and body map
            start:f.BRepFace = startFace if startFace else extruded.startFaces[0]
            for body in extruded.bodies:
                bodyData = LayerBodyData.createNew(body, self.layerCount + i, totalBodyCount, start.entityToken, thicknesses[thicknessIndex], isFlipped)
                bodyData.profile = layerProfiles
                if len(appearanceList) > i:
                    bodyData.appearanceIndex = appearanceList[i]
                self.layers[bodyData.layerIndex].append(bodyData)
                totalBodyCount += 1

            extrudes.append(extruded)
            startFace = extruded.endFaces[0]
        self.layerCount += newLayerCount
        return extrudes

    def allLayerBodies(self):
        return self.getBodiesFrom(*range(self.layerCount))

    def getBodiesFrom(self, *extrudeIndexes:int):
        result = []
        for index in extrudeIndexes:
            for bodyData in self.layers[index]:
                if bodyData.body:
                    result.append(bodyData.body)
        return result

    def startFaceAt(self, extrudeIndex:int) -> f.BRepFace:  
        return self.extrudes[extrudeIndex].startFaces.item(0)

    def endFaceAt(self, extrudeIndex:int) -> f.BRepFace:
        return self.extrudes[extrudeIndex].endFaces.item(0)

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
    def __init__(self, body:f.BRepBody, layerIndex:int, bodyIndex:int, startFaceToken:str, thickness, isFlipped:bool):
        self.body = body
        self.layerIndex:int = layerIndex
        self.bodyIndex:int = bodyIndex
        self.startFaceToken:str = startFaceToken
        self.thickness = thickness
        self.isFlipped:bool = isFlipped
        self.profiles:f.ObjectCollection = None # collection of profiles if known
        self.appearanceIndex:int = -1 # appearance index if known
        if self.body:
            self.setBody(body)

    # def __init__(self, body:f.BRepBody):
    #     self.body = body
    #     self.layerIndex, self.bodyIndex, self.startFaceToken, self.thickness, self.isFlipped = self._getBodyAttributes(body)
    #     self.startFace = TurtleUtils.activeDesign().findEntityByToken(self.startFaceToken)

    @classmethod
    def createWithExisting(cls, body:f.BRepBody):
        #body, layerIndex, bodyIndex, startFaceToken, thickness, isFlipped = cls._getBodyAttributes(body)
        result = cls(body, cls._getBodyAttributes(body))
        return result

    @classmethod
    def createNew(cls, body:f.BRepBody, layerIndex:int, bodyIndex:int, startFaceToken:str, thickness, isFlipped:bool):
        result = cls(body, layerIndex, bodyIndex, startFaceToken, thickness, isFlipped)
        return result
        
    @classmethod
    def createWithoutBody(cls, layerIndex:int, bodyIndex:int, startFaceToken:str, thickness, isFlipped:bool):
        return cls(None, layerIndex, bodyIndex, startFaceToken, thickness, isFlipped)

    def setBody(self, body:f.BRepBody):
        self.body = body
        self._applyAttributesToBody(self.body)

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

    def _applyAttributesToBody(self, body:f.BRepBody):
        body.attributes.add("Turtle", "layerIndex", str(self.layerIndex))
        body.attributes.add("Turtle", "bodyIndex", str(self.bodyIndex))
        body.attributes.add("Turtle", "startFace", self.startFaceToken)
        body.attributes.add("Turtle", "thickness", str(self.thickness))
        body.attributes.add("Turtle", "isFlipped", str(self.isFlipped))
        if self.profiles:
            profileString = "["
            comma = ""
            for profile in self.profiles:
                profileString += comma + profile.entityToken
                comma = ","
            profileString += "]"
            body.attributes.add("Turtle", "profiles", profileString)
        if self.appearanceIndex > -1:
            body.attributes.add("Turtle", "appearanceIndex", str(selfappearanceIndex))
