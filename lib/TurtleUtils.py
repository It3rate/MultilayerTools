import adsk.core, adsk.fusion, adsk.cam, traceback
import tkinter as tk

__decimalPlaces__ = 4

class TurtleUtils:
    def __init__(self):
        super().__init__()
        
    @classmethod
    def initGlobals(cls):
        global f
        global core
        global app
        global ui
        global design
        global root
        f = adsk.fusion
        core = adsk.core
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = f.Design.cast(app.activeProduct)
        root = f.Component.cast(design.rootComponent)
        return f,core,app,ui,design,root


    @classmethod
    def getTargetSketch(cls, selType, showMessage = True):
        result = None
        typeName = selType.__name__
        title = "Selection Required"
        if not design:
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
                    ui.messageBox('Selected object needs to be a ' + typeName + ". It is a " + str(type(selected)) + ".", title)

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
    def getClipboardText(cls):
        # f = open("sketchData.txt", "w")
        # f.write(result)
        # f.close()
        # command = 'type sketchData.txt | clip'
        # os.system(command)
        root = tk.Tk()
        root.withdraw()
        try:
            result = root.clipboard_get()
            # this clipboard is quite flakey, without this text can be on the clipboard but not detected
            cls.clearClipboardText()
            #cls.setClipboardText(result) 
        except tk.TclError:
            #print(traceback.format_exc())
            result = ""
        return result

    @classmethod
    def setClipboardText(cls, data):
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(data)
        root.update() # now it stays on the clipboard after the window is closed
        root.destroy()

    @classmethod
    def clearClipboardText(cls):
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.update()
        root.destroy()