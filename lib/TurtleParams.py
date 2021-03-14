
import adsk.core, adsk.fusion, traceback
import os, math, re, sys
from .TurtleUtils import TurtleUtils

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class TurtleParams:

    __useInstance = 'Use Instance'
    _turtleParamsInstance = None

    def __init__(self, useInstance, units:str="mm"):
        self.curUnits = units

    @classmethod
    def instance(cls, units:str="mm"):
        if(cls._turtleParamsInstance == None):
            cls._turtleParamsInstance = TurtleParams(cls.__useInstance, units)
        return cls._turtleParamsInstance

    def getValue(self, name):
        param = design.userParameters.itemByName(name)
        return "" if param is None else param.expression

    def addParams(self, *nameValArray):
        result = []
        for i in range(0, len(nameValArray), 2):
            result.append(self.addParam(nameValArray[i], nameValArray[i+1]))
        return result

    # Create parameter if it doesn't already exist
    def addParam(self, name, val, unitKind="", msg=""):
        units = self.curUnits if unitKind=="" else unitKind
        result = design.userParameters.itemByName(name)
        if result is None:
            fval = self.createValue(val, units)
            result = design.userParameters.add(name, fval, units, msg)
        return result

    # Create or change value of parameter
    def setParam(self, name, val, unitKind="", msg=""):
        units = self.curUnits if unitKind=="" else unitKind
        result = design.userParameters.itemByName(name)
        if not result:
            result = self.addParam(name, val, units, msg)
        else:
            result.expression = val
        return result

    def createValue(self, val, unitKind=""):
        units = self.curUnits if unitKind=="" else unitKind
        if isinstance(val, str):
            return core.ValueInput.createByString(val)
        elif isinstance(val, (int, float)):
            return core.ValueInput.createByString(str(val) + units)
        elif isinstance(val, bool):
            return core.ValueInput.createByBoolean(val)
        else:
            return core.ValueInput.createByObject(val)

    def getUserParams(self):
        result = {}
        for param in design.userParameters:
            result[param.name] = param.expression
        return result

    def printAllParams(self):
        for param in design.userParameters:
            print(param.name + ": " + param.expression)

    

