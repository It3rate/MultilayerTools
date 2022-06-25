
import adsk.core, adsk.fusion, adsk.cam, traceback
import os, math, re, ast
from collections.abc import Iterable
from .TurtleUtils import TurtleUtils
from .TurtleSketch import TurtleSketch
from .TurtleParams import TurtleParams
from .TurtlePath import TurtlePath

f,core,app,ui = TurtleUtils.initGlobals()

class TurtleDecoder:

    def __init__(self, data:str, sketch:f.Sketch, reverse:bool = False, mirror:bool = False):
        self.data = data
        if sketch:
            self.sketch = sketch
            self.tsketch = TurtleSketch.createWithSketch(self.sketch)
        self.isReversed:bool = reverse
        self.isMirrored:bool = mirror

        self.parameters = TurtleParams.instance()

        self.transform:core.Matrix3D = core.Matrix3D.create()
        self.userGuideline:f.SketchLine = None
        self.userStartGuidePoint:core.Point3D = None
        self.userEndGuidePoint:core.Point3D = None

        self.hasEncodedGuideline = False
        self.encStartGuideIndex = -1
        self.encEndGuideIndex = -1
        self.encStartGuidePoint = None
        self.encEndGuidePoint = None      
        self.encGuideIndex = -1
        self.encGuideFlipped = False
        self.decodeSketchData(self.data)

    @classmethod
    def createWithSketch(cls, data, sketch:f.Sketch, reverse = False, mirror = False):
        decoder = TurtleDecoder(data, sketch, reverse, mirror)
        decoder.run()
        return decoder

    @classmethod
    def createWithGuidelines(cls, data, guidelines:list[f.SketchLine], reverse = False, mirror = False, callback = None):
        decoder = TurtleDecoder(data, None, reverse, mirror)
        for guideline in guidelines:
            decoder.sketch = guideline.parentSketch
            decoder.tsketch = TurtleSketch.createWithSketch(guideline.parentSketch)
            decoder.userGuideline = guideline
            decoder.userStartGuidePoint = guideline.startSketchPoint.geometry
            decoder.userEndGuidePoint = guideline.endSketchPoint.geometry
            decoder.run()
            if callback:
                callback(decoder)
        return decoder
    @classmethod
    def createWithPointChain(cls, data, sketch:f.Sketch, points:list[tuple[core.Point3D, core.Point3D]], reverse = False, mirror = False, callback = None):
        decoder = TurtleDecoder(data, sketch, reverse, mirror)
        for ptPair in points:
            decoder.userStartGuidePoint = ptPair[0]
            decoder.userEndGuidePoint = ptPair[1]
            decoder.run()
            if callback:
                callback(decoder)
        return decoder

    def run(self):
        self.sketch.isComputeDeferred = True
        self.transform.setToIdentity()
        # if self.userStartGuidePoint:
        #     self.userStartGuidePoint.isFixed = True
        # if self.userEndGuidePoint:
        #     self.userEndGuidePoint.isFixed = True

        self.assessTransform()
        self.decodeFromSketch()

        # if self.userStartGuidePoint:
        #     self.userStartGuidePoint.isFixed = False
        # if self.userEndGuidePoint:
        #     self.userEndGuidePoint.isFixed = False

        self.sketch.isComputeDeferred = False
        
    def assessTransform(self):
        if not self.userStartGuidePoint:
            self.userStartGuidePoint = self.encStartGuidePoint
        if not self.userEndGuidePoint:
            self.userEndGuidePoint = self.encEndGuidePoint

        if self.encStartGuidePoint and self.encEndGuidePoint:
            scale, originPoint = self.createTransformFromGuidePoints(\
                self.encStartGuidePoint, self.encEndGuidePoint, self.userStartGuidePoint, self.userEndGuidePoint)
            self.guideScale = scale
        
    def decodeSketchData(self, data = None):
        data = data if data else self.data
        self.params = data["Params"] if "Params" in data else {}
        self.pointValues = data["Points"] if "Points" in data else []
        self.chainValues = data["Chains"] if "Chains" in data else []
        self.constraintValues = data["Constraints"] if "Constraints" in data else []
        self.dimensionValues = data["Dimensions"] if "Dimensions" in data else []
        self.profileCentroids = data["ProfileCentroids"] if "ProfileCentroids" in data else []
        self.orgNamedProfiles = data["NamedProfiles"] if "NamedProfiles" in data else {}
        self.guidelineValues = self.data["Guideline"] if "Guideline" in self.data else None
        if self.guidelineValues:
            self.hasEncodedGuideline = True
             # needed for generating transform before points are generated
            self.encStartGuideIndex = self.parseIndexOnly(self.guidelineValues[0])
            self.encEndGuideIndex = self.parseIndexOnly(self.guidelineValues[1])
            self.encStartGuidePoint,_ = self.parsePoint(self.pointValues[self.encStartGuideIndex])
            self.encEndGuidePoint,_ = self.parsePoint(self.pointValues[self.encEndGuideIndex])
        self.addedDimensions = []
        self.dimensionNameMap = []
        idx = 0
        for dim in self.dimensionValues:
            regex = re.compile("(?<![a-zA-Z0-9_])__" + str(idx) + "(?![a-zA-Z0-9_])")
            self.dimensionNameMap.append(regex)
            idx += 1
        self.namedProfiles = self.orgNamedProfiles.copy()

    def decodeFromSketch(self):
        self.offsetRefs = {}
        self.forwardExpressions = {}
        self.sketchPoints = self.generatePoints(self.pointValues)
        self.curves = self.generateChains(self.chainValues)

        self.constraints = self.generateConstraints(self.constraintValues)
        for name in self.params:
            self.addUserParam(name)

        self.generateDimensions(self.dimensionValues) # added to self.addedDimensions
        self.profileMap = self.mapProfiles(self.profileCentroids)
    
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
            self.parameters.addOrGetParam(name, encoding)

    def createTransformFromGuidePoints(self, enc0:core.Point3D, enc1:core.Point3D, guide0:core.Point3D, guide1:core.Point3D):
            reverseVal = -1 if self.isReversed else 1
            mirrorVal = -1 if self.isMirrored else 1

            vc = core.Vector3D.create
            encVec = vc((enc1.x - enc0.x), (enc1.y - enc0.y), 0)
            guideVec = vc((guide1.x - guide0.x), (guide1.y - guide0.y), 0)

            gOrigin = guide1 if self.isReversed else guide0

            guideVec = vc(-guideVec.x, -guideVec.y * mirrorVal, 0)\
                 if self.isReversed else\
                 vc(guideVec.x, guideVec.y * mirrorVal, 0)

            gxVec = vc(guideVec.x, guideVec.y * mirrorVal, 0)
            gyVec = vc(guideVec.y, -guideVec.x * mirrorVal, 0)\
                if self.isReversed else\
                vc(-guideVec.y, guideVec.x * mirrorVal, 0)
                
            self.transform.setToAlignCoordinateSystems(
                enc0, 
                encVec,
                vc(encVec.y,encVec.x,0),
                vc(0,0,1),
                gOrigin, 
                gxVec,
                gyVec,
                vc(0,0,1)
            )
            scale = guideVec.length / encVec.length
            origin = self.tsketch.findPointAt(gOrigin)
            return (scale, origin)

        
    def parsePoint(self, pointVal:list[float]) -> tuple[core.Point3D, bool]:
        isFixed = False
        if len(pointVal) > 2 and pointVal[2] == 'f':
            isFixed = True
            pointVal.pop()
        pt = self.asTransformedPoint3D(pointVal)
        return (pt, isFixed)

    def generatePoints(self, ptVals, startIndex:int = 0, count:int = -1) -> list[f.SketchPoint]:
        (origin, xAxis, yAxis, zAxis) = self.transform.getAsCoordinateSystem()
        self.hasRotation = xAxis.y != 0 or yAxis.x!= 0

        result = []
        idx = startIndex
        for pv in ptVals:
            isFixed = False
            if len(pv) > 2 and pv[2] == 'f':
                isFixed = True
                pv.pop()
                
            pt = self.asTransformedPoint3D(pv)
            if idx == 0 and pv[0] == 0 and pv[1] == 0:
                result.append(self.sketch.sketchPoints.item(0))
            else:
                result.append(self.sketch.sketchPoints.add(pt))
            result[-1].isFixed = isFixed

            if idx == self.encStartGuideIndex or idx == self.encEndGuideIndex:
                result[-1].isFixed = True
                
            idx += 1
            if count > 0 and idx >= count:
                break
        return result
    
    def generateChains(self, chains):
        result = []
        self.pointChains = []
        sketchCurves = self.sketch.sketchCurves
        self.generatedCurves = []
        for chain in chains:
            segs = chain.split(" ")
            curPointChain = []
            self.pointChains.append(curPointChain)
            for seg in segs:
                try:
                    # can't capture repeating groups with re, so max 4 params. Use pip regex to improve, but sticking with this for now. Could put it in a loop as well.
                    parse = re.findall(r"([xX])([fF])([LACEOS])([pvase][0-9\[\]\.\-,|]*)([pvase][0-9\[\]\.\-,|]*)?([pvase][0-9\[\]\.\-,|]*)?([pvase][0-9\[\]\.\-,|]*)?", seg)[0]
                    
                    isConstruction = parse[0] == "x"
                    isFixed = parse[1] == "f"
                    kind = parse[2]
                    params = self.parseParams(parse[3:])
                    curve = None
                    if kind == "L":
                        curve = self.replaceLine(params[0], params[1]) # check for generated line match, add if present
                        if not curve: # else create line (normal path)
                            curve = sketchCurves.sketchLines.addByTwoPoints(params[0], params[1])
                    elif kind == "A":
                        curve = sketchCurves.sketchArcs.addByThreePoints(params[0], self.asTransformedPoint3D(params[1]), params[2])
                        if len(params) > 2:
                            self.replacePoint(params[3], curve.centerSketchPoint)
                    elif kind == "C":
                        curve = sketchCurves.sketchCircles.addByCenterRadius(params[0], params[1][0] * self.guideScale)
                    elif kind == "E":
                        curve = sketchCurves.sketchEllipses.add(params[0], params[1].geometry, params[2].geometry)
                        # merge auto generated guides and points with drawn ones, maybe do this in the encoder.
                        # note: the constraints will not be able to be reapplied, will result in warnings. Fix if too bothersome.
                        self.replacePoint(params[0], curve.centerSketchPoint)
                        self.generatedCurves.append(curve.majorAxisLine)
                        self.generatedCurves.append(curve.minorAxisLine)
                    elif kind == "O":
                        # seems there is no add for conic curves yet?
                        #curve = sketchCurves.sketchConicCurves.add()
                        pass
                    elif kind == "S":
                        splinePoints = params[0]
                        if params[1] != 0: # check if closed
                            splinePoints.append(splinePoints[0])
                        pts = TurtleUtils.ensureObjectCollection(params[0])
                        curve = sketchCurves.sketchFittedSplines.add(pts)
                        fitPoints = curve.fitPoints
                        count = 0
                        for pt in params[0]:
                            self.replacePoint(pt, fitPoints.item(count))
                            count += 1

                    if curve:
                        curve.isConstruction = isConstruction
                        curve.isFixed = isFixed
                        result.append(curve)

                        if len(curPointChain) == 0:
                            curPointChain.append(curve.startSketchPoint)
                        curPointChain.append(curve.endSketchPoint)

                        if curve != self.userGuideline:
                             curve.attributes.add("Turtle", "generated", str(len(result) - 1))
                except:
                    print(seg + ' Curve Generation Failed:\n{}'.format(traceback.format_exc()))
        return result
    
    def replaceLine(self, pt0, pt1):
        result = None
        for line in self.generatedCurves:
            if TurtlePath.isEquivalentLine(line, pt0, pt1):
                result = line
                self.replacePoint(pt0, line.startSketchPoint)
                self.replacePoint(pt1, line.endSketchPoint)
                break
            elif TurtlePath.isEquivalentLine(line, pt1, pt0):
                result = line
                self.replacePoint(pt1, line.startSketchPoint)
                self.replacePoint(pt0, line.endSketchPoint)
                break
        if result:
            self.generatedCurves.remove(result)
        return result

    def replacePoint(self, orgPoint, newPoint):
        result = True
        try:
            idx = self.sketchPoints.index(orgPoint)
            self.sketchPoints[idx] = newPoint
            orgPoint.deleteMe()
        except:
            print("Error replacing points:")
            TurtlePath.printPoints([orgPoint, newPoint])
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
                    if not self.hasRotation and not p0 == self.userGuideline: # don't set vert/horz if transforming with rotation
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
                        oc = TurtleUtils.ensureObjectCollection(p0)
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


    def mapProfiles(self, profileCentroids):
        if len(profileCentroids) != len(self.sketch.profiles):
            return
        # map data centroids to current transform, preserve data indexes
        dataCentroids = self.pt = self.asTransformedPoint3Ds(profileCentroids)
        # make indexed table of current sketch profile centroids
        # map two tables based on distance diff of centroids
        # adjust namedProfile indexes to reflect new sketch indexes. 
        # Convert to entity IDs rather than indexes if final parm transforms are too disruptive (if helpful)
        dataToSketchMap = [-1] * len(dataCentroids)
        logMinDists = []
        for sketchProfileIndex, profile in enumerate(self.sketch.profiles):
            centroid = profile.areaProperties().centroid
            minDist = 99999.0
            mapIndex = 0
            for i, dc in enumerate(dataCentroids):
                if dc:
                    dist = centroid.distanceTo(dc)
                    if dist < minDist:
                        mapIndex = i
                        minDist = dist
            dataToSketchMap[mapIndex] = sketchProfileIndex
            dataCentroids[mapIndex] = None
            logMinDists.append(minDist)
        
        self.namedProfiles = {}
        for key in self.orgNamedProfiles:
            mappedIndexes = []
            for index in self.orgNamedProfiles[key]:
                mappedIndexes.append(dataToSketchMap[index])
            self.namedProfiles[key] = mappedIndexes

        return dataToSketchMap

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
                    dimension = dimensions.addDistanceDimension(p0, p1, p2, self.asTransformedPoint3D(p4))
                    dimension.parameter.expression = p3
            elif kind == "SOD": # SketchOffsetDimension
                dimension = dimensions.addOffsetDimension(p0,p1,self.asTransformedPoint3D(p3))
                dimension.parameter.expression = p2
            elif kind == "SAD": # SketchAngularDimension
                midText = self.textPoint(p0, p1) # this must be mid centers as the quadrant dimensioned is based on the text postion.
                dimension = dimensions.addAngularDimension(p0,p1, midText)
                dimension.parameter.expression = p2
            elif kind == "SDD": # SketchDiameterDimension
                dimension = dimensions.addDiameterDimension(p0, self.asTransformedPoint3D(p2)) 
                dimension.parameter.expression = p1
            elif kind == "SRD": # SketchRadialDimension
                dimension = dimensions.addRadialDimension(p0, self.asTransformedPoint3D(p2))
                dimension.parameter.expression = p1
            elif kind == "SMA": # SketchEllipseMajorRadiusDimension
                dimension = dimensions.addEllipseMajorRadiusDimension(p0, self.asTransformedPoint3D(p2))
                dimension.parameter.expression = p1
            elif kind == "SMI": # SketchEllipseMinorRadiusDimension
                dimension = dimensions.addEllipseMinorRadiusDimension(p0, self.asTransformedPoint3D(p2))
                dimension.parameter.expression = p1
            elif kind == "SCC": # SketchConcentricCircleDimension
                dimension = dimensions.addConcentricCircleDimension(p0,p1,self.asTransformedPoint3D(p3))
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
        if self.userGuideline: 
            gl = self.userGuideline
            startMatch = gl.startSketchPoint == p0 or gl.startSketchPoint == p1
            endMatch = gl.endSketchPoint == p0 or gl.endSketchPoint == p1
            # gl = self.selectedGuideline
            # startMatch = gl.startSketchPoint.geometry.isEqualTo(p0) or gl.startSketchPoint.geometry.isEqualTo(p1) 
            # endMatch = gl.endSketchPoint.geometry.isEqualTo(p0) or gl.endSketchPoint.geometry.isEqualTo(p1) 
            notSame = startMatch != endMatch
            result = gl and startMatch and endMatch and notSame
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

    def parseIndexOnly(self, param):
        val = param[1:]
        return int(val)

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
            result = self.sketchPoints[int(val)]
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
                result.append(self.sketchPoints[int(idx)])
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

    def asTransformedPoint3Ds(self, pts):
        result = []
        for pt in pts:
            result.append(self.asTransformedPoint3D(pt))
        return result

    def asTransformedPoint3D(self, pts):
        if isinstance(pts, Iterable):
            pts.extend([0.0] * max(0, (3 - len(pts)))) # ensure three elements
            tpts = pts
        elif type(pts) == f.SketchPoint:
            tpts = [pts.geometry.x,pts.geometry.y,pts.geometry.z]
        result = core.Point3D.create(tpts[0], tpts[1], tpts[2])
        result.transformBy(self.transform)
        return result

    # todo: These only make sense with single paste or callbacks.
    def getPointByName(self, name:str) -> f.SketchPoint:
        return self.parseParam(name)

    def getPointByIndex(self, index:int) -> f.SketchPoint:
        return self.sketchPoints[index]

    def getLongestPointChain(self) -> list[f.SketchPoint]:
        result = None
        maxLen = 0
        for chain in self.pointChains:
            if len(chain) > maxLen:
                result = chain
                maxLen = len(chain)
        return result

