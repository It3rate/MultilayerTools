
import adsk.core, adsk.fusion, adsk.cam, traceback
import os, math, re, sys
from collections.abc import Iterable
from .TurtleUtils import TurtleUtils
from .TurtleComponent import TurtleComponent
from .TurtleSketch import TurtleSketch
from .TurtleParams import TurtleParams
from .TurtlePath import TurtlePath
from .TurtleLayers import TurtleLayers

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class SketchEncoder:
    def __init__(self, sketch:f.Sketch = None, guideline:f.SketchLine = None):
        
        self.guideline = guideline
        self.autoGuideline = (sketch == None) # only autodetect guidelines if this isn't a UI command
        self.sketch:f.Sketch = sketch
        if not self.sketch:
            self.sketch = TurtleUtils.getTargetSketch(f.Sketch)
        if not self.sketch:
            return
        
        self.points = {}
        self.pointKeys = []
        self.pointValues = []
        self.curves = {}
        self.curveKeys = []
        self.curveValues = []
        self.chains = []
        self.constraints = {}
        self.dimensions = {}
        
        # python seems to not compare sys.float_info.min well
        self.bounds = [core.Point2D.create(float("inf"), float("inf")), core.Point2D.create(float("-inf"), float("-inf"))]
        self.offsetParams = []

        self.parseSketchData()
        self.encodeAll()
        TurtleUtils.selectEntity(self.sketch)

    def parseSketchData(self):
        os.system('cls')
        self.data = {}

        tparams = TurtleParams.instance()
        self.usedParams = []
        self.params = tparams.getUserParams()

        self.assessDimensionNames()

        self.parseAllPoints()
        self.pointKeys = list(self.points)
        self.pointValues = list(self.points.values())

        self.chains = self.parseAllChains()
        self.curveKeys = list(self.curves)
        self.curveValues = list(self.curves.values())

        self.parseAllConstraints()
        self.parseAllDimensions()


    def encodeAll(self):
        # need to remove all unused points?
        self.data["Params"] = self.params
        self.data["Points"] = self.pointValues
        self.data["Chains"] = self.chains
        self.data["Constraints"] = self.constraints.values()
        self.data["Dimensions"] = self.dimensions.values()

        result = "#Turtle Generated Data\n{\n"
        result += "\'CoordinateSystem\':" + self.encodeList(self.sketch.transform.asArray(), False, 4) + ",\n"
        result += "\'Params\':{\n" + self.encodeParams() + "},\n"
        result += "\'PointBounds\':[" + self.encodePoints(self.bounds[0], self.bounds[1]) + "],\n"
        result += "\'Points\':[\n" + self.encodePoints(*self.data["Points"]) + "\n],\n"
        result += "\'Chains\':[\n" + self.encodeChains(self.data["Chains"]) + "\n],\n"
        if len(self.data["Constraints"]) > 0:
            result += "\'Constraints\':" + self.encodeList(self.data["Constraints"]) + ",\n" #               [\n\'" + "\',\'".join(self.data["Constraints"]) + "\'\n],\n")
        if len(self.data["Dimensions"]) > 0:
            result += "\'Dimensions\':" + self.encodeList(self.data["Dimensions"]) + ",\n" #             [\n\'" + "\',\'".join(self.data["Dimensions"]) + "\'\n],\n")
        if self.guideline:
            result += "\'Guideline\':[" + self.encodePoints(self.guideline) + ",\'" + self.encodeEntity(self.guideline) + "\']\n"
        else: 
            result += "\'Guideline\':[]\n" 
        result += "}\n\n"


        TurtleUtils.setClipboardText(result)
        
        print(result)
        print("\n\nSketch data is now on clipboard.")
    
    def assessDimensionNames(self):
        self.dimensionNameMap = {}
        dimensions:f.SketchDimensions = self.sketch.sketchDimensions
        idx = 0
        for dim in dimensions:
            name = dim.parameter.name
            regex = re.compile("(?<![a-zA-Z0-9_])" + name + "(?![a-zA-Z0-9_])")
            self.dimensionNameMap[name] = [regex, "__" + str(idx)]

    def parseAllPoints(self):
        for point in self.sketch.sketchPoints:
            self.points[point.entityToken] = point
            if point.connectedEntities and point.connectedEntities.count > 0:
                if(point.geometry.x < self.bounds[0].x):
                    self.bounds[0].x = point.geometry.x
                if(point.geometry.y < self.bounds[0].y):
                    self.bounds[0].y = point.geometry.y
                if(point.geometry.x > self.bounds[1].x):
                    self.bounds[1].x = point.geometry.x
                if(point.geometry.y > self.bounds[1].y):
                    self.bounds[1].y = point.geometry.y


    def parseAllChains(self):
        tokens = []
        chains = []
        for line in self.sketch.sketchCurves:
            if not line.entityToken in tokens:
                chains.append(self.appendConnectedCurves(line, tokens))
        return chains

    def parseAllConstraints(self):
        for con in self.sketch.geometricConstraints:
            econ = self.encodeConstraint(con)
            if econ != "":
                self.constraints[con.entityToken] = econ

    def parseAllDimensions(self):
        for dim in self.sketch.sketchDimensions:
            edim = self.encodeDimension(dim)
            if edim != "":
                self.dimensions[dim.entityToken] = edim
    


    def appendConnectedCurves(self, baseLine:f.SketchLine, tokens:list):
        connected = self.sketch.findConnectedCurves(baseLine)
        result = []
        for curve in connected:
            self.curves[curve.entityToken] = curve
            result.append(len(self.curves) - 1)
            tokens.append(curve.entityToken)
        return result

    def findConnectedCurves(self, baseLine:f.SketchLine):
        connected = self.sketch.findConnectedCurves(baseLine)
        result = []
        for line in connected:
            result.append(line)
        return result

    def pointIndex(self, token):
        return self.pointKeys.index(token)

    def linePointIndexes(self, line:f.SketchLine):
        return [self.pointIndex(line.startSketchPoint.entityToken), self.pointIndex(line.endSketchPoint.entityToken)]

    def encodeCurve(self, curve:f.SketchCurve):
        result = ""
        tp = type(curve)
        result += "x" if curve.isConstruction else "X"
        result += "f" if curve.isFixed else "F"

        if tp is f.SketchLine:
            result += "L"  + self.encodeEntities(curve.startSketchPoint, curve.endSketchPoint)
            if self.autoGuideline and curve.isConstruction and not self.guideline:
                self.guideline = curve
        elif tp is f.SketchArc:
            pointOnLine = TurtleSketch.getMidpoint(curve)
            #return "A" + ctrn + self.encodeEntities(curve.centerSketchPoint, curve.startSketchPoint, curve.endSketchPoint) + self.encodeExpression(curve.geometry.endAngle)
            result += "A" + self.encodeEntities(curve.startSketchPoint) + self.encodeExpression(pointOnLine) + self.encodeEntities(curve.endSketchPoint, curve.centerSketchPoint) 
        elif tp is f.SketchCircle:
            result += "C" + self.encodeEntities(curve.centerSketchPoint) + self.encodeExpression(curve.radius)
        elif tp is f.SketchEllipse:
            result += "E" + self.encodeEntities(curve.centerSketchPoint, curve.majorAxisLine.startSketchPoint, curve.minorAxisLine.startSketchPoint)
        elif tp is f.SketchConicCurve:
            result += "O" + self.encodeEntities(curve.startSketchPoint, curve.apexSketchPoint, curve.endSketchPoint) + self.encodeExpressions(curve.length)
        elif tp is f.SketchFittedSpline:
            #note: control point splines are not supported, only fixed point splines work.
            result += "S" + self.encodeEntities(curve.fitPoints) + self.encodeEnum(curve.isClosed) 
        else: 
            print("*** Curve not parsed: " + str(tp))
        return result
    #  SketchConicCurve SketchEllipticalArc SketchFittedSpline SketchFixedSpline 

    def encodeConstraint(self, con:f.GeometricConstraint):
        result = ""
        tp = type(con)
        if(tp is f.VerticalConstraint or tp is f.HorizontalConstraint):
            result = "VH" + self.encodeEntity(con.line)
        elif(tp is f.ParallelConstraint):
            cCon:f.ParallelConstraint = con
            result = "PA" + self.encodeEntities(cCon.lineOne,cCon.lineTwo)
        elif(tp is f.PerpendicularConstraint):
            cCon:f.PerpendicularConstraint = con
            result = "PE" + self.encodeEntities(cCon.lineOne,cCon.lineTwo)
        elif(tp is f.EqualConstraint):
            cCon:f.EqualConstraint = con
            result = "EQ" + self.encodeEntities(cCon.curveOne,cCon.curveTwo)
        elif(tp is f.ConcentricConstraint):
            cCon:f.ConcentricConstraint = con
            result = "CC" + self.encodeEntities(cCon.entityOne,cCon.entityTwo)
        elif(tp is f.CollinearConstraint):
            cCon:f.CollinearConstraint = con
            result = "CL" + self.encodeEntities(cCon.lineOne,cCon.lineTwo)
        elif(tp is f.CoincidentConstraint):
            cCon:f.CoincidentConstraint = con
            result = "CO" + self.encodeEntities(cCon.point, cCon.entity)
        elif(tp is f.MidPointConstraint):
            cCon:f.MidPointConstraint = con
            result = "MI" + self.encodeEntities(cCon.point,cCon.midPointCurve)
        elif(tp is f.OffsetConstraint):
            cCon:f.OffsetConstraint = con
            result += "OF" + self.encodeEntities(cCon.parentCurves, cCon.distance, cCon.childCurves)
        elif(tp is f.SmoothConstraint):
            cCon:f.SmoothConstraint = con
            result = "SM" + self.encodeEntities(cCon.curveOne, cCon.curveTwo)
        elif(tp is f.SymmetryConstraint):
            cCon:f.SymmetryConstraint = con
            result = "SY" + self.encodeEntities(cCon.entityOne,cCon.entityTwo,cCon.symmetryLine)
        elif(tp is f.TangentConstraint):
            cCon:f.TangentConstraint = con
            result = "TA" + self.encodeEntities(cCon.curveOne, cCon.curveTwo)
        else:
            # not supported?
            # PolygonConstraint, RectangularPatternConstraint, CircularPatternConstraint
            print("*** Constraint not parsed: " + str(tp))
        return result


    def encodeDimension(self, dim:f.SketchDimension):
        result = ""
        tp = type(dim)
        parameter = self.encodeParameter(dim.parameter.expression)
        if(tp == f.SketchLinearDimension):
            tdim:f.SketchLinearDimension = dim # DistanceDimension
            result = "SLD" + self.encodeEntities(tdim.entityOne,tdim.entityTwo) + self.encodeEnum(tdim.orientation) + parameter + self.encodeExpressions(tdim.textPosition)

        elif(tp == f.SketchOffsetDimension):
            tdim:f.SketchOffsetDimension = dim
            result = "SOD" + self.encodeEntities(tdim.line,tdim.entityTwo) + parameter + self.encodeExpressions(tdim.textPosition)

        elif(tp == f.SketchAngularDimension):
            tdim:f.SketchAngularDimension = dim
            result = "SAD" + self.encodeEntities(tdim.lineOne,tdim.lineTwo) + parameter + self.encodeExpressions(tdim.textPosition)

        elif(tp == f.SketchDiameterDimension):
            tdim:f.SketchDiameterDimension = dim
            result = "SDD" + self.encodeEntities(tdim.entity) + parameter + self.encodeExpressions(tdim.textPosition)

        elif(tp == f.SketchRadialDimension):
            tdim:f.SketchRadialDimension = dim
            result = "SRD" + self.encodeEntities(tdim.entity) + parameter + self.encodeExpressions(tdim.textPosition)

        elif(tp == f.SketchEllipseMajorRadiusDimension):
            tdim:f.SketchEllipseMajorRadiusDimension = dim
            result = "SMA" + self.encodeEntities(tdim.ellipse) + parameter + self.encodeExpressions(tdim.textPosition)

        elif(tp == f.SketchEllipseMinorRadiusDimension):
            tdim:f.SketchEllipseMinorRadiusDimension = dim
            result = "SMI" + self.encodeEntities(tdim.ellipse) + parameter + self.encodeExpressions(tdim.textPosition)

        elif(tp == f.SketchConcentricCircleDimension):
            tdim:f.SketchConcentricCircleDimension = dim
            result = "SCC" + self.encodeEntities(tdim.circleOne,tdim.circleTwo) + parameter + self.encodeExpressions(tdim.textPosition)

        elif(tp == f.SketchOffsetCurvesDimension):
            tdim:f.SketchOffsetCurvesDimension = dim
            result = "SOC" + self.encodeEntities(tdim.offsetConstraint) + parameter + self.encodeExpressions(tdim.textPosition)

        else:
            print("*** Dimension not parsed: " + str(tp))

        return result

    def encodeList(self, items, asStrings = True, lineStep = 5):
        result = "[" if lineStep == 0 else "[\n"
        quote = "\'" if asStrings else ""
        comma = ""
        idx = 0
        for item in items:
            result += comma + quote + str(item) + quote
            comma = ",\t"
            idx += 1
            if lineStep > 0 and idx % lineStep == 0:
                comma = ", # " + str(idx - lineStep) + " - " + str(idx - 1) + "\n"
        result += "]" if lineStep == 0 else "\n]"
        return result

    def encodeParams(self):
        result = ""
        for key in self.usedParams:
            result += "\'" + key + "\':\'" + self.encodeParameter(self.params[key]) + "\'\n"
        return result

    def encodeParameter(self, expr:str):
        result = expr
        self.checkExpressionForUserParam(result)
        # convert internal dimension references to __index format
        for regPair in self.dimensionNameMap.values():
            result = regPair[0].sub(regPair[1], result)
        return "d[" + result + "]"

    # check if expression contains a user variable
    def checkExpressionForUserParam(self, expr:str):
        for pname in self.params:
            match = re.search("(?<![a-zA-Z0-9_])" + pname + "(?![a-zA-Z0-9_])", expr)
            if match and (not pname in self.usedParams):
                self.usedParams.append(pname)

    def encodeEntities(self, *points):
        result = ""
        if not points:
            return result

        if points:
            for pt in points:
                result += self.encodeEntity(pt)
        return result

    def encodeEntity(self, entity):
        result = ""
        if not entity:
            return result

        if entity in self.pointValues:
            result = "p" + str(self.pointValues.index(entity))
        elif entity in self.curveValues:
            result = "c" + str(self.curveValues.index(entity))
        elif type(entity) == f.SketchPointList: # splines
            result = "s"
            sep = ""
            for c in entity:
                result += sep + str(self.pointValues.index(c))
                sep = "|"
        elif isinstance(entity, Iterable): # curves
            result = "a"
            sep = ""
            for c in entity:
                result += sep + str(self.curveValues.index(c))
                sep = "|"
        elif type(entity) == f.OffsetConstraint:
            result = "o" + str(list(self.constraints).index(entity.entityToken))
        else:
            result = self.encodeExpression(entity)

        return result

    def encodeEnum(self, enumVal):
        return "e" + str(int(enumVal))

    def encodeExpressions(self, *expressions):
        result = ""
        if not expressions:
            return result

        for expr in expressions:
            result += self.encodeExpression(expr)
        return result

    def encodeExpression(self, expr):
        result = ""
        if not expr:
            return result

        tp = type(expr)
        result = "v"
        if tp is float or tp is int:
            result += "[" + TurtleUtils.round(expr) + "]"
        elif tp is f.ModelParameter:
            p = str(expr.expression)
            result += p
            for pname in self.params:
                match = re.search("(?<![a-zA-Z0-9_])" + pname + "(?![a-zA-Z0-9_])", p)
                if match and (not pname in self.usedParams):
                    self.usedParams.append(pname)
        else:
            result += self.encodePoint(expr)
        return result

    def encodePoints(self, *points, lineStep = 5):
        result = ""
        if not points:
            return result
        comma = ""
        idx = 0
        for pt in points:
            if type(pt) is f.SketchLine:
                result += comma + self.encodePoint(pt.startSketchPoint) + "," + self.encodePoint(pt.endSketchPoint) 
            else:
                result += comma + self.encodePoint(pt)
            comma=",\t"
            idx += 1
            if lineStep > 0 and idx % lineStep == 0:
                comma = ", # " + str(idx - lineStep) + " - " + str(idx - 1) + "\n"
        return result

    def encodePoint(self, pt:f.SketchPoint):  
        result = ""
        if not pt:
            return result
        tp = type(pt)
        x = 0.0
        y = 0.0
        isFixed = ""
        if tp is f.SketchPoint:
            x = pt.geometry.x
            y = pt.geometry.y
            if pt.isFixed:
                isFixed = ",\'f\'"
        elif tp is core.Point2D or tp is core.Vector2D:
            x = pt.x
            y = pt.y
        elif tp is core.Point3D or tp is core.Vector3D:
            x = pt.x
            y = pt.y # ignore z unless extending to 3D sketches
        
        result += "["+TurtleUtils.round(x)+","+TurtleUtils.round(y) + isFixed + "]"
        return result
        
    def encodeChains(self, chains):
        result = []
        if not chains:
            return result

        index = 0
        for chain in chains:
            startIndex = index
            s = "\'"
            comma = ""
            for curveIndex in chain:
                curve:f.SketchCurve = self.curveValues[curveIndex]
                s += comma + self.encodeCurve(curve)
                comma = " "
                index += 1
            rng = str(startIndex) + "-" + str(index - 1) if index - 1 > startIndex else str(startIndex)
            s += "\', # " + rng
            result.append(s)
        return "\n".join(result)
