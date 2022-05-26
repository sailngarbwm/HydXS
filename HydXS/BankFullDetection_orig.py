#!/usr/bin/env python
# coding: utf-8

# ## deRosa original code : tools / BankFullDetection.py
# 
# https://github.com/pierluigiderosa/BankFullDetection/blob/master/tools/BankElevationDetection.py
#

##------------------------------------------------------------------------------------------------------------------------
## changes required for Python 3 (original written in Python 2)
## 1. add : code uses a python function that no longer exists - so redefine here
def cmp(a, b):
    return bool(a > b) - bool(a < b)
## 2. REPLACED : is (with) ==
## 3. added more elements to mainFun output because we're not printing/graphing

##------------------------------------------------------------------------------------------------------------------------
## Tweak 1
# commented out code that appears not used
# commented out graphing code
## Tweak 2
# commented out terrace code because looks like not being used anywhere other than graphing
# remove all original deRosa commentary just for clarity
# error trapping, so runs aren't so manual
##


##------------------------------------------------------------------------------------------------------------------------


from shapely.geometry import Polygon
from shapely.geometry import box
from shapely.geometry import LineString
import numpy as np
   
from riv_extract.d03_modelling.deRosa.spline_withR_orig import runAlg as splineR

def WTable(polygon,h):
    minx, miny, maxx, maxy=polygon.bounds
    WTLine = LineString([(minx,h),(maxx,h)])
    return WTLine

def hdepth(polygon,h):
    minx, miny, maxx, maxy=polygon.bounds
    b = box(minx, miny, maxx, h)
    return b

def diff_n(Harray,locMax,dist):
    leftIndex = max(locMax-dist,0)
    rightIndex = min(locMax + dist, len(Harray)-1)
    lGrad = Harray[locMax] - Harray[leftIndex]
    rGrad = Harray[rightIndex] - Harray[locMax]
    if ((cmp(lGrad,0)>0) & (cmp(rGrad,0)<0) & (lGrad != rGrad)):
        return True
    else:
        return False

def local_maxmin(Harray):
    gradients=np.diff(Harray)
    maxima_num=0
    minima_num=0
    max_locations=[]
    min_locations=[]
    count=0
    ranks = []
    rank = 1
    for i in gradients[:-1]:
        count+=1
        if ((cmp(i,0)>0) & (cmp(gradients[count],0)<0) & (i != gradients[count])):
            maxima_num+=1
            max_locations.append(count)     
            while (diff_n(Harray,count,rank) and rank<len(Harray)):
                rank += 1
            ranks.append(rank)
        if ((cmp(i,0)<0) & (cmp(gradients[count],0)>0) & (i != gradients[count])):
            minima_num+=1
            min_locations.append(count)
    turning_points = {'maxima_number':maxima_num,'minima_number':minima_num,'maxima_locations':max_locations,'minima_locations':min_locations,
                      'maxima_ranks': ranks
    }  
    return turning_points

def mainFun(pointList,nVsteps=100,minVdep=1,Graph=0):
    
    polygonXSorig = Polygon(pointList)
    borderXS = LineString(pointList)
    
    minY=polygonXSorig.bounds[1]
    maxY=polygonXSorig.bounds[-1]
    pointList.insert(0,(polygonXSorig.bounds[0],maxY+1))
    pointList.append((polygonXSorig.bounds[2],maxY+1))
    polygonXS = Polygon(pointList)
    
    depts = np.linspace(minY+0.1, maxY-0.1, nVsteps)
    
    HydRad = np.array([])
    HydDept = np.array([])
    for dept in depts:
        wdep=hdepth(polygonXSorig,dept)
        wdepLine = WTable(polygonXSorig,dept)
        wetArea = polygonXS.intersection(wdep)
        wetPerimeter=borderXS.intersection(wdep)
        wetWTLine = wdepLine.intersection(polygonXS)
        HydRad = np.append(HydRad,wetArea.area/wetPerimeter.length)
        HydDept = np.append(HydDept,wetArea.area/wetWTLine.length)
    
    deptsLM, HydDeptLM , spar  = splineR(depts,HydDept)

    ##~TWEAK1 : looks like this is only used for graphing  
#     from scipy.interpolate import UnivariateSpline
#     splHydDept= UnivariateSpline(depts, HydDept)
#     splHydDept.set_smoothing_factor(spar)
#     HydDept_smth=splHydDept(depts)  
#     xfine = np.linspace(min(depts),max(depts),1000)
#     HydDept_smthfine= splHydDept(xfine)
    

    if len(deptsLM)>0:
        
#         max_loc_filtered = [i for i in range(len(HydDeptLM)) if HydDeptLM[i] >= minVdep] 
        ##~ Tweak 2 : add in error trapping here
        max_loc_filtered = []
        for i in range(0,len(HydDeptLM)):
            try:
                if HydDeptLM[i] >= minVdep:
                    max_loc_filtered.append(i) 
            except TypeError:
                pass 

#         bankfullIndex = max_loc_filtered[0]
#         bankfullLine = WTable(polygonXSorig,deptsLM[bankfullIndex])
#         wdep=hdepth(polygonXSorig,deptsLM[bankfullIndex])        
        ##~ Tweak 2: add error trap here
        if len(max_loc_filtered)>0:
            bankfullIndex = max_loc_filtered[0]
            bankfullLine = WTable(polygonXSorig,deptsLM[bankfullIndex])
            wdep=hdepth(polygonXSorig,deptsLM[bankfullIndex])   
        else: 
            bankfullLine = WTable(polygonXSorig,depts[-1])
            wdep=hdepth(polygonXSorig,depts[-1])
        ##~ 
        
    else:
        bankfullLine = WTable(polygonXSorig,depts[-1])
        wdep=hdepth(polygonXSorig,depts[-1])

        
    ##~TWEAK2 : looks like this is only used for graphing 
#     turning_points = local_maxmin(HydDept)
#     terrace = [] 
#     for i in range(len(turning_points['maxima_locations'])):
#         if turning_points['maxima_ranks'][i] == max(turning_points['maxima_ranks'])  :
#             terrace.append(turning_points['maxima_locations'][i])  
#     terraceIndex=terrace[0]
#     terraceLine=WTable(polygonXSorig,depts[terraceIndex])
#     tdep=hdepth(polygonXSorig,depts[terraceIndex])
#     tArea = polygonXS.intersection(tdep)
    ##~
 
    wetArea = polygonXS.intersection(wdep)
    boundsOK = ()
    Area = 0
    #if wetArea.type is 'MultiPolygon':   REPLACE
    if wetArea.type == 'MultiPolygon':
        nchannel=str(len(wetArea))
        for wetPolygon in wetArea:
            if wetPolygon.area > Area:
                Area = wetPolygon.area
                boundsOK = wetPolygon.bounds
    else:
        boundsOK = wetArea.bounds
        nchannel='1'
    
    if Graph == 1:
#         from matplotlib import pyplot
#         from descartes.patch import PolygonPatch
#         from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas     
#         fig = pyplot.figure(1, figsize=(4,3), dpi=300)
#         fig = pyplot.figure()
#         ax = fig.add_subplot(211)
#         ax.clear()
#         plot_line(ax,borderXS,'#6699cc')               # plot line of XS
#         plot_line(ax,bankfullLine,'#0000F5')           # plot hor line of bankfull
#         ax.set_title('Cross Section')
#         #if wetArea.type is 'MultiPolygon':    REPLACE
#         if wetArea.type == 'MultiPolygon':
#             for wetPolygon in wetArea:
#                 patch = PolygonPatch(wetPolygon, fc='#00FFCC', ec='#B8B8B8', alpha=0.5, zorder=2)
#                 ax.add_patch(patch)
#         else:
#             patch = PolygonPatch(wetArea, fc='#00FFCC', ec='#B8B8B8', alpha=0.5, zorder=2)
#             ax.add_patch(patch)   
#         ax = fig.add_subplot(212)
#         ax.clear()
#         ax.plot(depts,HydDept,'bo')
#         ax.plot(xfine,HydDept_smthfine)
#         ax.plot(deptsLM[bankfullIndex],HydDeptLM[bankfullIndex],'rs')
#         ax.set_title('hydraulic depth')     
#         canvas = FigureCanvas(fig)
#         canvas.updateGeometry()
         return canvas


    else:
#         filecsv = open("/tmp/test.csv","a")
#         filecsv.write(str(wetArea.bounds[2]-wetArea.bounds[0]))     #bankfull width
#         filecsv.write(',')                              
#         filecsv.write(nchannel)                     #n channels
#         filecsv.write(',')
#         filecsv.write(str(wetArea.area))                     #Area
#         filecsv.write(',')
#         filecsv.write(str(wetArea.length))                   #Perimeter
#         filecsv.write(',')
#         filecsv.write(str(wetArea.bounds[1]))                #min height
#         filecsv.write(',')
#         filecsv.write(str(wetArea.bounds[3]))                #min height
#         filecsv.write('\n')
        #return boundsOK[0],boundsOK[2] #,len(wetArea),wetArea.area, wetArea.length 
        #return boundsOK[0],boundsOK[2],wetArea.bounds[1], wetArea.bounds[3] 
        return boundsOK[0],boundsOK[2],wetArea.bounds[1], wetArea.bounds[3], nchannel 

    
def plot_coords(ax, ob,Ncolor):
    x, y = ob.xy
    ax.plot(x, y, 'o', color=Ncolor, zorder=1)

def plot_line(ax, ob,Ncolor):
    x, y = ob.xy
    ax.plot(x, y, color=Ncolor, alpha=0.7, linewidth=3, solid_capstyle='round', zorder=2)

def plot_lines(ax, ob,Ncolor):
    for line in ob:
        x, y = line.xy
        ax.plot(x, y, color=Ncolor, alpha=0.7, linewidth=3, solid_capstyle='round', zorder=2)

