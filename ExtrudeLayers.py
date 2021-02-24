# #Author-Robin Debreuil
# #Extrudes a profile into multiple layer bodies of parameterized thicknesses. Can also be used to cut, intersect existing layered components.

import adsk.core, adsk.fusion, traceback
from .lib.TurtleUtils import TurtleUtils
from .lib.TurtleUICommand import TurtleUICommand
from .lib.TurtleSketch import TurtleSketch
from .lib.SketchEncoder import SketchEncoder

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class ExtrudeLayersCommand(TurtleUICommand):
    def __init__(self):
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
            # Get the CommandInputs collection associated with the command.
            inputs = eventArgs.command.commandInputs

            # Select profiles
            self.sketchSelection = inputs.addSelectionInput('selProfile', 'Select Profile', 'Select profile to extrude.')
            self.sketchSelection.setSelectionLimits(1,0)
            self.sketchSelection.addSelectionFilter('Profiles')
            
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
            self.resetUI()
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))
        
    def onValidateInputs(self, eventArgs:core.ValidateInputsEventArgs):
            super().onValidateInputs(eventArgs)
        
    def onExecute(self, eventArgs:core.CommandEventArgs):
        #enc = SketchEncoder(self.sketch, self.guideline)
        adsk.autoTerminate(False)
    
    def resetUI(self):
        pass

    def onDestroy(self, eventArgs:core.CommandEventArgs):
        super().onDestroy(eventArgs)
