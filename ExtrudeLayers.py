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
        cmdId = 'ddwExtrudeLayersId'
        cmdName = 'Extrude Layers'
        cmdDescription = 'Extrudes a profile into multiple layer bodies of parameterized thicknesses. Can also be used to cut, intersect existing layered components.'
        targetPanels = self.getTargetPanels()
        super().__init__(cmdId, cmdName, cmdDescription, True, targetPanels)

    def getTargetPanels(self):
        return ui.allToolbarPanels.itemById('SolidCreatePanel'), ui.allToolbarPanels.itemById('SketchCreatePanel')

    # def onStartedRunning(self, eventArgs:core.CommandCreatedEventArgs):
    #     super().onStartedRunning(eventArgs)

    def onCreated(self, eventArgs:core.CommandCreatedEventArgs):
        self._createDialog(eventArgs.command.commandInputs)  
      
    def onInputsChanged(self, eventArgs:core.InputChangedEventArgs):
        try:
            inputs = eventArgs.inputs
            cmdInput = eventArgs.input
            id = cmdInput.id
            isLayerTable = cmdInput.parentCommandInput and cmdInput.parentCommandInput.id == "tbLayers"
            rowIndex = -1
            
            if id.startswith("MaterialInput"):
                rowIndex = int(id[-1])
                ddIndex = cmdInput.selectedItem.index
                state = self.stateTable[rowIndex]
                state[0] = ddIndex
                thicknessValue = self.paramTable[ddIndex][1]
                state[1] = thicknessValue
                self._updateLayer(rowIndex)

            elif id.startswith("MaterialThickness"):
                rowIndex = int(id[-1])
                if cmdInput.isValidExpression:
                    state = self.stateTable[rowIndex]
                    val = cmdInput.expression
                    if val != state[1]:
                        state[1] = cmdInput.expression
                        # When two layers use the same material, an update in thickness should effect both.
                        changes = self.updateValues(rowIndex, state[0], state[1])
                        for index in changes:
                            self._updateLayer(index)

            elif id.startswith("Lock"):
                rowIndex = int(id[-1])
                self.stateTable[rowIndex][2] = False
                # ddItem = inputs.itemById("MaterialInput" + str(rowIndex))
                # ddChoice = ddItem.selectedItem.index
                self._updateLayer(rowIndex)

            elif id.startswith("Unlock"):
                rowIndex = int(id[-1])
                self.stateTable[rowIndex][2] = True
                # ddItem = inputs.itemById("MaterialInput" + str(rowIndex))
                # ddChoice = ddItem.selectedItem.index
                self._updateLayer(rowIndex)

            elif id == 'tableAdd':
                if len(self.stateTable) < 6:
                    self._addLayer(len(self.stateTable))
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
            
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
        
    def updateLocks(self, rowIndex = -1):
        for i, state in enumerate(self.stateTable):
            if not state[2] and i != rowIndex:
                state[2] = True
            self._updateLayer(i)

    def updateValues(self, rowSource, materialIndex, value):
        changes = []
        for i, state in enumerate(self.stateTable):
            if i != rowSource and state[0] == materialIndex:
                state[1] = value
                changes.append(i)
        return changes

    def onKeyUp(self, eventArgs:core.KeyboardEventArgs):
        if eventArgs.keyCode == core.KeyCodes.EnterKeyCode or eventArgs.keyCode == core.KeyCodes.ReturnKeyCode:
            self.updateLocks()

    def onValidateInputs(self, eventArgs:core.ValidateInputsEventArgs):
            super().onValidateInputs(eventArgs)
        
    def onPreview(self, eventArgs:core.CommandEventArgs):
        profiles = []
        for index in range(self.profilesSelection.selectionCount):
            profiles.append(self.profilesSelection.selection(index).entity)

        # Probably need to switch to changing paramters for preview and changing them back on cancel.
        # Other elements are affected by param changes and probably should see that in preview.
        # For now just use numbers for preview and params for final.
        distances = [state[1] for state in self.stateTable]
        layers = self._extrude(profiles, distances)
        layers.sketch.isVisible = True

    def onExecute(self, eventArgs:core.CommandEventArgs):
        self._execute(eventArgs)
        adsk.autoTerminate(False)

    def writeDefaultLayerIndexes(self, layerParamIndexes:list):
        indexes = "(["
        comma = ""
        for index in layerParamIndexes:
            indexes += comma + str(index)
            comma = ","
        indexes += "], " + str(self.flipDirection.value) + "," + str(self.reversed.value) + ")"
        return app.activeDocument.attributes.add("ExtrudeLayers", "defaultLayerIndexes", indexes)

    def readDefaultLayerIndexes(self):
        attr = app.activeDocument.attributes.itemByName("ExtrudeLayers", "defaultLayerIndexes")
        if attr:
            result = eval(attr.value)
        else:
            result = ([0,1,0], False, False)
        return result


    # Custom Feature
    def onEditCreated(self, eventArgs:core.CommandCreatedEventArgs):
        super().onEditCreated(eventArgs)
        existingDependencies = self._editedCustomFeature.dependencies
        sketchDep = existingDependencies.itemById('sketch')
        sketchDep.entity.isVisible = True
        #self._createDialog(eventArgs.command.commandInputs, True)  

    def onEditExecute(self, eventArgs:core.CommandEventArgs):
        self._execute(eventArgs, True)
        super().onEditExecute(eventArgs)
        adsk.autoTerminate(False)
    



    def _execute(self, eventArgs:core.CommandEventArgs, isEditMode = False):
        profiles = []
        for index in range(self.profilesSelection.selectionCount):
            profiles.append(self.profilesSelection.selection(index).entity)
            
        count = len(self.stateTable)
        for i, state in enumerate(self.stateTable):
            ddIndex = self.stateTable[i][0]
            paramVal = self.params.getValue(self.thicknessParamNames[ddIndex])
            if paramVal != state[1]:
                self.params.setParam(self.thicknessParamNames[ddIndex], state[1])
        distances = []
        for state in self.stateTable:
            distances.append(self.thicknessParamNames[state[0]]) # use param names for final extrude thickness
        
        tLayers = self._extrude(profiles, distances)

        indexes = [state[0] for state in self.stateTable]
        attr = self.writeDefaultLayerIndexes(indexes)

        if self.isCustomCommand: # and not isEditMode:
            comp:f.Component = tLayers.tcomponent.component
            customFeatures:f.CustomFeatures = comp.features.customFeatures
            if isEditMode:
                # name = self._editedCustomFeature.name
                # compare = customFeatures.itemByName(name)
                oldFeatures = []
                for feature in self._editedCustomFeature.features:
                    oldFeatures.append(feature)
                self._editedCustomFeature.startFeature =  tLayers.extrudes[0]
                self._editedCustomFeature.endFeature =  tLayers.extrudes[-1]

                oldFeatures.reverse()
                for feature in oldFeatures:
                    try:
                        feature.deleteMe()
                    except:
                        pass
                # existingDependencies = self._editedCustomFeature.dependencies
                # sketchDep = existingDependencies.itemById('sketch')
                # sketchDep.entity = profiles[0].parentSketch
            else:
                custFeatInput = comp.features.customFeatures.createInput(self.customFeatureDef, tLayers.extrudes[0], tLayers.extrudes[-1])    
                custFeatInput.addDependency('sketch', profiles[0].parentSketch)
                comp.features.customFeatures.add(custFeatInput) 
            # lengthInput = adsk.core.ValueInput.createByString(_lengthInput.expression)
            # custFeatInput.addCustomParameter('length', 'Length', lengthInput, defLengthUnits, True)            
            #custFeatInput.addDependency('sketch', profiles[0].parentSketch)

        return tLayers

    def _extrude(self, profiles, distances):
        #profiles = self.profilesSelection.selection
        sketch = profiles[0].parentSketch
        comp:TurtleComponent = TurtleComponent.createFromSketch(sketch)
        count = len(self.stateTable)
        appearanceList = [state[0] for state in self.stateTable]
        if self.reversed.value:
            distances.reverse()
            appearanceList.reverse()
        return comp.createLayers([profiles], distances, count, self.flipDirection.value, appearanceList)

    def _addLayer(self, ddChoice):
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
         
    def _updateLayer(self, row):
        if row < 0:
            return
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

    def _createDialog(self, inputs, isEditMode = False):
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

            # Select profiles
            self.profilesSelection = inputs.addSelectionInput('selProfile', 'Select Profile', 'Select profile to extrude.')
            self.profilesSelection.setSelectionLimits(1,0)
            self.profilesSelection.addSelectionFilter('Profiles')

            
            # Create table input
            self.tbLayers = inputs.addTableCommandInput('tbLayers', 'Layers', 4, '6:4:1')
             # Note: more items than maxvisiblerows results in text not appearing correctly.
            self.tbLayers.maximumVisibleRows = 6

            intitalLayers, isFlipped, isReversed = self.readDefaultLayerIndexes()
            for layerIndex in intitalLayers:
                self._addLayer(layerIndex)    

            btAddItem = inputs.addBoolValueInput('tableAdd', 'Add', False, "resources/Add/", True)
            self.tbLayers.addToolbarCommandInput(btAddItem)
            btDeleteItem = inputs.addBoolValueInput('tableDelete', 'Delete', False, "resources/Remove/", True)
            self.tbLayers.addToolbarCommandInput(btDeleteItem)
            
            # Flip direction
            self.flipDirection = inputs.addBoolValueInput('bFlip', 'Flip Direction', True, "resources/Flip/", isFlipped)
            # Reverse Order
            self.reversed = inputs.addBoolValueInput('bReverse', 'ReverseOrder', True, "resources/Reverse/", isReversed)

            # * maybe not: Start (Profile Plane, Offset, Object)
            # Direction (One Side, Two Sides, Symmetric)
            # Operation (new bodies --- cut merge into existing, intersect existing)
            #                       --- Objects to cut/merge/intersect

        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
            
