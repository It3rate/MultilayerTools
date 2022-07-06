import os, math, re, ast, traceback
from enum import Enum
import adsk.core, adsk.fusion, adsk.cam
from ..TurtleUtils import TurtleUtils

f:adsk.fusion
core:adsk.core
f,core,app,ui = TurtleUtils.initGlobals()

class BuiltInDrawing(Enum):
    default = 0
    offsetHole = 1
    edgeHole = 2
    edgeFilletHole = 3
    edgeFinger = 4
    edgeFilletFinger = 5
    notches = 6

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
        self.profileCentroids :tuple[float, float] = None
        self.namedProfiles :list[int] = None
        self.hasEncodedGuideline:bool = False
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
    def createFromBuiltIn(cls, kind:BuiltInDrawing):
        if kind == BuiltInDrawing.offsetHole:
            data = cls.offsetHole()
        elif kind == BuiltInDrawing.edgeHole:
            data = cls.edgeHole()
        elif kind == BuiltInDrawing.edgeFilletHole:
            data = cls.edgeFilletHole()
        elif kind == BuiltInDrawing.edgeFinger:
            data = cls.edgeFinger()
        elif kind == BuiltInDrawing.edgeFilletFinger:
            data = cls.edgeFilletFinger()
        elif kind == BuiltInDrawing.notches:
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
        self.profileCentroids = data["ProfileCentroids"] if "ProfileCentroids" in data else []
        self.namedProfiles = data["NamedProfiles"] if "NamedProfiles" in data else {}
        if self.guidelineValues:
            self.hasEncodedGuideline = True


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
'XFLp2p3 xFLp3p4 XFLp4p1 XFLp1p2', # 0-3
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
'slotLength':'d[10 mm]',
'wallThickness':'d[24 mm]',
},
'PointBounds':[[2.232345,3.198654],	[3.232345,5.598654]],
'Points':[
[0.0,0.0,'f'],	[2.232345,3.198654],	[2.232345,5.498654],	[2.332345,5.598654],	[2.332345,5.498654], # 0 - 4
[3.132345,5.598654],	[3.232345,5.498654],	[3.132345,5.498654],	[3.232345,3.198654]
],
'Chains':[
'XFAp3v[2.261634,5.569364]p2p4 XFLp3p5 XFAp6v[3.203056,5.569364]p5p7 XFLp6p8 xFLp8p1 XFLp1p2', # 0-5
],
'Constraints':[
'VHc5',	'TAc0c5',	'TAc2c1',	'EQc0c2',	'TAc0c1', # 0 - 4
'TAc2c3',	'VHc1'
],
'Dimensions':[
'SODc4c1d[wallThickness]v[4.194711,4.130123]',	'SRDc0d[1 mm]v[2.188161,5.696191]'
],
'Guideline':['p1','p8','c4','flip'],
'ProfileCentroids':[

],
'NamedProfiles':{

}
}







    @classmethod
    def getDefaultRawData(cls):
        return cls.edgeFilletFinger()
