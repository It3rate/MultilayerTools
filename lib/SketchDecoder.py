
import adsk.core, adsk.fusion, adsk.cam, traceback
import os, math, re, ast
from collections.abc import Iterable
from .TurtleUtils import TurtleUtils
from .TurtleComponent import TurtleComponent
from .TurtleSketch import TurtleSketch
from .TurtleParams import TurtleParams
from .TurtlePath import TurtlePath
from .TurtleLayers import TurtleLayers

f,core,app,ui,design,root = TurtleUtils.initGlobals()

class SketchDecoder:
    def __init__(self, data, transform = core.Matrix3D.create(), flipX = False, flipY = False):
        self.sketch:f.Sketch = TurtleUtils.getTargetSketch(f.Sketch)
        if not self.sketch:
            return
        self.tcomponent = TurtleComponent.createFromSketch(self.sketch)
        self.tsketch = self.tcomponent.activeSketch
        self.tparams = TurtleParams.instance()

        # It doesn't make sense to map transforms, as the sketch transform in fusion isn't constant.
        # Tt will be based on where the camera is when entering the sketch, so just use identity, and allow flipping.
        self.transform = transform
        self.flipX = flipX
        self.flipY = flipY
        self.assessGuidelineTransform(data) # align to selected guideline

        self.decodeSketchData(data)
        self.decodeFromSketch()

        TurtleUtils.selectEntity(self.sketch)

        
    def decodeSketchData(self, data):
        self.params = data["Params"] if "Params" in data else {}
        self.pointValues = data["Points"] if "Points" in data else []
        self.chainValues = data["Chains"] if "Chains" in data else []
        self.constraintValues = data["Constraints"] if "Constraints" in data else []
        self.dimensionValues = data["Dimensions"] if "Dimensions" in data else []
        self.assessDimensionNames()

    def decodeFromSketch(self):
        self.offsetRefs = {}
        self.forwardExpressions = {}
        self.points = self.generatePoints(self.pointValues)
        self.curves = self.generateCurves(self.chainValues)
        self.constraints = self.generateConstraints(self.constraintValues)
        for name in self.params:
            self.addUserParam(name)

        self.dimensions = self.generateDimensions(self.dimensionValues)
    
    def addUserParam(self, name, currentDimIndex:int = -1):
        forwardRefs = []
        encoding = self.parseDParam(self.params[name], forwardRefs)
        if(len(forwardRefs) > 0):
            lastRef:int = forwardRefs[-1]
            if lastRef in self.forwardExpressions:
                self.forwardExpressions[lastRef].append(name)  
            else:
                self.forwardExpressions[lastRef] = [name]
        else:
            self.tparams.addParam(name, encoding)


    def assessDimensionNames(self):
        self.addedDimensions = []
        self.dimensionNameMap = []
        idx = 0
        for dim in self.dimensionValues:
            regex = re.compile("(?<![a-zA-Z0-9_])__" + str(idx) + "(?![a-zA-Z0-9_])")
            self.dimensionNameMap.append(regex)
            idx += 1

    def assessGuidelineTransform(self, data):
        gl = data["Guideline"] if "Guideline" in data else []
        guidePts = [self.asPoint3D(gl[0]),self.asPoint3D(gl[1])] if len(gl) > 1 else []
        cline:f.SketchLine = self.tsketch.getSingleConstructionLine()
        self.guideline = cline
        self.guideIndex = -1
        self.guideScale = 1.0
        if cline and len(guidePts) > 1:
            self.guideIndex = int(gl[2][1:])
            gl0 = guidePts[0]
            gl1 = guidePts[1]
            cl0 = cline.startSketchPoint.geometry
            cl1 = cline.endSketchPoint.geometry
            
            vc = core.Vector3D.create
            gVec = vc((gl1.x-gl0.x), (gl1.y - gl0.y), 0)
            destVec = vc((cl1.x-cl0.x), (cl1.y - cl0.y), 0)
            # adjust original encoded guideline to create flips
            gOrigin = gl1 if self.flipX else gl0
            gxVec = vc(-gVec.x, -gVec.y, 0) if self.flipX else gVec
            gyVec = vc(-gVec.y,gVec.x,0) if self.flipY else vc(gVec.y,-gVec.x,0)
            self.transform.setToAlignCoordinateSystems(
                gOrigin, 
                gxVec,
                gyVec,
                vc(0,0,1),
                cl0, 
                destVec,
                vc(destVec.y,-destVec.x,0),
                vc(0,0,1)
            )
            self.guideScale = destVec.length / gVec.length

        
    def generatePoints(self, ptVals):
        (origin, xAxis, yAxis, zAxis) = self.transform.getAsCoordinateSystem()
        self.hasRotation = xAxis.y != 0 or yAxis.x!= 0

        result = []
        idx = 0
        for pv in ptVals:
            isFixed = False
            if len(pv) > 2 and pv[2] == 'f':
                isFixed = True
                pv.pop()
                
            pt = self.asPoint3D(pv)
            if idx == 0 and pv[0] == 0 and pv[1] == 0:
                result.append(self.sketch.sketchPoints.item(0))
            else:
                result.append(self.sketch.sketchPoints.add(pt))

            result[-1].isFixed = isFixed
            
            idx += 1
        return result

    def generateCurves(self, chains):
        result = []
        sketchCurves = self.sketch.sketchCurves
        for chain in chains:
            segs = chain.split(" ")
            for seg in segs:
                # can't capture repeating groups with re, so max 4 params. Use pip regex to improve, but sticking with this for now. Could put it in a loop as well.
                parse = re.findall(r"([xX])([fF])([LACEOS])([pvase][0-9\[\]\.\-,|]*)([pvase][0-9\[\]\.\-,|]*)?([pvase][0-9\[\]\.\-,|]*)?([pvase][0-9\[\]\.\-,|]*)?", seg)[0]
                
                isConstruction = parse[0] == "x"
                isFixed = parse[1] == "f"
                kind = parse[2]
                params = self.parseParams(parse[3:])
                curve = None
                if kind == "L":
                    if self.guideIndex > -1 and len(result) == self.guideIndex:
                        # don't duplicate existing guideline
                        self.replacePoint(params[0], self.guideline.startSketchPoint)
                        self.replacePoint(params[1], self.guideline.endSketchPoint)
                        curve = self.guideline
                    else:
                        curve = sketchCurves.sketchLines.addByTwoPoints(params[0], params[1])
                elif kind == "A":
                    curve = sketchCurves.sketchArcs.addByThreePoints(params[0], self.asPoint3D(params[1]), params[2])
                    if len(params) > 2:
                        self.replacePoint(params[3], curve.centerSketchPoint)
                elif kind == "C":
                    curve = sketchCurves.sketchCircles.addByCenterRadius(params[0], params[1][0] * self.guideScale)
                elif kind == "E":
                    curve = sketchCurves.sketchEllipses.add(params[0], self.asPoint3D(params[1]), self.asPoint3D(params[2]))
                elif kind == "O":
                    # seems there is no add for conic curves yet?
                    #curve = sketchCurves.sketchConicCurves.add()
                    pass
                elif kind == "S":
                    splinePoints = params[0]
                    if params[1] != 0: # check if closed
                        splinePoints.append(splinePoints[0])
                    pts = self.asObjectCollection(params[0])
                    curve = sketchCurves.sketchFittedSplines.add(pts)
                    fitPoints = curve.fitPoints
                    count = 0
                    for pt in params[0]:
                        self.replacePoint(pt, fitPoints.item(count))
                        # idx = self.points.index(pt)
                        # self.points[idx] = fitPoints.item(count)
                        # pt.deleteMe()
                        count += 1

                if curve:
                    curve.isConstruction = isConstruction
                    curve.isFixed = isFixed
                    result.append(curve)
        return result
    
    def replacePoint(self, orgPoint, newPoint):
        result = True
        try:
            idx = self.points.index(orgPoint)
            self.points[idx] = newPoint
            orgPoint.deleteMe()
        except:
            result = False
        return result

    def generateConstraints(self, cons):
        result = []
        constraints:f.GeometricConstraints = self.sketch.geometricConstraints
        index = 0
        for con in cons:
            constraint = None
            parse = re.findall(r"(VH|PA|PE|EQ|CC|CL|CO|MI|OC|OF|SY|SM|TA)([pcav][0-9|\[\]\.\-,]*)([pcav][0-9|\[\]\.\-,]*)?([pcav][0-9|\[\]\.\-,]*)?", con)[0]

            kind = parse[0]
            params = self.parseParams(parse[1:])
            p0 = params[0]
            p1 = params[1] if len(params) > 1 else None
            p2 = params[2] if len(params) > 2 else None
            try:
                if(kind == "VH"):
                    if not self.hasRotation: # don't set vert/horz if transforming with rotation
                        sp = p0.startSketchPoint.geometry
                        ep = p0.endSketchPoint.geometry
                        if(abs(sp.x - ep.x) < abs(sp.y - ep.y)):
                            constraint = constraints.addVertical(p0)
                        else:
                            constraint = constraints.addHorizontal(p0)
                elif(kind == "PA"):
                    constraint = constraints.addParallel(p0, p1)
                elif(kind == "PE"):
                    constraint = constraints.addPerpendicular(p0, p1)
                elif(kind == "EQ"):
                    constraint = constraints.addEqual(p0, p1)
                elif(kind == "CC"):
                    constraint = constraints.addConcentric(p0, p1)
                elif(kind == "CL"):
                    constraint = constraints.addCollinear(p0, p1)
                elif(kind == "CO"):
                    constraint = constraints.addCoincident(p0, p1)
                elif(kind == "MI"):
                    constraint = constraints.addMidPoint(p0, p1)
                elif(kind == "SY"):
                    constraint = constraints.addSymmetry(p0, p1, p2)
                elif(kind == "SM"):
                    constraint = constraints.addSmooth(p0, p1)
                elif(kind == "TA"):
                    constraint = constraints.addTangent(p0, p1)

                elif(kind == "OF"):
                    # offsets are weird, but this helps: https://forums.autodesk.com/t5/fusion-360-api-and-scripts/create-a-parametric-curves-offset-from-python-api/m-p/9391531
                    try:
                        c0 = p2[0]
                        if type(c0) == f.SketchCircle:
                            dirPoint = c0.geometry.center
                            dist = -abs(p1[0])
                        else:
                            dirPoint = c0.startSketchPoint.geometry
                            dist = abs(p1[0])
                        dirPoint.transformBy(self.transform)

                        #dirPoint = c0.geometry.center if type(c0) == f.SketchCircle else c0.startSketchPoint.geometry
                        oc = self.asObjectCollection(p0)
                        # the direction is set by the dirPoint geometry afaict, so distance is always positive relative to that
                        # this will generate new curves
                        offsetCurves = self.sketch.offset(oc, dirPoint, dist)

                        # now remove matching elements that were generated
                        for rc in p2:
                            for curve in offsetCurves:
                                if(TurtlePath.isEquivalentCurve(curve, rc, 0.01)):
                                    idx = self.curves.index(rc)
                                    self.curves[idx] = curve
                                    rc.deleteMe()
                                    break
                        self.offsetRefs[index] = self.sketch.parentComponent.modelParameters[self.sketch.parentComponent.modelParameters.count - 1]
                    except:
                        print('Failed:\n{}'.format(traceback.format_exc()))

            except:
                print("Unable to generate constraint: " + con)
            index += 1
        return result



    def generateDimensions(self, dims):
        dimensions:f.SketchDimensions = self.sketch.sketchDimensions
        idx = 0
        paramIndex = 0
        for dim in dims:
            dimension = None
            orientation = f.DimensionOrientations.AlignedDimensionOrientation
            parse = re.findall(r"(SLD|SOD|SAD|SDD|SRD|SMA|SMI|SCC|SOC)([pcvo][^pcvod]*|d\[[^\]]*\])([pcvoe][^pcvoed]*|d\[[^\]]*\])?([pcvoe][^pcvoed]*|d\[[^\]]*\])?([pcvoe][^pcvoed]*|d\[[^\]]*\])?([pcvoe][^pcvoed]*|d\[[^\]]*\])?", dim)[0]
            kind = parse[0]
            params = self.parseParams(parse[1:])
            p0 = params[0]
            p1 = params[1] if len(params) > 1 else None
            p2 = params[2] if len(params) > 2 else None
            p3 = params[3] if len(params) > 3 else None
            p4 = params[4] if len(params) > 4 else None

            if kind == "SLD": # SketchDistanceDimension
                if not self.isGuideline(p0, p1):
                    dimension = dimensions.addDistanceDimension(p0, p1, p2, self.asPoint3D(p4))
                    dimension.parameter.expression = p3
            elif kind == "SOD": # SketchOffsetDimension
                dimension = dimensions.addOffsetDimension(p0,p1,self.asPoint3D(p3))
                dimension.parameter.expression = p2
            elif kind == "SAD": # SketchAngularDimension
                midText = self.textPoint(p0, p1) # this must be mid centers as the quadrant dimensioned is based on the text postion.
                dimension = dimensions.addAngularDimension(p0,p1, midText)
                dimension.parameter.expression = p2
            elif kind == "SDD": # SketchDiameterDimension
                dimension = dimensions.addDiameterDimension(p0, self.asPoint3D(p2)) 
                dimension.parameter.expression = p1
            elif kind == "SRD": # SketchRadialDimension
                dimension = dimensions.addRadialDimension(p0, self.asPoint3D(p2))
                dimension.parameter.expression = p1
            elif kind == "SMA": # SketchEllipseMajorRadiusDimension
                dimension = dimensions.addEllipseMajorRadiusDimension(p0, self.asPoint3D(p2))
                dimension.parameter.expression = p1
            elif kind == "SMI": # SketchEllipseMinorRadiusDimension
                dimension = dimensions.addEllipseMinorRadiusDimension(p0, self.asPoint3D(p2))
                dimension.parameter.expression = p1
            elif kind == "SCC": # SketchConcentricCircleDimension
                dimension = dimensions.addConcentricCircleDimension(p0,p1,self.asPoint3D(p3))
                dimension.parameter.expression = p2
            elif kind == "SOC": # SketchOffsetCurvesDimension
                parameter = self.offsetRefs[p0]
                parameter.expression = p1
                
            self.addedDimensions.append(dimension)
            if idx in self.forwardExpressions:
                for name in self.forwardExpressions[idx]:
                    self.addUserParam(name)

            idx += 1

    def isGuideline(self, p0, p1):
        result = False
        if self.guideline:
            gl = self.guideline
            startMatch = gl.startSketchPoint == p0 or gl.startSketchPoint == p1
            endMatch = gl.endSketchPoint == p0 or gl.endSketchPoint == p1
            result = gl and startMatch and endMatch
        return result

    def encodeExpression(self, expr):
        result = expr
        for regPair in self.dimensionNameMap.values():
            result = regPair[0].sub(regPair[1], result)
        return result

    def textPoint(self, p0, p1 = None):
        if p1 == None:
            return core.Point3D.create(p0.x + 1,p0.y+1,0)
        else:
            g0 = TurtleSketch.getMidpoint(p0) if type(p0) == f.SketchLine else p0.geometry
            g1 = TurtleSketch.getMidpoint(p1) if type(p1) == f.SketchLine else p1.geometry
            distance = g0.distanceTo(g1)
            angle = -0.5 * math.pi
            offset = distance * 0.2
            mid = core.Point3D.create(g0.x + (g1.x - g0.x)/2.0, g0.y + (g1.y - g0.y)/2.0)
            x = mid.x + offset * math.cos(angle)
            y = mid.y + offset * math.sin(angle)
            return core.Point3D.create(x, y, 0)


    def parseParams(self, params):
        result = []
        for param in params:
            if not param == "":
                result.append(self.parseParam(param))
        return result

    def parseParam(self, param):
        result = None
        kind = param[0]
        val = param[1:]

        if kind == "p": # point
            result = self.points[int(val)]
        elif kind == "c": # curve
            result = self.curves[int(val)]
        elif kind == "e": # enum
            result = int(val)
        elif kind == "v": # array of values
            if val.startswith("["):
                result = ast.literal_eval(val) # self.parseNums(val)
            else:
                result = val
        elif kind == "d": # curve
            result = self.parseDParam(val)
        elif kind == "o": # object index (so far just used for tracking offset constraints)
            result = int(val)
        elif kind == "a": # list of curve indexes
            result = []
            idxs = val.split("|")
            for idx in idxs:
                result.append(self.curves[int(idx)])
        elif kind == "s": # list of point indexes (for splines)
            result = []
            idxs = val.split("|")
            for idx in idxs:
                result.append(self.points[int(idx)])
        return result

    def parseDParam(self, dParam:str,  forwardRefs = []):
        firstD = dParam.index('[') + 1
        result = dParam[firstD:-1] # strip the outsides of d[...] or [...]
        validIndex = len(self.addedDimensions)
        idx = 0
        for regex in self.dimensionNameMap:
            if regex.search(result):
                if validIndex > idx:
                    name = self.addedDimensions[idx].parameter.name
                    result = regex.sub(name, result)
                else:
                    forwardRefs.append(idx)
            idx += 1
        return result

    def asPoint3Ds(self, pts):
        result = []
        for pt in pts:
            result.append(self.asPoint3D(pt))
        return result

    def asPoint3D(self, pts):
        if isinstance(pts, Iterable):
            #tpts = [pts[0], pts[1], 0]
            pts.extend([0.0] * max(0, (3 - len(pts)))) # ensure three elements
            tpts = pts
        elif type(pts) == f.SketchPoint:
            tpts = [pts.geometry.x,pts.geometry.y,pts.geometry.z]
        result = core.Point3D.create(tpts[0], tpts[1], tpts[2])
        result.transformBy(self.transform)
        return result

    def asObjectCollection(self, items):
        result = core.ObjectCollection.create()
        for item in items:
            result.add(item)
        return result
