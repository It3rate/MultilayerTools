import adsk.core, adsk.fusion, adsk.cam, traceback
import os, math, re
from .TurtleUtils import TurtleUtils, baseMethod, hasOverride
from .TurtleUICommand import TurtleUICommand, BaseCommandCreatedHandler, BaseCommandExecuteHandler

f:adsk.fusion
core:adsk.core
f,core,app,ui = TurtleUtils.initGlobals()

_handlers = []

class TurtleCustomCommand(TurtleUICommand):
    def __init__(self, cmdId:str, cmdName:str, cmdDesc:str):
        super().__init__(cmdId, cmdName, cmdDesc)
        self.isCustomCommand = True
        self.isEditMode = False
        self._editedCustomFeature = None
        
        self.editCommandDefinition = ui.commandDefinitions.itemById(self.cmdId + "_edit")
        if not self.editCommandDefinition:
            self.editCommandDefinition = ui.commandDefinitions.addButtonDefinition(self.cmdId + "_edit", cmdName, cmdDesc, self.resFolder)

        editCreated = self.getEditCreatedHandler() 
        self.editCommandDefinition.commandCreated.add(editCreated)
        _handlers.append(editCreated)
        
        self.customFeatureDef = f.CustomFeatureDefinition.create(self.cmdId, cmdName,  self.resFolder)
        self.customFeatureDef.editCommandId = self.cmdId + "_edit"
        print(self.customFeatureDef.editCommandId)

        # Connect to the compute event for the custom feature.
        computeCustomFeature = self.getComputeCustomFeatureHandler()
        self.customFeatureDef.customFeatureCompute.add(computeCustomFeature)
        _handlers.append(computeCustomFeature)

        adsk.autoTerminate(False)
        

    # custom features
    @baseMethod
    def onEditCreated(self, eventArgs:core.CommandCreatedEventArgs):
        pass
    @baseMethod
    def onEditActivate(self, eventArgs:core.CommandEventArgs):
        pass
    @baseMethod
    def onEditDeactivate(self, eventArgs:core.CommandEventArgs):
        pass
    @baseMethod
    def onEditExecute(self, eventArgs:core.CommandEventArgs):
        pass
    @baseMethod
    def onComputeCustomFeature(self, eventArgs:f.CustomFeatureEventArgs):
        pass
    
    def getEditCreatedHandler(self):
        return BaseEditCreatedHandler(self)
    def getEditActivateHandler(self):
        return BaseEditActivateHandler(self)
    def getEditDeactivateHandler(self):
        return BaseEditDeactivateHandler(self)
    def getEditExecuteHandler(self):
        return BaseEditExecuteHandler(self)
    def getComputeCustomFeatureHandler(self):
        return BaseComputeCustomFeature(self)
   
class BaseEditCreatedHandler(BaseCommandCreatedHandler): 
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__(turtleUICommand)
        self.autoRun = False

    def notify(self, args):
        self.turtleUICommand.isEditMode = True
        self.turtleUICommand._editedCustomFeature:f.CustomFeature = ui.activeSelections.item(0).entity
        if self.turtleUICommand._editedCustomFeature is None:
            print("No active custom feature.")

        super().notify(args)

        eventArgs:core.CommandCreatedEventArgs = args
        cmd = eventArgs.command

        if hasOverride(self.turtleUICommand.onEditActivate):
            if self.turtleUICommand.activateHandler:
                cmd.activate.remove(self.turtleUICommand.activateHandler)
            onEditActivate = self.turtleUICommand.getEditActivateHandler()
            cmd.activate.add(onEditActivate)
            _handlers.append(onEditActivate)

        if hasOverride(self.turtleUICommand.onEditExecute):
            if self.turtleUICommand.executeHandler:
                cmd.execute.remove(self.turtleUICommand.executeHandler)
            onEditExecute = self.turtleUICommand.getEditExecuteHandler()
            cmd.execute.add(onEditExecute)
            _handlers.append(onEditExecute)

        if hasOverride(self.turtleUICommand.onEditDeactivate):
            if self.turtleUICommand.deactivateHandler:
                cmd.deactivate.remove(self.turtleUICommand.deactivateHandler)
            onEditDeactivate = self.turtleUICommand.getEditDeactivateHandler()
            cmd.deactivate.add(onEditDeactivate)
            _handlers.append(onEditDeactivate)
            

        self.turtleUICommand.onEditCreated(eventArgs)


class BaseEditActivateHandler(core.CommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        if not self.turtleUICommand._editedCustomFeature:
            return
        eventArgs:core.CommandEventArgs = args
        # automatically roll the timeline to just before the edit
        design = TurtleUtils.activeDesign()
        markerPosition = design.timeline.markerPosition
        self.turtleUICommand._restoreTimelineObject = design.timeline.item(markerPosition - 1)
        self.turtleUICommand._editedCustomFeature.timelineObject.rollTo(rollBefore = True)
        self.turtleUICommand._isRolledForEdit = True
        eventArgs.command.beginStep()

        self.turtleUICommand.onEditActivate(eventArgs)

class BaseEditDeactivateHandler(core.CommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        self.turtleUICommand.onEditDeactivate(eventArgs)

class BaseEditExecuteHandler(core.CommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        eventArgs:core.CommandEventArgs.cast = args
        self.turtleUICommand.onEditExecute(eventArgs)
        
        # automatically roll the timeline back to where it started when edit is complete
        if self.turtleUICommand._isRolledForEdit:
            try:
                self.turtleUICommand._restoreTimelineObject.rollTo(False)
            except:
                TurtleUtils.activeDesign().timeline.moveToEnd()
            self.turtleUICommand._isRolledForEdit = False

        self.turtleUICommand.isEditMode = False
        self.turtleUICommand._editedCustomFeature = None
        adsk.autoTerminate(False)

class BaseComputeCustomFeature(f.CustomFeatureEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        eventArgs:f.CustomFeatureEventArgs = args
        self.turtleUICommand.onComputeCustomFeature(eventArgs)
