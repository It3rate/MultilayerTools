
import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from .TurtleUtils import TurtleUtils
from .TurtleParams import TurtleParams
from .TurtleComponent import TurtleComponent

f,core,app,ui = TurtleUtils.initGlobals()

class TurtleLayers:
    # pass lists, or optionally single elements if specifying layerCount. layerCount should match list sizes if one is passed.
    def __init__(self, tcomponent:TurtleComponent):
        self.tcomponent = tcomponent
        self.component = tcomponent.component
        self.parameters = TurtleParams.instance()
        self.layers = []
        self.layerCount = 0

    @classmethod
    def createFromExisting(cls, tcomponent:TurtleComponent):
        result = cls(tcomponent)
        attrCount = tcomponent.component.attributes.itemByName("Turtle", "layerCount")
        if attrCount:
            for feature in tcomponent.component.features:
                if type(feature) == f.ExtrudeFeature:
                    layerData = LayerData.createWithExisting(feature)
                    self.layers.append(layerData)
        else:
            print("Mapped layers with non TurtleLayer component (layers will be empty).")
        return result

    @classmethod
    def createFromProfiles(cls, tcomponent:TurtleComponent, profiles:list, thicknesses:list, layerCount:int = -1, isFlipped = False, appearanceList = []):
        result = cls(tcomponent)

        isListProfiles = isinstance(profiles, list)
        isListThickness = isinstance(thicknesses, list)
        profileCount = len(profiles) if isListProfiles else 1
        thicknessCount = len(thicknesses) if isListThickness else 1
        newLayerCount = layerCount if layerCount > 0 else max(profileCount, thicknessCount)
        profiles = profiles if isListProfiles else [profiles] * newLayerCount
        thicknesses = thicknesses if isListThickness else [thicknesses] * newLayerCount
        
        result._extrudeNewBodies(newLayerCount, profiles, thicknesses, isFlipped, appearanceList)

        countAttr = result.component.attributes.itemByName("Turtle", "layerCount")
        count = int(countAttr.value) if countAttr else 0
        result.component.attributes.add("Turtle", "layerCount", str(newLayerCount + count))

        return result


    def _extrudeNewBodies(self, newLayerCount:int, profiles:list, thicknesses:list, isFlipped:bool, appearanceList = []):
        # for i in range(newLayerCount):
        #     self.layers.append([])

        startFace = None # zero distance from profile plane is default, startFrom is not set
        for i in range(newLayerCount):
            profileIndex = i if len(profiles) > i else len(profiles) - 1
            thicknessIndex = i if len(thicknesses) > i else len(thicknesses) - 1
            layerProfiles = TurtleUtils.ensureObjectCollection(profiles[profileIndex])
            extruded:f.ExtrudeFeature = self.tcomponent.extrude(layerProfiles, startFace, thicknesses[thicknessIndex], isFlipped)

            appearanceIndex = -1
            if len(appearanceList) > i:
                self.tcomponent.colorExtrudedBodiesByIndex(extruded, appearanceList[i])
                appearanceIndex = i
            else:
                self.tcomponent.colorExtrudedBodiesByThickness(extruded, thicknesses[thicknessIndex])

            # mark layers with extrude index and body map
            start:f.BRepFace = startFace if startFace else extruded.startFaces[0]
            extrudeData = LayerData.createNew(extruded, self.layerCount + i, thicknesses[thicknessIndex], isFlipped, appearanceIndex)
            self.layers.append(extrudeData)

            startFace = extruded.endFaces[0]
        self.layerCount += newLayerCount

    def extrudeForLayer(self, extrudeIndex:int) -> f.ExtrudeFeature:  
        return self.layers[index].extrude if len(self.layers) > index else None

    def firstLayerExtrude(self, extrudeIndex:int) -> f.ExtrudeFeature:  
        return self.layers[0].extrude if len(self.layers) > 0 else None
    def lastLayerExtrude(self, extrudeIndex:int) -> f.ExtrudeFeature:  
        return self.layers[-1].extrude if len(self.layers) > 0 else None

    def allLayerBodies(self):
        return self.getBodiesFrom(*range(self.layerCount))

    def getBodiesFrom(self, *extrudeIndexes:int):
        result = []
        for index in extrudeIndexes:
            if len(self.layers) > index:
                result.append(*self.layers[index].getBodyList())
        return result

    def startFaceAt(self, extrudeIndex:int) -> f.BRepFace:  
        return self.layers[0].getAStartFace() if len(self.layers) > 0 else None

    def endFaceAt(self, extrudeIndex:int) -> f.BRepFace:
        return self.layers[-1].getAnEndFace() if  len(self.layers) > 0 else None

    def cutWithProfiles(self, cutProfiles):
        self.cutBodiesWithProfiles(cutProfiles, *range(self.layerCount))

    def cutBodiesWithProfiles(self, cutProfiles, *bodyIndexes:int):
        cutProfiles = cutProfiles if isinstance(cutProfiles, list) else [cutProfiles] * len(bodyIndexes)
        for i in range(len(bodyIndexes)):
            bodies = self.getBodiesFrom(bodyIndexes[i])
            pindex = min(i, len(cutProfiles) - 1)
            for body in bodies:
                self.tcomponent.cutBodyWithProfile(cutProfiles[pindex], body)

    def mirrorLayers(self, plane:f.ConstructionPlane, isJoined:bool = False):
        mirrorFeatures = self.component.features.mirrorFeatures
        inputEntites = core.ObjectCollection.create()
        for body in self.allLayerBodies():
            inputEntites.add(body)
        mirrorInput:f.MirrorFeatureInput = mirrorFeatures.createInput(inputEntites, plane)
        mirrorInput.isCombine = isJoined
        mirrorFeature = mirrorFeatures.add(mirrorInput)
        return mirrorFeature



class LayerData:
    def __init__(self, extrude:f.ExtrudeFeature, layerIndex:int, thickness, isFlipped:bool, appearanceIndex:int = -1):
        self.extrude = extrude
        self.layerIndex:int = layerIndex
        self.thickness = thickness
        self.isFlipped:bool = isFlipped
        self.appearanceIndex:int = appearanceIndex
        if self.extrude:
            self.setExtrude(extrude)

    # def __init__(self, body:f.BRepBody):
    #     self.body = body
    #     self.layerIndex, self.bodyIndex, self.startFaceToken, self.thickness, self.isFlipped = self._getBodyAttributes(body)
    #     self.startFace = TurtleUtils.activeDesign().findEntityByToken(self.startFaceToken)

    @classmethod
    def createWithExisting(cls, extrude:f.ExtrudeFeature):
        #body, layerIndex, bodyIndex, startFaceToken, thickness, isFlipped = cls._getAttributes(body)
        result = cls(extrude, cls._getAttributes(extrude))
        return result

    @classmethod
    def createNew(cls, extrude:f.ExtrudeFeature, layerIndex:int, thickness, isFlipped:bool, appearanceIndex:int = -1):
        result = cls(extrude, layerIndex, thickness, isFlipped, appearanceIndex)
        return result
        
    @classmethod
    def createWithoutBody(cls, layerIndex:int, thickness, isFlipped:bool, appearanceIndex:int = -1):
        return cls(None, layerIndex, thickness, isFlipped, appearanceIndex)

    def setExtrude(self, extrude:f.ExtrudeFeature):
        self.extrude = extrude
        self._applyAttributesToExtrude(self.extrude)

    def getBodyList(self):
        return TurtleUtils.ensureList(self.extrude.bodies) if self.extrude else []
    def getProfileList(self):
        return TurtleUtils.ensureList(self.extrude.profile) if self.extrude else []
    def getStartFaceList(self):
        return TurtleUtils.ensureList(self.extrude.startFaces) if self.extrude else []
    def getAStartFace(self):
        return self.extrude.startFaces[0] if self.extrude else None
    def getEndFaceList(self):
        return TurtleUtils.ensureList(self.extrude.endFaces) if self.extrude else []
    def getAnEndFace(self):
        return self.extrude.endFaces[0] if self.extrude else None
    def getExtrudeToken(self):
        return self.extrude.entityToken

    @classmethod
    def _getAttributes(cls, extrude:f.ExtrudeFeature):
        attrs = extrude.attributes
        attr = attrs.itemByName("Turtle", "layerIndex")
        layerIndex = int(attr.value) if attr else -1
        attr = attrs.itemByName("Turtle", "thickness")
        thickness = attr.value if attr else "0"
        attr = attrs.itemByName("Turtle", "isFlipped")
        isFlipped = bool(attr.value) if attr else False
        attr = attrs.itemByName("Turtle", "appearanceIndex")
        appearanceIndex = bool(attr.value) if attr else -1
        return layerIndex, thickness, isFlipped, appearanceIndex

    def _applyAttributesToExtrude(self, body:f.BRepBody):
        body.attributes.add("Turtle", "layerIndex", str(self.layerIndex))
        body.attributes.add("Turtle", "thickness", str(self.thickness))
        body.attributes.add("Turtle", "isFlipped", str(self.isFlipped))
        body.attributes.add("Turtle", "appearanceIndex", str(self.appearanceIndex))
