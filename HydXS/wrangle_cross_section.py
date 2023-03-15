###############################################################################################################################
#
# created by Russell-MDAP team March-September 2021
# wrangle_cross_section.py
#
# "wrangle_cross_section" function used in step 1 HydXS 
# input: *****to fill in
# output: a dataframe with XS (many rows per XS) + x_sec_id , x_sec_order , POINT_X , POINT_Y , POINT_Z + XY point + DZ point + Distance 
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
# # point_df is the cross-section dataframe, OR geopandas dataframe, OR path to a csv or GIS file
# # input_type : DF (dataframe) / GDF (geopandas dataframe) / CSV (path to CSV) / GIS (path to GIS)
# # xy_col : names of X and Y columns
# #   if dataframe, is a tuple of the names of the X and Y columns 
# #   if geopandas, then name of the XY 'geometry' column
# #   if CSV path, is a tuple of the names of the X and Y columns  
# # z_col : name of elevation column, eg. POINT_Z
# # xs_id_col : name of cross-section unique identifier column 
# # xs_order_col : name of column that sorts the points of the cross-section in order 
# # riv_centre : name of column that is TRUE/1 at river centre (only one value/row per cross-section)
# #           OR path to shapefile if 'point_df' is geopandas or path

def wrangle_cross_section( point_df , input_type='DF' , 
                            xy_col=('POINT_X','POINT_Y') , z_col='POINT_Z' , 
                            xs_id_col='x_sec_id' , xs_order_col='x_sec_order' , riv_centre='RivCentre'):
    
    # check consistency of data input
    if (input_type=='DF' and not type(point_df)==pd.DataFrame) or (input_type=='GDF' and not type(point_df)==GeoDataFrame) or (input_type=='CSV' and not (type(point_df)==str and point_df[-3:].upper()=="CSV")) or (input_type=='GIS' and not (type(point_df)==str and point_df[-3:].upper()=="GIS")):
        raise ValueError('mismatch between input_type and point_df')

    # bring in data
    if input_type in ('DF','GDF'):
        xs = pd.DataFrame(point_df)
    elif input_type == 'CSV':
        pass #to do
    elif input_type == 'GIS':
        pass #to do
    print(xs.head())
    xs['POINT_Z'] = pd.to_numeric(xs[z_col], errors = 'coerce')

    xs["x_sec_id"] = xs[xs_id_col]
    xs["x_sec_order"] = xs[xs_order_col]
    xs["RivCentre"] = xs[riv_centre]
#not complete if shape file

    # add XY point geometry
    if input_type == 'GDF':
        xs["PointXY"] = xs[xy_col]
    else:
        xs["POINT_X"] = pd.to_numeric(xs[xy_col[0]], errors = 'coerce')
        xs["POINT_Y"] = pd.to_numeric(xs[xy_col[1]], errors = 'coerce')
        
        xs["PointXY"] = xs.apply(make_xs_point_xy,axis=1)
    # add distance
    # initialise output
    xs["Distance"] = 0.0
    # loop over unique values of x_sec_id (in case they are not sequential)
    for i in set(xs[xs_id_col]):
        xs_i = xs[xs[xs_id_col] == i]
        xs_i = xs_distance(xs_i, sort_column=xs_order_col)
        xs.loc[xs[xs_id_col] == i,'Distance'] = xs_i['Distance'].to_list()
    # add Distance-Depth points
    xs["PointDZ"] = xs.apply(make_xs_point_distZ,axis=1)

    return xs[['x_sec_id','x_sec_order','POINT_X','POINT_Y','POINT_Z','PointXY','Distance','PointDZ','RivCentre']]
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
