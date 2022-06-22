###############################################################################################################################
#
# Created by Russell-MDAP team March-September 2021
# 02_preprocess_cross_section.py
#
# "preprocess_cross_section" function used in step 2 in HydXS 
# input: wrangled dataframe from step 1 
# output: dataframe with subset of XSs 
# if HydXS: exclude weird XS via dR_excl
#         where the minimum of the XS is not in the river channel, the edges of the XS are removed
#         bottom of the river channel is within 10 rows/points of the field identifying river centre (RivCentre)
#
# example, used in HydXS: 
#     exclude = (239,242,374,647,648)
#     first = 1 
#     last = 648
#     window = 10       
#     centre = "RivCentre"
#     XSdata2 = preprocess_cross_section( XSdata1 , dR_first = first , dR_last = last , dR_cutoff=True , dR_centre = centre , dR_window = window , dR_excl = exclude )
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
def preprocess_cross_section(xs ,
                             dR_first  , dR_last  , dR_cutoff = True ,
                             dR_centre = "RivCentre" , dR_window = 10 , dR_excl = (0,9999)
                            ):
    # Take output from wrangle_cross_section()
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
#end preprocess_cross_section
    
    
#removes edge of XS where there is a minimum outside the river channel ---------------------------------------------------------
# required for HydXS to work - would ideally have some kind of coping calc within HydXS, but this is simpler for now
# run per XS, returns a subset of the XS
# used in preprocess_cross_section above
def XS_UseCentre ( xs , centre = "RivCentre" , window = 10 ):
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
        if (xs.loc[j,"x_sec_order"] <= leftMin) and (xs.loc[j,"POINT_Z"] < riverMin) :
            left = j
        if (xs.loc[j,"x_sec_order"] >= rightMin) and (xs.loc[j,"POINT_Z"] < riverMin) :
            right = j
            break
    #return full XS with new column True/False as to whether to include in HydXS model run
    xs["riverMin"] = riverMin
    xs["inXS"] = False
    for j in range(0,len(xs)):
        if xs.loc[j,"x_sec_order"] > left+1 and xs.loc[j,"x_sec_order"] < right+1 :
            xs.loc[j,"inXS"] = True
    return xs
#end XS_UseCentre


