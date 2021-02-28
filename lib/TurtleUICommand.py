import adsk.core, adsk.fusion, adsk.cam, traceback
import os, math, re
from .TurtleUtils import TurtleUtils

f,core,app,ui,design,root = TurtleUtils.initGlobals()

_handlers = []

def baseMethod(method):
  method.isBaseMethod = True
  return method

class TurtleUICommand():
    def __init__(self, cmdId:str, cmdName:str, cmdDesc:str, isCustomCommand:bool, *targetPanels):
        super().__init__()
        self.cmdId = cmdId
        self.targetPanels = targetPanels
        self.isEditMode = False
        try:
            self.resFolder = "resources/" + self.cmdId 

            self.commandDefinition = ui.commandDefinitions.itemById(self.cmdId + "_create")
            if not self.commandDefinition:
                self.commandDefinition = ui.commandDefinitions.addButtonDefinition(self.cmdId + "_create", cmdName, cmdDesc, self.resFolder)
            self.createAddinUI()

            onCommandCreated = self.getCreatedHandler()
            self.commandDefinition.commandCreated.add(onCommandCreated)
            _handlers.append(onCommandCreated)

            self.isCustomCommand = isCustomCommand
            if self.isCustomCommand:
                # Create the command definition for the edit command.
                self.editCommandDefinition = ui.commandDefinitions.itemById(self.cmdId + "_edit")
                if not self.editCommandDefinition:
                    self.editCommandDefinition = ui.commandDefinitions.addButtonDefinition(self.cmdId + "_edit", cmdName, cmdDesc, self.resFolder)

                editCreated = self.getEditCreatedHandler()
                self.editCommandDefinition.commandCreated.add(editCreated)
                _handlers.append(editCreated)
             
                self.customFeatureDef = f.CustomFeatureDefinition.create(self.cmdId, cmdName,  self.resFolder)
                self.customFeatureDef .editCommandId = self.cmdId + "_edit"

                # Connect to the compute event for the custom feature.
                computeCustomFeature = self.getComputeCustomFeatureHandler()
                self.customFeatureDef .customFeatureCompute.add(computeCustomFeature)
                _handlers.append(computeCustomFeature)

            adsk.autoTerminate(False)
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))

    def hasOverride(self, method):
        return not hasattr(method, 'isBaseMethod')

    def getTargetPanels(self):
        if not self.targetPanels:
            self.targetPanels = [ui.allToolbarPanels.itemById('SolidScriptsAddinsPanel')]
        return self.targetPanels

    def createAddinUI(self):
        targetPanels = self.getTargetPanels()
        for targetPanel in targetPanels:
            if not targetPanel.controls.itemById(self.commandDefinition.id):
                buttonControl = targetPanel.controls.addCommand(self.commandDefinition)
                buttonControl.isPromotedByDefault = False
                buttonControl.isPromoted = False

    def destroyAddinUI(self):
        targetPanels = self.getTargetPanels()
        for targetPanel in targetPanels:
            buttonControl = targetPanel.controls.itemById(self.cmdId)
            if buttonControl:
                buttonControl.deleteMe()

    # Override 'on' methods to add custom funcionality
    def onStartedRunning(self, eventArgs:core.CommandCreatedEventArgs):
        pass

    @baseMethod
    def onCreated(self, eventArgs:core.CommandCreatedEventArgs):
        pass
        
    @baseMethod
    def onSelect(self, eventArgs:core.SelectionEventArgs):
        pass
        
    @baseMethod
    def onPreSelect(self, eventArgs:core.SelectionEventArgs):
        pass
        
    @baseMethod
    def onPreSelectMouseMove(self, eventArgs:core.SelectionEventArgs):
        pass
        
    @baseMethod
    def onPreSelectEnd(self, eventArgs:core.SelectionEventArgs):
        pass
        
    @baseMethod
    def onUnselect(self, eventArgs:core.SelectionEventArgs):
        pass
        
    @baseMethod
    def onMouseDown(self, eventArgs:core.MouseEventArgs):
        pass
    @baseMethod
    def onMouseUp(self, eventArgs:core.MouseEventArgs):
        pass

    @baseMethod
    def onKeyDown(self, eventArgs:core.KeyboardEventArgs):
        pass
    @baseMethod
    def onKeyUp(self, eventArgs:core.KeyboardEventArgs):
        pass

    @baseMethod
    def onInputsChanged(self, eventArgs:core.InputChangedEventArgs):
        pass
        
    @baseMethod
    def onValidateInputs(self, eventArgs:core.ValidateInputsEventArgs):
        pass
      
    @baseMethod  
    def onPreview(self, eventArgs:core.CommandEventArgs):
        pass
        
    @baseMethod
    def onExecute(self, eventArgs:core.CommandEventArgs):
        pass

    @baseMethod
    def onDestroy(self, eventArgs:core.CommandEventArgs):
        self.destroyAddinUI()

    # get handlers, only need to override to inject custom handlers
    def getCreatedHandler(self):
        return BaseCommandCreatedHandler(self)

    def getSelectHandler(self):
        return BaseSelectHandler(self)
        
    def getPreSelectHandler(self):
        return BasePreSelectHandler(self)

    def getPreSelectMouseMoveHandler(self):
        return BasePreSelectMouseMoveHandler(self)

    def getPreSelectEndHandler(self):
        return BasePreSelectEndHandler(self)

    def getUnselectHandler(self):
        return BaseUnselectHandler(self)

    def getMouseDownHandler(self):
        return BaseMouseDownHandler(self)

    def getMouseUpHandler(self):
        return BaseMouseUpHandler(self)

    def getKeyDownHandler(self):
        return BaseKeyDownHandler(self)

    def getKeyUpHandler(self):
        return BaseKeyUpHandler(self)

    def getInputChangedHandler(self):
        return BaseInputChangedHandler(self)

    def getValidateInputsHandler(self):
        return BaseValidateInputsHandler(self)

    def getExecuteHandler(self):
        return BaseCommandExecuteHandler(self)

    def getPreviewHandler(self):
        return BasePreviewHandler(self)

    def getDestroyHandler(self):
        return BaseDestroyHandler(self)

    # custom features
    def onEditCreated(self, eventArgs:core.CommandCreatedEventArgs):
        self._editedCustomFeature:f.CustomFeature = ui.activeSelections.item(0).entity
        if self._editedCustomFeature is None:
            print("No active custom feature.")
        
    def onEditActivate(self, eventArgs:core.CommandEventArgs):
        if not self._editedCustomFeature:
            return
        markerPosition = design.timeline.markerPosition
        self._restoreTimelineObject = design.timeline.item(markerPosition - 1)
        self._editedCustomFeature.timelineObject.rollTo(True)
        self._isRolledForEdit = True
        # Define a transaction marker so the the roll is not aborted with each change.
        eventArgs.command.beginStep()
        # Get the point and add it to the selection input.
        # skPoint = _editedCustomFeature.dependencies.itemById('point').entity
        # _pointSelectInput.addSelection(skPoint)

    def onEditExecute(self, eventArgs:core.CommandEventArgs):
        if self._isRolledForEdit:
            self._restoreTimelineObject.rollTo(False)
            self._isRolledForEdit = False
        self._editedCustomFeature = None

    def onComputeCustomFeature(self, eventArgs:f.CustomFeatureEventArgs):
        pass

    def getEditCreatedHandler(self):
        return BaseEditCreatedHandler(self)
    def getEditActivateHandler(self):
        return BaseEditActivateHandler(self)
    def getEditExecuteHandler(self):
        return BaseEditExecuteHandler(self)
    def getComputeCustomFeatureHandler(self):
        return BaseComputeCustomFeature(self)


class BaseCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand

    def notify(self, eventArgs):
        self.turtleUICommand.isEditMode = False
        cmd = eventArgs.command
            
        if self.turtleUICommand.hasOverride(self.turtleUICommand.onInputsChanged):
            onInputChanged = self.turtleUICommand.getInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)    
    
        if self.turtleUICommand.hasOverride(self.turtleUICommand.onSelect):
            onSelect = self.turtleUICommand.getSelectHandler()
            cmd.select.add(onSelect)       
            _handlers.append(onSelect)

        if self.turtleUICommand.hasOverride(self.turtleUICommand.onPreSelect):
            onPreSelect = self.turtleUICommand.getPreSelectHandler()
            cmd.preSelect.add(onPreSelect)       
            _handlers.append(onPreSelect)

        if self.turtleUICommand.hasOverride(self.turtleUICommand.onPreSelectMouseMove):
            onPreSelectMouseMove = self.turtleUICommand.getPreSelectMouseMoveHandler()
            cmd.preSelectMouseMove.add(onPreSelectMouseMove)       
            _handlers.append(onPreSelectMouseMove)

        if self.turtleUICommand.hasOverride(self.turtleUICommand.onPreSelectEnd):
            onPreSelectEnd = self.turtleUICommand.getPreSelectEndHandler()
            cmd.preSelectEnd.add(onPreSelectEnd)       
            _handlers.append(onPreSelectEnd)

        if self.turtleUICommand.hasOverride(self.turtleUICommand.onUnselect):
            onUnselect = self.turtleUICommand.getUnselectHandler()
            cmd.unselect.add(onUnselect)       
            _handlers.append(onUnselect)
            
        
        if self.turtleUICommand.hasOverride(self.turtleUICommand.onMouseDown):
            onMouseDown = self.turtleUICommand.getMouseDownHandler()
            cmd.mouseDown.add(onMouseDown)
            _handlers.append(onMouseDown)

        if self.turtleUICommand.hasOverride(self.turtleUICommand.onMouseUp):
            onMouseUp = self.turtleUICommand.getMouseUpHandler()
            cmd.mouseUp.add(onMouseUp)
            _handlers.append(onMouseUp)

        if self.turtleUICommand.hasOverride(self.turtleUICommand.onKeyDown):
            onKeyDown = self.turtleUICommand.getKeyDownHandler()
            cmd.keyDown.add(onKeyDown)
            _handlers.append(onKeyDown)

        if self.turtleUICommand.hasOverride(self.turtleUICommand.onKeyUp):
            onKeyUp = self.turtleUICommand.getKeyUpHandler()
            cmd.keyUp.add(onKeyUp)
            _handlers.append(onKeyUp)

        if self.turtleUICommand.hasOverride(self.turtleUICommand.onValidateInputs):
            onValidateInputs = self.turtleUICommand.getValidateInputsHandler()
            cmd.validateInputs.add(onValidateInputs)
            _handlers.append(onValidateInputs)

        if self.turtleUICommand.hasOverride(self.turtleUICommand.onPreview):
            onPreview = self.turtleUICommand.getPreviewHandler()
            cmd.executePreview.add(onPreview)
            _handlers.append(onPreview)

        if self.turtleUICommand.hasOverride(self.turtleUICommand.onExecute):
            onExecute = self.turtleUICommand.getExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)

        # This will destroy the command, for single shot use.
        if self.turtleUICommand.hasOverride(self.turtleUICommand.onDestroy):
            onDestroy = self.turtleUICommand.getDestroyHandler()
            cmd.destroy.add(onDestroy)
            _handlers.append(onDestroy)

        self.turtleUICommand.onStartedRunning(eventArgs)
        self.turtleUICommand.onCreated(eventArgs)

class BaseMouseDownHandler(core.MouseEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onMouseDown(eventArgs)
        
class BaseMouseUpHandler(core.MouseEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onMouseUp(eventArgs)

class BaseKeyUpHandler(core.KeyboardEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onKeyUp(eventArgs)
class BaseKeyDownHandler(core.KeyboardEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onKeyDown(eventArgs)


class BaseInputChangedHandler(core.InputChangedEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onInputsChanged(eventArgs)

# Fires when hovering over elements in the UI, decides if they are selectable
class BaseSelectHandler(core.SelectionEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        self.turtleUICommand.onSelect(eventArgs)

class BasePreSelectHandler(core.SelectionEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        self.turtleUICommand.onPreSelect(eventArgs)

class BasePreSelectMouseMoveHandler(core.SelectionEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        self.turtleUICommand.onPreSelectMouseMove(eventArgs)

class BasePreSelectEndHandler(core.SelectionEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        self.turtleUICommand.onPreSelectEnd(eventArgs)

class BaseUnselectHandler(core.SelectionEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        self.turtleUICommand.onUnselect(eventArgs)

class BaseValidateInputsHandler(core.ValidateInputsEventHandler):
    def __init__(self, turtleCommand:TurtleUICommand):
        super().__init__()
        self.turtleCommand = turtleCommand
    def notify(self, eventArgs):
        self.turtleCommand.onValidateInputs(eventArgs)

class BasePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self, turtleCommand:TurtleUICommand):
        super().__init__()
        self.turtleCommand = turtleCommand
    def notify(self, eventArgs):
        self.turtleCommand.onPreview(eventArgs)

class BaseCommandExecuteHandler(core.CommandEventHandler):
    def __init__(self, turtleCommand:TurtleUICommand):
        super().__init__()
        self.turtleCommand = turtleCommand
    def notify(self, eventArgs):
        self.turtleCommand.onExecute(eventArgs)

class BaseDestroyHandler(core.CommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onDestroy(eventArgs)
        adsk.terminate()
        
# custom command handlers

class BaseEditCreatedHandler(BaseCommandCreatedHandler): #adsk.core.CommandCreatedEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__(turtleUICommand)
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        super().notify(args)
        self.turtleUICommand.isEditMode = True
        eventArgs:core.CommandCreatedEventArgs = args
        cmd = eventArgs.command

        if self.turtleUICommand.hasOverride(self.turtleUICommand.onEditActivate):
            onEditActivate = self.turtleUICommand.getEditActivateHandler()
            cmd.activate.add(onEditActivate)
            _handlers.append(onEditActivate)

        if self.turtleUICommand.hasOverride(self.turtleUICommand.onEditExecute):
            onEditExecute = self.turtleUICommand.getEditExecuteHandler()
            cmd.execute.add(onEditExecute)
            _handlers.append(onEditExecute)

        self.turtleUICommand.onEditCreated(eventArgs)


class BaseEditActivateHandler(adsk.core.CommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        eventArgs:core.CommandEventArgs = args
        self.turtleUICommand.onEditActivate(eventArgs)

class BaseEditExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        eventArgs:core.CommandEventArgs.cast = args
        self.turtleUICommand.onEditExecute(eventArgs)

class BaseComputeCustomFeature(adsk.fusion.CustomFeatureEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        eventArgs:f.CustomFeatureEventArgs = args
        self.turtleUICommand.onComputeCustomFeature(eventArgs)
