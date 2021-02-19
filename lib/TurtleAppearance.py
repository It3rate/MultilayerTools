
import adsk.core, adsk.fusion, traceback
from .TurtleUtils import TurtleUtils

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class TurtleAppearance(list):
    __useInstance = 'Use Instance'
    _instance = None

    def __init__(self, useInstance):
        self.appearances = self._generateAppearances()
        self.extend(self.appearances)
        self._thicknessMap = {}
        self._counter = 0

    @classmethod
    def instance(cls):
        if(cls._instance == None):
            cls._instance = TurtleAppearance(cls.__useInstance)
        return cls._instance

    def getAppearance(self, thickness):
       return self._thicknessMap[thickness] if thickness in self._thicknessMap else self._nextAppearance(thickness)

    def _nextAppearance(self, thickness):
        result = self.appearances[self._counter]
        self._thicknessMap[thickness] = result
        self._counter = min(len(self.appearances) - 1, self._counter + 1)
        return result

    def _generateAppearances(self):
        result = []
        colors = [
            "Plastic - Translucent Matte (Yellow)",
            "Plastic - Translucent Matte (Green)",
            "Plastic - Translucent Matte (Red)",
            "Plastic - Translucent Matte (Blue)",
            "Plastic - Translucent Matte (Gray)",
            "Plastic - Translucent Matte (White)",
        ]
        materialLib = app.materialLibraries.item(2).appearances
        for col in colors:
            appearance = materialLib.itemByName(col)
            appearance.copyTo(design)
            result.append(appearance)
        return result
    