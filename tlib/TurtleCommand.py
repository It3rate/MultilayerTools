import adsk.core, adsk.fusion, adsk.cam, traceback
import os, math, re
from .TurtleUtils import TurtleUtils
from .JointMaker import JointMaker

f:adsk.fusion
core:adsk.core
f,core,app,ui = TurtleUtils.initGlobals()

_handlers = []

class TurtleCommand():
    def __init__(self, cmdId:str, cmdName:str, cmdDesc:str):
        super().__init__()
        try:
            self.commandDefinition = ui.commandDefinitions.itemById(cmdId)
            if not self.commandDefinition:
                self.commandDefinition = ui.commandDefinitions.addButtonDefinition(cmdId, cmdName, cmdDesc)

            onCommandCreated = self.createdHandler()
            self.commandDefinition.commandCreated.add(onCommandCreated)
            _handlers.append(onCommandCreated)
            self.commandDefinition.execute()
            # Prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
            adsk.autoTerminate(False)
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

    def onExecute(self, eventArgs):
        pass

    def executeHandler(self):
        return UICommandExecuteHandler(self)

    def createdHandler(self):
        return UICommandCreatedHandler(self)

class UICommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, turtleCommand:TurtleCommand):
        super().__init__()
        self.turtleCommand = turtleCommand

    def notify(self, args):
        try:
            self.turtleCommand.onExecute(args)
            adsk.terminate()
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class UICommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, turtleCommand:TurtleCommand):
        super().__init__()
        self.turtleCommand = turtleCommand

    def notify(self, args):
        cmd = args.command
        onExecute = self.turtleCommand.executeHandler()
        cmd.execute.add(onExecute)
        _handlers.append(onExecute)   
