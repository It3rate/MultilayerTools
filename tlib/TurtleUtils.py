import adsk.core, adsk.fusion, adsk.cam, traceback, os
import tkinter as tk

__decimalPlaces__ = 6

class TurtleUtils:
    def __init__(self):
        super().__init__()
        
    @classmethod
    def initGlobals(cls):
        global f
        global core
        global app
        global ui
        # global design
        # global root
        f = adsk.fusion
        core = adsk.core
        app = adsk.core.Application.get()
        ui  = app.userInterface
        # design:f.Design = app.activeProduct
        # root:f.Component = design.rootComponent
        return f,core,app,ui#,design,root

    @classmethod
    def activeDesign(cls):
        return app.activeProduct
    @classmethod
    def activeRoot(cls):
        return app.activeProduct.rootComponent

    @classmethod
    def getTargetSketch(cls, selType, showMessage = True):
        result = None
        typeName = selType.__name__
        title = "Selection Required"
        if not TurtleUtils.activeDesign():
            if showMessage:
                ui.messageBox('No active Fusion design', title)
        elif selType is f.Sketch and app.activeEditObject.classType == f.Sketch.classType: # in sketch
            result = app.activeEditObject
        elif ui.activeSelections.count < 1:
            if showMessage:
                ui.messageBox('Select ' + typeName + ' before running command.', title)
        else:
            result = ui.activeSelections.item(0).entity
            if not type(result) is selType:
                result = None
                if showMessage:
                    ui.messageBox('Selected object needs to be a ' + typeName + ". It is a " + str(type(ui.activeSelections.item(0))) + ".", title)

        return result

    @classmethod
    def getSelectedTypeOrNone(cls, selType):
        result = None
        if app.activeEditObject.classType == selType:
            result = app.activeEditObject
        return result
    
    @classmethod
    def selectEntity(cls, entity):
        ui.activeSelections.clear()
        ui.activeSelections.add(entity)
    
    @classmethod
    def round(cls, val):
        return str(round(val, __decimalPlaces__))

    @classmethod
    def areFloatsEqual(cls, val0:float, val1:float):
        return abs(val0 - val1) < 0.000000001        

    @classmethod
    def getClipboardText(cls):
        result = ""
        # f = open("sketchData.txt", "w")
        # f.write(result)
        # f.close()
        # command = 'type sketchData.txt | clip'
        # os.system(command)
        root = TurtleUtils.activeRoot()
        root = tk.Tk()
        root.withdraw()
        try:
            #result = root.selection_get(selection = "CLIPBOARD") 
            result = root.clipboard_get()
            root.update()
            # this clipboard is quite flakey, without this text can be on the clipboard but not detected
            # cls.clearClipboardText()
            #cls.setClipboardText(result) 
        except tk.TclError:
            #pass
            print(traceback.format_exc())
        return result

    @classmethod
    def setClipboardText(cls, data):
        root = TurtleUtils.activeRoot()
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(data)
        root.update() # now it stays on the clipboard after the window is closed
        root.destroy()

    @classmethod
    def clearClipboardText(cls):
        root = TurtleUtils.activeRoot()
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.update()
        root.destroy()
        
    @classmethod
    def ensureObjectCollection(cls, itemList):
        result = itemList
        if not itemList or type(itemList) != core.ObjectCollection: 
            result = core.ObjectCollection.create()
            if isinstance(itemList, list):
                for item in itemList:
                    result.add(item)
            else:
                result.add(itemList)
        return result

    @classmethod
    def ensureList(cls, itemList):
        result = itemList
        if not itemList or type(itemList) != list: 
            result = []
            if hasattr(itemList, "__iter__"):
                for item in itemList:
                    result.append(item)
            elif hasattr(itemList, "count"):
                for i in range(itemList.count):
                    result.append(itemList[i])
            else:
                result.append(itemList)
        return result

    @classmethod
    def reverseVector(cls, vec:adsk.core.Vector3D) -> adsk.core.Vector3D:
        result = vec.copy()
        invMatrix = adsk.core.Matrix3D.create()
        invMatrix.setWithArray([-1,0,0,0,0,-1,0,0,0,0,-1,0,0,0,0,-1])
        result.transformBy(invMatrix)
        return result

    @classmethod
    def bbArea(cls, bb:adsk.core.BoundingBox3D) -> float:
        w = bb.maxPoint.x - bb.minPoint.x
        h = bb.maxPoint.y - bb.minPoint.y
        return w * h


# used to detect overrides - only hook up events if there is a handler implemented
def baseMethod(method):
  method.isBaseMethod = True
  return method

def hasOverride(method):
    return not hasattr(method, 'isBaseMethod')
    
