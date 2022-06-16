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
        comp:f.Component = TurtleUtils.activeDesign().activeComponent
        if not comp.bRepBodies.count == 1 or not comp.bRepBodies.item(0).faces.count == 11:
            return
        body = comp.bRepBodies.item(0)
        allFaces:list[f.BRepFace] = []
        for face in body.faces:
            allFaces.append(face)
            print([face.geometry.normal.x, face.geometry.normal.y, face.geometry.normal.z])
        f0 = body.faces.item(0)
        f1 = body.faces.item(1)
        f2 = body.faces.item(2)
        f3 = body.faces.item(3)
        f4 = body.faces.item(4)
        f5 = body.faces.item(5)
        f6 = body.faces.item(6)
        f7 = body.faces.item(7)
        f8 = body.faces.item(8)
        f9 = body.faces.item(9)
        f10 = body.faces.item(10)
        self.body = comp.bRepBodies.item(0)
        self.faces = self.body.faces
        self.topFace = next(face for face in self.faces if face.loops.count == 2)
        allFaces.remove(self.topFace)

        self.upNorm = self.topFace.geometry.normal
        self.downNorm = TurtleUtils.reverseVector(self.upNorm)
        if abs(self.upNorm.z) > 0.1:
            self.rightNorm = core.Vector3D.create(1,0,0)
            self.backNorm = core.Vector3D.create(0,1,0) 
        elif abs(self.upNorm.x) > 0.1:
            self.rightNorm = core.Vector3D.create(0, self.upNorm.x, 0)
            self.backNorm = core.Vector3D.create(0, 0 ,self.upNorm.x) 
        else: # y
            self.rightNorm = core.Vector3D.create(0, 0, self.upNorm.y)
            self.backNorm = core.Vector3D.create(self.upNorm.y, 0, 0) 
        self.leftNorm = TurtleUtils.reverseVector(self.rightNorm)
        self.frontNorm = TurtleUtils.reverseVector(self.backNorm)

        self.floorFace = TurtleUtils.firstNormMatch(self.upNorm, allFaces)
        self.bottomFace = TurtleUtils.firstNormMatch(self.downNorm, allFaces)
        self.leftOuterFace = TurtleUtils.firstNormMatch(self.leftNorm, allFaces, True)
        self.leftInnerFace = TurtleUtils.firstNormMatch(self.leftNorm, allFaces, False)
        self.rightOuterFace = TurtleUtils.firstNormMatch(self.rightNorm, allFaces, True)
        self.rightInnerFace = TurtleUtils.firstNormMatch(self.rightNorm, allFaces, False)
        self.frontOuterFace = TurtleUtils.firstNormMatch(self.frontNorm, allFaces, True)
        self.frontInnerFace = TurtleUtils.firstNormMatch(self.frontNorm, allFaces, False)
        self.backOuterFace = TurtleUtils.firstNormMatch(self.backNorm, allFaces, True)
        self.backInnerFace = TurtleUtils.firstNormMatch(self.backNorm, allFaces, False)

        if comp.features.shellFeatures.count == 1:
            shellFeature = comp.features.shellFeatures.item(0)
            self.ShellThicknessVal = shellFeature.insideThickness.value
            self.ShellThicknessExpr = shellFeature.insideThickness.expression

        # body = comp.bRepBodies.item(0)
        # f0 = body.faces.item(0)
        # f1 = body.faces.item(1)
        # f2 = body.faces.item(2)
        # f3 = body.faces.item(3)
        # f4 = body.faces.item(4)
        # f5 = body.faces.item(5)
        # f6 = body.faces.item(6)
        # f7 = body.faces.item(7)
        # f8 = body.faces.item(8)
        # f9 = body.faces.item(9)
        # f10 = body.faces.item(10)
        # topClue = f5.loops.count # 2 
        # f5Norm = f5.geometry.normal
        # pts = f5.vertices # 8
        # edges = f5.edges # 8
        # shellFeature = comp.features.shellFeatures.item(0)
        # thickness = shellFeature.insideThickness.value # or expression 
        # faces=shellFeature.faces
        # boxFeature = comp.features.boxFeatures.item(0)
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
            self.thicknessParamNames = ['mat0', 'mat1', 'mat2', 'mat3', 'mat4', 'mat5']
            self.params.addParams(
                self.thicknessParamNames[0], 2,
                self.thicknessParamNames[1], 3.5,
                self.thicknessParamNames[2], 3,
                self.thicknessParamNames[3], 4,
                self.thicknessParamNames[4], 5,
                self.thicknessParamNames[5], 6)
            
            self.reverseSelection = inputs.addBoolValueInput('bReverse', 'Reverse', True)
            self.mirrorSelection = inputs.addBoolValueInput('bMirror', 'Mirror', True)

            # self.bFlipDirection = inputs.addBoolValueInput('iAxis', 'Rotate Axis', True, "resources/Flip/", isFlipped)
            # self.bReversed = inputs.addBoolValueInput('bReverse', 'Rotate Axis', True, "resources/Reverse/", isReversed)

            ddOperation = inputs.addDropDownCommandInput("ddOperation", "Operation",  core.DropDownStyles.LabeledIconDropDownStyle)
            ddOperation.isFullWidth = True
            ddOperation.listItems.add("Join Component", False, 'resources/BooleanAdd')
            ddOperation.listItems.add("New Component", True, 'resources/BooleanNewComponent')

        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
            