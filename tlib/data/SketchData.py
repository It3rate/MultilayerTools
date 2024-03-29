import os, math, re, ast, traceback
from enum import Enum
import adsk.core, adsk.fusion, adsk.cam
from ..TurtleUtils import TurtleUtils

f:adsk.fusion
core:adsk.core
f,core,app,ui = TurtleUtils.initGlobals()

class SlotKind(Enum):
    default = 0
    hole = 10
    holeLock = 11
    finger = 20
    fingerLock = 21
    fingerPunch = 22
    brace = 30
class Sketches(Enum):
    # new body op
    default = 0
    # cut ops 10-19
    offsetHole = 10
    edgeHole = 11
    edgeFilletHole = 12
    # join ops 20-29
    edgeFinger = 20
    edgeFilletFinger = 21
    edgeExtendFinger = 22
    edgePokeFinger = 23
    notches = 23
    # intersect ops 30-39
    # new component ops 40-49
    # new body op 50+


    @classmethod
    def normalOperationForDrawing(cls, drawingKind) -> f.FeatureOperations:
        result = f.FeatureOperations.NewBodyFeatureOperation
        kind = drawingKind.value
        if kind < 10:
            result = f.FeatureOperations.NewBodyFeatureOperation
        elif kind < 20:
            result = f.FeatureOperations.CutFeatureOperation
        elif kind < 30:
            result = f.FeatureOperations.JoinFeatureOperation
        elif kind < 40:
            result = f.FeatureOperations.IntersectFeatureOperation
        elif kind < 50:
            result = f.FeatureOperations.NewComponentFeatureOperation
        else:
            result = f.FeatureOperations.NewBodyFeatureOperation
    
        return result

class SketchData:
    
    def __init__(self,data:str):
        self.coordinateSystem :list[float] = None
        self.params :dict[str,str] = None
        self.pointBounds :list[tuple[float, float]] = None
        self.pointValues :list[tuple[float, float, str]] = None
        self.chainValues :list[str] = None
        self.constraintValues :list[str] = None
        self.dimensionValues :list[str] = None
        self.guideline :tuple[str,str, str, str] = None
        self.guidepoint :tuple[str] = None
        self.profileCentroids :tuple[float, float] = None
        self.namedProfiles :list[int] = None
        self.hasEncodedGuideline:bool = False
        self.hasEncodedGuidepoint:bool = False
        self.encStartGuideIndex:int = None
        self.encEndGuideIndex:int = None
        self.encStartGuidePoint:core.Point3D = None
        self.encEndGuidePoint:core.Point3D = None

        self.decodeSketchData(data)

    @classmethod
    def createFromFile(cls, filename:str):
        file = open(filename, "r")
        sData = file.read()
        file.close()
        if sData is None or not sData.startswith("{#Turtle Generated Data"):
            data = SketchData.getDefaultRawData()
        else:
            data = eval(sData)
        return cls(data)

    @classmethod
    def createFromClipboard(cls):
        clip = TurtleUtils.getClipboardText()
        if clip is None or not clip.startswith("{#Turtle Generated Data"):
            data = SketchData.getDefaultRawData()
        else:
            data = eval(clip)
        return cls(data)

    @classmethod
    def createFromNamed(cls, name:str):
        namedMethod = getattr(cls, name, None)
        if callable(namedMethod):
            data = namedMethod(cls)
        else:
            data = SketchData.getDefaultRawData()
        return cls(data)

    @classmethod
    def createFromBuiltIn(cls, kind:Sketches):
        if kind == Sketches.offsetHole:
            data = cls.offsetHole()
        elif kind == Sketches.edgeHole:
            data = cls.edgeHole()
        elif kind == Sketches.edgeFilletHole:
            data = cls.edgeFilletHole()
        elif kind == Sketches.edgeFinger:
            data = cls.edgeFinger()
        elif kind == Sketches.edgeFilletFinger:
            data = cls.edgeFilletFinger()
        elif kind == Sketches.edgeExtendFinger:
            data = cls.edgeExtendFinger()
        elif kind == Sketches.edgePokeFinger:
            data = cls.edgePokeLockFinger()
        elif kind == Sketches.notches:
            data = cls.notches()
        else:
            data = cls.getDefaultRawData()
        
        return cls(data)

    @classmethod
    def createFromData(cls, data:list):
        return cls(data)

    def decodeSketchData(self, data):
        self.orgStringData = data
        self.params = data["Params"] if "Params" in data else {}
        self.pointValues = data["Points"] if "Points" in data else []
        self.chainValues = data["Chains"] if "Chains" in data else []
        self.constraintValues = data["Constraints"] if "Constraints" in data else []
        self.dimensionValues = data["Dimensions"] if "Dimensions" in data else []
        self.guidelineValues = data["Guideline"] if "Guideline" in data else None
        self.guidepointValues = data["Guidepoint"] if "Guidepoint" in data else None
        self.profileCentroids = data["ProfileCentroids"] if "ProfileCentroids" in data else []
        self.namedProfiles = data["NamedProfiles"] if "NamedProfiles" in data else {}
        if self.guidelineValues:
            self.hasEncodedGuideline = True
        if self.guidepointValues:
            self.hasEncodedGuidepoint = True


    def parseIndexOnly(self, param):
        val = param[1:]
        return int(val)


    @classmethod
    def loadData(cls, filename:str):
        file = open(filename, "r")
        result = file.read()
        file.close()
        return result

    @classmethod
    def saveData(cls, filename:str, data:str):
        file = open(filename, "w")
        file.write(data)
        file.close()






    @classmethod
    def notches(cls):
        return \
{#Turtle Generated Data
'CoordinateSystem':[
1.0,	0.0,	0.0,	0.0, # 0 - 3
0.0,	1.0,	0.0,	0.0, # 4 - 7
0.0,	0.0,	1.0,	0.0, # 8 - 11
0.0,	0.0,	0.0,	1.0
],
'Params':{
'wallThickness':'d[4 mm]',
'lipWidth':'d[1.5 mm]',
'slotLength':'d[16 mm]',
'midThickness':'d[5 mm]',
},
'PointBounds':[[0.773588,0.477809],	[3.0,2.164327]],
'Points':[
[0.0,0.0,'f'],	[1.004737,0.477809,'f'],	[0.773588,1.909266],	[2.353127,2.164327],	[2.377039,2.016245], # 0 - 4
[1.982155,1.95248],	[2.04592,1.557595],	[2.440804,1.621361],	[2.520511,1.127755],	[2.125626,1.063989], # 5 - 9
[2.189391,0.669105],	[3.0,0.8]
],
'Chains':[
'XFLp9p10 XFLp8p9 XFLp7p8 XFLp6p7 XFLp5p6 XFLp4p5 XFLp3p4 XFLp2p3 XFLp1p2 xfLp1p11', # 0-9
],
'Constraints':[
'PEc7c8',	'PEc5c8',	'PEc4c5',	'PEc3c8',	'PEc2c5', # 0 - 4
'PEc1c2',	'PEc0c1',	'CLc0c4',	'CLc2c6',	'COp10c9', # 5 - 9
'PEc8c9',	'EQc4c0'
],
'Dimensions':[
'SLDp8p9e0d[wallThickness]v[2.309405,1.150052]',	'SLDp5p6e0d[wallThickness]v[2.087208,1.761623]',	'SLDp3p4e0d[lipWidth]v[1.877397,1.93553]',	'SLDp2p3e0d[slotLength]v[1.547447,1.956778]',	'SLDp7p8e0d[midThickness]v[2.369184,1.418186]'
],
'Guideline':['p1','p11','c9','noFlip'],
'ProfileCentroids':[

],
'NamedProfiles':{

}
}

    @classmethod
    def hole(cls):
        return \
{#Turtle Generated Data
'CoordinateSystem':[
1.0,	0.0,	0.0,	0.0, # 0 - 3
0.0,	0.0,	1.0,	0.0, # 4 - 7
0.0,	-1.0,	0.0,	0.0, # 8 - 11
0.0,	0.0,	0.0,	1.0
],
'Params':{
'slotLength':'d[16 mm]',
'wallThickness':'d[4 mm]',
},
'PointBounds':[[1.565922,-4.165594],	[4.460214,-3.190977]],
'Points':[
[0.0,0.0,'f'],	[1.565922,-3.190977],	[4.460214,-3.957327],	[2.239718,-3.369384],	[2.137334,-3.756059], # 0 - 4
[3.684034,-4.165594],	[3.786418,-3.778919],	[3.013068,-3.574152]
],
'Chains':[
'xfLp1p2', # 0
'XFLp4p5 XFLp5p6 XFLp3p6 XFLp3p4', # 1-4
],
'Constraints':[
'COp3c0',	'PEc4c0',	'PEc1c4',	'COp6c0',	'PEc2c0', # 0 - 4
'MIp7c3',	'MIp7c0'
],
'Dimensions':[
'SLDp4p5e0d[slotLength]v[2.903598,-4.031639]',	'SLDp5p6e0d[wallThickness]v[3.83367,-3.970938]'
],
'Guideline':['p1','p2','c0','noFlip'],
'ProfileCentroids':[
[2.961876,-3.767489]
],
'NamedProfiles':{

}
}

    @classmethod
    def offsetHole(cls):
        return \
{#Turtle Generated Data
'CoordinateSystem':[
1.0,	0.0,	0.0,	0.0, # 0 - 3
0.0,	1.0,	0.0,	0.0, # 4 - 7
0.0,	0.0,	1.0,	0.0, # 8 - 11
0.0,	0.0,	0.0,	1.0
],
'Params':{
'wallThickness':'d[4 mm]',
'lipWidth':'d[1.5 mm]',
'slotLength':'d[10 mm]',
},
'PointBounds':[[0.509103,1.772822],	[2.440954,2.69231]],
'Points':[
[0.0,0.0,'f'],	[1.134415,2.69231],	[2.100341,2.433491],	[1.996814,2.04712],	[1.030888,2.305939], # 0 - 4
[0.509103,2.29046,'f'],	[2.440954,1.772822,'f'],	[1.475028,2.031641],	[1.617378,2.5629],	[1.513851,2.17653]
],
'Chains':[
'XFLp2p3 XFLp3p4 XFLp4p1 XFLp1p2', # 0-3
'xfLp5p6', # 4
'xFLp8p7 xFLp9p7', # 5-6
],
'Constraints':[
'PEc1c2',	'PEc3c0',	'MIp7c4',	'PEc5c1',	'MIp8c3', # 0 - 4
'PEc2c3',	'MIp9c1'
],
'Dimensions':[
'SODc3c4d[lipWidth + wallThickness]v[2.437089,2.019286]',	'SODc2c0d[slotLength]v[2.86289,2.615331]',	'SLDp9p7e0d[lipWidth]v[1.090963,2.364511]'
],
'Guideline':['p5','p6','c4','noFlip'],
'ProfileCentroids':[
[1.565615,2.369715]
],
'NamedProfiles':{
    'hole0':[0]
}
}

    @classmethod
    def edgeHole(cls):
        return \
{#Turtle Generated Data
'CoordinateSystem':[
1.0,	0.0,	0.0,	0.0, # 0 - 3
0.0,	1.0,	0.0,	0.0, # 4 - 7
0.0,	0.0,	1.0,	0.0, # 8 - 11
0.0,	0.0,	0.0,	1.0
],
'Params':{
'wallThickness':'d[24 mm]',
},
'PointBounds':[[0.757969,0.284003],	[1.596632,2.684003]],
'Points':[
[0.0,0.0,'f'],	[0.757969,2.684003],	[1.596632,2.684003],	[1.596632,0.284003],	[0.757969,0.284003]
],
'Chains':[
'XFLp2p3 XFLp3p4 XFLp4p1 xFLp1p2', # 0-3
],
'Constraints':[
'VHc3',	'VHc0',	'VHc1',	'VHc2'
],
'Dimensions':[
'SODc3c1d[wallThickness]v[0.473736,1.246182]'
],
'Guideline':['p1','p2','c3','noFlip'],
'ProfileCentroids':[

],
'NamedProfiles':{

}
}


    @classmethod
    def edgeFilletHole(cls):
        return \
{#Turtle Generated Data
'CoordinateSystem':[
1.0,	0.0,	0.0,	0.0, # 0 - 3
0.0,	1.0,	0.0,	0.0, # 4 - 7
0.0,	0.0,	1.0,	0.0, # 8 - 11
0.0,	0.0,	0.0,	1.0
],
'Params':{
'wallThickness':'d[24 mm]',
},
'PointBounds':[[2.04115,0.300593],	[3.112026,2.700593]],
'Points':[
[0.0,0.0,'f'],	[2.150425,2.700593],	[3.012026,2.700593],	[3.012026,0.300593],	[3.012026,0.300593], # 0 - 4
[2.150425,0.300593],	[2.150425,0.300593],	[3.012026,2.600593],	[3.112026,2.700593],	[3.112026,2.600593], # 5 - 9
[2.150425,2.600593],	[2.04115,2.700162],	[2.050425,2.600593]
],
'Chains':[
'XFLp6p1 xFLp1p2 XFLp2p3', # 0-2
'XFLp4p5', # 3
'XFAp8v[3.041315,2.671304]p7p9', # 4
'XFAp10v[2.117777,2.67451]p11p12', # 5
],
'Constraints':[
'VHc3',	'VHc0',	'VHc2',	'TAc4c2',	'COp7c2', # 0 - 4
'TAc4c1',	'COp4p3',	'COp5p6',	'TAc5c0',	'COp10c0', # 5 - 9
'TAc5c1'
],
'Dimensions':[
'SODc1c3d[wallThickness]v[2.280897,1.333019]',	'SRDc4d[1 mm]v[3.077277,2.624332]',	'SRDc5d[1.00 mm]v[2.069705,2.615648]'
],
'Guideline':['p1','p2','c1','noFlip'],
'ProfileCentroids':[

],
'NamedProfiles':{

}
}



    @classmethod
    def edgeFinger(cls):
        return \
{#Turtle Generated Data
'CoordinateSystem':[
1.0,	0.0,	0.0,	0.0, # 0 - 3
0.0,	1.0,	0.0,	0.0, # 4 - 7
0.0,	0.0,	1.0,	0.0, # 8 - 11
0.0,	0.0,	0.0,	1.0
],
'Params':{
'wallThickness':'d[24 mm]',
},
'PointBounds':[[3.463447,0.284003],	[4.288074,2.684003]],
'Points':[
[0.0,0.0,'f'],	[3.463447,2.684003],	[4.288074,2.684003],	[4.288074,0.284003],	[3.463447,0.284003]
],
'Chains':[
'XFLp2p3 XFLp3p4 XFLp4p1 XFLp1p2', # 0-3
],
'Constraints':[
'VHc3',	'VHc0',	'VHc1',	'VHc2'
],
'Dimensions':[
'SODc1c3d[wallThickness]v[4.186312,2.038338]'
],
'Guideline':['p4','p3','c1','flip'],
'ProfileCentroids':[

],
'NamedProfiles':{

}
}


    @classmethod
    def edgeFilletFinger(cls):
        return \
{#Turtle Generated Data
'CoordinateSystem':[
1.0,	0.0,	0.0,	0.0, # 0 - 3
0.0,	1.0,	0.0,	0.0, # 4 - 7
0.0,	0.0,	1.0,	0.0, # 8 - 11
0.0,	0.0,	0.0,	1.0
],
'Params':{
'wallThickness':'d[24 mm]',
},
'PointBounds':[[2.232345,3.198654],	[3.232345,6.098654]],
'Points':[
[0.0,0.0,'f'],	[2.232345,3.198654,'f'],	[2.232345,5.698654],	[2.632345,6.098654],	[2.832345,6.098654], # 0 - 4
[3.232345,5.698654],	[3.232345,3.198654,'f'],	[2.632345,5.698654],	[2.832345,5.698654],	[2.232345,5.598654], # 5 - 9
[3.232345,5.598654],	[2.382345,5.608654],	[3.082345,5.608654],	[3.082345,5.598654],	[2.382345,5.598654]
],
'Chains':[
'XFLp1p2 XFLp6p1 XFLp5p6 XFAp5v[3.115188,5.981497]p4p8 XFLp3p4 XFAp3v[2.349502,5.981497]p2p7', # 0-5
'xFLp9p10', # 6
'XFLp12p13 XFLp13p14 XFLp14p11 XFLp11p12', # 7-10
],
'Constraints':[
'VHc0',	'VHc4',	'TAc5c0',	'TAc3c4',	'TAc5c4', # 0 - 4
'TAc3c2',	'EQc5c3',	'COp9c0',	'COp10c2',	'PEc6c2', # 5 - 9
'VHc10',	'VHc7',	'VHc8',	'VHc9',	'CLc8c6'
],
'Dimensions':[
'SRDc5d[4 mm]v[2.432344,5.898655]',	'SODc6c1d[wallThickness]v[1.66168,4.469859]',	'SODc6c4d[5 mm]v[1.732752,5.887185]',	'SODc9c0d[1.50 mm]v[2.302102,5.633102]',	'SODc7c2d[1.50 mm]v[3.154125,5.644182]'
],
'Guideline':['p1','p6','c1','flip'],
'ProfileCentroids':[
[2.732345,4.613203],	[2.732345,5.603654]
],
'NamedProfiles':{

}
}


    @classmethod
    def edgeExtendFinger(cls):
        return \
{#Turtle Generated Data
'CoordinateSystem':[
1.0,	0.0,	0.0,	0.0, # 0 - 3
0.0,	0.0,	1.0,	0.0, # 4 - 7
0.0,	-1.0,	0.0,	0.0, # 8 - 11
0.0,	0.0,	0.0,	1.0
],
'Params':{
'wallThickness':'d[14 mm]',
'shellThickness':'d[15 mm]',
},
'PointBounds':[[2.232345,3.198654],	[3.232345,7.998654]],
'Points':[
[0.0,0.0,'f'],	[2.232345,3.198654,'f'],	[2.232345,7.598655],	[2.632344,7.998654],	[2.832346,7.998654], # 0 - 4
[3.232345,7.598655],	[3.232345,3.198654,'f'],	[2.232345,7.498654],	[3.232345,7.498654],	[2.382345,7.523654], # 5 - 9
[3.082345,7.523654],	[3.082345,7.498654],	[2.382345,7.498654],	[2.832346,7.598655],	[2.632344,7.598655], # 10 - 14
[2.232345,4.598654],	[3.232345,4.598654],	[2.232345,6.098654],	[3.232345,6.098654]
],
'Chains':[
'XFAp3v[2.349502,7.881497]p2p14 XFLp3p4 XFAp5v[3.115188,7.881497]p4p13 XFLp5p6 XFLp6p1 XFLp1p2', # 0-5
'xFLp7p8', # 6
'XFLp11p12 XFLp12p9 XFLp9p10 XFLp10p11', # 7-10
'xFLp15p16', # 11
'xFLp17p18', # 12
],
'Constraints':[
'COp7c5',	'COp8c3',	'PEc6c3',	'VHc5',	'VHc1', # 0 - 4
'VHc9',	'VHc10',	'VHc7',	'VHc8',	'TAc0c5', # 5 - 9
'TAc2c1',	'TAc0c1',	'TAc2c3',	'EQc0c2',	'CLc7c6', # 10 - 14
'COp15c5',	'COp16c3',	'PEc11c3',	'COp17c5',	'COp18c3', # 15 - 19
'PEc12c3'
],
'Dimensions':[
'SRDc0d[4 mm]v[2.432345,7.798654]',	'SODc6c1d[5 mm]v[2.182266,7.740315]',	'SODc8c5d[1.50 mm]v[2.436533,7.629362]',	'SODc10c3d[1.50 mm]v[3.082345,7.518654]',	'SODc11c4d[wallThickness]v[1.774795,3.965611]', # 0 - 4
'SODc11c12d[shellThickness]v[1.876032,5.451411]',	'SODc6c12d[wallThickness]v[2.037587,6.561944]',	'SODc12c9d[wallThickness + 0.25 mm]v[2.093126,7.793123]'
],
'Guideline':['p1','p6','c4','flip'],
'ProfileCentroids':[
[2.732345,5.557892],	[2.732345,7.511154]
],
'NamedProfiles':{

}
}



    @classmethod
    def edgePokeLockFinger(cls):
        return \
{#Turtle Generated Data
'CoordinateSystem':[
1.0,	0.0,	0.0,	0.0, # 0 - 3
0.0,	1.0,	0.0,	0.0, # 4 - 7
0.0,	0.0,	1.0,	0.0, # 8 - 11
0.0,	0.0,	0.0,	1.0
],
'Params':{
'wallThickness':'d[2.8 mm]',
'shellThickness':'d[15 mm]',
'lipWidth':'d[3 mm]',
},
'PointBounds':[[5.987035,3.570218],	[6.737035,5.830218]],
'Points':[
[0.0,0.0,'f'],	[6.587035,3.570218,'f'],	[6.137035,3.570218,'f'],	[6.137035,3.850218],	[5.987035,3.850218], # 0 - 4
[5.987035,5.350218],	[6.082035,5.350218],	[6.082035,5.830218],	[6.642035,5.830218],	[6.642035,5.350218], # 5 - 9
[6.737035,5.350218],	[6.737035,3.850218],	[6.587035,3.850218],	[6.082035,5.730218],	[6.182035,5.830218], # 10 - 14
[6.542035,5.830218],	[6.642035,5.730218],	[6.137035,5.200218],	[6.587035,5.200218],	[6.587035,4.000218], # 15 - 19
[6.137035,4.000218],	[6.362035,4.000218],	[6.362035,3.570218],	[6.137035,4.600218],	[5.987035,4.600218], # 20 - 24
[6.182035,5.730218],	[6.542035,5.730218],	[6.082035,5.630218],	[6.642035,5.630218]
],
'Chains':[
'XFLp3p4 XFLp4p5 XFLp5p6 XFLp6p13 XFAp14v[6.111324,5.800929]p13p25 XFLp14p15 XFAp16v[6.612746,5.800929]p15p26 XFLp16p9 XFLp9p10 XFLp10p11 XFLp11p12 XFLp12p1 XFLp1p2 XFLp2p3', # 0-13
'XFLp19p20 XFLp20p17 XFLp17p18 XFLp18p19', # 14-17
'xFLp21p22', # 18
'xFLp23p24', # 19
'xFLp27p28', # 20
],
'Constraints':[
'COp7c3',	'COp7c5',	'COp8c5',	'COp8c7',	'PEc13c12', # 0 - 4
'PEc0c13',	'PEc1c12',	'PEc2c1',	'PEc3c2',	'PEc5c3', # 5 - 9
'PEc7c2',	'PEc8c7',	'PEc9c2',	'PEc10c9',	'PEc11c12', # 10 - 14
'VHc16',	'VHc17',	'VHc14',	'VHc15',	'VHc18', # 15 - 19
'VHc19',	'TAc3c4',	'TAc5c4',	'TAc5c6',	'TAc7c6', # 20 - 24
'EQc1c9',	'EQc8c2',	'EQc0c10',	'EQc4c6',	'MIp21c14', # 25 - 29
'MIp22c12',	'MIp23c15',	'MIp24c1',	'CLc8c2',	'COp27c3', # 30 - 34
'COp28c7',	'PEc20c7'
],
'Dimensions':[
'SLDp7p8e1d[wallThickness * 2]v[6.362035,5.830218]',	'SLDp2p3e2d[wallThickness]v[6.137035,3.710218]',	'SLDp4p5e2d[shellThickness]v[5.987035,4.600218]',	'SLDp3p4e1d[lipWidth / 2]v[6.062035,3.850218]',	'SRDc4d[1.00 mm]v[6.132035,5.780218]', # 0 - 4
'SLDp23p24e1d[lipWidth / 2]v[6.062035,4.600218]',	'SLDp21p22e2d[wallThickness + lipWidth / 2]v[6.362035,3.785218]',	'SODc2c20d[wallThickness]v[5.814884,5.530052]',	'SODc20c5d[2 mm]v[5.845338,5.769901]'
],
'Guideline':['p2','p1','c12','flip'],
'ProfileCentroids':[
[6.362035,4.752742],	[6.362035,4.600218]
],
'NamedProfiles':{

}
}






    @classmethod
    def getDefaultRawData(cls):
        return cls.edgeFilletFinger()
