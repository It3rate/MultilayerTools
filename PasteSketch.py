#Author-Robin Debreuil
#Description-'Pastes sketch curves, constraints, parameters and dimesions. Optionally choose a guideline to allow transformed pasting if a guideline was selected while copying.'

import adsk.core, adsk.fusion, traceback
from .lib.TurtleUtils import TurtleUtils
from .lib.TurtleUICommand import TurtleUICommand
from .lib.TurtleSketch import TurtleSketch
from .lib.SketchDecoder import SketchDecoder
from .lib.data.SketchData import SketchData

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class PasteSketchCommand(TurtleUICommand):
    def __init__(self):
        cmdId = 'PasteSketchId'
        cmdName = 'Paste Sketch Command'
        cmdDescription = 'Pastes sketch curves, constraints, parameters and dimesions. Optionally choose a guideline to allow transformed pasting if a guideline was selected while copying.'
        super().__init__(cmdId, cmdName, cmdDescription)

    def onStartedRunning(self, eventArgs:core.CommandCreatedEventArgs):
        super().onStartedRunning(eventArgs)

    def onCreateUI(self, eventArgs:core.CommandCreatedEventArgs):
        try:
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

            # Flip checkboxes
            self.flipHSelection = inputs.addBoolValueInput('bFlipH', 'Flip Horizontal', True)
            self.flipVSelection = inputs.addBoolValueInput('bFlipV', 'Flip Vertical', True)

            if self.sketch and not self.guideline:
                tSketch = TurtleSketch.createWithSketch(self.sketch)
                lines = tSketch.getSingleLines()
                if(len(lines) == 1):
                    self.guideline = lines[0]
                    

            if self.sketch:
                self.sketchSelection.addSelection(self.sketch)
            self.resetUI()
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
            elif cmdInput.id == 'selSketch':
                self.sketch = cmdInput.selection(0).entity
                if(self.guideline and self.guideline.parentSketch != self.sketch):
                    self.guideline = None
                    self.guidelineSelection.selection = None

            self.resetUI()
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
        
    def onValidateInputs(self, eventArgs:core.ValidateInputsEventArgs):
            # print("isValid: " + str(eventArgs.areInputsValid))
            super().onValidateInputs(eventArgs)
        
    def onPreview(self, eventArgs:core.CommandEventArgs):
        data = self.getSketchData()
        enc = SketchDecoder.createWithGuideline(data, self.guideline, self.flipHSelection.value, self.flipVSelection.value)

    def onExecute(self, eventArgs:core.CommandEventArgs):
        data = self.getSketchData()
        flipX = self.flipHSelection.value
        flipY = self.flipVSelection.value
        if self.guideline:
            SketchDecoder.createWithGuideline(data, self.guideline, flipX, flipY)
        else:
            SketchDecoder.createWithSketch(data, self.sketch, flipX, flipY)
        adsk.autoTerminate(False)

    def getSketchData(self):
        result = TurtleUtils.getClipboardText()
        if result == None or not (result.startswith("#Turtle Generated Data")):
            result = SketchData.getTestData()
        else:
            result = eval(result)
        return result
    
    def resetUI(self):
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

    def onDestroy(self, eventArgs:core.CommandEventArgs):
        super().onDestroy(eventArgs)

