# #Author-Robin Debreuil
# #Description-Copies sketch points, lines, constraints and dimensions, including parameters. Optionally relative to a guideline for relative pasting.

# import adsk.core, adsk.fusion, adsk.cam, traceback

# def run(context):
#     ui = None
#     try:
#         app = adsk.core.Application.get()
#         ui  = app.userInterface
#         ui.messageBox('Hello addin')

#     except:
#         if ui:
#             ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# def stop(context):
#     ui = None
#     try:
#         app = adsk.core.Application.get()
#         ui  = app.userInterface
#         ui.messageBox('Stop addin')

#     except:
#         if ui:
#             ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
#Author-Autodesk Inc.
#Description-Demo command input examples
import adsk.core, adsk.fusion, traceback
from .lib.TurtleUtils import TurtleUtils
from .lib.TurtleUICommand import TurtleUICommand
from .lib.TurtleSketch import TurtleSketch
from .lib.SketchEncoder import SketchEncoder

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class CopySketchCommand(TurtleUICommand):
    def __init__(self):
        cmdId = 'CopySketchId'
        cmdName = 'Copy Sketch Command'
        cmdDescription = 'Copies sketch curves, constraints, parameters and dimesions. Optionally choose a guideline to allow relative pasting.'
        super().__init__(cmdId, cmdName, cmdDescription)

    def onStartedRunning(self, eventArgs:core.CommandCreatedEventArgs):
        pass

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

            if self.sketch and not self.guideline:
                tSketch = TurtleSketch(self.sketch)
                lines = tSketch.getSingleLines()
                if(len(lines) == 1):
                    self.guideline = lines[0]
                    

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
            self.resetUI()
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
        
    def onValidateInputs(self, eventArgs:core.ValidateInputsEventArgs):
            # print("isValid: " + str(eventArgs.areInputsValid))
            pass
        
    def onExecute(self, eventArgs:core.CommandEventArgs):
        print ("enc")
        enc = SketchEncoder(self.sketch, self.guideline)
        print ("enc done")

    # def onDestroy(self, eventArgs:core.CommandEventArgs):
    #     pass
    
    def resetUI(self):
        if self.guideline or self.isInSketch:
            self.sketchSelection.isVisible = False
            self.sketchText.isVisible = True
            self.guidelineSelection.hasFocus = True 
        else:
            self.sketchSelection.isVisible = True
            self.sketchText.isVisible = False


commandHandle = None
def run(context):
    commandHandle = CopySketchCommand()

# _app = None
# _ui  = None
# _rowNumber = 0

# # Global set of event handlers to keep them referenced for the duration of the command
# _handlers = []

# # Event handler that reacts to any changes the user makes to any of the command inputs.
# class MyCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
#     def __init__(self):
#         super().__init__()
#     def notify(self, args):
#         try:
#             eventArgs = adsk.core.InputChangedEventArgs.cast(args)
#             inputs = eventArgs.inputs
#             cmdInput = eventArgs.input
#             print(inputs)
#             if cmdInput.id == 'selGuideline':
#                 inputs.item(0).isEnabled = True
#                 if cmdInput.selectionCount > 0:
#                     gl:f.SketchLine = cmdInput.selection(0).entity
#                     inputs.item(0).clearSelection()
#                     inputs.item(0).addSelection(gl.parentSketch)
#         except:
#             _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# # Event handler that reacts to when the command is destroyed. This terminates the script.            
# class MyCommandDestroyHandler(adsk.core.CommandEventHandler):
#     def __init__(self):
#         super().__init__()
#     def notify(self, args):
#         try:
#             # When the command is done, terminate the script
#             # This will release all globals which will remove all event handlers
#             adsk.terminate()
#         except:
#             _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# class MyValidateInputsHandler(adsk.core.ValidateInputsEventHandler):
#     def __init__(self):
#         super().__init__()
#     def notify(self, args):
#         try:
#             print(str(args.areInputsValid))
#         except:
#             _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
#     def __init__(self):
#         super().__init__()
#     def notify(self, args):
#         try:
#             # Get the command that was created.
#             cmd = adsk.core.Command.cast(args.command)

#             # Connect to the command destroyed event.
#             onDestroy = MyCommandDestroyHandler()
#             cmd.destroy.add(onDestroy)
#             _handlers.append(onDestroy)

#             # Connect to the input changed event.           
#             onInputChanged = MyCommandInputChangedHandler()
#             cmd.inputChanged.add(onInputChanged)
#             _handlers.append(onInputChanged)    

#             onValidateInputs = MyValidateInputsHandler()
#             cmd.validateInputs.add(onValidateInputs)
#             _handlers.append(onValidateInputs)

#             # Get the CommandInputs collection associated with the command.
#             inputs = cmd.commandInputs

#             # Select sketch.
#             self.sketchSelection = inputs.addSelectionInput('selSketch', 'Select Sketch', 'Select sketch to copy.')
#             self.sketchSelection.setSelectionLimits(1,1)
#             self.sketchSelection.addSelectionFilter('Sketches')

#             # Select optional guideline.
#             self.guidelineSelection = inputs.addSelectionInput('selGuideline', 'Select Guideline', 'Optional reference guideline used if transforming sketch.')
#             self.guidelineSelection.setSelectionLimits(0, 1)
#             self.guidelineSelection.addSelectionFilter('SketchLines')

#             sketch:f.Sketch = TurtleUtils.getTargetSketch(f.Sketch)
#             if sketch:
#                 tSketch = TurtleSketch(sketch)
#                 #self.sketchSelection.addSelection(sketch)
#                 lines = tSketch.getSingleLines()
#                 if(len(lines) == 1):
#                     self.guidelineSelection.addSelection(lines[0])
#         except:
#             _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# def run(context):
    # try:
    #     global _app, _ui
    #     _app = adsk.core.Application.get()
    #     _ui = _app.userInterface

    #     # Get the existing command definition or create it if it doesn't already exist.
    #     cmdDef = _ui.commandDefinitions.itemById('cmdInputsSample')
    #     if not cmdDef:
    #         cmdDef = _ui.commandDefinitions.addButtonDefinition('cmdInputsSample', 'Command Inputs Sample', 'Sample to demonstrate various command inputs.')

    #     # Connect to the command created event.
    #     onCommandCreated = MyCommandCreatedHandler()
    #     cmdDef.commandCreated.add(onCommandCreated)
    #     _handlers.append(onCommandCreated)

    #     # Execute the command definition.
    #     cmdDef.execute()

    #     # Prevent this module from being terminated when the script returns, because we are waiting for event handlers to fire.
    #     adsk.autoTerminate(False)
    # except:
    #     if _ui:
    #         _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))