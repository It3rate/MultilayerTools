
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
{
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
    def holeOutline(cls):
        return \
{
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
[0.0,0.0,'f'],	[1.565922,-3.190977,'f'],	[4.460214,-3.957327,'f'],	[2.239718,-3.369385],	[2.137334,-3.75606], # 0 - 4
[3.684034,-4.165594],	[3.786418,-3.778919],	[2.910684,-3.960827],	[3.013068,-3.574152]
],
'Chains':[
'xfLp1p2', # 0
'XFLp3p4 XFLp4p5 XFLp5p6', # 1-3
'xFLp7p8', # 4
],
'Constraints':[
'COp3c0',	'PEc1c0',	'PEc2c1',	'COp6c0',	'PEc3c0', # 0 - 4
'MIp7c2',	'MIp8c0',	'PEc4c0'
],
'Dimensions':[
'SLDp4p5e0d[slotLength]v[2.721045,-3.993624]',	'SLDp5p6e0d[wallThickness]v[3.708759,-4.056609]'
],
'Guideline':['p1','p2','c0','noFlip'],
'ProfileCentroids':[

],
'NamedProfiles':{

}
}




    @classmethod
    def finger(cls):
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
'wallThickness':'d[24 mm]',
},
'PointBounds':[[2.415458,-3.211172],	[4.019041,-0.631445]],
'Points':[
[0.0,0.0,'f'],	[2.415458,-0.898015],	[3.055226,-3.211172],	[4.019041,-2.944603],	[3.379274,-0.631445], # 0 - 4
[3.537134,-3.077887],	[2.897366,-0.76473],	[2.415458,-0.898015,'f'],	[3.379274,-0.631445,'f']
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
'SLDp2p3e0d[slotLength]v[3.176184,-2.505851]',	'SLDp5p6e0d[wallThickness]v[2.689405,-0.77777]'
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
