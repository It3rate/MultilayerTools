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
            self.tbLayers = inputs.addTableCommandInput('tbLayers', 'Layers', 4, '6:4:1')
             # Note: more items than maxvisiblerows results in text not appearing correctly.
            self.tbLayers.maximumVisibleRows = 6
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
            id = cmdInput.id
            rowIndex = -1
            print(id)
            
            if id.startswith("MaterialInput"):
                rowIndex = int(id[-1])
                ddIndex = cmdInput.selectedItem.index
                self.stateTable[rowIndex][0] = ddIndex
                thicknessField = cmdInput.parentCommandInput.getInputAtPosition(rowIndex, 1)
                thicknessValue = self.params.getValue("mat" + str(ddIndex))
                thicknessField.expression = thicknessValue # todo: keep table of thickness expression changes, only commit to params at end. Use lock icon?
            
            elif id.startswith("MaterialThickness"):
                rowIndex = int(id[-1])   
                self.stateTable[rowIndex][1] = cmdInput.expression

            elif id.startswith("Lock"):
                rowIndex = int(id[-1])
                self.stateTable[rowIndex][2] = False
                # ddItem = inputs.itemById("MaterialInput" + str(rowIndex))
                # ddChoice = ddItem.selectedItem.index
                self.updateLayer(rowIndex)

            elif id.startswith("Unlock"):
                rowIndex = int(id[-1])
                self.stateTable[rowIndex][2] = True
                # ddItem = inputs.itemById("MaterialInput" + str(rowIndex))
                # ddChoice = ddItem.selectedItem.index
                self.updateLayer(rowIndex)

            elif id == 'tableAdd':
                if len(self.stateTable) < 6:
                    self.addLayer(len(self.stateTable))
                if len(self.stateTable) >= 6:
                    cmdInput.isEnabled = False

            elif id == 'tableDelete':
                if self.tbLayers.selectedRow == -1:
                    ui.messageBox('Select one row to delete.')
                else:
                    selectedIndex = cmdInput.parentCommandInput.selectedRow
                    self.tbLayers.deleteRow(selectedIndex)
                    self.stateTable.pop(selectedIndex)
                    cmdInput.isEnabled = True
                    
            if not id.startswith("MaterialThickness"):
                self.updateLocks(rowIndex)

            self.resetUI()
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
        
    def updateLocks(self, rowIndex = -1):
        for index, state in enumerate(self.stateTable):
            if not state[2] and index != rowIndex:
                state[2] = True
                self.updateLayer(index)

    def onKeyUp(self, eventArgs:core.KeyboardEventArgs):
        if eventArgs.keyCode == core.KeyCodes.EnterKeyCode or eventArgs.keyCode == core.KeyCodes.ReturnKeyCode:
            self.updateLocks()

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
        count = len(self.stateTable)
        distances = self.thicknessParamNames[:count]
        return comp.createLayers([profiles], distances, count, self.flipDirection.value)

    def addLayer(self, ddChoice):
        cmdInputs:core.CommandInputs = self.tbLayers.commandInputs
        materialCount = 6
        row = self.tbLayers.rowCount 
        ddMaterial = cmdInputs.addDropDownCommandInput('MaterialInput{}'.format(row), 'ddMaterial', core.DropDownStyles.LabeledIconDropDownStyle)
        ddItems = ddMaterial.listItems
        for i in range(materialCount):
            ddItems.add('Material ' + str(i + 1), i == ddChoice, 'resources/ColorChip' + str(i))
            
        paramItem = self.paramTable[ddChoice]
        thicknessValue = paramItem[1]
        valueInput = cmdInputs.addTextBoxCommandInput('MaterialText{}'.format(row), 'Value', str(thicknessValue), 1, True)
        lockIcon = cmdInputs.addImageCommandInput('Lock{}'.format(row), '', 'resources/Lock/16x24.png')
 
        self.tbLayers.addCommandInput(ddMaterial, row, 0)
        self.tbLayers.addCommandInput(valueInput, row, 1)
        self.tbLayers.addCommandInput(lockIcon, row, 2)
        self.stateTable.append([ddChoice, thicknessValue, True])
         
    def updateLayer(self, row):
        cmdInputs:core.CommandInputs = self.tbLayers.commandInputs
        ddIndex = self.stateTable[row][0]
        thicknessValue = self.stateTable[row][1]
        isLocked = self.stateTable[row][2]

        if isLocked: # Locked
            valueInput = cmdInputs.addTextBoxCommandInput('MaterialText{}'.format(row), 'Value', str(thicknessValue), 1, True)
            lockIcon = cmdInputs.addImageCommandInput('Lock{}'.format(row), '', 'resources/Lock/16x24.png')
        else:
            valueInput = cmdInputs.addValueInput('MaterialThickness{}'.format(row), 'Value', 'mm', self.params.createValue(thicknessValue))
            lockIcon = cmdInputs.addImageCommandInput('Unlock{}'.format(row), '', 'resources/Unlock/16x24.png')
        
        self.tbLayers.removeInput(row, 1)
        self.tbLayers.removeInput(row, 2)
        self.tbLayers.addCommandInput(valueInput, row, 1)
        self.tbLayers.addCommandInput(lockIcon, row, 2)

            
