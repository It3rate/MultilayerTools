
import adsk.core, adsk.fusion, adsk.cam, traceback
import os, math, re
from .TurtleUtils import TurtleUtils
from .TurtleSketch import TurtleSketch
from .TurtleParams import TurtleParams
from .TurtlePath import TurtlePath
from .TurtleLayers import TurtleLayers
from .TurtleAppearance import TurtleAppearance


f,core,app,ui,design,root = TurtleUtils.initGlobals()

class TurtleComponent:

    def __init__(self, component:f.Component):
        self.component = component
        self.parameters = TurtleParams.instance()
        self.appearances = TurtleAppearance.instance()
        self._sketches = []
        self.activeSketch = None
        self.__wrapExistingSketches()

    @classmethod
    def createFromSketch(cls, sketch:f.Sketch):
        result = cls(sketch.parentComponent)
        return result

    def createNew(self, name:str = None):
        component = self.createComponent(self.component, name)
        result = TurtleComponent(component)
        return result

    def createLayers(self,profiles:list, thicknesses:list, layerCount:int = 1):
        return TurtleLayers(self, profiles, thicknesses, layerCount)

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

    def extrude(self, profile, start, expression):
        if profile is None:
            return
        extrudes = self.component.features.extrudeFeatures
        dist = self.parameters.createValue(expression)
        extrudeInput = extrudes.createInput(profile, f.FeatureOperations.NewBodyFeatureOperation) 
        extentDistance = f.DistanceExtentDefinition.create(dist) 
        extrudeInput.setOneSideExtent(extentDistance, f.ExtentDirections.PositiveExtentDirection)
        if start:
            startFrom = f.FromEntityStartDefinition.create(start, self.parameters.createValue(0))
            extrudeInput.startExtent = startFrom

        extruded = extrudes.add(extrudeInput) 
        # bug: Need to reassign expression
        extDef = f.DistanceExtentDefinition.cast(extruded.extentOne)
        extDef.distance.expression = expression

        self.colorExtrudedBodies(extruded, expression)
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
        cutInput = extrudes.createInput(profile, f.FeatureOperations.CutFeatureOperation) 

        toExtent = f.ToEntityExtentDefinition.create(body, False)
        toExtent.isMinimumSolution = False
        cutInput.setOneSideExtent(toExtent, f.ExtentDirections.SymmetricExtentDirection)

        cutInput.participantBodies = [body]
        extrude = extrudes.add(cutInput) 
        return extrude

    def colorExtrudedBodies(self, extruded:f.ExtrudeFeature, thickness):
        appr = self.appearances.getAppearance(thickness)
        for body in extruded.bodies:
            body.appearance = appr

    def getBodies(self):
        bodies = []
        for body in self.component.bRepBodies:
            bodies.append(body)
        return pBodies

    @classmethod
    def createComponent(cls, parent:f.Component, name):
        occ = parent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        if name:
            occ.component.name = name
        return occ.component