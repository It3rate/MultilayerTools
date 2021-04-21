
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
'mat0':'d[4.39 mm]',
'mat1':'d[5.95 mm]',
'extend':'d[10 mm]',
'halfShelfWidth':'d[100 mm]',
'lip':'d[mat1]',
},
'PointBounds':[[7.122,-10.0],	[11.473,1.0]],
'Points':[
[0.0,0.0,'f'],	[8.0,0.0],	[10.0,-0.0],	[7.122,-10.0],	[7.122,-1.473], # 0 - 4
[8.595,-1.473],	[8.595,1.0],	[10.595,1.0],	[10.595,0.0],	[10.0,-0.0], # 5 - 9
[10.0,-1.473],	[11.473,-1.473],	[11.473,-10.0],	[8.595,-0.0],	[8.595,0.875], # 10 - 14
[7.122,1.0],	[8.595,0.75],	[8.595,0.625],	[8.595,0.5],	[8.595,0.375], # 15 - 19
[8.595,0.25],	[8.595,0.125]
],
'Chains':[
'xFLp1p2', # 0
'XFLp6p7 XFLp7p8 XFLp8p9 XFLp9p10 XFLp10p11 XFLp11p12 XFLp12p3 XFLp3p4', # 1-8
'XFLp4p5 XFLp5p13', # 9-10
'XFLp4p15 XFLp15p6', # 11-12
'XFLp6p14', # 13
'XFLp16p17', # 14
'XFLp18p19', # 15
'XFLp20p21', # 16
],
'Constraints':[
'PEc9c8',	'PEc2c1',	'COp9c0',	'PEc4c3',	'PEc5c4', # 0 - 4
'PEc6c5',	'PEc8c7',	'PEc7c6',	'EQc5c9',	'COp9p2', # 5 - 9
'PAc0c1',	'CLc5c9',	'COp13c0',	'PEc10c0',	'PEc11c9', # 10 - 14
'PEc11c12',	'PEc13c12',	'CLc13c10',	'VHc13',	'VHc14', # 15 - 19
'VHc15',	'VHc16',	'CLc13c14',	'CLc13c15',	'CLc13c16'
],
'Dimensions':[
'SLDp10p11e1d[mat0 + mat1 + mat0]v[8.730857,-4.119561]',	'SODc5c3d[mat0 + mat1 + mat0]v[12.016011,-0.888105]',	'SLDp7p8e2d[extend]v[11.330606,0.698224]',	'SODc0c7d[halfShelfWidth]v[4.531937,-6.638582]',	'SLDp8p9e1d[lip]v[10.423964,-0.271658]', # 0 - 4
'SODc10p1d[lip]v[8.358185,-0.308645]',	'SLDp16p17e2d[extend / 8]v[8.691181,0.716807]',	'SLDp18p19e2d[extend / 8]v[8.660338,0.436305]',	'SLDp20p21e2d[extend / 8]v[8.70288,0.201576]',	'SLDp20p19e2d[extend / 8]v[8.477405,0.31275]', # 5 - 9
'SLDp18p17e2d[extend / 8]v[8.45507,0.555448]',	'SLDp14p16e2d[extend / 8]v[8.389717,0.837366]',	'SLDp21p13e2d[extend / 8]v[8.342767,0.087967]'
],
'Guideline':[[8.0,0.0],	[10.0,-0.0],'c0'],
'ProfileCentroids':[
[9.193806,-4.78018]
],
'NamedProfiles':{

}
}

