import adsk.core, adsk.fusion, traceback, os

from .CopySketch import CopySketchCommand
from .PasteSketch import PasteSketchCommand
from .ExtrudeLayers import ExtrudeLayersCommand
from .SketchBuilder import SketchBuilder
from .MoldBuilder import MoldBuilder
from .tlib.CreateShelves import CreateShelves

commandHandles = []
def run(context):
    commandHandles.append(MoldBuilder())
    commandHandles.append(CopySketchCommand())
    commandHandles.append(PasteSketchCommand())
    commandHandles.append(ExtrudeLayersCommand())
    #commandHandles.append(SketchBuilder())
    #commandHandles.append(CreateShelves())

def stop(context):
    for cmd in commandHandles:
        try:
            cmd.destroyAddinUI()
        except:
            print(cmd)
    commandHandles.clear()
