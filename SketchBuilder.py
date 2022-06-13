# #Author-Robin Debreuil
# #Extrudes a profile into multiple layer bodies of parameterized thicknesses. Can also be used to cut, intersect existing layered components.

import adsk.core, adsk.fusion, traceback
from .tlib.TurtleUtils import TurtleUtils
from .tlib.TurtleUICommand import TurtleUICommand
from .tlib.TurtleSketch import TurtleSketch
from .tlib.TurtleParams import TurtleParams
from .tlib.TurtleComponent import TurtleComponent
from .tlib.TurtleLayers import TurtleLayers
from .tlib.TurtleCustomCommand import TurtleCustomCommand

f,core,app,ui = TurtleUtils.initGlobals()

class SketchBuilder(TurtleCustomCommand):
    def __init__(self):
        self.params = TurtleParams.instance()
        cmdId = 'ddwSketchBuilderId'
        cmdName = 'Sketch Builder'
        cmdDescription = 'Creates a structure using a sketch and build recipes.'
        super().__init__(cmdId, cmdName, cmdDescription)
        
    def getTargetPanels(self):
        return [ui.allToolbarPanels.itemById('SolidCreatePanel'), ui.allToolbarPanels.itemById('SketchCreatePanel')]

    def onCreated(self, eventArgs:core.CommandCreatedEventArgs):
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
            
            self.paramTable = []
            for i in range(len(self.thicknessParamNames)):
                paramVal = self.params.getValue(self.thicknessParamNames[i])
                self.paramTable.append([self.thicknessParamNames[i], paramVal])

            self.stateTable = []
            
            self.guidelineSelection = inputs.addSelectionInput('selGuideline', 'Select Guidelines', 'Reference guideline for sketch generation.')
            self.guidelineSelection.setSelectionLimits(0,0)
            self.guidelineSelection.addSelectionFilter('SketchLines')

            self.btLoadText = inputs.addButtonRowCommandInput("btLoad", "Change Sketch Folder", False)
            self.btLoadText.listItems.add('Change Sketch Folder', False, 'resources/ddwCopySketchId')

            # Create table input
            self.tbLayers = inputs.addTableCommandInput('tbLayers', 'Layers', 3, '1:5:5')
            self.tbLayers.maximumVisibleRows = 6

            intitalLayers, isFlipped, isReversed, opType  = ([0,1,2], False, False, 0)# self._readDefaultLayerIndexes()
            for layerIndex in intitalLayers:
                self._addLayer(layerIndex)
            
            tbInputs = self.tbLayers.commandInputs
            self.btAddItem = tbInputs.addBoolValueInput('tableAdd', 'Add', False, "resources/Add/", True)
            self.tbLayers.addToolbarCommandInput(self.btAddItem)
            self.btDeleteItem = tbInputs.addBoolValueInput('tableDelete', 'Delete', False, "resources/Remove/", True)
            self.tbLayers.addToolbarCommandInput(self.btDeleteItem)
            
            self.reverseSelection = inputs.addBoolValueInput('bReverse', 'Reverse', True)
            self.mirrorSelection = inputs.addBoolValueInput('bMirror', 'Mirror', True)

            # self.bFlipDirection = inputs.addBoolValueInput('iAxis', 'Rotate Axis', True, "resources/Flip/", isFlipped)
            # self.bReversed = inputs.addBoolValueInput('bReverse', 'Rotate Axis', True, "resources/Reverse/", isReversed)

            ddOperation = inputs.addDropDownCommandInput("ddOperation", "Operation",  core.DropDownStyles.LabeledIconDropDownStyle)
            ddOperation.isFullWidth = True
            ddOperation.listItems.add("Join Component", False, 'resources/BooleanAdd')
            ddOperation.listItems.add("New Component", True, 'resources/BooleanNewComponent')
            self.opType = opType
            ddOperation.listItems[self.opType].isSelected = True

        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
            
    def _addLayer(self, ddChoice):
        cmdInputs:core.CommandInputs = self.tbLayers.commandInputs

        materialCount = 6
        row = self.tbLayers.rowCount 
        ddMaterial = cmdInputs.addDropDownCommandInput('MaterialInput{}'.format(row), 'ddMaterial', core.DropDownStyles.LabeledIconDropDownStyle)
        ddItems = ddMaterial.listItems
        for i in range(materialCount):
            ddItems.add('' + str(i + 1), i == ddChoice, 'resources/ColorChip' + str(i))
            
        ddSketch = cmdInputs.addDropDownCommandInput('SketchInput{}'.format(row), 'ddSketch', core.DropDownStyles.TextListDropDownStyle)
        ddItems = ddSketch.listItems
        ddItems.add('Sketch 1', True)
        ddItems.add('Sketch 2', False)
        ddItems.add('Sketch 3', False)

        ddProfile = cmdInputs.addDropDownCommandInput('ProfileInput{}'.format(row), 'ddProfile', core.DropDownStyles.TextListDropDownStyle)
        ddItems = ddProfile.listItems
        ddItems.add('Full Profile', True)
        ddItems.add('Profile 2', False)
        ddItems.add('Profile 3', False)
            
        #btLoadSketch = cmdInputs.addImageCommandInput("btLoad{}".format(row), 'ddLoad', 'resources/ddwCopySketchId/16x16-normal.png')

        #paramItem = self.paramTable[ddChoice]
        #thicknessValue = paramItem[1]
        #valueInput = cmdInputs.addTextBoxCommandInput('MaterialText{}'.format(row), 'Value', str(thicknessValue), 1, True)
        #lockIcon = cmdInputs.addImageCommandInput('Lock{}'.format(row), '', 'resources/Lock/16x24.png')
 
        self.tbLayers.addCommandInput(ddMaterial, row, 0)
        #self.tbLayers.addCommandInput(materialIcon, row, 0)
        self.tbLayers.addCommandInput(ddSketch, row, 1)
        #self.tbLayers.addCommandInput(btLoadSketch, row, 2)
        self.tbLayers.addCommandInput(ddProfile, row, 2)
        #self.stateTable.append([ddChoice, thicknessValue, True])