
import adsk.core, adsk.fusion, adsk.cam, traceback
import os, math, re
from .TurtleUtils import TurtleUtils
from .TurtleSketch import TurtleSketch
from .TurtleParams import TurtleParams
from .TurtlePath import TurtlePath
from .TurtleAppearance import TurtleAppearance


f,core,app,ui = TurtleUtils.initGlobals()

class TurtleComponent:

    def __init__(self, component:f.Component):
        self.component = component
        self.parameters = TurtleParams.instance()
        self.appearances = TurtleAppearance.instance()
        self._sketches = []
        self.activeSketch = None
        self.__wrapExistingSketches()

    @classmethod
    def createFromExisting(cls, existingComponent:f.Component):
        result = cls(existingComponent) 
        return result

    @classmethod
    def createFromParent(cls, parentComponent:f.Component, name:str):
        comp = cls.createComponent(parentComponent, name) 
        result = cls(comp)
        return result

    @classmethod
    def createFromSketch(cls, sketch:f.Sketch):
        result = cls(sketch.parentComponent)
        return result

    def createNew(self, name:str = None):
        component = self.createComponent(self.component, name)
        result = TurtleComponent(component)
        return result

    def __wrapExistingSketches(self):
        self._sketches = []
        for sketch in self.component.sketches:
            tsketch = TurtleSketch.createWithSketch(sketch)
            self._sketches.append(tsketch)
            self.activeSketch = tsketch

    def createSketch(self, planarEntity, name:str = None):
        tsketch = TurtleSketch.createWithPlane(self.component, planarEntity)
        if name :
            tsketch.sketch.name = name
        self._sketches.append(tsketch)
        self.activeSketch = tsketch
        return tsketch
    
    def getTSketchByName(self, name) -> TurtleSketch:
        result = None
        for sketch in self._sketches:
            if sketch.name == name:
                result = sketch
                break
        return result

    def getTSketch(self, sketch:f.Sketch) -> TurtleSketch:
        return self.getTSketchByName(sketch.name)


    def createOffsetPlane(self, referencePlane, offset, name:str = None):
        self.component.isConstructionFolderLightBulbOn = True
        planeInput:f.ConstructionPlaneInput = self.component.constructionPlanes.createInput()
        dist = self.parameters.createValue(offset)
        planeInput.setByOffset(referencePlane, dist)
        result = self.component.constructionPlanes.add(planeInput)
        if name:
            result.name = name
        return result

    def createOrthoganalPlane(self, line:f.SketchLine):
        planeInput = self.component.constructionPlanes.createInput()
        planeInput.setByAngle(line, adsk.core.ValueInput.createByReal(-math.pi/2.0), line.parentSketch.referencePlane)
        result = self.component.constructionPlanes.add(planeInput)
        return result

    def extrude(self, profile, start, expression, isFlipped = False) -> f.ExtrudeFeature:
        if profile is None:
            return
        extrudes = self.component.features.extrudeFeatures
        dist = self.parameters.createValue(expression)
        extrudeInput = extrudes.createInput(profile, f.FeatureOperations.NewBodyFeatureOperation) 
        extentDistance = f.DistanceExtentDefinition.create(dist) 
        direction = f.ExtentDirections.NegativeExtentDirection if isFlipped else f.ExtentDirections.PositiveExtentDirection
        extrudeInput.setOneSideExtent(extentDistance, direction)
        if start:
            startFrom = f.FromEntityStartDefinition.create(start, self.parameters.createValue(0))
            extrudeInput.startExtent = startFrom
        extruded = extrudes.add(extrudeInput) 
        return extruded

    def cutComponent(self, profile):
        bodies = self.getBodies()
        for body in bodies:
            self.cutBodyWithProfile(profile)

    # def cutComponent(self, profile):
    #     if profile is None:
    #         return
    #     extrudes = self.component.features.extrudeFeatures
    #     extrudeInput = extrudes.createInput(profile, f.FeatureOperations.CutFeatureOperation)
    #     extrudeInput.setAllExtent(adsk.fusion.ExtentDirections.SymmetricExtentDirection)
    #     extrudeInput.participantBodies = getBodies()
    #     extrude = extrudes.add(extrudeInput) 
    #     return extrude

    def cutBodyWithProfile(self, profile:f.Profile, body:f.BRepBody):
        extrudes = body.parentComponent.features.extrudeFeatures
        input = extrudes.createInput(profile, f.FeatureOperations.CutFeatureOperation) 

        toExtent = f.ToEntityExtentDefinition.create(body, False)
        toExtent.isMinimumSolution = False
        input.setOneSideExtent(toExtent, f.ExtentDirections.SymmetricExtentDirection)

        input.participantBodies = [body]
        extrude = extrudes.add(input) 
        return extrude

    def colorExtrudedBodiesByThickness(self, extruded:f.ExtrudeFeature, thickness):
        appr = self.appearances.getAppearanceByThickness(thickness)
        for body in extruded.bodies:
            body.appearance = appr

    def colorExtrudedBodiesByIndex(self, extruded:f.ExtrudeFeature, index):
        appr = self.appearances.getAppearanceByIndex(index)
        for body in extruded.bodies:
            body.appearance = appr

    def colorBodiesByOrder(self, ignoreIndexes:list[int]=[]):
        bodies = self.getBodies()
        index = 0
        for body in bodies:
            if not index in ignoreIndexes:
                appr = self.appearances.getAppearanceByIndex(index)
                body.appearance = appr
            index += 1

    def getBodyByIndex(self, index:int)->f.BRepBody:
        return self.component.bRepBodies.item(index) if index < self.component.bRepBodies.count else None

    def getBodies(self)->list[f.BRepBody]:
        bodies = []
        for body in self.component.bRepBodies:
            bodies.append(body)
        return bodies

    @classmethod
    def createComponent(cls, parent:f.Component, name):
        occ = parent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        if name:
            occ.component.name = name
        return occ.component