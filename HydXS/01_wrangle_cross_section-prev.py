###############################################################################################################################
#
# created by Russell-MDAP team March-September 2021
# wrangle_cross_section.py
#
# "wrangle_cross_section" function used in step 1 HydXS 
# input: XSdata = cross section data
#      : requires the following column names: x_sec_id , POINT_X , POINT_Y , POINT_Z , Sort_Value 
#      : requires a centreline, 0 for all rows but the centre line row
#        this variable name can be anything and is specified in function call (here is "CurCentre")
# output: a dataframe with XS (many rows per XS) + XY point + DZ point + Distance 
#
# example, used in HydXS: 
#   XSdata1 = wrangle_cross_section(XSdata)
#
###############################################################################################################################


# importing libraries etc  ----------------------------------------------------------------------------------------------------
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.geometry import box
from shapely.geometry import LineString
from shapely.geometry import Point


# high-level wrangle_cross_section function ---------------------------------------------------------------------------------
def wrangle_cross_section(XSdata):
    xs = XSdata
    
    # add XY point geometry
    xs["PointXY"] = xs.apply(make_xs_point_xy,axis=1)
    
    # add distance
    # initialise output
    xs['Distance'] = 0.0
    # loop over unique values of x_sec_id (in case they are not sequential)
    for i in set(xs['x_sec_id']):
        xs_i = xs[xs['x_sec_id'] == i]
        xs_i = xs_distance(xs_i, sort_column="Sort_Value")
        xs.loc[xs['x_sec_id'] == i,'Distance'] = xs_i['Distance'].to_list()
    # add Distance-Depth points
    xs["PointDZ"] = xs.apply(make_xs_point_distZ,axis=1)

    return xs
#end wrangle_cross_section


# redefine points as XY or Distance-Z ------------------------------------------------------------------------------------------
# both used in wrangle_cross_section 
def make_xs_point_xy(x):
    return Point(x["POINT_X"],x["POINT_Y"])
def make_xs_point_distZ(x):
    return Point(x["Distance"],x["POINT_Z"])


# distancing function ----------------------------------------------------------------------------------------------------------
def xs_distance(xs,sort_column="index"):
#input is single cross section
    tempxs = xs.reset_index().sort_values(by=sort_column)
    #initialise
    tempxs['Distance'] = 0.00
    distance = 0.00
    #set distance for all but first point, which will be set to zero
    for i in range(1,len(tempxs)):
        #distance between this and last point
        temp = tempxs.loc[i,'PointXY'].distance(Point(tempxs.loc[i-1,'PointXY']))
        #cumulative
        distance += temp
        #assign
        tempxs.loc[i,'Distance'] = distance
    return tempxs
#end xs_distance 
