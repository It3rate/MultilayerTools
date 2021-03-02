import adsk.core, adsk.fusion, adsk.cam, traceback
import os, math, re
from .TurtleUtils import TurtleUtils, baseMethod, hasOverride

f,core,app,ui,design,root = TurtleUtils.initGlobals()

_handlers = []

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

            # Events
            uiCmd = self.commandDefinition
            
            onCommandCreated = self.getCreatedHandler()
            uiCmd.commandCreated.add(onCommandCreated)
            _handlers.append(onCommandCreated)

            if hasOverride(self.onCommandStarting):
                onCommandStarting = self.getEditExecuteHandler()
                uiCmd.commandStarting.add(onCommandStarting)
                _handlers.append(onCommandStarting)
            
            if hasOverride(self.onCommandTerminated):
                onCommandTerminated = self.getEditExecuteHandler()
                uiCmd.commandTerminated.add(onCommandTerminated)
                _handlers.append(onCommandTerminated)

            # ui
            if hasOverride(self.onActiveSelectionChanged):
                onActiveSelectionChanged = self.getActiveSelectionChangedHandler()
                ui.activeSelectionChanged.add(onActiveSelectionChanged)
                _handlers.append(onActiveSelectionChanged)

            # app
            # todo: Custom Event https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-85edd118-c2a4-11e6-b401-3417ebc87622
            if hasOverride(self.onFusionStartupCompleted):
                onFusionStartupCompleted = self.getFusionStartupCompletedHandler()
                app.startupCompleted.add(onFusionStartupCompleted)
                _handlers.append(onFusionStartupCompleted)

            if hasOverride(self.onOnlineStatusChanged):
                onOnlineStatusChanged = self.getOnlineStatusChangedHandler()
                app.onlineStatusChanged.add(onOnlineStatusChanged)
                _handlers.append(onOnlineStatusChanged)

            if hasOverride(self.onCameraChanged):
                onCameraChanged = self.getCameraChangedHandler()
                app.cameraChanged.add(onCameraChanged)
                _handlers.append(onCameraChanged)
            
            # todo: document events

            self.isCustomCommand = False
            adsk.autoTerminate(False)
        except:
            print('Failed:\n{}'.format(traceback.format_exc()))

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

    # Fusion life cycle
    @baseMethod
    def onFusionStartupCompleted(self, eventArgs:core.ApplicationEventArgs):
        pass
    @baseMethod
    def onOnlineStatusChanged(self, eventArgs:core.ApplicationEventArgs):
        pass
    @baseMethod
    def onCameraChanged(self, eventArgs:core.CameraEventArgs):
        pass

    # Component life cycle
    @baseMethod
    def onCreated(self, eventArgs:core.CommandCreatedEventArgs):
        pass
    @baseMethod
    def onCommandStarting(self, eventArgs:core.ApplicationCommandEventArgs):
        pass
    @baseMethod
    def onCommandTerminated(self, eventArgs:core.ApplicationCommandEventArgs):
        pass
    
    # UI Selection
    @baseMethod
    def onActiveSelectionChanged(self, eventArgs:core.ActiveSelectionEventArgs):
        pass

    # Command session lifecycle
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
        
    # mouse events
    @baseMethod
    def onMouseClick(self, eventArgs:core.MouseEventArgs):
        pass
    @baseMethod
    def onMouseDoubleClick(self, eventArgs:core.MouseEventArgs):
        pass
    @baseMethod
    def onMouseDown(self, eventArgs:core.MouseEventArgs):
        pass
    @baseMethod
    def onMouseDrag(self, eventArgs:core.MouseEventArgs):
        pass
    @baseMethod
    def onMouseDragBegin(self, eventArgs:core.MouseEventArgs):
        pass
    @baseMethod
    def onMouseDragEnd(self, eventArgs:core.MouseEventArgs):
        pass
    @baseMethod
    def onMouseMove(self, eventArgs:core.MouseEventArgs):
        pass
    @baseMethod
    def onMouseUp(self, eventArgs:core.MouseEventArgs):
        pass
    @baseMethod
    def onMouseWheel(self, eventArgs:core.MouseEventArgs):
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
    def getFusionStartupCompletedHandler(self):
        return BaseFusionStartupCompletedHandler(self)

    def getOnlineStatusChangedHandler(self):
        return BaseOnlineStatusChangedHandler(self)

    def getCameraChangedHandler(self):
        return BaseCameraChangedHandler(self)

    def getCreatedHandler(self):
        return BaseCommandCreatedHandler(self)

    def getCommandStartingHandler(self):
        return BaseCommandStartingHandler(self)

    def getCommandTerminatedHandler(self):
        return BaseCommandTerminatedHandler(self)

    def getActiveSelectionChangedHandler(self):
        return BaseActiveSelectionChangedHandler(self)


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

    def getMouseClickHandler(self):
        return BaseMouseClickHandler(self)
    def getMouseDoubleClickHandler(self):
        return BaseMouseDoubleClickHandler(self)
    def getMouseDownHandler(self):
        return BaseMouseDownHandler(self)
    def getMouseDragHandler(self):
        return BaseMouseDragHandler(self)
    def getMouseDragBeginHandler(self):
        return BaseMouseDragBeginHandler(self)
    def getMouseDragEndHandler(self):
        return BaseMouseDragEndHandler(self)
    def getMouseMoveHandler(self):
        return BaseMouseMoveHandler(self)
    def getMouseUpHandler(self):
        return BaseMouseUpHandler(self)
    def getMouseWheelHandler(self):
        return BaseMouseWheelHandler(self)

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

# app
class BaseFusionStartupCompletedHandler(core.ApplicationEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onFusionStartupCompleted(eventArgs)

class BaseOnlineStatusChangedHandler(core.ApplicationEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onOnlineStatusChanged(eventArgs)

class BaseCameraChangedHandler(core.CameraEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onCameraChanged(eventArgs)

# UI
class BaseCommandStartingHandler(core.ApplicationCommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onCommandStarting(eventArgs)

class BaseCommandTerminatedHandler(core.ApplicationCommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onCommandTerminated(eventArgs)

class BaseCommandCreatedHandler(core.CommandCreatedEventHandler):
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
                if hasOverride(self.turtleUICommand.onEditActivate):
                    onEditActivate = self.turtleUICommand.getEditActivateHandler()
                    cmd.activate.add(onEditActivate)
                    _handlers.append(onEditActivate)

                if hasOverride(self.turtleUICommand.onEditExecute):
                    onEditExecute = self.turtleUICommand.getEditExecuteHandler()
                    cmd.execute.add(onEditExecute)
                    _handlers.append(onEditExecute)

                if hasOverride(self.turtleUICommand.onEditDeactivate):
                    onEditDeactivate = self.turtleUICommand.getEditDeactivateHandler()
                    cmd.deactivate.add(onEditDeactivate)
                    _handlers.append(onEditDeactivate)
            else:
                if hasOverride(self.turtleUICommand.onActivate):
                    onActivate = self.turtleUICommand.getActivateHandler()
                    cmd.activate.add(onActivate)
                    _handlers.append(onActivate)   

                if hasOverride(self.turtleUICommand.onExecute):
                    onExecute = self.turtleUICommand.getExecuteHandler()
                    cmd.execute.add(onExecute)
                    _handlers.append(onExecute)

                if hasOverride(self.turtleUICommand.onDeactivate):
                    onDeactivate = self.turtleUICommand.getDeactivateHandler()
                    cmd.deactivate.add(onDeactivate)
                    _handlers.append(onDeactivate) 


            if hasOverride(self.turtleUICommand.onInputsChanged):
                onInputChanged = self.turtleUICommand.getInputChangedHandler()
                cmd.inputChanged.add(onInputChanged)
                _handlers.append(onInputChanged)    
        
            if hasOverride(self.turtleUICommand.onSelect):
                onSelect = self.turtleUICommand.getSelectHandler()
                cmd.select.add(onSelect)       
                _handlers.append(onSelect)

            if hasOverride(self.turtleUICommand.onPreSelect):
                onPreSelect = self.turtleUICommand.getPreSelectHandler()
                cmd.preSelect.add(onPreSelect)       
                _handlers.append(onPreSelect)

            if hasOverride(self.turtleUICommand.onPreSelectMouseMove):
                onPreSelectMouseMove = self.turtleUICommand.getPreSelectMouseMoveHandler()
                cmd.preSelectMouseMove.add(onPreSelectMouseMove)       
                _handlers.append(onPreSelectMouseMove)

            if hasOverride(self.turtleUICommand.onPreSelectEnd):
                onPreSelectEnd = self.turtleUICommand.getPreSelectEndHandler()
                cmd.preSelectEnd.add(onPreSelectEnd)       
                _handlers.append(onPreSelectEnd)

            if hasOverride(self.turtleUICommand.onUnselect):
                onUnselect = self.turtleUICommand.getUnselectHandler()
                cmd.unselect.add(onUnselect)       
                _handlers.append(onUnselect)
                
            
            if hasOverride(self.turtleUICommand.onMouseClick):
                onMouseClick = self.turtleUICommand.getMouseClickHandler()
                cmd.mouseClick.add(onMouseClick)
                _handlers.append(onMouseClick)

            if hasOverride(self.turtleUICommand.onMouseDoubleClick):
                onMouseDoubleClick = self.turtleUICommand.getMouseDoubleClickHandler()
                cmd.mouseDoubleClick.add(onMouseDoubleClick)
                _handlers.append(onMouseDoubleClick)

            if hasOverride(self.turtleUICommand.onMouseDown):
                onMouseDown = self.turtleUICommand.getMouseDownHandler()
                cmd.mouseDown.add(onMouseDown)
                _handlers.append(onMouseDown)

            if hasOverride(self.turtleUICommand.onMouseDrag):
                onMouseDrag = self.turtleUICommand.getMouseDragHandler()
                cmd.mouseDrag.add(onMouseDrag)
                _handlers.append(onMouseDrag)

            if hasOverride(self.turtleUICommand.onMouseDragBegin):
                onMouseDragBegin = self.turtleUICommand.getMouseDragBeginHandler()
                cmd.mouseDragBegin.add(onMouseDragBegin)
                _handlers.append(onMouseDragBegin)

            if hasOverride(self.turtleUICommand.onMouseDragEnd):
                onMouseDragEnd = self.turtleUICommand.getMouseDragEndHandler()
                cmd.mouseDragEnd.add(onMouseDragEnd)
                _handlers.append(onMouseDragEnd)

            if hasOverride(self.turtleUICommand.onMouseMove):
                onMouseMove = self.turtleUICommand.getMouseMoveHandler()
                cmd.mouseMove.add(onMouseMove)
                _handlers.append(onMouseMove)

            if hasOverride(self.turtleUICommand.onMouseUp):
                onMouseUp = self.turtleUICommand.getMouseUpHandler()
                cmd.mouseUp.add(onMouseUp)
                _handlers.append(onMouseUp)

            if hasOverride(self.turtleUICommand.onMouseWheel):
                onMouseWheel = self.turtleUICommand.getMouseWheelHandler()
                cmd.mouseWheel.add(onMouseWheel)
                _handlers.append(onMouseWheel)




            if hasOverride(self.turtleUICommand.onKeyDown):
                onKeyDown = self.turtleUICommand.getKeyDownHandler()
                cmd.keyDown.add(onKeyDown)
                _handlers.append(onKeyDown)

            if hasOverride(self.turtleUICommand.onKeyUp):
                onKeyUp = self.turtleUICommand.getKeyUpHandler()
                cmd.keyUp.add(onKeyUp)
                _handlers.append(onKeyUp)

            if hasOverride(self.turtleUICommand.onValidateInputs):
                onValidateInputs = self.turtleUICommand.getValidateInputsHandler()
                cmd.validateInputs.add(onValidateInputs)
                _handlers.append(onValidateInputs)

            if hasOverride(self.turtleUICommand.onPreview):
                onPreview = self.turtleUICommand.getPreviewHandler()
                cmd.executePreview.add(onPreview)
                _handlers.append(onPreview)

            # This will destroy the command, for single shot use.
            if hasOverride(self.turtleUICommand.onDestroy):
                onDestroy = self.turtleUICommand.getDestroyHandler()
                cmd.destroy.add(onDestroy)
                _handlers.append(onDestroy)

            if not self.turtleUICommand.isEditMode:
                self.turtleUICommand.onCreated(eventArgs)
        except:
            eventArgs.executeFailed = True
            print('Execute: {}\n'.format(traceback.format_exc()))

# Command
class BaseActivateHandler(core.CommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onActivate(eventArgs)

class BaseDeactivateHandler(core.CommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onDeactivate(eventArgs)

class BaseMouseClickHandler(core.MouseEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onMouseClick(eventArgs)

class BaseMouseDoubleClickHandler(core.MouseEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onMouseDoubleClick(eventArgs)

class BaseMouseDownHandler(core.MouseEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onMouseDown(eventArgs)

class BaseMouseDragHandler(core.MouseEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onMouseDrag(eventArgs)

class BaseMouseDragBeginHandler(core.MouseEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onMouseDragBegin(eventArgs)

class BaseMouseDragEndHandler(core.MouseEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onMouseDragEnd(eventArgs)

class BaseMouseMoveHandler(core.MouseEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onMouseMove(eventArgs)

class BaseMouseUpHandler(core.MouseEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onMouseUp(eventArgs)

class BaseMouseWheelHandler(core.MouseEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onMouseWheel(eventArgs)


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
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onValidateInputs(eventArgs)

class BasePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onPreview(eventArgs)

class BaseCommandExecuteHandler(core.CommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onExecute(eventArgs)
        adsk.autoTerminate(False)

class BaseDestroyHandler(core.CommandEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onDestroy(eventArgs)
        adsk.terminate()
