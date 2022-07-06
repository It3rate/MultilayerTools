# #Author-Robin Debreuil
# # Generates a laser cuttable mold from a shelled box.

from xmlrpc.client import Boolean
from enum import Enum
import adsk.core, adsk.fusion, traceback
from .tlib.TurtleUtils import TurtleUtils
from .tlib.TurtleFace import *
from .tlib.TurtleUICommand import TurtleUICommand
from .tlib.TurtleSketch import TurtleSketch
from .tlib.TurtleParams import TurtleParams
from .tlib.TurtleComponent import TurtleComponent
from .tlib.TurtleLayers import TurtleLayers
from .tlib.TurtleCustomCommand import TurtleCustomCommand
from .tlib.TurtleDecoder import TurtleDecoder
from .tlib.data.SketchData import BuiltInDrawing, SketchData

f:adsk.fusion
core:adsk.core
f,core,app,ui = TurtleUtils.initGlobals()

class MoldBuilder(TurtleCustomCommand):
    def __init__(self):
        self.rootComponent = TurtleComponent(TurtleUtils.activeRoot())
        self.xAxis = self.rootComponent.component.xConstructionAxis
        self.yAxis = self.rootComponent.component.yConstructionAxis
        self.zAxis = self.rootComponent.component.zConstructionAxis
        self.parameters = TurtleParams.instance()
        cmdId = 'ddwMoldBuilderId'
        cmdName = 'Mold Builder'
        cmdDescription = 'Generates a laser cuttable mold from a shelled box.'
        self.workingPointList = None
        self.currentTSketch:TurtleSketch = None
        self.slotLengthVal = 1
        self.slotSpaceVal = 1

        self.slotCountWidth = 3
        self.slotCountDepth = 2
        self.slotCountHeight = 1
        # self.slotCountWidth = 1
        # self.slotCountDepth = 1
        # self.slotCountHeight = 1
        super().__init__(cmdId, cmdName, cmdDescription)
        
    def getTargetPanels(self):
        return [ui.allToolbarPanels.itemById('SolidCreatePanel')]

    def onCreated(self, eventArgs:core.CommandCreatedEventArgs):
        # investigations of a shelled box
        self.component:f.Component = TurtleUtils.activeDesign().activeComponent
        self.tComponent:TurtleComponent = TurtleComponent.createFromExisting(self.component)
        self.xAxis = self.component.xConstructionAxis
        self.yAxis = self.component.yConstructionAxis
        self.zAxis = self.component.zConstructionAxis
        if not self.component.bRepBodies.count == 1 or not self.component.bRepBodies.item(0).faces.count == 11:
            return
        self._parseFaces()
        
        self._createDialog(eventArgs.command.commandInputs)

    def onInputsChanged(self, eventArgs:core.InputChangedEventArgs):
        pass

    def onPreview(self, eventArgs:core.CommandEventArgs):
        self.setParameters()
        #self.createFloor(True)
        # self.createTopAndBottom(True)
        self.createInnerLeftAndRight(True)
        self.createInnerFrontAndBack(True)
        # self.createOuterFrontAndBack(True)
        # self.createOuterLeftAndRight(True)

        # self.curComponent.colorBodiesByOrder([0])
        # orgBody = self.curComponent.getBodyByIndex(0)
        # orgBody.isVisible = False

    def onExecute(self, eventArgs:core.CommandEventArgs):
        self.onPreview(eventArgs)
        return
        self.setParameters()
        self.createFloor(False)
        self.createTopAndBottom(False)
        self.createInnerLeftAndRight(False)
        self.createInnerFrontAndBack(False)
        self.createOuterFrontAndBack(False)
        self.createOuterLeftAndRight(False)


    # def getExpandedRectPoints(self, edges)->list[tuple[core.Point3D,core.Point3D]]:
    #     if(len(edges) == 2):
    #         pass
    #     else:
    #         pass
    #     return self.getSortedRectSegments(points)

    def extrudeLargest(self, colorIndex:int)->f.Feature:
        profile = self.currentTSketch.findLargestProfile()
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['wallThickness'])
        self.tComponent.colorExtrudedBodiesByIndex(newFeatures[0],colorIndex)
        return newFeatures[0]
        
    def getAxisOfLine(self, line:f.SketchLine)->f.ConstructionAxis:
        lineDir = line.geometry.asInfiniteLine().direction
        negation = 1
        if self.xAxis.geometry.direction.isParallelTo(lineDir):
            result = self.xAxis
            negation = lineDir.x
        elif self.yAxis.geometry.direction.isParallelTo(lineDir):
            result = self.yAxis
            negation = lineDir.y
        elif self.zAxis.geometry.direction.isParallelTo(lineDir):
            result = self.zAxis
            negation = lineDir.z
        return (result, lineDir, negation)

    def getLinesByAxis(self, axis:f.ConstructionAxis, sortAxis:f.ConstructionAxis, lines:list[f.SketchLine])->f.SketchLine:
        axisDir = axis.geometry.direction
        result = []
        for line in lines:
            lineDir = line.geometry.asInfiniteLine().direction
            if axisDir.isParallelTo(lineDir):
                result.append(line)
        return TurtleSketch.sortLinesMinToMax(result, sortAxis)

    def createFirstGuide(self, line:f.SketchLine)->f.SketchLine:
        pass

    def createInnerFrontAndBack(self, isPreview:bool):
        projectedList = self.sketchFromFace(self.backInnerFace, 0, True)
        # shrink bottom only, make holes in the sides, fingers in the bottom and top
        offsetLines = self.currentTSketch.offset([projectedList[3]], self.backInnerFace.centroid, '-wallThickness', True)[0]
        topLine = projectedList[1]
        bottomLine = offsetLines[0]
        # ptPairs = \
        #   self.getSortedRectSegments(topLine.startSketchPoint, bottomLine.startSketchPoint, bottomLine.endSketchPoint, topLine.endSketchPoint)
        ptPairs = self.currentTSketch.getRectPointChain([topLine, bottomLine], True)
        boundryLines = self.currentTSketch.drawLines(ptPairs)
        # main rect extrude
        rectFeature = self.extrudeLargest(1)

        bottomTop = self.getLinesByAxis(self.xAxis, self.yAxis, boundryLines)
        leftRight = self.getLinesByAxis(self.yAxis, self.xAxis, boundryLines)

        topLine = self.sketchFromFaceAndLines(self.backInnerFace, bottomTop[1])[0]
        #linePts, line = self.sketchFromFaceAndPoints(self.backInnerFace, ptPairs[0], True)
        tabPts = self.currentTSketch.createFirstTabPoints(topLine.startSketchPoint, topLine.endSketchPoint,\
             self.slotLengthVal, self.slotSpaceVal, 4)# self.slotCountHeight)
        drawData = SketchData.createFromBuiltIn(BuiltInDrawing.finger)
        decoder = TurtleDecoder.createWithPoints(drawData, self.currentTSketch.sketch, tabPts)
        fingerFeature = self.extrudeLargest(1)
        
        rectangularPatterns = self.component.features.rectangularPatternFeatures
        features = core.ObjectCollection.create()
        features.add(fingerFeature)
        axis, lineDir, negation = self.getAxisOfLine(topLine)# self.component.zConstructionAxis# self.currentTSketch.sketch.xDirection
        quantity = self.parameters.createValue("4")
        dist = self.parameters.createValue(str(self.slotLengthVal + self.slotSpaceVal) + "*" + str(negation) + "cm")
        rectangularPatternInput = rectangularPatterns.createInput(features, axis, quantity, dist, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)
        
        # Set the data for second direction
        #rectangularPatternInput.setDirectionTwo(yAxis, quantityTwo, distanceTwo)
        
        # Create the rectangular pattern
        rectangularFeature = rectangularPatterns.add(rectangularPatternInput)
        return

        self.drawHoleOutline(*ptPairs[0], False, False, self.slotCountHeight) # right
        self.drawFingerLine(*ptPairs[1], False, False, self.slotCountWidth) # top
        self.drawHoleOutline(*ptPairs[2], False, False, self.slotCountHeight) # left  
        self.drawFingerLine(*ptPairs[3], False, False, self.slotCountWidth) # bottom  

        #inner back wall extrude
        profile = self.currentTSketch.findLargestProfile()
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['wallThickness'])
        self.tComponent.colorExtrudedBodiesByIndex(newFeatures[0],1)
        #inner front wall extrude
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['-wallThickness'])
        self.tComponent.colorExtrudedBodiesByIndex(newFeatures[0],1)
        TurtleLayers.changeExturdeToPlaneOrigin(newFeatures[0], self.frontInnerFace.face, self.parameters.createValue(0))


    def createInnerLeftAndRight(self, isPreview:bool):
        # all wall coordinates are  from the perspective of pointing into the material
        projectedList = self.sketchFromFace(self.rightInnerFace, 0, True) # projects to rtlb by index
        # print('projectedList')
        # self.currentTSketch.printSketchLines(projectedList)

        # shrink left, bottom and right edges and make fingers into floor and sides (and top)
         # projects to ltrb by index (offset ensures clockwise accounting for sketch flipping)
        offsetChain = self.currentTSketch.offset([projectedList[2], projectedList[3], projectedList[0]], self.rightInnerFace.centroid, 'wallThickness', True)[0]
        # print('offset chain')
        # self.currentTSketch.printPointPairs(offsetChain)

        leftLine = offsetChain[0]
        rightLine = offsetChain[2]
        ptPairs = self.currentTSketch.getRectPointChain([leftLine, rightLine], True)
        self.currentTSketch.drawLines(ptPairs)
        # main rect extrude
        self.extrudeLargest(2)
        return
        # print('point pairs')
        # self.currentTSketch.printPointPairs(ptPairs)

        self.drawFingerLine(*ptPairs[0], False, True, self.slotCountHeight) # left side
        self.drawFingerLine(*ptPairs[1], False, True, self.slotCountDepth) # bottom 
        self.drawFingerLine(*ptPairs[2], False, True, self.slotCountHeight) # right side
        self.drawFingerLine(*ptPairs[3], False, True, self.slotCountDepth) # top 

        #left wall extrude
        profile = self.currentTSketch.findLargestProfile()
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['wallThickness'])
        self.tComponent.colorExtrudedBodiesByIndex(newFeatures[0],2)
        #right wall extrude
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['-wallThickness'])
        self.tComponent.colorExtrudedBodiesByIndex(newFeatures[0],2)
        TurtleLayers.changeExturdeToPlaneOrigin(newFeatures[0], self.leftInnerFace.face, self.parameters.createValue(0))

    def createFloor(self, isPreview:bool):
        projectedList = self.sketchFromFace(self.bottomInnerFace, 0, False)
        #innerRect, _ = self.currentTSketch.offset(projectedList, self.floorFace.centroid, 'wallThickness', False)
        ptPairs = self.currentTSketch.getRectPointChain(projectedList, True)
        slotCounts = [self.slotCountDepth,self.slotCountWidth,self.slotCountDepth,self.slotCountWidth]
        for pp in zip(ptPairs,slotCounts):
            self.drawHoleLine(*pp[0], False, False, pp[1])
        #floor extrude
        profile = self.currentTSketch.findLargestProfile()
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['wallThickness'])
        self.tComponent.colorExtrudedBodiesByIndex(newFeatures[0],0)

    def createOuterLeftAndRight(self, isPreview:bool):
        projectedList = self.sketchFromFace(self.leftOuterFace, 0, True)
        
        slotCounts = [self.slotCountHeight+1,self.slotCountDepth+1,self.slotCountHeight+1,self.slotCountDepth+1]
        ptPairs = self.currentTSketch.getRectPointChain(projectedList, True)
        for pp in zip(ptPairs,slotCounts):
            self.drawFingerLine(*pp[0], False, True, pp[1])
        #left wall extrude
        profile = self.currentTSketch.findOuterProfile()
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['wallThickness'])
        self.tComponent.colorExtrudedBodiesByIndex(newFeatures[0],2)
        #right wall extrude
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['-wallThickness'])
        self.tComponent.colorExtrudedBodiesByIndex(newFeatures[0],2)
        TurtleLayers.changeExturdeToPlaneOrigin(newFeatures[0], self.rightOuterFace.face, self.parameters.createValue(0))

    def createTopAndBottom(self, isPreview:bool):
        outerLoopIndex = 0 if self.topFace.loops[0].isOuter else 1
        projectedList = self.sketchFromFace(self.topFace, outerLoopIndex, True)
        
        outerRect, _ = self.currentTSketch.offset(projectedList, self.topFace.centroid, 'wallThickness + lipWidth', False)
        ptPairs = self.currentTSketch.getRectPointChain(projectedList, True)
        slotCounts = [self.slotCountDepth+1,self.slotCountWidth+1,self.slotCountDepth+1,self.slotCountWidth+1]
        for pp in zip(ptPairs,slotCounts):
            self.drawHoleLine(*pp[0], False, True, pp[1])

        # extrude top, uncut
        profile = self.currentTSketch.findOuterProfile()
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['wallThickness'])
        self.tComponent.colorExtrudedBodiesByIndex(newFeatures[0],0)
        topBody = newFeatures[0].bodies[0]
        #extrude  bottom
        profile = self.currentTSketch.findOuterProfile()
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['-wallThickness'])
        self.tComponent.colorExtrudedBodiesByIndex(newFeatures[0],0)
        TurtleLayers.changeExturdeToPlaneOrigin(newFeatures[0], self.bottomOuterFace.face, self.parameters.createValue(0))

        # cut top lid hole
        innerLoopIndex = 1 if self.topFace.loops[0].isOuter else 0
        projectedList = self.sketchFromFace(self.topFace, innerLoopIndex, False)
        innerRect, _ = self.currentTSketch.offset(projectedList, self.topFace.centroid, 'wallThickness + lipWidth', False)
        ptPairs = self.currentTSketch.getRectPointChain(projectedList, True)
        slotCounts = [self.slotCountDepth,self.slotCountWidth,self.slotCountDepth,self.slotCountWidth]
        for pp in zip(ptPairs,slotCounts):
            self.drawHoleLine(*pp[0], False, False, pp[1])

        profile = self.currentTSketch.allButOuterProfile()
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['wallThickness'])
        TurtleLayers.changeExtrudeToCut(newFeatures[0], [topBody])
        return

    def createOuterFrontAndBack(self, isPreview:bool):
        projectedList = self.sketchFromFace(self.frontOuterFace, 0, True)
        # generate side segments
        orgLeft = projectedList[0]
        orgRight = projectedList[2]
        leftLine = self.currentTSketch.offset([orgLeft], self.frontOuterFace.centroid, 'wallThickness', False)[0][0]
        rightLine = self.currentTSketch.offset([orgRight], self.frontOuterFace.centroid, '-wallThickness', False)[0][0]
        # (left, bottom, right, top) = \
        #     self.getSortedRectSegments(pLeft.startSketchPoint, pRight.startSketchPoint, pRight.endSketchPoint, pLeft.endSketchPoint)

            
        #offsetLines = self.currentTSketch.offset([projectedList[0],projectedList[1],projectedList[2]], self.frontOuterFace.centroid, 'wallThickness + lipWidth', True)[0]
        # leftLine = offsetLines[0]
        # rightLine = offsetLines[2]
        ptPairs = self.currentTSketch.getRectPointChain([leftLine, rightLine], True)
        #ptPairs = self.currentTSketch.getRectPointChain(projectedList, True)
        self.drawHoleLine(*ptPairs[0], False, False, self.slotCountHeight + 1) #left
        self.drawFingerLine(*ptPairs[1], False, False, self.slotCountWidth + 1) #top
        self.drawHoleLine(*ptPairs[2], False, False, self.slotCountHeight + 1) #right
        self.drawFingerLine(*ptPairs[3], False, False, self.slotCountWidth + 1) #bottom

        #front wall extrude
        profile = self.currentTSketch.findOuterProfile()
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['wallThickness'])
        self.tComponent.colorExtrudedBodiesByIndex(newFeatures[0],1)
        #back wall extrude
        _, newFeatures = TurtleLayers.createFromProfiles(self.curComponent, profile, ['-wallThickness'])
        self.tComponent.colorExtrudedBodiesByIndex(newFeatures[0],1)
        TurtleLayers.changeExturdeToPlaneOrigin(newFeatures[0], self.backOuterFace.face, self.parameters.createValue(0))




    def setParameters(self):
        self.parameters.setOrCreateParam('wallThickness', self.diagMoldWallThickness.expression)
        self.parameters.setOrCreateParam('lipWidth', self.diagLipThickness.expression)
        self.parameters.setOrCreateParam('slotLength', self.diagSlotLength.expression)
        self.parameters.setOrCreateParam('slotSpacing', self.diagSlotSpacing.expression)

        self.wallThicknessVal = self.parameters.getParamValueOrDefault('wallThickness', 1.0)
        self.lipWidthVal = self.parameters.getParamValueOrDefault('lipWidth', 1.0)
        self.slotLengthVal = self.parameters.getParamValueOrDefault('slotLength', 1.0)
        self.slotSpaceVal = self.parameters.getParamValueOrDefault('slotSpacing', 1.5)

    def sketchFromFace(self, face:f.BRepFace, projectLoopIndex:int = 0, asConstruction:bool = True)-> list[f.BRepEdges]:
        self.currentTSketch = face.createSketchAtPoint(face.centroid)
        self.currentTSketch.areProfilesShown = False
        self.curComponent = TurtleComponent.createFromSketch(self.currentTSketch.sketch)
        loop = face.loops[projectLoopIndex]
        return self.currentTSketch.projectList(loop.edges, asConstruction)

    def sketchFromFaceAndPoints(self, face:f.BRepFace, points:list[f.SketchPoint], drawLine:bool = True)-> tuple[list[f.SketchPoint], f.SketchLine]:
        self.currentTSketch = face.createSketchAtPoint(face.centroid)
        self.curComponent = TurtleComponent.createFromSketch(self.currentTSketch.sketch)
        result = self.currentTSketch.projectList(points, False)
        line = None
        if drawLine:
            line = self.currentTSketch.drawLine(*result)
        return (result, line)

    def sketchFromFaceAndLines(self, face:f.BRepFace, lines:list[f.SketchLine])-> list[f.SketchLine]:       
        self.currentTSketch = face.createSketchAtPoint(face.centroid)
        self.curComponent = TurtleComponent.createFromSketch(self.currentTSketch.sketch)
        result = self.currentTSketch.projectList([lines], False)
        return result

    # generate sorted point pairs of rect, direction is always left to right and top to bottom
    def getSortedRectSegments(self, tl:f.SketchPoint, tr:f.SketchPoint, br:f.SketchPoint, bl:f.SketchPoint)->list[list[f.SketchPoint]]:
        leftPair = TurtleSketch.sortedSketchPointsMinToMax(tl, bl)
        bottomPair = TurtleSketch.sortedSketchPointsMinToMax(bl, br)
        rightPair = TurtleSketch.sortedSketchPointsMinToMax(br, tr)
        topPair = TurtleSketch.sortedSketchPointsMinToMax(tl, tr)
        return [leftPair, bottomPair, rightPair, topPair]
        






    def drawHoleLine(self, startPoint:f.SketchPoint, endPoint:f.SketchPoint, reverse:bool, mirror:bool, count:int = -1) -> TurtleDecoder:
        drawData = SketchData.createFromBuiltIn(BuiltInDrawing.hole)
        segs = TurtleSketch.createCenteredTabs(startPoint.geometry, endPoint.geometry, self.slotLengthVal, self.slotSpaceVal, count)
        return TurtleDecoder.createWithPointChain(drawData, self.currentTSketch.sketch, segs, reverse, mirror)

    def drawFingerLine(self, startPoint:f.SketchPoint, endPoint:f.SketchPoint, reverse:bool, mirror:bool, count:int = -1) -> TurtleDecoder:
        drawData = SketchData.createFromBuiltIn(BuiltInDrawing.finger)
        callback = self.fingerSegmentsCallback
        segs = TurtleSketch.createCenteredTabs(startPoint.geometry, endPoint.geometry, self.slotLengthVal, self.slotSpaceVal, count)
        self.workingPointList = [startPoint]
        decoder = TurtleDecoder.createWithPointChain(drawData, self.currentTSketch.sketch, segs, reverse, mirror, callback)
        self.workingPointList.append(endPoint)
        spaces = zip(self.workingPointList[::2], self.workingPointList[1::2])
        self.currentTSketch.drawHVLines(spaces)
        return decoder
    def fingerSegmentsCallback(self, decoder:TurtleDecoder):
        startPt = decoder.getPointByName('p1')
        self.workingPointList.append(startPt)
        endPt = decoder.getPointByName('p8')

        # dimPt = TurtleSketch.getMidpointOfPoints(startPt.geometry, endPt.geometry)
        # dimension = startPt.parentSketch.sketchDimensions.addDistanceDimension(startPt, endPt, 0, dimPt)
        # dimension.parameter.expression = 'slotLength'

        self.workingPointList.append(endPt)

    def drawHoleOutline(self, startPoint:f.SketchPoint, endPoint:f.SketchPoint, reverse:bool, mirror:bool, count:int = -1) -> TurtleDecoder:
        drawData = SketchData.createFromBuiltIn(BuiltInDrawing.holeOutline)
        callback = self.holeOutlineCallback
        segs = TurtleSketch.createCenteredTabs(startPoint.geometry, endPoint.geometry, self.slotLengthVal, self.slotSpaceVal, count)
        self.workingPointList = [startPoint]
        decoder = TurtleDecoder.createWithPointChain(drawData, self.currentTSketch.sketch, segs, reverse, mirror, callback)
        self.workingPointList.append(endPoint)
        spaces = zip(self.workingPointList[::2], self.workingPointList[1::2])
        self.currentTSketch.drawHVLines(spaces)
        return decoder
    def holeOutlineCallback(self, decoder:TurtleDecoder):
        startPt = decoder.getPointByName('p1')
        self.workingPointList.append(startPt)
        endPt = decoder.getPointByName('p2')
        
        # dimPt = TurtleSketch.getMidpointOfPoints(startPt.geometry, endPt.geometry)
        # dimension = startPt.parentSketch.sketchDimensions.addDistanceDimension(startPt, endPt, 0, dimPt)
        # dimension.parameter.expression = 'slotLength'

        self.workingPointList.append(endPt)

    def drawNotchesLine(self, startPoint:f.SketchPoint, endPoint:f.SketchPoint, reverse:bool, mirror:bool, count:int = -1) -> TurtleDecoder:
        drawData = SketchData.createFromBuiltIn(BuiltInDrawing.notches)
        callback = self.notchesSegmentsCallback
        segs = TurtleSketch.createCenteredTabs(startPoint.geometry, endPoint.geometry, self.slotLengthVal, self.slotSpaceVal, count)
        self.workingPointList = [startPoint]
        decoder = TurtleDecoder.createWithPointChain(drawData, self.currentTSketch.sketch, segs, reverse, mirror, callback)
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




