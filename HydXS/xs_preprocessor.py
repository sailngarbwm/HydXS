###############################################################################################################################
#
# Created by Russell-MDAP team March-September 2021
# preprocess_cross_section.py
#
# "preprocess_cross_section" function used in step 2 in deRosa and neural network 
# input: wrangled dataframe from step 1 
# output: dataframe with subset of XSs 
# if deRosa: exclude weird XS via dR_excl
#         where the minimum of the XS is not in the river channel, the edges of the XS are removed
#         bottom of the river channel is within 10 rows/points of the field identifying river centre (CurCentre)
#
# example, used in deRosa: 
#     exclude = (239,242,374,647,648)
#     first = 1 
#     last = 648
#     window = 10       
#     centre = "CurCentre"
#     XSdata2 = preprocess_cross_section( XSdata1 , model="deRosa" , dR_first = first , dR_last = last , dR_cutoff=True ,
#                                         dR_centre = centre , dR_window = window , dR_excl = exclude )
#
# this can be used to process one XS at a time, or a subset of XSs
#
###############################################################################################################################


# importing libraries etc  -----------------------------------------------------------------------------------------------------
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.geometry import box
from shapely.geometry import LineString
from shapely.geometry import Point


# high-level preprocessing function  -------------------------------------------------------------------------------------------
# prepared to enable more than one kind of pre-processing for cross-sections, but only deRosa has been developed so far
def preprocess_cross_section(xs , model , 
                             dR_first  , dR_last  , dR_cutoff = True ,
                             dR_centre = "CurCentre" , dR_window = 10 , dR_excl = (0,9999)
                            ):
    # TO DO: open from derived folder
    # For now - take xs, output from wrangle_cross_section()
       
    #if deRosa modelling
    if model == "deRosa":
        xs_df = pd.DataFrame(xs)
        dataset2 = pd.DataFrame()
        #cycle through each XS
        for i in range ( dR_first , dR_last+1 ):
            temp = xs_df[xs_df["x_sec_id"] == i].reset_index()
            if len(temp) == 0 or i in dR_excl :
                pass
            else:
                if dR_cutoff == True:
                    #cutting off the XS where minimum is not in the river centre
                    newdata = XS_UseCentre ( temp , dR_centre , dR_window )
                else:
                    #pass through whole XS untampered 
                    temp["inXS"] = True
                    newdata = temp
                if i == dR_first :
                    dataset2 = newdata
                else:
                    dataset2 = dataset2.append(newdata,ignore_index=True)
        return dataset2       
    #end DeRosa model coding
        
    # add slope, curvature, relative elevation and openness
    # initialise output
#     xs['Slope','Curvature'] = [0.0,0.0]
#     # loop over unique values of x_sec_id (in case they are not sequential)
#     for i in set(xs['x_sec_id']):
#         xs_i = xs[xs['x_sec_id'] == i]
#         xs_i = xs_distance(xs_i, sort_column="Sort_Value")
#         xs.loc[xs['x_sec_id'] == i,'Distance'] = xs_i['Distance'].to_list()

#end preprocess_cross_section
    
    
#removes edge of XS where there is a minimum outside the river channel ---------------------------------------------------------
# required for deRosa to work - would ideally have some kind of coping calc within deRosa, but this is simpler for now
# run per XS, returns a subset of the XS
# used in preprocess_cross_section above
def XS_UseCentre ( xs , centre = "CurCentre" , window = 10 ):
    #riverMin 
    riverMin = min(xs["POINT_Z"])
    for j in range(0,len(xs)):
        window_min = max ( 0 , j-window )
        window_max = min ( j+window+1 , len(xs) )
        #if not pd.isna(xs.loc[j,centre]) :
        if not xs.loc[j,centre] == 0 :
            little = xs[window_min:window_max]
            riverMin = min(little["POINT_Z"])
            break
    #there are some XS where the minimum depth is at more than one point along bottom
    group = []
    for j in range(0,len(xs)):
        if xs.loc[j,"POINT_Z"] == riverMin:
            group.append(j)
    leftMin = group[0]
    rightMin = group[-1]
    #now check which parts of XS to exclude
    left = 0
    right = len(xs)-1
    for j in range(0,len(xs)):
        if (xs.loc[j,"Sort_Value"] <= leftMin) and (xs.loc[j,"POINT_Z"] < riverMin) :
            left = j
        if (xs.loc[j,"Sort_Value"] >= rightMin) and (xs.loc[j,"POINT_Z"] < riverMin) :
            right = j
            break
    #return full XS with new column True/False as to whether to include in deRosa model run
    xs["riverMin"] = riverMin
    xs["inXS"] = False
    for j in range(0,len(xs)):
        if xs.loc[j,"Sort_Value"] > left+1 and xs.loc[j,"Sort_Value"] < right+1 :
            xs.loc[j,"inXS"] = True
    return xs
#end XS_UseCentre


#### NOTE: this was prepared as alternative to deRosa, but has not yet been used -----------
## rectagular smoothing --------------------------------------------------------------------------------------------------------
def xs_smoothing_rect(dataset, column, rolling_window):
#presumes an ordered dataset
    new_column = 'avg_' + column
    dataset[new_column] = dataset[column].rolling(rolling_window,center=True).mean() 
    return dataset
#end xs_smoothing_rect


#### NOTE: this was prepared as alternative to deRosa, but has not yet been used -----------
## new rectagular smoothing ----------------------------------------------------------------------------------------------------
# to allow for a window size in meters, not in number of points
def xs_smooth_rect_meters(dataset, column, distance_field, window_size): 
#input is single cross section
#requires dataset to have Distance field
    tempdata = dataset.reset_index()
    maxDistance = tempdata.loc[len(tempdata)-1,distance_field]
    new_column = 'avg_' + column + '_byMeters'
    rows = len(tempdata)-1
    #loop through for each row
    for i in range(0,rows) :
        #first determine which initial rows are to be ignored
        if ( tempdata.loc[i,distance_field] < (window_size/2) ) :
            pass
        #determine which of last rows in dataset are to be ignored
        elif ( (maxDistance - tempdata.loc[i,distance_field] ) < (window_size/2) ) :
            pass 
        else:
            #initialise set
            temp_set = []
            current_point = tempdata.loc[i,distance_field]
            #go through rows to find which are within window
            for j in range(0,rows):
                dist = abs( current_point - tempdata.loc[j,distance_field] )
                if dist < (window_size/2):
                    temp_set.append(tempdata.loc[j,column])
                if tempdata.loc[j,distance_field] > current_point + (window_size/2) :
                    break
            tempdata.loc[i,new_column] = sum(temp_set) / len(temp_set)
    return tempdata
#end xs_smooth_rect_meters


#### NOTE: this was prepared as alternative to deRosa, but has not yet been used -----------
# angle of openness ------------------------------------------------------------------------------------------------------------
def openness_xs(xs):
    xs['Up_Openness'] = 0.0 # initialise up-openness column
    xs['Down_Openness'] = 0.0 # initialise down-openness column

    # loop through each point in cross-section
    i = 0
    for i in range(0, len(xs)):

        #create new temp xs with x-axis centred at point i (so intercept = xs.iloc[i]['z'])
        xs_temp = xs[['Distance','Z']]
        xs_temp['Distance'] = xs_temp['Distance'] - xs.iloc[i]['Distance']

        # select segment left of i
        xs_temp_left = xs_temp.iloc[:i]

        # define lines to left of i - step through all and record the tangents
        j = 0
        mtangent_left_up = 0.0
        mtangent_left_down = 0.0
        for j in range(i):
            m = (xs_temp.iloc[i]['Z'] - xs_temp_left.iloc[j]['Z'])/(xs_temp.iloc[i]['Distance'] - xs_temp_left.iloc[j]['Distance'])
            xs_temp_left['linez'] = m * xs_temp_left['Distance'] + xs_temp.iloc[i]['Z']
            xs_temp_left['linedep'] = xs_temp_left['linez'] - xs_temp_left['Z']
            if min(xs_temp_left['linedep']) == 0:
                mtangent_left_up = m
            elif max(xs_temp_left['linedep']) == 0:
                mtangent_left_down = m

        # select segment right of i
        xs_temp_right = xs_temp.iloc[(i+1):len(xs_temp)]

        # define lines to right of i - step through all and record the tangents
        j = 0
        mtangent_right_up = 0.0
        mtangent_right_down = 0.0
        for j in range(len(xs_temp_right)):
            m = (xs_temp_right.iloc[j]['Z'] - xs_temp.iloc[i]['Z'])/(xs_temp_right.iloc[j]['Distance'] - xs_temp.iloc[i]['Distance'])
            xs_temp_right['linez'] = m * xs_temp_right['Distance'] + xs_temp.iloc[i]['Z']
            xs_temp_right['linedep'] = xs_temp_right['linez'] - xs_temp_right['Z']
            if min(xs_temp_right['linedep']) == 0:
                mtangent_right_up = m
            elif max(xs_temp_right['linedep']) == 0:
                mtangent_right_down = m

        # fill in openness columns with up and down openness in radians
        xs.loc[i, 'Up_Openness'] = np.pi - np.arctan(-1*mtangent_left_up) - np.arctan(mtangent_right_up)
        xs.loc[i, 'Down_Openness'] = np.pi + np.arctan(-1*mtangent_left_down) + np.arctan(mtangent_right_down)
    
    return xs
#end openness_xs


