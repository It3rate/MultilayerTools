
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
'PointBounds':[[-6.393186,-4.883289],	[-1.349654,-1.799046]],
'Points':[
[0.0,0.0,'f'],	[-3.532641,-3.300626],	[-1.349654,-2.356632],	[-6.393186,-1.799046],	[-4.048336,-2.108083], # 0 - 4
[-3.532641,-3.300626],	[-6.019766,-4.883289]
],
'Chains':[
'xFLp1p2', # 0
'XFCp3v[0.524099]', # 1
'XFCp4v[0.252484]', # 2
'XFCp5v[0.738849]', # 3
'XFCp6v[3.353651]', # 4
],
'Constraints':[
'COp1p5'
],
'Guideline':[[-3.532641,-3.300626],	[-1.349654,-2.356632],'c0'],
'NamedProfiles':{
    'Test2':[4, 3, 5],
    'Outer':[1, 2, 0],
    'Circ':[6],
    'smallCircs':[4, 1, 3, 2, 5, 0]
}
}
