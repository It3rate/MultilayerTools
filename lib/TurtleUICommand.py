import adsk.core, adsk.fusion, adsk.cam, traceback
import os, math, re
from .TurtleUtils import TurtleUtils

f,core,app,ui,design,root = TurtleUtils.initGlobals()

_handlers = []

class TurtleUICommand():
    def __init__(self, cmdId:str, cmdName:str, cmdDesc:str, *targetPanels):
        super().__init__()
        self.cmdId = cmdId
        self.targetPanels = targetPanels
        try:
            self.commandDefinition = ui.commandDefinitions.itemById(self.cmdId)

            if not self.commandDefinition:
                self.resFolder = "resources/" + self.cmdId 
                self.commandDefinition = ui.commandDefinitions.addButtonDefinition(self.cmdId, cmdName, cmdDesc, self.resFolder)
            self.createAddinUI()

            onCommandCreated = self.getCreatedHandler()
            self.commandDefinition.commandCreated.add(onCommandCreated)
            _handlers.append(onCommandCreated)

            # self.commandDefinition.execute()
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

    # Override 'on' methods to add custom funcionality
    def onStartedRunning(self, eventArgs:core.CommandCreatedEventArgs):
        pass

    def onCreateUI(self, eventArgs:core.CommandCreatedEventArgs):
        pass
        
    def onSelectionEvent(self, eventArgs:core.SelectionEventArgs):
        pass
        
    def onInputsChanged(self, eventArgs:core.InputChangedEventArgs):
        pass
        
    def onValidateInputs(self, eventArgs:core.ValidateInputsEventArgs):
        pass
        
    def onPreview(self, eventArgs:core.CommandEventArgs):
        pass
        
    def onExecute(self, eventArgs:core.CommandEventArgs):
        pass

    def onDestroy(self, eventArgs:core.CommandEventArgs):
        self.destroyAddinUI()

    # get handlers, only need to override to inject custom handlers
    def getCreatedHandler(self):
        return BaseCommandCreatedHandler(self)

    def getSelectionEventHandler(self):
        return BaseSelectionEventHandler(self)

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


class BaseCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand

    def notify(self, eventArgs):
        cmd = eventArgs.command

        # This will destroy the command, for single shot use.
        # onDestroy = self.turtleUICommand.getDestroyHandler()
        # cmd.destroy.add(onDestroy)
        # _handlers.append(onDestroy)
        
        onInputChanged = self.turtleUICommand.getInputChangedHandler()
        cmd.inputChanged.add(onInputChanged)
        _handlers.append(onInputChanged)    

        # various selection events are available
        onSelectionEvent = self.turtleUICommand.getSelectionEventHandler()
        # cmd.preSelect.add(onSelectionEvent)
        # cmd.preSelectMouseMove.add(onSelectionEvent)
        # cmd.preSelectEnd.add(onSelectionEvent)
        cmd.select.add(onSelectionEvent)
        #cmd.unselect.add(onSelectionEvent)          
        _handlers.append(onSelectionEvent)
        
        onValidateInputs = self.turtleUICommand.getValidateInputsHandler()
        cmd.validateInputs.add(onValidateInputs)
        _handlers.append(onValidateInputs)

        onPreview = self.turtleUICommand.getPreviewHandler()
        cmd.executePreview.add(onPreview)
        _handlers.append(onPreview)

        onExecute = self.turtleUICommand.getExecuteHandler()
        cmd.execute.add(onExecute)
        _handlers.append(onExecute)

        self.turtleUICommand.onStartedRunning(eventArgs)
        self.turtleUICommand.onCreateUI(eventArgs)

class BaseInputChangedHandler(core.InputChangedEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, eventArgs):
        self.turtleUICommand.onInputsChanged(eventArgs)

# Fires when hovering over elements in the UI, decides if they are selectable
class BaseSelectionEventHandler(core.SelectionEventHandler):
    def __init__(self, turtleUICommand:TurtleUICommand):
        super().__init__()
        self.turtleUICommand = turtleUICommand
    def notify(self, args):
        self.turtleUICommand.onSelectionEvent(eventArgs)

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
        