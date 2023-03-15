###############################################################################################################################
#
# 03_BankFullDetection_NEW.py
#
# based on original deRosa BankFullDetection.py
# from: https://github.com/pierluigiderosa/BankFullDetection/blob/master/tools/BankElevationDetection.py
#
###############################################################################################################################
#
# to be run only in Python - not as a replacement for BankFullDetection.py in GIS add-in
#
###############################################################################################################################
#
# Amendments made by Russell-MDAP team March-September 2021
#
#   1. minor: introduced "def cmp" as more recent Python version(s) no longer have cmp as default
#   2. minor: replaced "is" with "==" for more recent Python version(s)
#   3. minor: removed code not used when used directly in Python (ie. not as GIS add-in)
#   4. minor: add elements to output to facilitate more detailed examination
#
#   5. minor: error trapping so runs aren't so manual (original code would error-out and cancel a whole run) 
#      : (original deRosa code, row 124+)
#        .    if len(deptsLM)>0:
#        .        max_loc_filtered = [i for i in range(len(HydDeptLM)) if HydDeptLM[i] >= minVdep] 
#        .        bankfullIndex = max_loc_filtered[0]
#        .        bankfullLine = WTable(polygonXSorig,deptsLM[bankfullIndex])
#        .        wdep=hdepth(polygonXSorig,deptsLM[bankfullIndex])
#        (change to)      
#        .    if len(deptsLM)>0:
#        .        max_loc_filtered = []      
#        .        for i in range(0,len(HydDeptLM)):
#        .            try:
#        .                if HydDeptLM[i] >= minVdep:
#        .                    max_loc_filtered.append(i) 
#        .            except TypeError:
#        .                pass 
#        .        if len(max_loc_filtered)>0:
#        .            bankfullIndex = max_loc_filtered[0]
#        .            bankfullLine = WTable(polygonXSorig,deptsLM[bankfullIndex])
#        .            wdep=hdepth(polygonXSorig,deptsLM[bankfullIndex])   
#        .        else: 
#        .            bankfullLine = WTable(polygonXSorig,depts[-1])
#        .            wdep=hdepth(polygonXSorig,depts[-1])
#
#   6. MAJOR: adjust for multi-polygons
#      : original deRosa appears to presume river channel is the only depression in the XS
#      : where there are more than one, the bottom point of the last depression appears to be selected as bankfull
#      : this has been corrected by "allow_multichannel=False" and only choosing the river containing the minimum depth
#        inserting the below code (after original code row 107)
#        .  if allow_multichannel ==False:
#        .      if wetArea.type == 'MultiPolygon':
#        .          for poly in wetArea:
#        .              if poly.bounds[1] == minY:
#        .                  wetArea = poly
#        .                  continue
#        .          wetPerimeter=wetArea.intersection(wetPerimeter)
#        .          wetWTLine = wetArea.intersection(wetWTLine)
#      : this creates issues if XS lowest point is not in the river - addressed by trimming the XS in pre-processing 
#
#   7. MAJOR: adjust for where largest wet area containing bankfull is not in the river channel
#      : original deRosa takes the bankfull calculated, and identifies the left and right bank according to the largest wet area
#      : this does not always give the correct answer, eg. a depression with a min<bankfull but which is not the river channel
#      : this has been corrected by changing 
#        from (original code row 159)
#        .            if wetPolygon.area > Area:
#        to (new code)
#        .            if wetPolygon.bounds[1] == minY:
#
#   8. MAJOR: original deRosa code permitted calculation of a bankfull that may intersect with the right or left XS boundary
#       : Russell-MDAP felt this was not appropriate as it was presuming information not available to make a judgement on
#       : it was difficult to integrate a change within the original deRosa mainFun to mitigate this, 
#         so instead the program that calls mainFun is set to check for this and re-run the code if the boundary is hit
#
#   9. MAJOR: variability of deRosa Bankfull output
#       : original deRosa spline_withR code uses a randomly selected smoothing parameter (spar)
#       : this means that for some XS the bankfull differs from one run to another
#       : the best way of mitigating this is to run the model a few times and look for the mode of the bankfull calculations
#       : this is handled in Russell-MDAP in the "deRosa_run" function deRosa_modelling.py and deRosa_output.py
#
#   10. NOTE: the extension to the polygon for purposes of calculating the hydraulic depth can be used as a parameter
#       : this code:
#        .    pointList.insert(0,(polygonXSorig.bounds[0],maxY+1))
#        .    pointList.append((polygonXSorig.bounds[2],maxY+1))
#       : original deRosa = 1m (ie. the addition to the maxY here)
#       : tested with 0.2m: suggested that the higher this extension the more smoothed the data that spline_withR uses ; 
#        so if more sensitive to in-river banks and kinks is required, use a smaller polygon extension (eg. 0.1m)
#
###############################################################################################################################
#
# input: pre-processed dataframe from step 2 
# uses: spline_withR (second critical deRosa element)
# output: tuple of values from modelling run
#
# if running over single XS, use the "HydXS_perXS " function in HydXS_modelling.py
# if running over a set of XS, use the "HydXS_run" function in HydXS_modelling.py
#
# example:  
#    dtemp = PointDZ , for single XS , from pre-processed data (ie. distance-depth points)
#    steps=200
#    minV=0.1
#    plot=False
#  var1, var2, var3, var4, var5, fig, spar = HydXS( dtemp, nVsteps=steps, minVdep=minV, create_plot=plot) 
#
###############################################################################################################################


# importing libraries etc  -----------------------------------------------------------------------------------------------------
from shapely.geometry import Polygon
from shapely.geometry import box
from shapely.geometry import LineString
import numpy as np
# specific library name  -----------------------------------------------------------------------------------------------------
from .spline_withR_NEW import runAlg as splineR


# underlying functions -------------------------------------------------------------------------------------------------------

def cmp(a, b):
    return bool(a > b) - bool(a < b)

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


# main HydXS function -------------------------------------------------------------------------------------------------------
#   pointList : the data for a single cross section, many rows, from pre-processed dataset
#   nVsteps : numeric : number of divisions the XS depths is divided into, for modelling against splineR
#   minVdep : meters : minimum hydraulic depth for bankful ; deRosa original = 1m ; MDAP amended = 0.2m
#   (new) allow_multichannel : boolean : True if replicating original deRosa; False if running MDAP amended
#   (new) create_plot : boolean : part of MDAP amendment, only use True if running single XS at a time
# OUTPUT: boundsOK[0],boundsOK[2],wetArea.bounds[1], wetArea.bounds[3], nchannel, fig, spar
# ie. LeftDistance(bank), RightDistance(bank), n/a, BankFull, nChannels, "-" or a graph, smoothing parameter from spline_withR 

def calc_hyd_outputs(pointList, dept, allow_multichannel=False):
    polygonXSorig = Polygon(pointList)
    borderXS = LineString(pointList)
    
    minY=polygonXSorig.bounds[1]
    maxY=polygonXSorig.bounds[-1]
    pointList.insert(0,(polygonXSorig.bounds[0],maxY+1))
    pointList.append((polygonXSorig.bounds[2],maxY+1))
    polygonXS = Polygon(pointList)
    wdep=hdepth(polygonXSorig,dept)
    wdepLine = WTable(polygonXSorig,dept)
    wetArea = polygonXS.intersection(wdep)
    wetPerimeter=borderXS.intersection(wdep)
    wetWTLine = wdepLine.intersection(polygonXS)
    #new HydXS code
    if allow_multichannel ==False:
        if wetArea.type == 'MultiPolygon':
            for poly in wetArea:
                if poly.bounds[1] == minY:
                    wetArea = poly
                    continue
            wetPerimeter=wetArea.intersection(wetPerimeter)
            wetWTLine = wetArea.intersection(wetWTLine)
    #end new HydXS code
    HydRad = wetArea.area/wetPerimeter.length
    HydDept = wetArea.area/wetWTLine.length
    width = wetWTLine.length
    return HydDept, HydRad, width 


def mainFun( pointList, nVsteps=200, minVdep=0.1, allow_multichannel=False, create_plot=False ):
    
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
        #new HydXS code
        if allow_multichannel ==False:
            if wetArea.type == 'MultiPolygon':
                try:
                    for poly in list(wetArea.geoms):
                        if poly.bounds[1] == minY:
                            wetArea = poly
                            break
                except Exception as e:
                    import pdb; pdb.set_trace()
                wetPerimeter=wetArea.intersection(wetPerimeter)
                wetWTLine = wetArea.intersection(wetWTLine)
        #end new HydXS code
        HydRad = np.append(HydRad,wetArea.area/wetPerimeter.length)
        HydDept = np.append(HydDept,wetArea.area/wetWTLine.length)
    deptsLM, HydDeptLM , spar , fit  = splineR(depts,HydDept)
    
    if len(deptsLM)>0:
        max_loc_filtered = []      
        #amended HydXS code
        for i in range(0,len(HydDeptLM)):
            try:
                if HydDeptLM[i] >= minVdep:
                    max_loc_filtered.append(i) 
            except TypeError:
                pass 
        if len(max_loc_filtered)>0:
            bankfullIndex = max_loc_filtered[0]
            bankfullLine = WTable(polygonXSorig,deptsLM[bankfullIndex])
            wdep=hdepth(polygonXSorig,deptsLM[bankfullIndex])   
        else: 
            bankfullLine = WTable(polygonXSorig,depts[-1])
            wdep=hdepth(polygonXSorig,depts[-1])
        #end HydXS amendment
    else:
        bankfullLine = WTable(polygonXSorig,depts[-1])
        wdep=hdepth(polygonXSorig,depts[-1])     
    
    wetArea = polygonXS.intersection(wdep)
    boundsOK = ()
    Area = 0
    if wetArea.type == 'MultiPolygon':
        nchannel=str(len(list(wetArea.geoms)))
        for wetPolygon in list(wetArea.geoms):
            #if wetPolygon.area > Area:       #original deRosa code
            if wetPolygon.bounds[1] == minY:  #amended HydXS code
                Area = wetPolygon.area
                boundsOK = wetPolygon.bounds
    else:
        boundsOK = wetArea.bounds
        nchannel='1'
    
    #amended HydXS code
    if create_plot == True:
        import matplotlib.pyplot as plt
        plt.rcParams["figure.figsize"] = (10,10)
        fig, ax = plt.subplots(ncols = 2, sharey=True)
        ax[0].plot(*polygonXS.exterior.xy ,'k', label='cross section')
        ax[0].hlines(deptsLM[bankfullIndex], polygonXSorig.bounds[0], polygonXSorig.bounds[2],colors='red',linestyles='--',)
        ax[0].legend()
        ax[1].plot(HydDept, depts, label = 'actual')
        ax[1].plot(fit, depts, label = 'Rsmoothed')
        ax[1].hlines(deptsLM[bankfullIndex], min(HydDept), max(HydDept),colors='red',linestyles='--',label = 'bankfull est')
        ax[0].set_ylabel('elevation (m)')
        ax[0].set_xlabel('distance along xs (m)')
        ax[1].set_xlabel('hydraulic depth (m)')
        ax[1].legend()
        return boundsOK[0],boundsOK[2],wetArea.bounds[1], wetArea.bounds[3], nchannel, fig, spar
    else: 
        return boundsOK[0],boundsOK[2],wetArea.bounds[1], wetArea.bounds[3], nchannel, "-", spar
    #end HydXS amendment
       
#end mainFun
