# #Author-Robin Debreuil
# # Generates a laser cuttable mold from a shelled box.

from xmlrpc.client import Boolean
import adsk.core, adsk.fusion, traceback
from .tlib.TurtleUtils import TurtleUtils
from .tlib.TurtleUICommand import TurtleUICommand
from .tlib.TurtleSketch import TurtleSketch
from .tlib.TurtleParams import TurtleParams
from .tlib.TurtleComponent import TurtleComponent
from .tlib.TurtleLayers import TurtleLayers
from .tlib.TurtleCustomCommand import TurtleCustomCommand

f,core,app,ui = TurtleUtils.initGlobals()

class MoldBuilder(TurtleCustomCommand):
    def __init__(self):
        self.params = TurtleParams.instance()
        cmdId = 'ddwMoldBuilderId'
        cmdName = 'Mold Builder'
        cmdDescription = 'Generates a laser cuttable mold from a shelled box.'
        super().__init__(cmdId, cmdName, cmdDescription)
        
    def getTargetPanels(self):
        return [ui.allToolbarPanels.itemById('SolidCreatePanel')]

    def onCreated(self, eventArgs:core.CommandCreatedEventArgs):
        # investigations of a shelled box
        self.component:f.Component = TurtleUtils.activeDesign().activeComponent
        if not self.component.bRepBodies.count == 1 or not self.component.bRepBodies.item(0).faces.count == 11:
            return
        self._parseFaces()

        self._createDialog(eventArgs.command.commandInputs)

    def onInputsChanged(self, eventArgs:core.InputChangedEventArgs):
        pass
    def onPreview(self, eventArgs:core.CommandEventArgs):
        pass
    def onExecute(self, eventArgs:core.CommandEventArgs):
        pass
    
    # Custom Feature Edit events
    def onEditCreated(self, eventArgs:core.CommandCreatedEventArgs):
        pass
    def onEditActivate(self, eventArgs:core.CommandEventArgs):
        pass
    def onEditDeactivate(self, eventArgs:core.CommandEventArgs):
        pass
    def onEditExecute(self, eventArgs:core.CommandEventArgs):
        pass

    
    def _createDialog(self, inputs):
        try:
            self.moldWallThickness = inputs.addDistanceValueCommandInput('txWallThickness', 'Mold Wall Thickness', self.params.createValue(3.0))
            self.moldWallThickness.setManipulator(self.frontOuterFace.centroid, self.frontNorm)
            # self.reverseSelection = inputs.addBoolValueInput('bReverse', 'Reverse', True)
            # self.mirrorSelection = inputs.addBoolValueInput('bMirror', 'Mirror', True)
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
            
    def _parseFaces(self):
        allFaces:list[f.BRepFace] = []
        self.body = self.component.bRepBodies.item(0)
        for face in self.body.faces:
            allFaces.append(face)

        self.faces = self.body.faces
        self.topFace = next(face for face in self.faces if face.loops.count == 2)
        allFaces.remove(self.topFace)

        self.topNorm = self.topFace.geometry.normal
        self.bottomNorm = TurtleUtils.reverseVector(self.topNorm)
        if abs(self.topNorm.z) > 0.1:
            self.rightNorm = core.Vector3D.create(1,0,0)
            self.backNorm = core.Vector3D.create(0,1,0) 
        elif abs(self.topNorm.x) > 0.1:
            self.rightNorm = core.Vector3D.create(0, self.topNorm.x, 0)
            self.backNorm = core.Vector3D.create(0, 0 ,self.topNorm.x) 
        else: # y
            self.rightNorm = core.Vector3D.create(0, 0, self.topNorm.y)
            self.backNorm = core.Vector3D.create(self.topNorm.y, 0, 0) 
        self.leftNorm = TurtleUtils.reverseVector(self.rightNorm)
        self.frontNorm = TurtleUtils.reverseVector(self.backNorm)

        self.floorFace = TurtleUtils.firstNormMatch(self.topNorm, allFaces)
        self.bottomFace = TurtleUtils.firstNormMatch(self.bottomNorm, allFaces)
        self.leftOuterFace = TurtleUtils.firstNormMatch(self.leftNorm, allFaces, True)
        self.leftInnerFace = TurtleUtils.firstNormMatch(self.leftNorm, allFaces, False)
        self.rightOuterFace = TurtleUtils.firstNormMatch(self.rightNorm, allFaces, True)
        self.rightInnerFace = TurtleUtils.firstNormMatch(self.rightNorm, allFaces, False)
        self.frontOuterFace = TurtleUtils.firstNormMatch(self.frontNorm, allFaces, True)
        self.frontInnerFace = TurtleUtils.firstNormMatch(self.frontNorm, allFaces, False)
        self.backOuterFace = TurtleUtils.firstNormMatch(self.backNorm, allFaces, True)
        self.backInnerFace = TurtleUtils.firstNormMatch(self.backNorm, allFaces, False)

        if self.component.features.shellFeatures.count == 1:
            shellFeature = self.component.features.shellFeatures.item(0)
            self.thicknessVal = shellFeature.insideThickness.value
            self.thicknessExpr = shellFeature.insideThickness.expression
        else:
            tempBR = f.TemporaryBRepManager.get()
            body1 = tempBR.copy(self.leftOuterFace)
            body2 = tempBR.copy(self.leftInnerFace)
            dist = app.measureManager.measureMinimumDistance(body1, body2)
            self.thicknessVal = dist.value
            self.thicknessExpr = f'{dist.value} cm'