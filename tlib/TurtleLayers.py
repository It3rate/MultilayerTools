import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from .TurtleUtils import TurtleUtils
from .TurtleParams import TurtleParams
from .TurtleComponent import TurtleComponent
from .TurtleLayerData import TurtleLayerData

f:adsk.fusion
core:adsk.core
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
                    layerData = TurtleLayerData.createWithExisting(feature)
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
        for i, layerData in enumerate(layerDataList):
            layerData.extrude = tcomponent.extrude(layerData.getProfileCollection(), startFace, layerData.thickness, layerData.isFlipped)
            layerData.layerIndex = self.layerCount

            if len(appearanceList) > i and layerData.appearanceIndex > -1:
                self.tcomponent.colorExtrudedBodiesByIndex(layerData.extrude, appearanceList[layerData.appearanceIndex])
            else:
                self.tcomponent.colorExtrudedBodiesByThickness(layerData.extrude, layerData.thickness)
            layerData.startFace = startFace if startFace else layerData.extrude.startFaces[0]
            startFace = layerData.extrude.endFaces[0]
            newFeatures.append(layerData.extrude)
            self.layers.append(layerData) # add to internal layers
            self.layerCount += 1
        
        return newFeatures

    @classmethod
    def createFromProfiles(cls, tcomponent:TurtleComponent, profiles:list, thicknesses:list, isFlipped = False, layerCount:int = -1, appearanceList = []):
        result = cls(tcomponent)
        layerDataList = TurtleLayerData.createLayerDataList(profiles, thicknesses, isFlipped)

        newFeatures = result._extrudeWithLayerData(tcomponent, layerDataList, appearanceList)

        countAttr = result.component.attributes.itemByName("Turtle", "layerCount")
        count = int(countAttr.value) if countAttr else 0
        result.component.attributes.add("Turtle", "layerCount", str(result.layerCount))

        return result, newFeatures

    @classmethod
    def changeExturdeToPlaneOrigin(cls, extrude:f.ExtrudeFeature, faceOrPlane:f.BRepFace, offsetValue:core.ValueInput):
        extrude.timelineObject.rollTo(True)
        extrude.startExtent = f.FromEntityStartDefinition.create(faceOrPlane, offsetValue)
        extrude.timelineObject.rollTo(False)

    @classmethod
    def changeExtrudeToCut(cls, extrude:f.ExtrudeFeature, praticipantBodies:list[f.BRepBody]):
        extrude.timelineObject.rollTo(True)
        extrude.operation = f.FeatureOperations.CutFeatureOperation
        extrude.participantBodies = praticipantBodies
        extrude.timelineObject.rollTo(False)


    def extrudeForLayer(self, extrudeIndex:int) -> f.ExtrudeFeature:  
        return self.layers[extrudeIndex].extrude if len(self.layers) > extrudeIndex else None

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
            extrudeData = TurtleLayerData.createNew(extruded, thicknesses[thicknessIndex], isFlipped, self.layerCount, appearanceIndex)
            self.layers.append(extrudeData)

            startFace = extruded.endFaces[0]
            self.layerCount += 1
        return extrusions

    def modifyWithProfiles(self, profiles, operation:f.FeatureOperations):
        extrusions = []
        profiles = profiles if isinstance(profiles, list) else [profiles] * len(self.layerIndexes)
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


