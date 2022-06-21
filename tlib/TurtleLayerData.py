
import adsk.core, adsk.fusion, traceback
from .TurtleUtils import TurtleUtils

f,core,app,ui = TurtleUtils.initGlobals()

class TurtleLayerData:
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
            layer = cls.createWithoutBody(profile, thickness, isFlipped)
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
