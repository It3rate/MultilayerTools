# #Author-Robin Debreuil
# #Extrudes a profile into multiple layer bodies of parameterized thicknesses. Can also be used to cut, intersect existing layered components.

import adsk.core, adsk.fusion, traceback
from .lib.TurtleUtils import TurtleUtils
from .lib.TurtleUICommand import TurtleUICommand
from .lib.TurtleSketch import TurtleSketch
from .lib.TurtleParams import TurtleParams
from .lib.TurtleComponent import TurtleComponent
from .lib.TurtleLayers import TurtleLayers
from .lib.TurtleCustomCommand import TurtleCustomCommand

f,core,app,ui = TurtleUtils.initGlobals()

class ExtrudeLayersCommand(TurtleCustomCommand):
    def __init__(self):
        self.params = TurtleParams.instance()
        cmdId = 'ddwExtrudeLayersId'
        cmdName = 'Extrude Layers'
        cmdDescription = 'Extrudes a profile into multiple layer bodies of parameterized thicknesses. Can also be used to cut, intersect existing layered components.'
        self.sketch = None
        self.sketchWasVisible = True
        self.isPreview = False
        self.design = TurtleUtils.activeDesign()
        super().__init__(cmdId, cmdName, cmdDescription)

    def getTargetPanels(self):
        return [ui.allToolbarPanels.itemById('SolidCreatePanel'), ui.allToolbarPanels.itemById('SketchCreatePanel')]

    def onCreated(self, eventArgs:core.CommandCreatedEventArgs):
        self._createDialog(eventArgs.command.commandInputs)  
      
    def onInputsChanged(self, eventArgs:core.InputChangedEventArgs):
        try:
            inputs = eventArgs.inputs
            cmdInput = eventArgs.input
            cmdId = cmdInput.id
            isLayerTable = cmdInput.parentCommandInput and cmdInput.parentCommandInput.id == "tbLayers"
            rowIndex = -1
            
            if cmdInput == "selProfile":
                pass
            elif cmdId.startswith("MaterialInput"):
                rowIndex = int(cmdId[-1])
                ddIndex = cmdInput.selectedItem.index
                state = self.stateTable[rowIndex]
                state[0] = ddIndex
                thicknessValue = self.paramTable[ddIndex][1]
                state[1] = thicknessValue
                self._updateLayer(rowIndex)

            elif cmdId.startswith("MaterialThickness"):
                rowIndex = int(cmdId[-1])
                if cmdInput.isValidExpression:
                    state = self.stateTable[rowIndex]
                    _ = cmdInput.value # Note: expression is not updated until value is read
                    val = cmdInput.expression
                    if val != state[1]:
                        state[1] = val
                        # When two layers use the same material, an update in thickness should effect both.
                        changes = self.updateValues(rowIndex, state[0], state[1])
                        for index in changes:
                            self._updateLayer(index)
                #eventArgs.inputs.command.doExecutePreview()

            elif cmdId.startswith("Lock"):
                rowIndex = int(cmdId[-1])
                self.stateTable[rowIndex][2] = False
                # ddItem = inputs.itemById("MaterialInput" + str(rowIndex))
                # ddChoice = ddItem.selectedItem.index
                self._updateLayer(rowIndex)

            elif cmdId.startswith("Unlock"):
                rowIndex = int(cmdId[-1])
                self.stateTable[rowIndex][2] = True
                # ddItem = inputs.itemById("MaterialInput" + str(rowIndex))
                # ddChoice = ddItem.selectedItem.index
                self._updateLayer(rowIndex)

            elif cmdId == 'tableAdd':
                if len(self.stateTable) < 6:
                    self._addLayer(len(self.stateTable))
                if len(self.stateTable) >= 6:
                    cmdInput.isEnabled = False

            elif cmdId == 'tableDelete':
                if self.tbLayers.selectedRow == -1:
                    ui.messageBox('Select one row to delete.')
                else:
                    selectedIndex = cmdInput.parentCommandInput.selectedRow
                    self.tbLayers.deleteRow(selectedIndex)
                    self.stateTable.pop(selectedIndex)
                    cmdInput.isEnabled = True

            elif cmdId == 'ddOperation':
                self.opType = cmdInput.selectedItem.index
                self._resetUI()
                print(str(self.opType) + " : " + cmdInput.selectedItem.name)

            if not cmdId.startswith("MaterialThickness"):
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

    # def onCameraChanged(self, eventArgs:core.CameraEventArgs):
    #     print("camera")
    # def onMouseDown(self, eventArgs:core.MouseEventArgs):
    #     print("down")
    # def onMouseUp(self, eventArgs:core.MouseEventArgs):
    #     print("up")
    # def onComputeCustomFeature(self, eventArgs:f.CustomFeatureEventArgs):
    #     print("compute")
    # def onValidateInputs(self, eventArgs:core.ValidateInputsEventArgs):
    #     pass
    # def onActivate(self, eventArgs:core.CommandCreatedEventArgs):
    #     pass
    
    def onKeyUp(self, eventArgs:core.KeyboardEventArgs):
        if eventArgs.keyCode == core.KeyCodes.EnterKeyCode or eventArgs.keyCode == core.KeyCodes.ReturnKeyCode:
            self.updateLocks()

    def onPreview(self, eventArgs:core.CommandEventArgs):
        self.isPreview = True
        self._execute(eventArgs)
        eventArgs.isValidResult = False
        self.isPreview = False

    def onExecute(self, eventArgs:core.CommandEventArgs):
        self._execute(eventArgs)
        self._writeDefaultLayerIndexes()
        if len(self.selectedProfiles) > 0:
            # When using an encoded or referenced sketch it may have been non visible (not currently doing that).
            self.selectedProfiles[0].parentSketch.isVisible = self.sketchWasVisible

    
    # Custom Feature Edit events
    def onEditCreated(self, eventArgs:core.CommandCreatedEventArgs):
        self._createDialog(eventArgs.command.commandInputs)  
    
    def onEditActivate(self, eventArgs:core.CommandEventArgs):
        self.profilesSelection.clearSelection()
        existingDependencies = self._editedCustomFeature.dependencies
        sketchDep = existingDependencies.itemById('sketch')
        if sketchDep:
            self.sketch = sketchDep.entity
            self.sketchWasVisible = self.sketch.isVisible
            self.sketch.isVisible = True

        usedProfiles = []
        # Get profiles from features that already exist. 
        # This doesn't work without exceptions I don't understand, but haven't found a better way yet.
        for feature in self._editedCustomFeature.features:
            if type(feature) == f.ExtrudeFeature:
                try:
                    profiles = feature.profile # this can throw an error (if profile is used in other layers?)
                    # single profiles are not in a collection, so create a collection to allow uniform access
                    profiles = profiles if type(profiles) == core.ObjectCollection else [profiles]
                    for profile in profiles:
                        # avoid adding the same profile more than once as each layer may reuse the same profile.
                        if not profile in usedProfiles:
                            usedProfiles.append(profile)
                            self.profilesSelection.addSelection(profile)
                except:
                     #print('Adding extrude error:\n{}'.format(traceback.format_exc()))
                     pass

    def onEditDeactivate(self, eventArgs:core.CommandEventArgs):
        print("deactivate")

    def onEditExecute(self, eventArgs:core.CommandEventArgs):
        self._execute(eventArgs)
        self._writeDefaultLayerIndexes()
    
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
            self.selectedProfiles = []

            # Select profiles
            self.profilesSelection = inputs.addSelectionInput('selProfile', 'Select Profile', 'Select profile to extrude.')
            self.profilesSelection.setSelectionLimits(1,0)
            self.profilesSelection.addSelectionFilter('Profiles')
            
            # Create table input
            self.tbLayers = inputs.addTableCommandInput('tbLayers', 'Layers', 4, '6:4:1')
             # Note: more items than maxvisiblerows results in text not appearing correctly.
            self.tbLayers.maximumVisibleRows = 6

            intitalLayers, isFlipped, isReversed, opType  = self._readDefaultLayerIndexes()
            for layerIndex in intitalLayers:
                self._addLayer(layerIndex)
            
            tbInputs = self.tbLayers.commandInputs
            self.btAddItem = tbInputs.addBoolValueInput('tableAdd', 'Add', False, "resources/Add/", True)
            self.tbLayers.addToolbarCommandInput(self.btAddItem)
            self.btDeleteItem = tbInputs.addBoolValueInput('tableDelete', 'Delete', False, "resources/Remove/", True)
            self.tbLayers.addToolbarCommandInput(self.btDeleteItem)
            
            # Flip direction
            self.bFlipDirection = inputs.addBoolValueInput('bFlip', 'Flip Direction', True, "resources/Flip/", isFlipped)
            # Reverse Order
            self.bReversed = inputs.addBoolValueInput('bReverse', 'ReverseOrder', True, "resources/Reverse/", isReversed)

            # * maybe not: Start (Profile Plane, Offset, Object)
            # Direction (One Side, Two Sides, Symmetric)

            img = inputs.addImageCommandInput("sep0", "-", 'resources/Separator/sep.png')
            img.isFullWidth = True
            # grOperation = inputs.addGroupCommandInput("grOperation", "")
            # grOperation.isEnabledCheckBoxChecked = False
            # grOperation.isEnabledCheckBoxDisplayed = False
            # grOperation.isFullWidth = True
            # grOperation.isEnabled = False

            ddOperation = inputs.addDropDownCommandInput("ddOperation", "Operation",  core.DropDownStyles.LabeledIconDropDownStyle)
            ddOperation.listItems.add("Join", False, 'resources/BooleanAdd')
            ddOperation.listItems.add("Cut", False, 'resources/BooleanSubtract')
            ddOperation.listItems.add("Intersect", False, 'resources/BooleanIntersect')
            ddOperation.listItems.add("New Body", False, 'resources/BooleanNewBody')
            ddOperation.listItems.add("New Component", False, 'resources/BooleanNewComponent')
            self.opType = opType
            ddOperation.listItems[self.opType].isSelected = True
            #                       --- Objects to cut/merge/intersect

            self.grObjectToCut = inputs.addGroupCommandInput("grObjectsToCut", "Objects to Cut")
            self.grObjectToCut.isVisible = False

        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
            
    def _execute(self, eventArgs:core.CommandEventArgs):
        self.selectedProfiles = []
        for index in range(self.profilesSelection.selectionCount):
            self.selectedProfiles.append(self.profilesSelection.selection(index).entity)
        
        sketch, tComp = self._getTComponent()

        if self.opType < 3: # modify existing
            # only operates on the active component, should be any selected component here though.
            tLayers:TurtleLayers = TurtleLayers.createFromExisting(tComp)
            # JoinFeatureOperation = 0 CutFeatureOperation = 1 IntersectFeatureOperation = 2
            newFeatures = tLayers.modifyWithProfiles([self.selectedProfiles], self.opType)
        
        elif self.opType == 3 or self.opType == 4: # NewBodyFeatureOperation = 3 NewComponentFeatureOperation = 4
            tLayers, newFeatures = self._extrude(tComp)

        sketch.isVisible = True

        if self.isCustomCommand:
            if self.isEditMode:
                # this is clearly not the correct way or even a good way to do this, waiting for better way.
                oldFeatures = []
                for feature in self._editedCustomFeature.features:
                    oldFeatures.append(feature)

                self._editedCustomFeature.features.clear()
                self._editedCustomFeature.startFeature =  tLayers.firstLayerExtrude()
                self._editedCustomFeature.endFeature =  tLayers.lastLayerExtrude()

                oldFeatures.reverse()
                for feature in oldFeatures:
                    try:
                        feature.deleteMe()
                    except:
                        #print('error deleting feature:\n{}'.format(traceback.format_exc()))
                        pass
                existingDependencies = self._editedCustomFeature.dependencies
                sketchDep = existingDependencies.itemById('sketch')
                sketchDep.entity = self.selectedProfiles[0].parentSketch
                # profilesDep = existingDependencies.itemById('profile')
                # profilesDep.entity = TurtleUtils.ensureObjectCollection(self.selectedProfiles)
            else:
                comp:f.Component = tLayers.tcomponent.component
                customFeatures = comp.features.customFeatures
                firstFeature = newFeatures[0] # tLayers.firstLayerExtrude()
                lastFeature = newFeatures[-1] # tLayers.lastLayerExtrude()
                customFeatInput:f.CustomFeatureInput = customFeatures.createInput(self.customFeatureDef, firstFeature, lastFeature)    

                customFeatInput.addDependency('sketch', self.selectedProfiles[0].parentSketch)
                # Seems we can't remove dependencies or use collections? Can't edit profile count in that case.
                # for i, profile in enumerate(self.selectedProfiles):
                #     customFeatInput.addDependency('profile_' + str(i), profile)

                val = adsk.core.ValueInput.createByString("0")                
                customFeatInput.addCustomParameter('dialogEncoding', 'dialogEncoding', val, "", False)
                
                customFeature = comp.features.customFeatures.add(customFeatInput) 
                param = customFeature.parameters.itemById('dialogEncoding') # add encoding as comment to allow string use in params
                param.comment = self._encodeDialogState()

    def _getTComponent(self):
        tComp = None
        sketch = None
        if len(self.selectedProfiles) > 0:
            sketch = self.selectedProfiles[0].parentSketch
            if self.opType < 3: # modify
                comp = self.selectedProfiles[0].parentSketch.parentComponent
                tComp = TurtleComponent.createFromExisting(comp)
            if self.opType == 3: # new bodies
                tComp = TurtleComponent.createFromSketch(sketch)
            elif self.opType == 4: # new Component
                comp = self.design.activeComponent
                nextIndex = comp.occurrences.count + 1
                tComp = TurtleComponent.createFromParent(comp, "LayeredComp" + str(nextIndex)) 
        return sketch, tComp

    def _extrude(self, tComp:TurtleComponent):            
        count = len(self.stateTable)
        for i, state in enumerate(self.stateTable):
            ddIndex = self.stateTable[i][0]
            paramVal = self.params.getValue(self.thicknessParamNames[ddIndex])
            if paramVal != state[1]:
                self.params.setParam(self.thicknessParamNames[ddIndex], state[1])
        distances = []
        for state in self.stateTable:
            distances.append(self.thicknessParamNames[state[0]]) # use param names for final extrude thickness
        
        count = len(self.stateTable)
        appearanceList = [state[0] for state in self.stateTable]
        if self.bReversed.value:
            distances.reverse()
            appearanceList.reverse()
        result, newFeatures = TurtleLayers.createFromProfiles(tComp, [self.selectedProfiles], distances, count, self.bFlipDirection.value, appearanceList)
        return result, newFeatures
        

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
        if row < 0 or not self.tbLayers.isVisible:
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

    def _resetUI(self):
        if self.opType == 3 or self.opType == 4: # new body or component
            self.tbLayers.isVisible = True
            self.bReversed.isVisible = True
            self.bFlipDirection.isVisible = True
            self.grObjectToCut.isVisible = False
        else:
            self.tbLayers.isVisible = False
            self.bReversed.isVisible = False
            self.bFlipDirection.isVisible = False
            self.grObjectToCut.isVisible = True

    def _encodeDialogState(self):
        layerParamIndexes = [state[0] for state in self.stateTable] 
        result = "(["
        comma = ""
        for index in layerParamIndexes:
            result += comma + str(index)
            comma = ","
        result += "], " + str(self.bFlipDirection.value) + "," + str(self.bReversed.value) + ","
        
        result += str(self.opType) + ""
        # result += "["
        # comma = ""
        # for profile in self.selectedProfiles:
        #     sketch = profile.parentSketch
        #     for index in range(sketch.profiles.count):
        #         if sketch.profiles[index] == profile: # no skecth
        #             result += comma + str(index)
        #             comma = ","
        #             break
        #     sketch.isVisible = True
        # result += "]"

        result += ")"
        return result

    def _decodeDialogState(self, encoding):
        return eval(encoding)

    def _writeDefaultLayerIndexes(self):
        encoding = self._encodeDialogState()
        return app.activeDocument.attributes.add("ExtrudeLayers", "defaultLayerIndexes", encoding)

    def _readDefaultLayerIndexes(self):
        if self.isEditMode:
            enc = self._editedCustomFeature.parameters.itemById('dialogEncoding').comment
            #enc = self._editedCustomFeature.attributes.itemByName("DialogState","dialogEncoding").value
        else:
            attr = app.activeDocument.attributes.itemByName("ExtrudeLayers", "defaultLayerIndexes")
            enc = attr.value if attr else None

        if enc:
            result = self._decodeDialogState(enc)
        else:
            result = ([0,1,0], False, False, 3)
        return result
