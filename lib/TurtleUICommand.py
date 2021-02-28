import adsk.core, adsk.fusion, adsk.cam, traceback
import os, math, re
from .TurtleUtils import TurtleUtils

f,core,app,ui,design,root = TurtleUtils.initGlobals()

_handlers = []

# used to detect overrides - only hook up events if there is a handler implemented
def baseMethod(method):
  method.isBaseMethod = True
  return method

class TurtleUICommand():
    def __init__(self, cmdId:str, cmdName:str, cmdDesc:str, isCustomCommand:bool, *targetPanels):
        super().__init__()
        self.cmdId = cmdId
        self.targetPanels = targetPanels
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
                self.customFeatureDef.editCommandId = self.cmdId + "_edit"

                # Connect to the compute event for the custom feature.
                computeCustomFeature = self.getComputeCustomFeatureHandler()
                self.customFeatureDef.customFeatureCompute.add(computeCustomFeature)
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
    def onActivate(self, eventArgs:core.CommandCreatedEventArgs):
        pass

    @baseMethod
    def onDeactivate(self, eventArgs:core.CommandCreatedEventArgs):
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


    # get handlers, only need to override to inject custom handlers
    def getCreatedHandler(self):
        return BaseCommandCreatedHandler(self)

    def getActivateHandler(self):
        return BaseActivateHandler(self)

    def getDeactivateHandler(self):
        return BaseDeactivateHandler(self)

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


class BaseCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
        self.turtleUICommand._editedCustomFeature = None

    def notify(self, eventArgs):
        cmd = eventArgs.command

        if type(self) == BaseCommandCreatedHandler:
            self.turtleUICommand.isEditMode = False

        try:
            if self.turtleUICommand.isEditMode:
                if self.turtleUICommand.hasOverride(self.turtleUICommand.onEditActivate):
                    onEditActivate = self.turtleUICommand.getEditActivateHandler()
                    cmd.activate.add(onEditActivate)
                    _handlers.append(onEditActivate)

                if self.turtleUICommand.hasOverride(self.turtleUICommand.onEditExecute):
                    onEditExecute = self.turtleUICommand.getEditExecuteHandler()
                    cmd.execute.add(onEditExecute)
                    _handlers.append(onEditExecute)

                if self.turtleUICommand.hasOverride(self.turtleUICommand.onEditDeactivate):
                    onEditDeactivate = self.turtleUICommand.getEditDeactivateHandler()
                    cmd.deactivate.add(onEditDeactivate)
                    _handlers.append(onEditDeactivate)
            else:
                if self.turtleUICommand.hasOverride(self.turtleUICommand.onActivate):
                    onActivate = self.turtleUICommand.getActivateHandler()
                    cmd.activate.add(onActivate)
                    _handlers.append(onActivate)   

                if self.turtleUICommand.hasOverride(self.turtleUICommand.onExecute):
                    onExecute = self.turtleUICommand.getExecuteHandler()
                    cmd.execute.add(onExecute)
                    _handlers.append(onExecute)

                if self.turtleUICommand.hasOverride(self.turtleUICommand.onDeactivate):
                    onDeactivate = self.turtleUICommand.getDeactivateHandler()
                    cmd.deactivate.add(onDeactivate)
                    _handlers.append(onDeactivate) 


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

            # This will destroy the command, for single shot use.
            if self.turtleUICommand.hasOverride(self.turtleUICommand.onDestroy):
                onDestroy = self.turtleUICommand.getDestroyHandler()
                cmd.destroy.add(onDestroy)
                _handlers.append(onDestroy)

            if not self.turtleUICommand.isEditMode:
                self.turtleUICommand.onStartedRunning(eventArgs)
                self.turtleUICommand.onCreated(eventArgs)
        except:
            eventArgs.executeFailed = True
            print('Execute: {}\n'.format(traceback.format_exc()))

class BaseActivateHandler(adsk.core.CommandEventHandler):
    def __init__(self, turtleCommand:TurtleUICommand):
        super().__init__()
        self.turtleCommand = turtleCommand
    def notify(self, eventArgs):
        self.turtleCommand.onActivate(eventArgs)

class BaseDeactivateHandler(adsk.core.CommandEventHandler):
    def __init__(self, turtleCommand:TurtleUICommand):
        super().__init__()
        self.turtleCommand = turtleCommand
    def notify(self, eventArgs):
        self.turtleCommand.onDeactivate(eventArgs)

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
    def notify(self, eventArgs):
        self.turtleUICommand.onSelect(eventArgs)

class BasePreSelectHandler(core.SelectionEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onPreSelect(eventArgs)

class BasePreSelectMouseMoveHandler(core.SelectionEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onPreSelectMouseMove(eventArgs)

class BasePreSelectEndHandler(core.SelectionEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onPreSelectEnd(eventArgs)

class BaseUnselectHandler(core.SelectionEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
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
        adsk.autoTerminate(False)

class BaseDestroyHandler(core.CommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onDestroy(eventArgs)
        adsk.terminate()
        
class BaseEditCreatedHandler(BaseCommandCreatedHandler): 
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__(turtleUICommand)
        self.turtleUICommand = turtleUICommand

    def notify(self, args):
        self.turtleUICommand.isEditMode = True
        self.turtleUICommand._editedCustomFeature:f.CustomFeature = ui.activeSelections.item(0).entity
        if self.turtleUICommand._editedCustomFeature is None:
            print("No active custom feature.")

        super().notify(args)
        eventArgs:core.CommandCreatedEventArgs = args
        cmd = eventArgs.command

        self.turtleUICommand.onEditCreated(eventArgs)


class BaseEditActivateHandler(adsk.core.CommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        if not self.turtleUICommand._editedCustomFeature:
            return
        eventArgs:core.CommandEventArgs = args
        # automatically roll the timeline to just before the edit
        markerPosition = design.timeline.markerPosition
        self.turtleUICommand._restoreTimelineObject = design.timeline.item(markerPosition - 1)
        self.turtleUICommand._editedCustomFeature.timelineObject.rollTo(True)
        self.turtleUICommand._isRolledForEdit = True
        eventArgs.command.beginStep()

        self.turtleUICommand.onEditActivate(eventArgs)

class BaseEditDeactivateHandler(adsk.core.CommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        self.turtleUICommand.onEditDeactivate(eventArgs)

class BaseEditExecuteHandler(adsk.core.CommandEventHandler):
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
                design.timeline.moveToEnd()
            self.turtleUICommand._isRolledForEdit = False

        self.turtleUICommand.isEditMode = False
        self.turtleUICommand._editedCustomFeature = None
        adsk.autoTerminate(False)

class BaseComputeCustomFeature(adsk.fusion.CustomFeatureEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        eventArgs:f.CustomFeatureEventArgs = args
        self.turtleUICommand.onComputeCustomFeature(eventArgs)
