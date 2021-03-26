
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
            for feature in tcomponent.component.features.extrudeFeatures:
                if feature.attributes.itemByName("Turtle", "layerIndex"):
                    layerData = LayerData.createWithExisting(feature)
                    result.layers.append(layerData)
        else:
            print("Mapped layers with non TurtleLayer component (layers will be empty).")
        return result

    @classmethod
    def createWithLayerData(cls, tcomponent:TurtleComponent, layerDataList:list, appearanceList = []):
        result = cls(tcomponent)
        countAttr = result.component.attributes.itemByName("Turtle", "layerCount")
        result.layerCount = int(countAttr.value) if countAttr else 0

        newFeatures = result._extrudeWithLayerData(tcomponent, layerDataList, appearanceList)
        
        result.component.attributes.add("Turtle", "layerCount", str(result.layerCount))
        return result, newFeatures

    def _extrudeWithLayerData(self, tcomponent:TurtleComponent,  layerDataList:list, appearanceList = []):
        newFeatures = []
        startFace = None # zero distance from profile plane is default, startFrom is not set
        for i, layer in enumerate(layerDataList):
            layer.extrude = tcomponent.extrude(layer.getProfileCollection(), startFace, layer.thickness, layer.isFlipped)
            layer.layerIndex = self.layerCount

            if len(appearanceList) > i and layer.appearanceIndex > -1:
                self.tcomponent.colorExtrudedBodiesByIndex(layer.extrude, appearanceList[layer.appearanceIndex])
            else:
                self.tcomponent.colorExtrudedBodiesByThickness(layer.extrude, layer.thickness)
            layer.startFace = startFace if startFace else layer.extrude.startFaces[0]
            startFace = layer.extrude.endFaces[0]
            newFeatures.append(layer.extrude)
            self.layerCount += 1
        
        return newFeatures

    @classmethod
    def createFromProfiles(cls, tcomponent:TurtleComponent, profiles:list, thicknesses:list, isFlipped = False, layerCount:int = -1, appearanceList = []):
        result = cls(tcomponent)
        layerDataList = LayerData.createLayerDataList(profiles, thicknesses, isFlipped)

        newFeatures = result._extrudeWithLayerData(tcomponent, layerDataList, appearanceList)

        countAttr = result.component.attributes.itemByName("Turtle", "layerCount")
        count = int(countAttr.value) if countAttr else 0
        result.component.attributes.add("Turtle", "layerCount", str(result.layerCount))

        return result, newFeatures


    def extrudeForLayer(self, extrudeIndex:int) -> f.ExtrudeFeature:  
        return self.layers[index].extrude if len(self.layers) > index else None

    def firstLayerExtrude(self) -> f.ExtrudeFeature:  
        return self.layers[0].extrude if len(self.layers) > 0 else None
    def lastLayerExtrude(self) -> f.ExtrudeFeature:  
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

    def _extrudeWithProfiles(self, newLayerCount:int, profiles:list, thicknesses:list, isFlipped:bool, appearanceList = []):
        # for i in range(newLayerCount):
        #     self.layers.append([])
        extrusions = []
        startFace = None # zero distance from profile plane is default, startFrom is not set
        for i in range(newLayerCount):
            profileIndex = i if len(profiles) > i else len(profiles) - 1
            thicknessIndex = i if len(thicknesses) > i else len(thicknesses) - 1
            layerProfiles = TurtleUtils.ensureObjectCollection(profiles[profileIndex])
            extruded:f.ExtrudeFeature = self.tcomponent.extrude(layerProfiles, startFace, thicknesses[thicknessIndex], isFlipped)
            extrusions.append(extruded)

            appearanceIndex = -1
            if len(appearanceList) > i:
                self.tcomponent.colorExtrudedBodiesByIndex(extruded, appearanceList[i])
                appearanceIndex = i
            else:
                self.tcomponent.colorExtrudedBodiesByThickness(extruded, thicknesses[thicknessIndex])

            # mark layers with extrude index and body map
            start:f.BRepFace = startFace if startFace else extruded.startFaces[0]
            extrudeData = LayerData.createNew(extruded, thicknesses[thicknessIndex], isFlipped, self.layerCount, appearanceIndex)
            self.layers.append(extrudeData)

            startFace = extruded.endFaces[0]
            self.layerCount += 1
        return extrusions

    def modifyWithProfiles(self, profiles, operation:f.FeatureOperations):
        extrusions = []
        profiles = profiles if isinstance(profiles, list) else [profiles] * len(layerIndexes)
        for i, layer in enumerate(self.layers):
            bodies = self.getBodiesFrom(i)
            pindex = min(i, len(profiles) - 1)
            for body in bodies:
                extrudes = self.component.features.extrudeFeatures
                dist = self.parameters.createValue(layer.thickness)
                extrudeInput = extrudes.createInput(profiles[pindex][0], operation) 

                endFace = layer.getAnEndFace()
                if endFace:
                    end = f.ToEntityExtentDefinition.create(endFace, False, self.parameters.createValue(0))
                    extrudeInput.setOneSideExtent(end, f.ExtentDirections.PositiveExtentDirection)
                else:
                    extrudeInput.setOneSideExtent(layer.extrude.extentOne, f.ExtentDirections.PositiveExtentDirection)

                start = layer.extrude.startExtent
                # if layers started based on the original profile, use the first start face (because the new join profile might not be on the same plane)
                if type(start) == f.ProfilePlaneStartDefinition:
                    start = f.FromEntityStartDefinition.create(layer.getAStartFace(), self.parameters.createValue(0))
                extrudeInput.startExtent = start
                extrudeInput.participantBodies = [body]
                extruded = extrudes.add(extrudeInput) 
                extrusions.append(extruded)
        return extrusions

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
    def __init__(self, extrude:f.ExtrudeFeature, profiles:f.Profiles, thickness, isFlipped:bool, layerIndex:int = -1, appearanceIndex:int = -1):
        self.extrude = extrude
        self.layerIndex:int = layerIndex
        self.thickness = thickness
        self.isFlipped:bool = isFlipped
        self.appearanceIndex:int = appearanceIndex
        self.profiles = profiles
        self.startFace = None
        if self.extrude:
            self.setExtrude(extrude)

    @classmethod
    def createWithExisting(cls, extrude:f.ExtrudeFeature):
        #body, layerIndex, bodyIndex, startFaceToken, thickness, isFlipped = cls._getAttributes(body)
        layerIndex, thickness, isFlipped, appearanceIndex = cls._getAttributes(extrude)
        result = cls(extrude, None, thickness, isFlipped, layerIndex, appearanceIndex)
        return result

    @classmethod
    def createNew(cls, extrude:f.ExtrudeFeature, thickness, isFlipped:bool, layerIndex:int, appearanceIndex:int = -1):
        result = cls(extrude, None, thickness, isFlipped, layerIndex, appearanceIndex)
        return result
        
    @classmethod
    def createWithoutBody(cls, profiles:f.Profiles, thickness, isFlipped:bool, appearanceIndex:int = -1):
        return cls(None, profiles, thickness, isFlipped, -1, appearanceIndex)

    @classmethod
    def createLayerDataList(cls, profiles:list, thicknesses:list, isFlipped = False, layerCount:int = -1):
        isListProfiles = isinstance(profiles, list)
        isListThickness = isinstance(thicknesses, list)
        profileCount = len(profiles) if isListProfiles else 1
        thicknessCount = len(thicknesses) if isListThickness else 1
        newLayerCount = layerCount if layerCount > 0 else max(profileCount, thicknessCount)
        profiles = profiles if isListProfiles else [profiles] * newLayerCount
        thicknesses = thicknesses if isListThickness else [thicknesses] * newLayerCount
        layerDataList = []
        for i in range(newLayerCount):
            profile = profiles[i] if len(profiles) > i else profiles[-1]
            thickness = thicknesses[i] if len(thicknesses) > i else thicknesses[-1]
            layer = LayerData.createWithoutBody(profile, thickness, isFlipped)
            layerDataList.append(layer)
        return layerDataList



    def setExtrude(self, extrude:f.ExtrudeFeature):
        self.extrude = extrude
        self._applyAttributesToExtrude(self.extrude)
        self.profiles = extrude.profile

    def getBodyList(self):
        return TurtleUtils.ensureList(self.extrude.bodies) if self.extrude else []
    def getProfileList(self):
        return TurtleUtils.ensureList(self.extrude.profile) if self.extrude else TurtleUtils.ensureList(self.profiles)
    def getProfileCollection(self):
        return TurtleUtils.ensureObjectCollection(self.extrude.profile) if self.extrude else TurtleUtils.ensureObjectCollection(self.profiles)
    def getStartFaceList(self):
        return TurtleUtils.ensureList(self.extrude.startFaces) if self.extrude else []
    def getAStartFace(self):
        result = None
        if self.extrude:
            for face in self.extrude.startFaces:
                if face: # faces can be None, weirdly
                    result = face
                    break
        return result
    def getEndFaceList(self):
        return TurtleUtils.ensureList(self.extrude.endFaces) if self.extrude else []
    def getAnEndFace(self):
        result = None
        if self.extrude:
            for face in self.extrude.endFaces:
                if face: # faces can be None, weirdly
                    result = face
                    break
        return result
        #return self.extrude.endFaces[0] if self.extrude else None
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
