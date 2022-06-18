
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
    def getTestData(self):
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
    def hole(self):
        return \
{
'CoordinateSystem':[
1.0,	0.0,	0.0,	0.0, # 0 - 3
0.0,	1.0,	0.0,	0.0, # 4 - 7
0.0,	0.0,	1.0,	0.0, # 8 - 11
0.0,	0.0,	0.0,	1.0
],
'Params':{
'slotLength':'d[10 mm]',
'wallThickness':'d[4 mm]',
'lipWidth':'d[1.5 mm]',
},
'PointBounds':[[1.247257,0.380654],	[3.179108,1.300142]],
'Points':[
[0.0,0.0,'f'],	[1.87257,1.300142],	[2.838496,1.041323],	[2.734968,0.654952],	[1.769042,0.913771], # 0 - 4
[1.247257,0.898292],	[3.179108,0.380654],	[2.213182,0.639473],	[2.355533,1.170732],	[1.73022,0.768883], # 5 - 9
[2.696145,0.510063]
],
'Chains':[
'XFLp4p1 XFLp1p2 XFLp2p3', # 0-2
'XFLp3p4', # 3
'xfLp5p6', # 4
'xFLp8p7', # 5
'xFLp4p9', # 6
'xFLp3p10', # 7
],
'Constraints':[
'PEc3c0',	'PEc1c2',	'MIp7c4',	'PEc5c3',	'COp9c4', # 0 - 4
'PEc6c4',	'COp10c4',	'PEc7c4',	'MIp8c1'
],
'Dimensions':[
'SLDp1p2e0d[slotLength]v[2.428976,1.238366]',	'SODc1c4d[lipWidth + wallThickness]v[3.021515,0.664548]',	'SODc3c4d[lipWidth]v[1.451067,1.021301]'
],
'Guideline':[[1.247257,0.898292],	[3.179108,0.380654],'c4','noFlip'],
'ProfileCentroids':[
[2.303769,0.977547]
],
'NamedProfiles':{
    'hole0':[0]
}
}

