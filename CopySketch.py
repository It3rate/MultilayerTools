# #Author-Robin Debreuil
# #Description-Copies sketch points, lines, constraints and dimensions, including parameters. Optionally relative to a guideline for relative pasting.

import adsk.core, adsk.fusion, traceback
from .lib.TurtleUtils import TurtleUtils
from .lib.TurtleUICommand import TurtleUICommand
from .lib.TurtleSketch import TurtleSketch
from .lib.SketchEncoder import SketchEncoder

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class CopySketchCommand(TurtleUICommand):
    def __init__(self):
        cmdId = 'ddwCopySketchId'
        cmdName = 'Copy Sketch'
        cmdDescription = 'Copies sketch curves, constraints, parameters and dimesions. Optionally choose a guideline to allow relative pasting.'
        targetPanels = self.getTargetPanels()
        super().__init__(cmdId, cmdName, cmdDescription, False, targetPanels)

    def getTargetPanels(self):
        return ui.allToolbarPanels.itemById('SolidCreatePanel'), ui.allToolbarPanels.itemById('SketchCreatePanel')

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
            self.guidelineSelection.setSelectionLimits(0, 1)
            self.guidelineSelection.addSelectionFilter('SketchLines')

            # Select sketch.
            self.sketchSelection = inputs.addSelectionInput('selSketch', 'Select Sketch', 'Select sketch to copy.')
            self.sketchSelection.setSelectionLimits(1,1)
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
            self.tbProfiles:f.addTableCommandInput = groupInput.addTableCommandInput('tbProfiles', 'Profiles', 3, '1:6:6')
            self.tbProfiles.maximumVisibleRows = 6
            self.tbProfiles.tablePresentationStyle = core.TablePresentationStyles.itemBorderTablePresentationStyle
            self.tbProfiles.columnSpacing = 1
            self.tbProfiles.rowSpacing = 1
            self.tbProfiles.hasGrid = False   

            btAddItem = groupInput.addBoolValueInput('profileAdd', '', False, "resources/Add/", True)
            self.tbProfiles.addToolbarCommandInput(btAddItem)
            btDeleteItem = groupInput.addBoolValueInput('profileDelete', '', False, "resources/Remove/", True)
            self.tbProfiles.addToolbarCommandInput(btDeleteItem)

            self._addLayer(inputs, "fullProfile")

            self.resetUI()
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))

    def onValidateInputs(self, eventArgs:core.ValidateInputsEventArgs):
            # print("isValid: " + str(eventArgs.areInputsValid))
            super().onValidateInputs(eventArgs)
        
    def onExecute(self, eventArgs:core.CommandEventArgs):
        enc = SketchEncoder(self.sketch, self.guideline)
    
    # def onMouseClick(self, eventArgs:core.MouseEventArgs):
    #     print("click")
    # def onMouseDown(self, eventArgs:core.MouseEventArgs):
    #     print("down")

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
                    
            elif cmdInput.id == 'selProfile':
                if self.tbProfiles.selectedRow > -1:
                    pass


            elif cmdInput.id.startswith('ProfileIcon'):
                print(cmdInput.id)
            elif cmdInput.id.startswith('profileName'):
                print(cmdInput.id)
            elif cmdInput.id.startswith('profileIndexes'):
                print(cmdInput.id)

            elif cmdInput.id == 'profileAdd':
                if len(self.namedProfiles) < 6:
                    self._addLayer(inputs)
                if len(self.namedProfiles) >= 6:
                    cmdInput.isEnabled = False

            elif cmdInput.id == 'profileDelete':
                if self.tbProfiles.selectedRow == -1:
                    ui.messageBox('Select one row to delete.')
                else:
                    selectedIndex = cmdInput.parentCommandInput.selectedRow
                    self.tbProfiles.deleteRow(selectedIndex)
                    cmdInput.isEnabled = True
                    
            self.resetUI()
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
        
    def _addLayer(self, inputs, name = ''):
        cmdInputs:core.CommandInputs = self.tbProfiles.commandInputs
        row = len(self.namedProfiles)
        name = "Profile_" + str(row) if name == '' else name
        
    # text = inputs.addStringValueInput('texta' + str(textBoxCount), 'Text ' + str(textBoxCount), 'Text ' + str(textBoxCount))
    # text.isReadOnly = True
    # table.addCommandInput(text, j, 0, False, False)

        profileIcon = inputs.addImageCommandInput('ProfileIcon{}'.format(row), '', 'resources/Profile/16x24.png')
        self.tbProfiles.addCommandInput(profileIcon, row, 0, False, False)

        nameInput = inputs.addStringValueInput('profileName{}'.format(row), 'Name', name)
        self.tbProfiles.addCommandInput(nameInput, row, 1, False, False)

        indexesInput = inputs.addStringValueInput('profileIndexes{}'.format(row), 'Indexes', '[ ]')
        #indexesInput = inputs.addBoolValueInput('profileIndexes{}'.format(row), 'Indexes', False)
        indexesInput.isReadOnly = True
        # indexesInput.isFullWidth = True
        #indexesInput = cmdInputs.addTextBoxCommandInput('profileIndexes{}'.format(row), 'Profile Indexes', '[  ]', 1, True)
        self.tbProfiles.addCommandInput(indexesInput, row, 2, False, False)

        self.namedProfiles.append(['profileName{}'.format(row), [], []])
 
         
    def resetUI(self):
        if self.guideline or self.isInSketch:
            self.sketchSelection.isVisible = False
            self.sketchText.isVisible = True
            self.guidelineSelection.hasFocus = True 
        else:
            self.sketchSelection.isVisible = True
            self.sketchText.isVisible = False
