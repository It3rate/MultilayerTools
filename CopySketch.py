# #Author-Robin Debreuil
# #Description-Copies sketch points, lines, constraints and dimensions, including parameters. Optionally relative to a guideline for relative pasting.

import adsk.core, adsk.fusion, traceback
from .lib.TurtleUtils import TurtleUtils
from .lib.TurtleUICommand import TurtleUICommand
from .lib.TurtleSketch import TurtleSketch
from .lib.TurtleEncoder import TurtleEncoder
from .lib.data.SketchData import SketchData

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class CopySketchCommand(TurtleUICommand):
    def __init__(self):
        cmdId = 'ddwCopySketchId'
        cmdName = 'Copy Sketch'
        cmdDescription = 'Copies sketch curves, constraints, parameters and dimesions. Optionally choose a guideline to allow relative pasting.'
        self.idIndex = 0
        super().__init__(cmdId, cmdName, cmdDescription)

    def getTargetPanels(self):
        return [ui.allToolbarPanels.itemById('SolidCreatePanel'), ui.allToolbarPanels.itemById('SketchCreatePanel')]

    def onCreated(self, eventArgs:core.CommandCreatedEventArgs):
        try:
            self.namedProfiles = []
            self.isInSketch = app.activeEditObject.classType == f.Sketch.classType
            self.guideline:f.SketchLine = TurtleUtils.getSelectedTypeOrNone(f.SketchLine)
            if self.guideline:
                self.sketch = self.guideline.parentSketch
            else:
                self.sketch:f.Sketch = TurtleUtils.getTargetSketch(f.Sketch, False)

            # Get the CommandInputs collection associated with the command.
            inputs = eventArgs.command.commandInputs

            # Select optional guideline.
            self.guidelineSelection = inputs.addSelectionInput('selGuideline', 'Select Guideline', 'Optional reference guideline used if transforming sketch.')
            self.guidelineSelection.setSelectionLimits(0, 0)
            self.guidelineSelection.addSelectionFilter('SketchLines')

            # Select sketch.
            self.sketchSelection = inputs.addSelectionInput('selSketch', 'Select Sketch', 'Select sketch to copy.')
            self.sketchSelection.setSelectionLimits(0,0)
            self.sketchSelection.addSelectionFilter('Sketches')

            self.sketchText = inputs.addTextBoxCommandInput('txSketch', 'Select Sketch', '<b>Auto selected.</b>', 1, True)

            if self.sketch and not self.guideline:
                tSketch = TurtleSketch(self.sketch)
                lines = tSketch.getSingleLines()
                if(len(lines) == 1):
                    self.guideline = lines[0]
                    

            self.profileGroup = inputs.addGroupCommandInput('profileGroup', 'Named Profiles')
            groupInput = self.profileGroup.children
            self.profileInput:core.SelectionCommandInput = groupInput.addSelectionInput('selProfile', 'Named Profiles', 'Select named profile.')
            self.profileInput.setSelectionLimits(0,0)
            self.profileInput.addSelectionFilter('Profiles')

            # Create table input
            self.profileIndex = 0
            self.currentEditIndex = -1
            self.tbProfiles:f.addTableCommandInput = groupInput.addTableCommandInput('tbProfiles', 'Profiles', 4, '1:6:6:1')
            self.tbProfiles.maximumVisibleRows = 6
            self.tbProfiles.tablePresentationStyle = core.TablePresentationStyles.itemBorderTablePresentationStyle
            self.tbProfiles.columnSpacing = 1
            self.tbProfiles.rowSpacing = 1
            self.tbProfiles.numberOfColumns = 4
            self.tbProfiles.hasGrid = False   

            btAddItem = groupInput.addBoolValueInput('profileAdd', '', False, "resources/Add/", True)
            self.tbProfiles.addToolbarCommandInput(btAddItem)
            btDeleteItem = groupInput.addBoolValueInput('profileDelete', '', False, "resources/Remove/", True)
            self.tbProfiles.addToolbarCommandInput(btDeleteItem)

            for i in range(20):
                self._createLayer(inputs, "Profile " + str(i))

            saveGroup = inputs.addGroupCommandInput("saveGroup", "Save To Disk")
            self.btSaveText = saveGroup.children.addButtonRowCommandInput("btSaveText", "Save Sketch", False)
            self.btSaveText.listItems.add('Save Sketch', False, 'resources/ddwPasteSketchId')

            self._resetUI()
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))

    def onInputsChanged(self, eventArgs:core.InputChangedEventArgs):
        try:
            inputs = eventArgs.inputs
            cmdInput = eventArgs.input
            if cmdInput.id == 'selGuideline':
                if cmdInput.selectionCount > 0:
                    self.guideline = cmdInput.selection(0).entity
                    self.sketch = self.guideline.parentSketch
                    if self.sketchSelection.selection != self.sketch:
                        self.sketchSelection.clearSelection()
                        self.sketchSelection.addSelection(self.sketch)
                else:
                    self.guideline = None
                self._resetUI()

            elif cmdInput.id == 'selProfile':
                row = self.tbProfiles.selectedRow
                if row > -1:
                    selCount = cmdInput.selectionCount
                    profile = cmdInput.selection(selCount - 1).entity
                    self.sketch = profile.parentSketch
                    if self.sketchSelection.selection != self.sketch:
                        self.sketchSelection.clearSelection()
                        self.sketchSelection.addSelection(self.sketch)
                    profileIndex = -1
                    for i, p in enumerate(self.sketch.profiles):
                        if p == profile:
                            profileIndex = i
                            break
                    if profileIndex != -1:
                        self.namedProfiles[row].append([profileIndex, profile])
                        self.tbProfiles.getInputAtPosition(row, 2).value += " " + str(profileIndex)
                    self._changeProfileInput(row)
                            
            elif cmdInput.id == 'btSaveText':
                if len(self.btSaveText.listItems) == 0: # elaborate hack to re-enable save button
                    self.btSaveText.listItems.add('Save Sketch', False, 'resources/ddwPasteSketchId')
                else:
                    filename = self._saveSketch()
                    if filename != "":
                        np = self._getNamedProfiles()
                        enc = TurtleEncoder(self.sketch, self.guideline, np)
                        SketchData.saveData(filename, enc.encodedSketch)
                    self.btSaveText.listItems.clear()
                
            elif cmdInput.parentCommandInput == self.tbProfiles:
                success, row, col, addcol, addrow = self.tbProfiles.getPosition(cmdInput)

                if cmdInput.id.startswith('ProfileIcon'):
                    pass

                if cmdInput.id.startswith('ClearIcon'):
                    self.namedProfiles[row] = []
                    
                if cmdInput.id.startswith('editText'):
                    pass
                    
                elif cmdInput.id.startswith('profileName'):
                    if self.currentEditIndex != -1:
                        formerEdit = self.tbProfiles.getInputAtPosition(self.currentEditIndex, col)
                        formerEdit.isReadOnly = True
                    self._createTextInput("editText", cmdInput.value, False, row, col)
                    self.currentEditIndex = row
                    
                elif cmdInput.id.startswith('profileIndexes'):
                    pass

                elif cmdInput.id == 'profileAdd':
                    if self.profileIndex < 20:
                        self._setTableRowVisibility(self.profileIndex, True)
                        row = self.profileIndex
                        self.tbProfiles.selectedRow = row
                        self.profileIndex += 1
                    else:
                        cmdInput.isEnabled = False

                elif cmdInput.id == 'profileDelete':
                    if self.tbProfiles.selectedRow == -1:
                        ui.messageBox('Select one row to delete.')
                    else:
                        selectedIndex = cmdInput.parentCommandInput.selectedRow
                        self.tbProfiles.deleteRow(selectedIndex)
                        cmdInput.isEnabled = True
                        row = -1

                self._changeProfileInput(row)
                    
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))

    def onExecute(self, eventArgs:core.CommandEventArgs):
        np = self._getNamedProfiles()
        enc = TurtleEncoder(self.sketch, self.guideline, np)
    
    def onValidateInputs(self, eventArgs:core.ValidateInputsEventArgs):
        eventArgs.areInputsValid = self.sketch
    # def onMouseClick(self, eventArgs:core.MouseEventArgs):
    #     print("click")
    # def onMouseDown(self, eventArgs:core.MouseEventArgs):
    #     print("down")


    def _getNamedProfiles(self):
        result = {}
        for i in range(self.tbProfiles.rowCount):
            profiles = self.namedProfiles[i]
            tableItem = self.tbProfiles.getInputAtPosition(i, 1)
            if tableItem.isVisible and len(profiles) > 0:
                name = tableItem.value
                indexes = []
                for p in profiles:
                    indexes.append(p[0])
                result[name] = indexes
        return result

    def _changeProfileInput(self, toIndex):
        if toIndex >= 0: #and toIndex != self.currentEditIndex:
            self.profileInput.clearSelection()
            selected = self.namedProfiles[toIndex]
            text = "["
            comma = ""
            for item in selected:
                self.profileInput.addSelection(item[1])
                text += comma + str(item[0])
                comma = ", "
            text = "" if len(selected) == 0 else text + "]"
            self.tbProfiles.getInputAtPosition(toIndex, 2).value = text

            self.profileInput.hasFocus = True

    def _createLayer(self, inputs, name = ''):
        cmdInputs:core.CommandInputs = self.tbProfiles.commandInputs
        row = len(self.namedProfiles)

        profileIcon = cmdInputs.addImageCommandInput('ProfileIcon{}'.format(row), '', 'resources/Profile/16x24.png')
        self.tbProfiles.addCommandInput(profileIcon, row, 0, False, False)

        name = "Profile " + str(row) if name == '' else name
        self._createTextInput('profileName', name, True, row, 1)

        indexesInput = inputs.addStringValueInput('profileIndexes{}'.format(row), 'Indexes', '')
        indexesInput.isReadOnly = True
        self.tbProfiles.addCommandInput(indexesInput, row, 2, False, False)

        profileIcon = cmdInputs.addImageCommandInput('ClearIcon{}'.format(row), '', 'resources/Remove/16x24.png')
        self.tbProfiles.addCommandInput(profileIcon, row, 3, False, False)

        self._setTableRowVisibility(row, False)

        self.namedProfiles.append([])
    
    def _createTextInput(self, idRoot:str, value:str, isReadOnly:bool, row:int, col:int):
        idName = idRoot + " " + str(self.idIndex)
        self.idIndex += 1
        nameInput = self.tbProfiles.commandInputs.addStringValueInput(idName, '', value)
        nameInput.isReadOnly = isReadOnly
        if self.tbProfiles.getInputAtPosition(row, col):
            self.tbProfiles.removeInput(row, col)
        self.tbProfiles.addCommandInput(nameInput, row, col, False, False)
        return self.tbProfiles.getInputAtPosition(row, col)
 
    def _setTableRowVisibility(self, row:int, isVisible:bool):
        cols = 8
        for col in range(cols):
            item = self.tbProfiles.getInputAtPosition(row, col)
            if item:
                item.isVisible = isVisible
            else:
                break
         
    def _resetUI(self):
        if self.guideline or self.isInSketch:
            self.sketchSelection.isVisible = False
            self.sketchText.isVisible = True
            self.guidelineSelection.hasFocus = True 
        else:
            self.sketchSelection.isVisible = True
            self.sketchText.isVisible = False

    def _saveSketch(self):
        result = ""
        fileDialog = ui.createFileDialog()
        fileDialog.isMultiSelectEnabled = False
        fileDialog.title = "Save Sketch"
        fileDialog.filter = 'Turtle Sketch Files (*.tsk)'
        fileDialog.filterIndex = 0
        dialogResult = fileDialog.showSave()
        if dialogResult == core.DialogResults.DialogOK:
            result = fileDialog.filename
        return result
