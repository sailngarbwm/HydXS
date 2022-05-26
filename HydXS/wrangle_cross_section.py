###############################################################################################################################
#
# created by Russell-MDAP team March-September 2021
# wrangle_cross_section.py
#
# "wrangle_cross_section" function used in step 1 in deRosa and neural network 
# input: XS = cross section data
#      : requires the following column names: x_sec_id , POINT_X , POINT_Y , POINT_Z , Sort_Value 
#      : requires a centreline, 0 for all rows but the centre line row
#        this variable name can be anything and is specified in function call (here is "CurCentre")
# output: a dataframe with XS (many rows per XS) + ground truth (0/1) + training category + XY point + DZ point + Distance 
#
# example, used in deRosa: 
#   XSdata1 = wrangle_cross_section()
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
# specific library name  -----------------------------------------------------------------------------------------------------
from riv_extract.d00_data.dataset import create_original


# high-level wrangle_cross_section function  (n.b. takes about a minute to run)------------------------------------------------
def wrangle_cross_section(groundtruth='xs'):
    # import cross-section data
    original = create_original()
    xs_points = original.get_cross_section_points() # gets the cross section points

    # import ground truth polygons and train-test polygons
    ground_truth = original.get_ground_truth(groundtruth=groundtruth) 
    train_test = original.get_train_test_split_polygons() 
    
    # add test train
    xs = add_test_train(xs_points, train_test)
    
    # add ground truth
    xs = add_ground_truth(xs, ground_truth)
    
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

    # keep all columns
    # save to derived folder - TO DO

    return xs
#end wrangle_cross_section


# add test/train/validation categories  ----------------------------------------------------------------------------------------
# used in wrangle_cross_section 
def add_test_train(xs_points, train_test):
    # flag cross-section points as test, training, validation
    xs_points_train_test = gpd.sjoin(xs_points, train_test, how='left', op='within')
    # if a cross-section has mixed categories, assign to the most common one
    # note: 9 cross-sections are outside training/test data extent - they are ignored by this method
    xs_grouped = xs_points_train_test\
        .groupby(['x_sec_id','category'])[['category']]\
        .count()\
        .rename(columns={'category':'count'})\
        .reset_index()\
        .sort_values('count', ascending=False)\
        .drop_duplicates(subset=['x_sec_id'])\
        .drop('count', axis=1)
    # apply category by x_sec_id - drops cross-sections outside training/test data extent
    xs_points_train_test_by_xs = xs_points.merge(xs_grouped,on='x_sec_id')
    return xs_points_train_test_by_xs
#end add_test_train


# add ground truth data (1/0)  -------------------------------------------------------------------------------------------------
# used in wrangle_cross_section 
def add_ground_truth(xs_points, ground_truth):
    # if ground truth is point data, table join
    if ground_truth.geom_type[1] == "Point":
        xs_points_ground_truth = pd.merge(xs_points, ground_truth[['UNQID','KR_ischann']], how = 'left', on = 'UNQID')
        xs_points_ground_truth = xs_points_ground_truth.rename(columns = {"KR_ischann": "ground_truth"})
    # otherwise, use spatial join
    else:
        # if ground truth is linestring data, buffer ground truth lines by 0.05 m
        if ground_truth.geom_type[1] == "LineString":
            ground_truth = ground_truth.drop(['x_sec_id'], axis=1)
            ground_truth['geometry'] = ground_truth.buffer(0.05,resolution=16)
            ground_truth = ground_truth.dissolve()
        # add ground truth data
        xs_points_ground_truth = gpd.sjoin(xs_points, ground_truth, how='left', op='within')\
            .drop(['Shape_Leng', 'SHAPE_Leng', 'SHAPE_Area'], axis=1, errors='ignore')
        # set points within ground truth polygons to 1
        xs_points_ground_truth['ground_truth'] = xs_points_ground_truth['index_right']*0+1
    # set NaNs to 0
    index = xs_points_ground_truth[xs_points_ground_truth['ground_truth'].isna()].index
    xs_points_ground_truth.loc[index,'ground_truth'] = 0
    return xs_points_ground_truth
#end add_ground_truth


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


# create category for test -----------------------------------------------------------------------------------------------------
# used in wrangle_cross_section 
def split_test_train(xs_points_train_test_by_xs):
    # split dataset into test and non-test (assumes we don't need a validation set or will do cross-validation)
    xs_points_test = xs_points_train_test_by_xs[xs_points_train_test_by_xs['category'] == 'test']
    xs_points_train = xs_points_train_test_by_xs[xs_points_train_test_by_xs['category'] != 'test'] 
    return(xs_points_test, xs_points_train)
#end split_test_train


# create category for test and validation --------------------------------------------------------------------------------------
# used in wrangle_cross_section 
def split_test_train_validation(xs_points_train_test_by_xs):
    # split dataset into test, train and validation
    xs_points_test = xs_points_train_test_by_xs[xs_points_train_test_by_xs['category'] == 'test']
    xs_points_train = xs_points_train_test_by_xs[xs_points_train_test_by_xs['category'] == 'training'] 
    xs_points_validation = xs_points_train_test_by_xs[xs_points_train_test_by_xs['category'] == 'validation'] 
    return(xs_points_test, xs_points_train, xs_points_validation)
#end split_test_train_validation


# reverse the XS to test any left-to-right issues ------------------------------------------------------------------------------
# is similar to regular wrangle code above, but with some additional intermediate coding
def wrangle_cross_section_reverse(groundtruth='xs'):
    original = create_original()
    xs_points = original.get_cross_section_points() # gets the cross section points

    # import ground truth polygons and train-test polygons
    ground_truth = original.get_ground_truth(groundtruth=groundtruth) 
    train_test = original.get_train_test_split_polygons() 

    for i in range(1,max(xs_points["x_sec_id"])+1):
    
        dataset = xs_points[xs_points["x_sec_id"] == i].reset_index()
        dataset["Sort_Value_orig"] = dataset["Sort_Value"]
        
        dataset.sort_values(by=["Sort_Value"],inplace=True,ascending=False)
        dataset = dataset.drop(columns=["index"]).reset_index()
        
        maxsort = max(dataset["Sort_Value"])
        for j in range(0,maxsort):
            dataset.loc[j,"Sort_Value"] = maxsort - dataset.loc[j,"Sort_Value_orig"] + 1

        if i == 1:
            XSdata1r = dataset
        else:
            XSdata1r = XSdata1r.append(dataset)

    XSdata1r_start = XSdata1r.reset_index().drop(columns=["index","level_0"])

    # add test train
    xs = add_test_train(XSdata1r_start, train_test)
    # add ground truth
    xs = add_ground_truth(xs, ground_truth)
    # add XY point geometry
    xs["PointXY"] = xs.apply(make_xs_point_xy,axis=1)
    # add distance
    xs['Distance'] = 0.0
    # loop over unique values of x_sec_id (in case they are not sequential)
    for i in set(xs['x_sec_id']):
        xs_i = xs[xs['x_sec_id'] == i]
        xs_i = xs_distance(xs_i, sort_column="Sort_Value")
        xs.loc[xs['x_sec_id'] == i,'Distance'] = xs_i['Distance'].to_list()
    # add Distance-Depth points
    xs["PointDZ"] = xs.apply(make_xs_point_distZ,axis=1)

    XSdata1r = xs 
    return XSdata1r

#end wrangle_cross_section_reverse

