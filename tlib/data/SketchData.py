
class SketchData:
    
    @classmethod
    def loadData(cls, filename:str):
        f = open(filename, "r")
        result = f.read()
        f.close()
        return result

    @classmethod
    def saveData(cls, filename:str, data:str):
        f = open(filename, "w")
        f.write(data)
        f.close()

    @classmethod
    def getTestData(cls):
        return \
{
'CoordinateSystem':[
1.0,	0.0,	0.0,	0.0, # 0 - 3
0.0,	0.0,	1.0,	0.0, # 4 - 7
0.0,	-1.0,	0.0,	0.0, # 8 - 11
0.0,	0.0,	0.0,	1.0
],
'Params':{
},
'PointBounds':[[0.275,-2.739607],	[4.275,-0.389607]],
'Points':[
[0.0,0.0,'f'],	[3.0,-0.889607],	[4.275,-0.889607],	[1.0,-2.239607],	[0.275,-0.389607], # 0 - 4
[1.275,-0.889607],	[1.275,-1.964607],	[1.275,-2.239607],	[4.275,-0.389607],	[0.275,-0.889607], # 5 - 9
[1.0,-2.739607],	[3.0,-2.739607],	[1.0,-1.964607],	[1.0,-1.164607],	[1.275,-1.164607]
],
'Chains':[
'XFLp11p1 XFLp1p2 XFLp2p8 XFLp8p4 XFLp4p9 XFLp9p5 XFLp5p14 XFLp14p13 XFLp13p12 XFLp12p6 XFLp6p7 XFLp7p3 XFLp3p10 XFLp10p11', # 0-13
],
'Constraints':[
'VHc3',	'PEc4c3',	'PEc5c4',	'PEc6c5',	'PEc7c6', # 0 - 4
'PEc8c7',	'PEc9c8',	'PEc10c9',	'PEc11c8',	'PEc12c11', # 5 - 9
'PEc13c12',	'PEc0c13',	'PEc1c0',	'PEc2c3',	'EQc12c4', # 10 - 14
'CLc10c6',	'CLc1c5'
],
'Dimensions':[
'SLDp13p12e2d[8 mm]v[-0.654818,-1.812213]',	'SLDp4p9e2d[5 mm]v[-1.194238,0.549307]'
],
'Guideline':[[0.275,-0.389607],	[4.275,-0.389607],'c3','noFlip'],
'ProfileCentroids':[
[2.122632,-1.397903]
],
'NamedProfiles':{

}
}

    @classmethod
    def notches(cls):
        return \
{
'CoordinateSystem':[
0.0,	0.0,	1.0,	0.0, # 0 - 3
1.0,	0.0,	0.0,	0.0, # 4 - 7
0.0,	1.0,	0.0,	0.0, # 8 - 11
0.0,	0.0,	0.0,	1.0
],
'Params':{
'lipWidth':'d[1.5 mm]',
'wallThickness':'d[4 mm]',
'midThickness':'d[15 mm]',
},
'PointBounds':[[0.517059,0.477809],	[2.02521,3.086057]],
'Points':[
[0.0,0.0,'f'],	[1.004737,0.477809],	[0.517059,2.878782],	[1.537532,3.086057],	[1.567389,2.939058], # 0 - 4
[1.175394,2.859438],	[1.255015,2.467442],	[1.64701,2.547063],	[1.945589,1.07708],	[1.553593,0.997459], # 5 - 9
[1.633214,0.605463],	[2.02521,0.685084]
],
'Chains':[
'xFLp11p8 xfLp1p11 XFLp1p2 XFLp2p3 XFLp3p4 XFLp4p5 XFLp5p6 XFLp6p7 XFLp7p8', # 0-8
'XFLp8p9 XFLp9p10', # 9-10
],
'Constraints':[
'PEc3c2',	'PEc5c2',	'PEc6c5',	'PEc7c2',	'PEc8c5', # 0 - 4
'PEc9c8',	'PEc10c9',	'CLc10c6',	'EQc10c6',	'CLc8c4', # 5 - 9
'CLc8c0',	'PEc1c0',	'COp10c1'
],
'Dimensions':[
'SLDp3p4e0d[lipWidth]v[1.084278,2.682401]',	'SLDp9p10e0d[wallThickness]v[1.784042,0.881221]',	'SLDp7p8e0d[midThickness]v[1.706167,1.778391]',	'SLDp8p9e0d[wallThickness]v[1.635527,1.202963]'
],
'Guideline':['p1','p11','c1','noFlip'],
'ProfileCentroids':[

],
'NamedProfiles':{

}
}

    @classmethod
    def hole(cls):
        return \
{
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
[0.0,0.0,'f'],	[1.134416,2.69231],	[2.100342,2.433491],	[1.996814,2.04712],	[1.030888,2.305939], # 0 - 4
[0.509103,2.29046,'f'],	[2.440954,1.772822,'f'],	[1.475028,2.031641],	[1.617379,2.5629],	[1.513851,2.17653]
],
'Chains':[
'XFLp1p2 XFLp2p3 XFLp3p4 XFLp4p1', # 0-3
'xfLp5p6', # 4
'xFLp8p7 XFLp9p7', # 5-6
],
'Constraints':[
'PEc2c3',	'PEc0c1',	'MIp7c4',	'PEc5c2',	'MIp8c0', # 0 - 4
'PEc3c0',	'MIp9c2'
],
'Dimensions':[
'SODc0c4d[lipWidth + wallThickness]v[2.300702,2.070315]',	'SODc3c1d[slotLength]v[2.473555,2.591631]',	'SLDp9p7e0d[lipWidth]v[0.9997,2.275998]'
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
    def finger(cls):
        return \
{
'CoordinateSystem':[
1.0,	0.0,	0.0,	0.0, # 0 - 3
0.0,	0.0,	1.0,	0.0, # 4 - 7
0.0,	-1.0,	0.0,	0.0, # 8 - 11
0.0,	0.0,	0.0,	1.0
],
'Params':{
'slotLength':'d[10 mm]',
'wallThickness':'d[4 mm]',
},
'PointBounds':[[2.415458,-1.283541],	[3.485902,-0.631445]],
'Points':[
[0.0,0.0,'f'],	[2.415458,-0.898015],	[2.522086,-1.283541],	[3.485902,-1.016971],	[3.379274,-0.631445], # 0 - 4
[3.003994,-1.150256],	[2.897366,-0.76473],	[2.415458,-0.898015],	[3.379274,-0.631445]
],
'Chains':[
'XFLp1p2 XFLp2p3 XFLp3p4', # 0-2
'xFLp5p6', # 3
'xFLp7p8', # 4
],
'Constraints':[
'PEc1c0',	'MIp5c1',	'PEc3c1',	'COp1c4',	'COp4c4', # 0 - 4
'MIp6c4',	'PEc0c4',	'PEc2c4',	'COp7p1'
],
'Dimensions':[
'SLDp2p3e0d[slotLength]v[3.066506,-0.79905]',	'SLDp5p6e0d[wallThickness]v[2.70812,-0.792736]'
],
'Guideline':['p7','p8','c4','noFlip'],
'ProfileCentroids':[

],
'NamedProfiles':{

}
}







    @classmethod
    def getDefaultData(cls):
        return cls.finger()
