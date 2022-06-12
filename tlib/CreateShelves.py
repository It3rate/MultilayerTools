import adsk.core, adsk.fusion, adsk.cam, traceback
import os, math, re
from .TurtleUtils import TurtleUtils
from .TurtleCommand import TurtleCommand
from .JointMaker import JointMaker
from .TurtleEncoder import TurtleEncoder
from .TurtleDecoder import TurtleDecoder

# command
f,core,app,ui = TurtleUtils.initGlobals()

class CreateShelves(TurtleCommand):
    def __init__(self):
        cmdId = 'CreateShelvesId'
        cmdName = 'Create Shelves Command'
        cmdDescription = 'Creates three layer shelves and side walls based on a sketch.'
        super().__init__(cmdId, cmdName, cmdDescription)

    def onExecute(self, eventArgs):
        JointMaker()


# def run(context):
#     cmd = CreateShelves()
