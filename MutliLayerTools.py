
import adsk.core, adsk.fusion, traceback
from .CopySketch import CopySketchCommand
from .PasteSketch import PasteSketchCommand

commandHandles = []
def run(context):
    commandHandles.append(CopySketchCommand())
    commandHandles.append(PasteSketchCommand())

def stop(context):
    for cmd in commandHandles:
        cmd.destroyAddinUI()
    commandHandles.clear()
