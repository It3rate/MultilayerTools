# #Author-Robin Debreuil
# #Extrudes a profile into multiple layer bodies of parameterized thicknesses. Can also be used to cut, intersect existing layered components.

import adsk.core, adsk.fusion, traceback
from .lib.TurtleUtils import TurtleUtils
from .lib.TurtleUICommand import TurtleUICommand
from .lib.TurtleSketch import TurtleSketch
from .lib.TurtleParams import TurtleParams
from .lib.TurtleComponent import TurtleComponent

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class ExtrudeLayersCommand(TurtleUICommand):
    def __init__(self):
        self.params = TurtleParams.instance()
        cmdId = 'ExtrudeLayersId'
        cmdName = 'Extrude Layers Command'
        cmdDescription = 'Extrudes a profile into multiple layer bodies of parameterized thicknesses. Can also be used to cut, intersect existing layered components.'
        targetPanels = self.getTargetPanels()
        super().__init__(cmdId, cmdName, cmdDescription, targetPanels)

    def getTargetPanels(self):
        return ui.allToolbarPanels.itemById('SolidCreatePanel'), ui.allToolbarPanels.itemById('SketchCreatePanel')

    def onStartedRunning(self, eventArgs:core.CommandCreatedEventArgs):
        super().onStartedRunning(eventArgs)

    def onCreateUI(self, eventArgs:core.CommandCreatedEventArgs):
        try:
            self.thicknessParamNames = ['mat0', 'mat1', 'mat2', 'mat3', 'mat4', 'mat5']
            self.params.addParams(
                self.thicknessParamNames[0], 2,
                self.thicknessParamNames[1], 3,
                self.thicknessParamNames[2], 3.5,
                self.thicknessParamNames[3], 4,
                self.thicknessParamNames[4], 4.5,
                self.thicknessParamNames[5], 5)
            
            self.paramTable = []
            for i in range(len(self.thicknessParamNames)):
                paramVal = self.params.getValue(self.thicknessParamNames[i])
                self.paramTable.append([self.thicknessParamNames[i], paramVal, True])

            self.layerCount = 0
            # Get the CommandInputs collection associated with the command.
            inputs = eventArgs.command.commandInputs

            # Select profiles
            self.profilesSelection = inputs.addSelectionInput('selProfile', 'Select Profile', 'Select profile to extrude.')
            self.profilesSelection.setSelectionLimits(1,0)
            self.profilesSelection.addSelectionFilter('Profiles')

            # Flip direction
            self.flipDirection = inputs.addBoolValueInput('bFlip', 'Flip Direction', True, "resources/Flip/", False)
            #self.flipDirection = inputs.addDirectionCommandInput('bFlip', 'Flip Direction')#, "./resources/Flip/")
            
            # Create table input
            self.tbLayers = inputs.addTableCommandInput('tbLayers', 'Layers', 3, '6:4:1')
            self.addLayer(0)       
            self.addLayer(1)       
            self.addLayer(0)       
            btAddItem = inputs.addBoolValueInput('tableAdd', 'Add', False, "resources/Add/", True)
            self.tbLayers.addToolbarCommandInput(btAddItem)
            btDeleteItem = inputs.addBoolValueInput('tableDelete', 'Delete', False, "resources/Remove/", True)
            self.tbLayers.addToolbarCommandInput(btDeleteItem)

            # * maybe not: Start (Profile Plane, Offset, Object)
            # Direction (One Side, Two Sides, Symmetric)
            # Layers (count, auto params or names?)
            # Operation (new bodies --- cut merge into existing, intersect existing)
            #                       --- Objects to cut/merge/intersect

            self.resetUI()
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
        
    def onInputsChanged(self, eventArgs:core.InputChangedEventArgs):
        try:
            inputs = eventArgs.inputs
            cmdInput = eventArgs.input
            
            if cmdInput.id.startswith("MaterialInput"):
                inputIndex = int(cmdInput.id[-1])
                selectedIndex = cmdInput.selectedItem.index
                thicknessField = cmdInput.parentCommandInput.getInputAtPosition(inputIndex, 1)
                thicknessValue = self.params.getValue("mat" + str(selectedIndex))
                thicknessField.expression = thicknessValue # todo: keep table of thickness expression changes, only commit to params at end. Use lock icon?
            elif cmdInput.id.startswith("MaterialThickness"):
                inputIndex = int(cmdInput.id[-1])
            elif cmdInput.id == 'tableAdd':
                if self.layerCount < 6:
                    self.addLayer(self.layerCount)
                if self.layerCount >= 5:
                    cmdInput.isEnabled = False
            elif cmdInput.id == 'tableDelete':
                if self.tbLayers.selectedRow == -1:
                    ui.messageBox('Select one row to delete.')
                else:
                    selectedIndex = cmdInput.parentCommandInput.selectedRow
                    self.tbLayers.deleteRow(selectedIndex)
                    cmdInput.isEnabled = True
                    
            self.resetUI()
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
        
    def onValidateInputs(self, eventArgs:core.ValidateInputsEventArgs):
            super().onValidateInputs(eventArgs)
        
    def onPreview(self, eventArgs:core.CommandEventArgs):
        layers = self.extrude()
        layers.sketch.isVisible = True

    def onExecute(self, eventArgs:core.CommandEventArgs):
        self.extrude()
        adsk.autoTerminate(False)

    def resetUI(self):
        pass

    def onDestroy(self, eventArgs:core.CommandEventArgs):
        super().onDestroy(eventArgs)

    
    def extrude(self):
        profiles = []
        for index in range(self.profilesSelection.selectionCount):
            profiles.append(self.profilesSelection.selection(index).entity)
        #profiles = self.profilesSelection.selection
        sketch = profiles[0].parentSketch
        comp:TurtleComponent = TurtleComponent.createFromSketch(sketch)
        return comp.createLayers([profiles], ['3mm', '1mm', '2mm'], 3, self.flipDirection.value)

    def addLayer(self, selectedIndex):
        cmdInputs:core.CommandInputs = self.tbLayers.commandInputs

        materialCount = 6
        ddMaterial =  cmdInputs.addDropDownCommandInput('MaterialInput{}'.format(self.layerCount), 'ddMaterial', core.DropDownStyles.LabeledIconDropDownStyle)
        ddItems = ddMaterial.listItems
        for i in range(materialCount):
            ddItems.add('Material ' + str(i + 1), i == selectedIndex, 'resources/ColorChip' + str(i))
        
        paramItem = self.paramTable[selectedIndex]
        thicknessValue = paramItem[1]
        if paramItem[2]: # Locked
            valueInput = cmdInputs.addTextBoxCommandInput('MaterialThickness{}'.format(self.layerCount), 'Value', str(thicknessValue), 1, True)
            lockIcon = cmdInputs.addImageCommandInput('LockThickness{}'.format(self.layerCount), str(thicknessValue), 'resources/Lock/16x24.png')
        else:
            valueInput = cmdInputs.addValueInput('MaterialThickness{}'.format(self.layerCount), 'Value', 'mm', self.params.createValue(thicknessValue))
            lockIcon = cmdInputs.addImageCommandInput('LockThickness{}'.format(self.layerCount), '', 'resources/Unlock/16x24.png')
        
        row = self.tbLayers.rowCount
        self.tbLayers.addCommandInput(ddMaterial, row, 0)
        self.tbLayers.addCommandInput(valueInput, row, 1)
        self.tbLayers.addCommandInput(lockIcon, row, 2)

        self.layerCount += 1