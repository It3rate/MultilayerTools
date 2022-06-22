# #Author-Robin Debreuil
# # Generates a laser cuttable mold from a shelled box.

from xmlrpc.client import Boolean
import adsk.core, adsk.fusion, traceback
from .tlib.TurtleUtils import TurtleUtils
from .tlib.TurtleFace import TurtleFace
from .tlib.TurtleUICommand import TurtleUICommand
from .tlib.TurtleSketch import TurtleSketch
from .tlib.TurtleParams import TurtleParams
from .tlib.TurtleComponent import TurtleComponent
from .tlib.TurtleLayers import TurtleLayers
from .tlib.TurtleCustomCommand import TurtleCustomCommand
from .tlib.TurtleDecoder import TurtleDecoder
from .tlib.data.SketchData import SketchData

f,core,app,ui = TurtleUtils.initGlobals()

class MoldBuilder(TurtleCustomCommand):
    def __init__(self):
        self.rootComponent = TurtleComponent(TurtleUtils.activeRoot())
        self.parameters = TurtleParams.instance()
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
        self.setParameters()
        self.createTop(True)

    def onExecute(self, eventArgs:core.CommandEventArgs):
        self.setParameters()
        self.createTop(False)

    def setParameters(self):
        self.parameters.setOrCreateParam('wallThickness', self.moldWallThickness.expression)
        self.parameters.setOrCreateParam('lipWidth', self.lipThickness.expression)
        self.parameters.setOrCreateParam('slotLength', self.slotLength.expression)
        self.parameters.setOrCreateParam('slotSpacing', self.slotSpacing.expression)


    def createTop(self, isPreview:bool):
        curFace = self.topFace
        #curFace = self.frontOuterFace
        curTSketch = curFace.createSketchAtPoint(curFace.centroid)
        self.curComponent = TurtleComponent.createFromSketch(curTSketch.sketch)
        offsetExpr = 'wallThickness + lipWidth'
        pasteData = SketchData.hole()
        curTSketch.areProfilesShown = False
        l0 = curFace.loops[0]
        l1 = curFace.loops[1]
        loops = [l0, l1] if l0.isOuter else [l1, l0]
        offsetChains = []
        if isPreview:
            for loop in loops:
                projectedList = curTSketch.projectList(loop.edges, True) 
                cent = curFace.centroid if(loop.isOuter) else core.Point3D.create(-9999,-9999,-9999)
                offsetElements, offsetConstraint = curTSketch.offset(projectedList, cent, offsetExpr, False)
                offsetChains.append(offsetElements)
        else:
            sortedLoops = []
            for loop in loops: 
                sortedLoops.insert(0, loop) if loop.isOuter else sortedLoops.append(loop)
    
            # need to do offsets first or Fusion gets confused. This could be because profiles and sketch calculations are off.
            for loop in sortedLoops:           
                projectedList = curTSketch.projectList(loop.edges, True) 
                cent = curFace.centroid if(loop.isOuter) else core.Point3D.create(-9999,-9999,-9999)
                isConstruction = not loop.isOuter
                offsetElements, offsetConstraint = curTSketch.offset(projectedList, cent, offsetExpr, isConstruction)
                offsetChains.append(offsetElements)

            chainIndex = 0
            for chain in offsetChains:
                #BRepCoEdge objects flow around the outer boundary in a counter-clockwise direction, while inner boundaries are clockwise
                isInner = chainIndex > 0
                cw = isInner

                ptPairs = curTSketch.getPointChain(chain, cw)
                slotLen = self.parameters.getParamValueOrDefault('slotLength', 1.0)
                slotSpc = self.parameters.getParamValueOrDefault('slotSpacing', 1.5)
                tabbedSegments = []
                for pair in ptPairs:
                    segs = TurtleSketch.createCenteredTabs(pair[0], pair[1], slotLen, slotSpc)
                    tabbedSegments = tabbedSegments + segs
                TurtleDecoder.createWithPointChain(pasteData, curTSketch.sketch, tabbedSegments, False, False)

                profile = curTSketch.findOuterProfile()
                _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['wallThickness'])
                if not isInner:
                    extrude = newFeatures[0]
                    extrude.timelineObject.rollTo(True)
                    extrude.startExtent = f.FromEntityStartDefinition.create(self.bottomFace.face, self.parameters.createValue('wallThickness'))
                    extrude.timelineObject.rollTo(False)
                    for line in offsetElements: # make top extrusion have hole
                        line.isConstruction = False
                chainIndex += 1

            curTSketch.areProfilesShown = True



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
            wallThicknessParam = self.parameters.addOrGetParam('wallThickness', '4 mm')
            self.moldWallThickness = inputs.addDistanceValueCommandInput('txWallThickness', 'Mold Wall Thickness',\
                 self.parameters.createValue(wallThicknessParam.expression))
            self.moldWallThickness.setManipulator(self.frontOuterFace.centroid, self.frontNorm)

            lipWidthParam = self.parameters.addOrGetParam('lipWidth', '2 mm')
            self.lipThickness = inputs.addDistanceValueCommandInput('txLipWidth', 'Lip Width', self.parameters.createValue(lipWidthParam.expression))
            self.lipThickness.setManipulator(self.rightOuterFace.maxPoint, self.rightNorm)
            
            # better to specify max slots per wall
            slotLengthParam = self.parameters.addOrGetParam('slotLength', '10 mm')
            self.slotLength = inputs.addDistanceValueCommandInput('txSlotLen', 'Slot Length', self.parameters.createValue(slotLengthParam.expression))
            #self.slotLength.setManipulator(self.rightOuterFace.maxPoint, self.rightNorm)

            slotSpacingParam = self.parameters.addOrGetParam('slotSpacing', '12 mm')
            self.slotSpacing = inputs.addDistanceValueCommandInput('txSlotSpacing', 'Slot Spacing', self.parameters.createValue(slotSpacingParam.expression))
            
            
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
        self.topFace = next(tface for tface in allFaces if tface.loops.count == 2)
        allFaces.remove(self.topFace)

        # the normal points into the material, not out of it.
        self.topNorm = self.topFace.normal
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

        self.floorFace:TurtleFace = self.faceWithNormalMatch(self.topNorm, allFaces)
        self.bottomFace:TurtleFace = self.faceWithNormalMatch(self.bottomNorm, allFaces)
        self.frontOuterFace:TurtleFace = self.faceWithNormalMatch(self.frontNorm, allFaces, True)
        self.frontInnerFace:TurtleFace = self.faceWithNormalMatch(self.frontNorm, allFaces, False)
        self.backOuterFace:TurtleFace = self.faceWithNormalMatch(self.backNorm, allFaces, True)
        self.backInnerFace:TurtleFace = self.faceWithNormalMatch(self.backNorm, allFaces, False)
        self.leftOuterFace:TurtleFace = self.faceWithNormalMatch(self.leftNorm, allFaces, True)
        self.leftInnerFace:TurtleFace = self.faceWithNormalMatch(self.leftNorm, allFaces, False)
        self.rightOuterFace:TurtleFace = self.faceWithNormalMatch(self.rightNorm, allFaces, True)
        self.rightInnerFace:TurtleFace = self.faceWithNormalMatch(self.rightNorm, allFaces, False)

        topLengths = self.topFace.xyzLengths
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
            
    def faceWithNormalMatch(self, norm:core.Vector3D, tfaces:list[TurtleFace], findLargest:bool = False) -> TurtleFace:
        result = None
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
            tfaces.remove(result)
        return result