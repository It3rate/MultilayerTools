
import adsk.core, adsk.fusion, adsk.cam, traceback
import os, math, re
from .TurtleUtils import TurtleUtils
from .TurtleComponent import TurtleComponent
from .TurtleSketch import TurtleSketch
from .TurtleParams import TurtleParams
from .TurtlePath import TurtlePath
from .TurtleLayers import TurtleLayers

f,core,app,ui,design,root = TurtleUtils.initGlobals()

pMID = "mid"
pOUTER = "outer"
pFULL = "full"
pLIP = "lip"
pSHELF_WIDTH = "shelfWidth"
pZIP_WIDTH = "zipWidth"
pZIP_LENGTH = "zipLength"

class JointMaker:
    def __init__(self):
        sketch:f.Sketch = TurtleUtils.getTargetSketch(f.Sketch)
        if not sketch:
            return
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType

        self.rootComponent = TurtleComponent(root)
        self.baseComponent = TurtleComponent.createFromSketch(sketch)

        self.baseSketch = TurtleSketch(sketch)
        TurtleParams.instance().addParams(
            pMID, 3,
            pOUTER, 2,
            pFULL, pMID + "+" + pOUTER + " * 2",
            pLIP, 1,
            pSHELF_WIDTH, 40,
            pZIP_WIDTH, 1,
            pZIP_LENGTH, pZIP_WIDTH + " * 10")

        self.midPlane = self.rootComponent.createOffsetPlane(self.baseSketch.referencePlane, pSHELF_WIDTH, "MidPlane")
        fullProfile = self.baseSketch.combineProfiles()
        self.shelfLines = self.baseSketch.getSingleLines()

        self.createWalls(fullProfile)
        self.createShelves()
    
    def createWalls(self, profile):
        layers = TurtleLayers(self.baseComponent, profile, [pOUTER, pMID, pOUTER])
        # wall cuts
        outerWallSketch = self.baseComponent.createSketch(layers.startFaceAt(0), "outerWallSketch")
        outerProfile = self.drawWallOuterCuts(outerWallSketch)
        innerWallSketch = self.baseComponent.createSketch(layers.startFaceAt(1), "innerWallSketch")
        innerProfile = self.drawWallInsideCuts(innerWallSketch)
        layers.cutWithProfiles([outerProfile, innerProfile, innerProfile])

        layers.mirrorLayers(self.midPlane, False)

    def createShelves(self):
        for idx, line in enumerate(self.shelfLines):
            layers = self.createHalfShelf(line, idx)
            layers.mirrorLayers(self.midPlane, True)

    def createHalfShelf(self, line:f.SketchLine, index) -> TurtleLayers:
        tcomp = self.rootComponent.createNew("shelf"+ str(index))
        plane = tcomp.createOrthoganalPlane(line)
        tsketch = tcomp.createSketch(plane)
        baseLine = tsketch.projectLine(line)
        construction = tsketch.addMidpointConstructionLine(baseLine)
        lines = tsketch.draw(construction, 
            "M10 LM1",
            "#0 F47",
            "#1 RF200",
            "#2 LF2",
            "#3 RF400",
            "#4 RF100",
            "#5 RF400",
            "#6 RF2",
            "#7 LF200",
            "#8 RF47",
            "#9 RF200",
            "#10 RF2",
            "#11 LF100",
            "#12 LF4",
            "#13 LF300",
            "#14 LF2")

        tsketch.constrain( [
            "ME", [0,0,13,1, 9,0,14,1],
            "PA", [baseLine, 0],
            "EQ", [baseLine, 4],
            "CL", [0,8, 2,6],
            "PA", [0,4, 1,7, 3,5, 9,13, 11,13, 12,10],
            "SY", [9,13,construction, 1,7,construction, 3,5,construction],
            "PE", [2,3, 9,10],

            "LD", [0,baseLine,pOUTER],
            "LL", [11, pZIP_LENGTH + " - " + pLIP, 
                    13, pZIP_LENGTH, 
                    1, pOUTER + " + " + pMID, 
                    3, pSHELF_WIDTH + " - " + pFULL, 
                    14, pZIP_WIDTH,
                    12, pZIP_WIDTH + " * 2",
                    2, pLIP]
        ] )

        cutProfile = tsketch.getProfileAt(0)
        fullProfile = tsketch.combineProfiles()
        layers = TurtleLayers(tcomp, [fullProfile,cutProfile,fullProfile], [pOUTER, pMID, pOUTER])
        return layers
    
    
    def drawWallInsideCuts(self, tsketch:TurtleSketch) -> f.Profile:
        for line in self.shelfLines:
            baseLine:f.SketchLine = tsketch.projectLine(line, True)
            construction = tsketch.addMidpointConstructionLine(baseLine, None, True)

            lines = tsketch.drawClosed(construction, "RM20L180 F40 RF2 RF40 RF20")
            tsketch.constrain( [
                "PA", [0,2, 1,3],
                "PE", [0, 1],
                "CL", [0, baseLine],
                "LL", [1, pFULL],
                "SY", [1, 3, construction],
                "PD", [baseLine, 0, 0, 0, pLIP]
            ])

        fullProfile = tsketch.combineProfiles()
        fullProfile.removeByIndex(0)
        return fullProfile

    def drawWallOuterCuts(self, tsketch:TurtleSketch) -> f.Profile:
        for line in self.shelfLines:
            self.drawZipNotch(tsketch, line)
        fullProfile = tsketch.combineProfiles()
        tsketch.removeLargestProfile(fullProfile)
        return fullProfile

    def drawZipNotch(self, tsketch:TurtleSketch, shelfLine:f.SketchLine):
        baseLine:f.SketchLine = tsketch.projectLine(shelfLine)
        construction = tsketch.addMidpointConstructionLine(baseLine, pOUTER, True)

        tsketch.draw(construction, "M75LF50 RF50 RF50 RF50")
        tsketch.constrain( [
            "ME", [0,0,3,1],
            "PE", [0, construction],
            "PA", [0,2, 1,3],
            "PE", [0, 1],
            "MI", [construction, 1, 0],
            "LL", [0, pZIP_WIDTH, 
                    1, pMID]
        ])


    def createComponent(self, name):
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ.component.name = name
        return occ.component



