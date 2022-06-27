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
        self.workingPointList = None
        self.currentTSketch = None
        self.slotLengthVal = 1
        self.slotSpaceVal = 1
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
        # self.createTopAndBottom(True)
        # self.createFrontAndBack(True)
        self.createLeftAndRight(True)
        self.curComponent.colorBodiesByOrder()

    def onExecute(self, eventArgs:core.CommandEventArgs):
        self.setParameters()
        self.createTopAndBottom(False)
        self.createFrontAndBack(False)
        self.createLeftAndRight(True)
        self.curComponent.colorBodiesByOrder()
        
    def setParameters(self):
        self.parameters.setOrCreateParam('wallThickness', self.diagMoldWallThickness.expression)
        self.parameters.setOrCreateParam('lipWidth', self.diagLipThickness.expression)
        self.parameters.setOrCreateParam('slotLength', self.diagSlotLength.expression)
        self.parameters.setOrCreateParam('slotSpacing', self.diagSlotSpacing.expression)

        self.wallThicknessVal = self.parameters.getParamValueOrDefault('wallThickness', 1.0)
        self.lipWidthVal = self.parameters.getParamValueOrDefault('lipWidth', 1.0)
        self.slotLengthVal = self.parameters.getParamValueOrDefault('slotLength', 1.0)
        self.slotSpaceVal = self.parameters.getParamValueOrDefault('slotSpacing', 1.5)

    def createLeftAndRight(self, isPreview:bool):
        projectedList = self.sketchFromFace(self.leftOuterFace, 0, True)
        self.currentTSketch.areProfilesShown = False
        ptPairs = self.currentTSketch.getPointChain(projectedList, True)
        for pp in ptPairs:
            self.drawFingerLine(*pp, True)
        self.currentTSketch.areProfilesShown = True
        #left wall extrude
        profile = self.currentTSketch.findOuterProfile()
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['wallThickness'])
        #right wall extrude
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['-wallThickness'])
        TurtleLayers.changeExturdeToPlaneOrigin(newFeatures[0], self.rightOuterFace.face, self.parameters.createValue(0))
        self.currentTSketch.areProfilesShown = True

    def createTopAndBottom(self, isPreview:bool):
        outerLoopIndex = 0 if self.topFace.loops[0].isOuter else 1
        projectedList = self.sketchFromFace(self.topFace, outerLoopIndex, True)
        self.currentTSketch.areProfilesShown = False
        
        outerRect, _ = self.currentTSketch.offset(projectedList, self.topFace.centroid, 'wallThickness + lipWidth', False)
        ptPairs = self.currentTSketch.getPointChain(projectedList, True)
        for pp in ptPairs:
            self.drawHoleLine(*pp, True)

        # extrude top, uncut
        profile = self.currentTSketch.findOuterProfile()
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['wallThickness'])
        topBody = newFeatures[0].bodies[0]
        #extrude  bottom
        profile = self.currentTSketch.findOuterProfile()
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['-wallThickness'])
        TurtleLayers.changeExturdeToPlaneOrigin(newFeatures[0], self.bottomFace.face, self.parameters.createValue(0))
        self.currentTSketch.areProfilesShown = True
        # cut top lid hole
        innerLoopIndex = 1 if self.topFace.loops[0].isOuter else 0
        projectedList = self.sketchFromFace(self.topFace, innerLoopIndex, False)
        self.currentTSketch.areProfilesShown = False
        innerRect, _ = self.currentTSketch.offset(projectedList, self.topFace.centroid, 'wallThickness + lipWidth', False)
        ptPairs = self.currentTSketch.getPointChain(projectedList, True)
        for pp in ptPairs:
            self.drawHoleLine(*pp, False)

        profile = self.currentTSketch.allButOuterProfile()
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['wallThickness'])
        TurtleLayers.changeExtrudeToCut(newFeatures[0], [topBody])
        self.currentTSketch.areProfilesShown = True
        return

    def createFrontAndBack(self, isPreview:bool):
        projectedList = self.sketchFromFace(self.frontOuterFace, 0, True)
        self.currentTSketch.areProfilesShown = False
        # generate side segments
        orgLeft = projectedList[0]
        orgRight = projectedList[2]
        pLeft = self.currentTSketch.offset([orgLeft], self.frontOuterFace.centroid, 'wallThickness + lipWidth', False)[0][0]
        pRight = self.currentTSketch.offset([orgRight], self.frontOuterFace.centroid, '-(wallThickness + lipWidth)', False)[0][0]
        (left, bottom, right, top) = \
            self.getSortedRectSegments(pLeft.startSketchPoint, pRight.startSketchPoint, pRight.endSketchPoint, pLeft.endSketchPoint)

        self.drawHoleLine(orgLeft.startSketchPoint, orgLeft.endSketchPoint, False)
        self.drawHoleLine(orgRight.startSketchPoint, orgRight.endSketchPoint, True)
        self.drawFingerLine(*top, True)
        self.drawFingerLine(*bottom, False)
        #front wall extrude
        profile = self.currentTSketch.findOuterProfile()
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['wallThickness'])
        #back wall extrude
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['-wallThickness'])
        TurtleLayers.changeExturdeToPlaneOrigin(newFeatures[0], self.backOuterFace.face, self.parameters.createValue(0))
        self.currentTSketch.areProfilesShown = True

    def sketchFromFace(self, face:f.BRepFace, projectLoopIndex:int = 0, asConstruction:bool = True)-> list[f.BRepEdges]:
        self.currentTSketch = face.createSketchAtPoint(face.centroid)
        self.curComponent = TurtleComponent.createFromSketch(self.currentTSketch.sketch)
        loop = face.loops[projectLoopIndex]
        return self.currentTSketch.projectList(loop.edges, asConstruction)

    # generate sorted point pairs of rect, direction is always left to right and top to bottom
    def getSortedRectSegments(self, tl:f.SketchPoint, tr:f.SketchPoint, br:f.SketchPoint, bl:f.SketchPoint)->list[list[f.SketchPoint]]:
        leftPair = TurtleSketch.sortedSketchPointsMinToMax(tl, bl)
        bottomPair = TurtleSketch.sortedSketchPointsMinToMax(bl, br)
        rightPair = TurtleSketch.sortedSketchPointsMinToMax(br, tr)
        topPair = TurtleSketch.sortedSketchPointsMinToMax(tl, tr)
        return [leftPair, bottomPair, rightPair, topPair]
        
    def drawHoleLine(self, startPoint:f.SketchPoint, endPoint:f.SketchPoint, mirror:bool) -> TurtleDecoder:
        drawData = SketchData.hole()
        segs = TurtleSketch.createCenteredTabs(startPoint.geometry, endPoint.geometry, self.slotLengthVal, self.slotSpaceVal)
        return TurtleDecoder.createWithPointChain(drawData, self.currentTSketch.sketch, segs, False, mirror)

    def drawFingerLine(self, startPoint:f.SketchPoint, endPoint:f.SketchPoint, mirror:bool) -> TurtleDecoder:
        drawData = SketchData.finger()
        callback = self.fingerSegmentsCallback
        segs = TurtleSketch.createCenteredTabs(startPoint.geometry, endPoint.geometry, self.slotLengthVal, self.slotSpaceVal)
        self.workingPointList = [startPoint]
        decoder = TurtleDecoder.createWithPointChain(drawData, self.currentTSketch.sketch, segs, False, mirror, callback)
        self.workingPointList.append(endPoint)
        spaces = zip(self.workingPointList[::2], self.workingPointList[1::2])
        self.currentTSketch.drawLines(spaces)
        return decoder
    def fingerSegmentsCallback(self, decoder:TurtleDecoder):
        startPt = decoder.getPointByName('p1')
        self.workingPointList.append(startPt)
        endPt = decoder.getPointByName('p4')
        self.workingPointList.append(endPt)

    def drawNotchesLine(self, startPoint:f.SketchPoint, endPoint:f.SketchPoint, mirror:bool) -> TurtleDecoder:
        drawData = SketchData.notches()
        callback = self.notchesSegmentsCallback
        segs = TurtleSketch.createCenteredTabs(startPoint.geometry, endPoint.geometry, self.slotLengthVal, self.slotSpaceVal)
        self.workingPointList = [startPoint]
        decoder = TurtleDecoder.createWithPointChain(drawData, self.currentTSketch.sketch, segs, False, mirror, callback)
        self.workingPointList.append(endPoint)
        spaces = zip(self.workingPointList[::2], self.workingPointList[1::2])
        self.currentTSketch.drawLines(spaces)
        return decoder
    def notchesSegmentsCallback(self, decoder:TurtleDecoder):
        startPt = decoder.getPointByName('p1')
        self.workingPointList.append(startPt)
        endPt = decoder.getPointByName('p10')
        self.workingPointList.append(endPt)




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
            self.diagMoldWallThickness = inputs.addDistanceValueCommandInput('txWallThickness', 'Mold Wall Thickness',\
                 self.parameters.createValue(wallThicknessParam.expression))
            self.diagMoldWallThickness.setManipulator(self.frontOuterFace.centroid, self.frontNorm)

            lipWidthParam = self.parameters.addOrGetParam('lipWidth', '2 mm')
            self.diagLipThickness = inputs.addDistanceValueCommandInput('txLipWidth', 'Lip Width', self.parameters.createValue(lipWidthParam.expression))
            self.diagLipThickness.setManipulator(self.rightOuterFace.maxPoint, self.rightNorm)
            
            # better to specify max slots per wall
            slotLengthParam = self.parameters.addOrGetParam('slotLength', '10 mm')
            self.diagSlotLength = inputs.addDistanceValueCommandInput('txSlotLen', 'Slot Length', self.parameters.createValue(slotLengthParam.expression))
            #self.diagSlotLength.setManipulator(self.rightOuterFace.maxPoint, self.rightNorm)

            slotSpacingParam = self.parameters.addOrGetParam('slotSpacing', '12 mm')
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
