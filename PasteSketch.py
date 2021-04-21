#Author-Robin Debreuil
#Description-'Pastes sketch curves, constraints, parameters and dimesions. Optionally choose a guideline to allow transformed pasting if a guideline was selected while copying.'

import adsk.core, adsk.fusion, traceback
from .lib.TurtleUtils import TurtleUtils
from .lib.TurtleUICommand import TurtleUICommand
from .lib.TurtleSketch import TurtleSketch
from .lib.TurtleDecoder import TurtleDecoder
from .lib.data.SketchData import SketchData

f,core,app,ui = TurtleUtils.initGlobals()

class PasteSketchCommand(TurtleUICommand):
    def __init__(self):
        cmdId = 'ddwPasteSketchId'
        cmdName = 'Paste Sketch'
        cmdDescription = 'Pastes sketch curves, constraints, parameters and dimesions. Optionally choose a guideline to allow transformed pasting if a guideline was selected while copying.'
        super().__init__(cmdId, cmdName, cmdDescription)

    def getTargetPanels(self):
        return [ui.allToolbarPanels.itemById('SolidCreatePanel'), ui.allToolbarPanels.itemById('SketchCreatePanel')]

    def onCreated(self, eventArgs:core.CommandCreatedEventArgs):
        try:
            self.isInSketch = app.activeEditObject.classType == f.Sketch.classType
            self.guideline:f.SketchLine = TurtleUtils.getSelectedTypeOrNone(f.SketchLine)
            if self.guideline:
                self.sketch = self.guideline.parentSketch
            else:
                self.sketch = TurtleUtils.getTargetSketch(f.Sketch, False)
            self.data = None
            self.decoder = None
            self.selectedProfileIndex = 0
            self.tabIndex = 0
                
            # Get the CommandInputs collection associated with the command.
            topLevelInputs = eventArgs.command.commandInputs

            tabPaste = topLevelInputs.addTabCommandInput('tabSelection', 'Paste')
            inputs = tabPaste.children

            # Select optional guideline.
            self.guidelineSelection = inputs.addSelectionInput('selGuideline', 'Select Guideline', 'Optional reference guideline used if transforming sketch.')
            self.guidelineSelection.setSelectionLimits(0,0)
            self.guidelineSelection.addSelectionFilter('SketchLines')

            # Select sketch.
            self.sketchSelection = inputs.addSelectionInput('selSketch', 'Select Sketch', 'Select sketch to copy.')
            self.sketchSelection.setSelectionLimits(0,0)
            self.sketchSelection.addSelectionFilter('Sketches')

            self.sketchText = inputs.addTextBoxCommandInput('txSketch', 'Select Sketch', '<b>Auto selected.</b>', 1, True)

            # Flip checkboxes
            self.flipHSelection = inputs.addBoolValueInput('bFlipH', 'Flip Sketch', True)
            self.flipVSelection = inputs.addBoolValueInput('bFlipV', 'Mirror Sketch', True)

            if self.sketch and not self.guideline:
                tSketch = TurtleSketch.createWithSketch(self.sketch)
                lines = tSketch.getSingleLines()
                if(len(lines) == 1):
                    self.guideline = lines[0]
            
            loadGroup = inputs.addGroupCommandInput("loadGroup", "Load From Disk")
            self.btLoadText = loadGroup.children.addButtonRowCommandInput("btLoadText", "Load Sketch", False)
            self.btLoadText.listItems.add('Load Sketch', False, 'resources/ddwCopySketchId')

            # use a separate tab for profiles, this almost solves the multiple kinds of selections issues
            tabProfiles = topLevelInputs.addTabCommandInput('tabProfiles', 'Inspect Profiles')
            inputs = tabProfiles.children
            self.radioProfiles = inputs.addRadioButtonGroupCommandInput('radioProfiles', 'Named Profiles')
            self.radioProfiles.isFullWidth = True

            if self.sketch:
                self.sketchSelection.addSelection(self.sketch)

            self._resetUI()
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
        
    def onInputsChanged(self, eventArgs:core.InputChangedEventArgs):
        try:
            inputs = eventArgs.inputs
            cmdInput = eventArgs.input
            if cmdInput.id == 'selGuideline':
                if cmdInput.selectionCount > 0:
                    guide = cmdInput.selection(0).entity
                    if not guide.attributes.itemByName("Turtle", "generated"): # can use own drawn line as guideline
                        self.guideline = cmdInput.selection(0).entity
                        self.sketch = self.guideline.parentSketch
                    else:
                        self.guideline = None
                else:
                    self.guideline = None

            elif cmdInput.id == 'selSketch':
                if self.sketchSelection.selectionCount > 0:
                    self.sketch = cmdInput.selection(0).entity
                    if(self.guideline and self.guideline.parentSketch != self.sketch):
                        self.guideline = None
                else:
                    self.sketch = None
                    self.guideline = None

            elif cmdInput.id == 'radioProfiles':
                self.selectedProfileIndex = cmdInput.selectedItem.index

            elif cmdInput.id == 'APITabBar':
                self.tabIndex = 1 if self.tabIndex == 0 else 0 # not sure to tell which tab was clicked?
                if self.tabIndex == 0:
                    self._resetSelections()
                else:
                    self._updateProfiles()
                    
            elif cmdInput.id == 'btLoadText':
                if len(self.btLoadText.listItems) == 0: # elaborate hack to re-enable load button
                    self.btLoadText.listItems.add('Load Sketch', False, 'resources/ddwCopySketchId')
                else:
                    filename = self._loadSketch()
                    if filename != "":
                        textData = SketchData.loadData(filename)
                        self.data = eval(textData)
                    self.btLoadText.listItems.clear()
            
            self._resetUI()
                
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
      
    def onValidateInputs(self, eventArgs:core.ValidateInputsEventArgs):
        # Can't turn off OK button here or preview won't run
        eventArgs.areInputsValid = True if self.sketch else False # and self.tabIndex == 0 else False

    def onPreSelect(self, eventArgs:core.SelectionEventArgs):
        sel = eventArgs.selection.entity
        # never allow selecting guidelines that are self drawn
        if type(sel) == f.SketchLine and sel.attributes.itemByName("Turtle", "generated"):
            eventArgs.isSelectable = False
            eventArgs.additionalEntities.add(sel)

    def onPreview(self, eventArgs:core.CommandEventArgs):
        self.onExecute(eventArgs)
        if self.tabIndex == 1 and self.decoder and len(self.decoder.namedProfiles) > 0:
            indexList = list(self.decoder.namedProfiles.values())
            for profileIndex in indexList[self.selectedProfileIndex]:
                ui.activeSelections.add(self.sketch.profiles[profileIndex])
        eventArgs.isValidResult = True

    def onExecute(self, eventArgs:core.CommandEventArgs):
        self.sketch.areProfilesShown = False
        self.sketch.computeDeferred = True

        self._ensureSketchData()
        flipX = self.flipHSelection.value
        flipY = self.flipVSelection.value
        if self.guideline:
            self.decoder = TurtleDecoder.createWithGuideline(self.data, self.guideline, flipX, flipY)
        elif self.sketch:
            self.decoder = TurtleDecoder.createWithSketch(self.data, self.sketch, flipX, flipY)
            
        self.sketch.areProfilesShown = True
        self.sketch.computeDeferred = False

    def _resetSelections(self):
        ui.activeSelections.clear()
        self.guidelineSelection.clearSelection()
        self.sketchSelection.clearSelection()
        if self.guideline and not self.guideline.isValid:
            self.guideline = None

        if self.guideline:
            self.guidelineSelection.addSelection(self.guideline)
        elif self.sketch:
            self.sketchSelection.addSelection(self.sketch)

    def _updateProfiles(self):
        radioItems = self.radioProfiles.listItems
        if len(radioItems) == 0:
            radioItems.clear()
            if self.decoder and len(self.decoder.namedProfiles) > 0: 
                for i, name in enumerate(self.decoder.namedProfiles):
                    item = radioItems.add(name, i == self.selectedProfileIndex, 'resources/Profile/16x24.png')

    def _ensureSketchData(self):
        if not self.data:
            clip = TurtleUtils.getClipboardText()
            if clip == None or not (clip.startswith("#Turtle Generated Data")):
                self.data = SketchData.getTestData()
            else:
                self.data = eval(clip)
    
    def _resetUI(self):
        if self.guideline or self.isInSketch:
            self.sketchSelection.isVisible = False
            self.sketchText.isVisible = True
            self.guidelineSelection.hasFocus = True 
        else:
            self.sketchSelection.isVisible = True
            self.sketchText.isVisible = False
        
        if self.guideline:
            self.flipHSelection.isEnabled = True
            self.flipVSelection.isEnabled = True
        else:
            self.flipHSelection.isEnabled = False
            self.flipVSelection.isEnabled = False

        # not sure of a better way to do this...
        # on the second tab, the first tab's selection is still updated and deselected etc, so things will not redraw without this
        if self.guideline:
            self.guidelineSelection.clearSelection() 
            self.guidelineSelection.addSelection(self.guideline)
        else:
            self.guidelineSelection.clearSelection() 
            if self.sketch:
                self.sketchSelection.clearSelection()
                self.sketchSelection.addSelection(self.sketch)
            else:
                self.sketchSelection.clearSelection()

    def _loadSketch(self):
        result = ""
        fileDialog = ui.createFileDialog()
        fileDialog.isMultiSelectEnabled = False
        fileDialog.title = "Load Sketch"
        fileDialog.filter = 'Turtle Sketch Files (*.tsk)'
        fileDialog.filterIndex = 0
        dialogResult = fileDialog.showOpen()
        if dialogResult == core.DialogResults.DialogOK:
            result = fileDialog.filename
        return result
