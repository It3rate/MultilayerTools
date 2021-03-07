
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
'PointBounds':[[-3.50557713,-6.20722084],	[-1.89092533,-4.71646049]],
'Points':[
[0.0,0.0,'f'],	[-3.46209913,-5.34898465],	[-3.01811582,-5.52130694],	[-2.65522536,-5.3246568],	[-2.03376054,-5.23117103], # 0 - 4
[-3.02419779,-6.1639677],	[-2.65928,-5.60037246],	[-3.16002829,-5.08137828],	[-2.53966806,-4.71646049],	[-1.89092533,-5.22531807], # 5 - 9
[-3.00249022,-6.20722084],	[-1.93857141,-5.23379767],	[-3.50557713,-5.39909461],	[-2.04194432,-5.29700697]
],
'Chains':[
'XFSs1|2|3|4e0', # 0
'XFSs5|6|7|8|9e0', # 1
'XFSs10|11e0', # 2
'XFSs12|13e0', # 3
],
'Constraints':[
'OFa1v[0.04839475]a2',	'OFa0v[0.06634264]a3'
],
'Dimensions':[
'SOCo0d[0.4839475235 mm]v[-2.62878718,-5.91081288]',	'SOCo1d[0.6634263551 mm]v[-2.45141547,-5.28056671]'
],
'Guideline':[],
'NamedProfiles':{

}
}
