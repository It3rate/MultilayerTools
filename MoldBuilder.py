# #Author-Robin Debreuil
# # Generates a laser cuttable mold from a shelled box.

from xmlrpc.client import Boolean
from enum import Enum
import adsk.core, adsk.fusion, traceback

from .tlib.TurtleWall import TurtleWall
from .tlib.WallData import *
from .tlib.TurtleUtils import TurtleUtils
from .tlib.TurtleUtils import SurfaceKind
from .tlib.TurtleFace import TurtleFace
from .tlib.TurtleUICommand import TurtleUICommand
from .tlib.TurtleSketch import TurtleSketch
from .tlib.TurtleParams import TurtleParams
from .tlib.TurtleComponent import TurtleComponent
from .tlib.TurtleLayers import TurtleLayers
from .tlib.TurtleCustomCommand import TurtleCustomCommand
from .tlib.TurtleDecoder import TurtleDecoder
from .tlib.data.SketchData import Sketches, SketchData

f:adsk.fusion
core:adsk.core
f,core,app,ui = TurtleUtils.initGlobals()

class MoldBuilder(TurtleCustomCommand):
    def __init__(self):
        self.rootComponent = TurtleComponent(TurtleUtils.activeRoot())
        self.parameters = TurtleParams.instance()
        cmdId = 'ddwMoldBuilderId'
        cmdName = 'Mold Builder'
        cmdDescription = 'Generates a laser cuttable mold from a shelled box.'
        self.workingPointList = None
        self.currentTSketch:TurtleSketch = None
        self.slotLengthVal = 1
        self.slotSpaceVal = 1

        self.faceMap = {}
        self.slotCountWidth = 6
        self.slotCountDepth = 4
        self.slotCountHeight = 2
        self.wallThicknessExpr = "wallThickness"
        super().__init__(cmdId, cmdName, cmdDescription)
        
    @property
    def xAxis(self):
        return self.tComponent.xAxis if self.tComponent else self.rootComponent.component.xConstructionAxis
    @property
    def yAxis(self):
        return self.tComponent.yAxis if self.tComponent else self.rootComponent.component.yConstructionAxis   
    @property
    def zAxis(self):
        return self.tComponent.zAxis if self.tComponent else self.rootComponent.component.zConstructionAxis    

    def getTargetPanels(self):
        return [ui.allToolbarPanels.itemById('SolidCreatePanel')]

    def onCreated(self, eventArgs:core.CommandCreatedEventArgs):
        # investigations of a shelled box
        self.component:f.Component = TurtleUtils.activeDesign().activeComponent
        self.tComponent:TurtleComponent = TurtleComponent.createFromExisting(self.component)
        if not self.component.bRepBodies.count == 1 or not self.component.bRepBodies.item(0).faces.count == 11:
            return
        self._parseFaces()
        self._createDialog(eventArgs.command.commandInputs)

    def onInputsChanged(self, eventArgs:core.InputChangedEventArgs):
        pass

    def onPreview(self, eventArgs:core.CommandEventArgs):
        self.setParameters()
        self.createSpecificWalls([WallKind.frontOuter, WallKind.leftOuter, WallKind.bottomInner])

    def onExecute(self, eventArgs:core.CommandEventArgs):
        self.setParameters()
        self.createAllWalls()
        self.body.isVisible = False

    def setWallData(self):
        self.wallData = {
            WallKind.topOuter:[[SlotKind.hole, self.slotCountWidth + 1], [SlotKind.hole, self.slotCountDepth + 1],[SlotKind.hole, self.slotCountWidth, True], [SlotKind.hole, self.slotCountDepth, True]],
            WallKind.bottomInner:[[SlotKind.holeLock, self.slotCountWidth], [SlotKind.holeLock, self.slotCountDepth]],
            WallKind.bottomOuter:[[SlotKind.hole, self.slotCountWidth + 1, True], [SlotKind.hole, self.slotCountDepth + 1]],

            WallKind.frontOuter:[[SlotKind.fingerLock, self.slotCountWidth + 1], [SlotKind.holeLock, self.slotCountHeight + 1]],
            WallKind.backInner:[[SlotKind.fingerLock, self.slotCountWidth], [SlotKind.holeLock, self.slotCountHeight]],
            # left right need to be last as they can potentially punch through to lock multiple walls
            WallKind.leftOuter:[[SlotKind.fingerLock, self.slotCountDepth + 1], [SlotKind.fingerLock, self.slotCountHeight + 1]],
            WallKind.rightInner:[[SlotKind.fingerLock, self.slotCountDepth], [SlotKind.fingerLock, self.slotCountHeight]],
        }
    def createSpecificWalls(self, wallKinds:list[SlotKind]):
        self.setWallData()
        for key in wallKinds:
            self.createWall(key, self.wallData[key])
        self.tComponent.component.isConstructionFolderLightBulbOn = False

    def createAllWalls(self):
        self.setWallData()
        for key in self.wallData:
            self.createWall(key, self.wallData[key])
        self.tComponent.component.isConstructionFolderLightBulbOn = False

    def createWall(self, wallKind, wallData):
        wallDesc = zip(wallData[::2], wallData[1::2])
        isFeature = False
        for wallEdgeData in wallDesc:
            data0 = self.parseWallData(wallEdgeData[0])
            crossData = WallSlotData.create(*data0)
            data1 = self.parseWallData(wallEdgeData[1])
            outwardData = WallSlotData.create(*data1)
            if isFeature:
                wall.addFeatures(crossData, outwardData, False)
            else:
                face = self.faceMap[wallKind]
                wall = TurtleWall.create(face, wallKind, crossData, outwardData)
                isFeature = True
    def parseWallData(self, wallEdgeData):
            slotSketch = self.getSlotSketchForSlotKind(wallEdgeData[0])
            slotCount = wallEdgeData[1]
            isMirrored = wallEdgeData[2] if len(wallEdgeData) > 2 else False
            return (slotSketch, slotCount, isMirrored)

    def getSlotSketchForSlotKind(self, slotKind:SlotKind):
        result = Sketches.default
        if slotKind == SlotKind.hole:
            result = Sketches.edgeHole
        if slotKind == SlotKind.holeLock or slotKind == SlotKind.holeEdge:
            result = Sketches.edgeFilletHole
        if slotKind == SlotKind.finger:
            result = Sketches.edgeFinger
        if slotKind == SlotKind.fingerLock or slotKind == SlotKind.fingerEdge:
            result = Sketches.edgeFilletFinger
        return result

    def createTop(self, isPreview:bool):
        crossData = WallSlotData.create(Sketches.edgeHole, 9)
        outwardData = WallSlotData.create(Sketches.edgeHole, 5)
        wall = TurtleWall.create(self.topOuterFace, WallKind.topOuter, crossData, outwardData)
        crossData = WallSlotData.create(Sketches.edgeHole, 8, True)
        outwardData = WallSlotData.create(Sketches.edgeHole, 3, True)
        wall.addFeatures(crossData, outwardData, False)
    def createFloor(self, isPreview:bool):
        crossData = WallSlotData.create(Sketches.edgeHole, 8)
        outwardData = WallSlotData.create(Sketches.edgeHole, 3)
        wall = TurtleWall.create(self.bottomInnerFace, WallKind.bottomInner, crossData, outwardData)
    def createBottom(self, isPreview:bool):
        crossData = WallSlotData.create(Sketches.edgeHole, 9, True)
        outwardData = WallSlotData.create(Sketches.edgeHole, 5)
        wall = TurtleWall.create(self.bottomOuterFace, WallKind.bottomOuter, crossData, outwardData)

    def createOuterFrontAndBack(self, isPreview:bool):
        crossData = WallSlotData.create(Sketches.edgeFilletFinger, 9)
        outwardData = WallSlotData.create(Sketches.edgeFilletHole, 4)
        wall = TurtleWall.create(self.frontOuterFace, WallKind.frontOuter, crossData, outwardData)
    def createInnerFrontAndBack(self, isPreview:bool):
        crossData = WallSlotData.create(Sketches.edgeFilletFinger, 8)
        outwardData = WallSlotData.create(Sketches.edgeFilletHole, 4)
        wall = TurtleWall.create(self.backInnerFace, WallKind.backInner, crossData, outwardData)

    def createOuterLeftAndRight(self, isPreview:bool):
        crossData = WallSlotData.create(Sketches.edgeFinger, 5)
        outwardData = WallSlotData.create(Sketches.edgeFinger, 4)
        wall = TurtleWall.create(self.leftOuterFace, WallKind.leftOuter, crossData, outwardData)
    def createInnerLeftAndRight(self, isPreview:bool):
        crossData = WallSlotData.create(Sketches.edgeFilletFinger, 3)
        outwardData = WallSlotData.create(Sketches.edgeFilletFinger, 4)
        wall = TurtleWall.create(self.rightInnerFace, WallKind.rightInner, crossData, outwardData)

        


    def setParameters(self):
        self.parameters.setOrCreateParam(self.wallThicknessExpr, self.diagMoldWallThickness.expression)
        self.parameters.setOrCreateParam('lipWidth', self.diagLipThickness.expression)
        self.parameters.setOrCreateParam('slotLength', self.diagSlotLength.expression)
        self.parameters.setOrCreateParam('slotSpacing', self.diagSlotSpacing.expression)

        self.wallThicknessVal = self.parameters.getParamValueOrDefault(self.wallThicknessExpr, 1.0)
        self.lipWidthVal = self.parameters.getParamValueOrDefault('lipWidth', 1.0)
        self.slotLengthVal = self.parameters.getParamValueOrDefault('slotLength', 1.0)
        self.slotSpaceVal = self.parameters.getParamValueOrDefault('slotSpacing', 1.5)



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
            wallThicknessParam = self.parameters.addOrGetParam(self.wallThicknessExpr, '2.8 mm')
            self.diagMoldWallThickness = inputs.addDistanceValueCommandInput('txWallThickness', 'Mold Wall Thickness',\
                 self.parameters.createValue(wallThicknessParam.expression))
            self.diagMoldWallThickness.setManipulator(self.frontOuterFace.centroid, self.frontNorm)

            lipWidthParam = self.parameters.addOrGetParam('lipWidth', '3 mm')
            self.diagLipThickness = inputs.addDistanceValueCommandInput('txLipWidth', 'Lip Width', self.parameters.createValue(lipWidthParam.expression))
            self.diagLipThickness.setManipulator(self.rightOuterFace.maxPoint, self.rightNorm)
            
            # better to specify max slots per wall
            slotLengthParam = self.parameters.addOrGetParam('slotLength', '8 mm')
            self.diagSlotLength = inputs.addDistanceValueCommandInput('txSlotLen', 'Slot Length', self.parameters.createValue(slotLengthParam.expression))
            #self.diagSlotLength.setManipulator(self.rightOuterFace.maxPoint, self.rightNorm)

            slotSpacingParam = self.parameters.addOrGetParam('slotSpacing', '5 mm')
            self.diagSlotSpacing = inputs.addDistanceValueCommandInput('txSlotSpacing', 'Slot Spacing', self.parameters.createValue(slotSpacingParam.expression))
            
            
            # self.reverseSelection = inputs.addBoolValueInput('bReverse', 'Reverse', True)
            # self.mirrorSelection = inputs.addBoolValueInput('bMirror', 'Mirror', True)
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
            
    def _parseFaces(self):
        allFaces:list[f.BRepFace] = []
        self.body = self.component.bRepBodies.item(0)
        self.tFaces = []
        for face in self.body.faces:
           self.tFaces.append(TurtleFace.createWithFace(face))

        allFaces = self.tFaces.copy()
        self.topOuterFace = next(tface for tface in allFaces if tface.loops.count == 2)
        allFaces.remove(self.topOuterFace)

        # the normal points into the material, not out of it.
        self.topNorm = self.topOuterFace.normal
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

        self.bottomInnerFace:TurtleFace = self.faceWithNormalMatch(self.topNorm, allFaces, False, SurfaceKind.bottomInner)
        self.bottomOuterFace:TurtleFace = self.faceWithNormalMatch(self.bottomNorm, allFaces, False, SurfaceKind.bottomOuter)
        self.frontOuterFace:TurtleFace = self.faceWithNormalMatch(self.frontNorm, allFaces, True, SurfaceKind.frontOuter)
        self.backOuterFace:TurtleFace = self.faceWithNormalMatch(self.backNorm, allFaces, True, SurfaceKind.backOuter)
        self.frontInnerFace:TurtleFace = self.faceWithNormalMatch(self.backNorm, allFaces, False, SurfaceKind.frontInner)
        self.backInnerFace:TurtleFace = self.faceWithNormalMatch(self.frontNorm, allFaces, False, SurfaceKind.backInner)
        self.leftOuterFace:TurtleFace = self.faceWithNormalMatch(self.leftNorm, allFaces, True, SurfaceKind.leftOuter)
        self.rightOuterFace:TurtleFace = self.faceWithNormalMatch(self.rightNorm, allFaces, True, SurfaceKind.rightOuter)
        self.leftInnerFace:TurtleFace = self.faceWithNormalMatch(self.rightNorm, allFaces, False, SurfaceKind.leftInner)
        self.rightInnerFace:TurtleFace = self.faceWithNormalMatch(self.leftNorm, allFaces, False, SurfaceKind.rightInner)

        self.faceMap = {
            WallKind.topOuter:self.topOuterFace,
            WallKind.bottomInner:self.bottomInnerFace,
            WallKind.bottomOuter:self.bottomOuterFace,
            WallKind.frontOuter:self.frontOuterFace,
            WallKind.backOuter:self.backOuterFace,
            WallKind.frontInner:self.frontInnerFace,
            WallKind.backInner:self.backInnerFace,
            WallKind.leftOuter:self.leftOuterFace,
            WallKind.rightOuter:self.rightOuterFace,
            WallKind.leftInner:self.leftInnerFace,
            WallKind.rightInner:self.rightInnerFace
        }
        topLengths = self.topOuterFace.xyzLengths
        frontLengths = self.frontOuterFace.xyzLengths
        sideLengths = self.rightOuterFace.xyzLengths
        self.frontWidth = frontLengths[0]
        self.frontHeight = frontLengths[2]
        self.sideWidth = sideLengths[1]

        if self.component.features.shellFeatures.count == 1:
            shellFeature = self.component.features.shellFeatures.item(0)
            self.shellThicknessVal = shellFeature.insideThickness.value
            self.shellThicknessExpr = shellFeature.insideThickness.expression
        else:
            tempBR = f.TemporaryBRepManager.get()
            body1 = tempBR.copy(self.leftOuterFace)
            body2 = tempBR.copy(self.leftInnerFace)
            dist = app.measureManager.measureMinimumDistance(body1, body2)
            self.shellThicknessVal = dist.value
            self.shellThicknessExpr = f'{dist.value} cm'
            
    def faceWithNormalMatch(self, norm:core.Vector3D, tfaces:list[TurtleFace], findLargest:bool, surfaceKind:SurfaceKind) -> TurtleFace:
        result:TurtleFace = None
        area = 0
        for tface in tfaces:
            if tface.isNormalEqualTo(norm):
                if findLargest:
                     if tface.area > area:
                        result = tface
                        area = tface.area
                else:
                    result = tface
                    break
        if result:
            result.surfaceKind = surfaceKind
            #result.face.attributes.add("wall","surfaceKind", str(surfaceKind.value))
            tfaces.remove(result)
        return result




