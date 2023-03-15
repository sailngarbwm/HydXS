###############################################################################################################################
#
# created by Russell-MDAP team March-September 2021
# 03_deRosa_modelling.py
#
# "HydXS_run" function used in step 3  
# INPUT: pre-processed XS dataframe from step 2 
# OUTPUT: 
#   dataframe and .csv PER run, with one row per XS 
#       CrossSection / BankFull / LeftDistance / RightDistance / nChannels / spar / runs
#   AND single .csv for ALL runs, with one row per XS and 3 columns per run (n)
#       CrossSection / BankFull(n) / LeftDistance(n) / RightDistance(n) 
# results are then combined and exported into csv using HydXS_output.py
# example, used in HydXS: 
#     nVsteps = 200
#     minVdep = 0.2
#     maxr = 3         
#     nruns = 11       #make an odd number of runs, so mode is possible (if even, and split, then mode cannot be calc'd)
#     XSdata3 = HydXS_run( XSdata2, first,last, num_runs=nruns, output_path=path, maxrun=maxr, steps=nVsteps, minV=minVdep )
#
# a single XS can be run once by using 
#   HydXS1 = HydXS_perXS(XSdata2,641,641,maxrun=maxr,steps=nVsteps,minV=minVdep,plot=True)
#   print(HydXS1) 
#  the output will be the printed values and a graph
#
###############################################################################################################################


# importing libraries etc  ----------------------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from pathlib import Path
# specific library name  -----------------------------------------------------------------------------------------------------
from .BankFullDetection_NEW import mainFun as HydXS


# multiple runs of AMENDED Russell-MDAP HydXS Bankfull calculation , over single/multiple XSs---------------------------------
# INPUT : 
#   data = full dataframe from pre-processing step 
#   a : first XS identity, min = 1 , max = any number, if XS doesn't exist in "data" then the code will pass it over
#   b : last XS identity ; ie. this will run the Bankfull calculation over XSs a to b inclusive
#   num_runs : how many times to run the Bankfull calculation per XS ; to assess variability due to spar differences
#   boundary = False for AMENDED Russell-MDAP ; ie. does not permit bankfull that hits boundaries
#   maxrun = how many times to try a single XS calc if bankfull hits boundaries
# OUTPUT: 
#   dataframe and .csv PER run, with one row per XS 
#       CrossSection / BankFull / LeftDistance / RightDistance / nChannels / spar / runs
#   AND single .csv for ALL runs, with one row per XS and 3 columns per run (n)
#       CrossSection / BankFull(n) / LeftDistance(n) / RightDistance(n) 
# results are then combined and exported into csv using HydXS_output.py
def HydXS_run ( data , a,b, num_runs , output_path = None , boundary=False, maxrun=3, steps=200, minV=0.1 ):
    for k in range ( 1 , num_runs+1 ):
        print("run: " , k)
        #variable names
        run_name = "run_" + str(k)
        csv_name = output_path/("HydXS_run" + str(k) + ".csv")
        bankfull_name = "bankfull_" + str(k)
        left_name = "left_" + str(k)
        right_name = "right_" + str(k)
        #individual run
        model = HydXS_perXS(data,a,b,allow_boundary=boundary,maxrun=maxrun,steps=steps,minV=minV)
        dtemp = pd.DataFrame(model)
        dtemp[bankfull_name] = round(dtemp.BankFull,2)
        dtemp[left_name] = round(dtemp.LeftDistance,2)
        dtemp[right_name] = round(dtemp.RightDistance,2)
        dtemp.to_csv(csv_name, index = False)
        dtemp = dtemp.drop(columns=['BankFull','LeftDistance','RightDistance','runs','spar','nChannels'])
        #group datasets/runs together
        if k == 1 :
            results = dtemp
        else:
            results = results.join( dtemp.set_index('CrossSection') , on='CrossSection')
    results = results.astype({"CrossSection": int }).reset_index()
    return results
##end HydXS_run


# single run of Bankfull calculation, over single/multiple XS------------------------------------------------------------------
# can be run stand-alone 
# used in "HydXS_run" function above
# this code tries "maxrun" number of times to get a BankFull calc that doesn't hit the left or right boundaries
# INPUT : full dataframe from pre-processing step 
# OUTPUT : dataframe for all XSs in the single run, one row per XS
#    CrossSection / BankFull / LeftDistance / RightDistance / nChannels / spar / runs
def HydXS_perXS ( full_dataset , a,b, allow_boundary = False, maxrun = 3, steps=200, minV=0.1, plot=False ):
    output = pd.DataFrame()
    for i in range(a,b+1):
        print(i)
        subset = full_dataset[(full_dataset["x_sec_id"] == i) & (full_dataset["inXS"] == True)].reset_index()
        if len(subset) == 0 :
            pass
        else:
            dtemp = list(subset.PointDZ)
            runs = 0
            if allow_boundary :
                try:
                    var1, var2, var3, var4, var5, fig, spar= HydXS( dtemp, nVsteps=steps, minVdep=minV, create_plot=plot)
                except Exception as e:
                    import pdb; pdb.set_trace()
                    var1, var2, var3, var4, var5, fig, spar = None, None, None, None, None, "-" ,None                     
            else:
                var1 = min(subset["Distance"])
                var2 = max(subset["Distance"])
                while ( ( var1 == min(subset["Distance"]) ) or ( var2 == max(subset["Distance"]) ) ) and runs < maxrun:
                    runs = runs + 1
                    try:
                        var1, var2, var3, var4, var5, fig, spar  = HydXS(dtemp, nVsteps=steps, minVdep=minV, create_plot=plot) 
                    except Exception as e:
                        import pdb; pdb.set_trace()
                        var1, var2, var3, var4, var5, fig, spar = var1, var2, None, None, None, "-" ,None  
                if runs == maxrun and ( ( var1 == min(subset["Distance"]) ) or ( var2 == max(subset["Distance"]) ) ):
                    runs = 99  #set for output trigger
            output = HydXS_output( output , i , var1, var2, var3, var4, var5, fig, spar ,runs )                
    if len(output) == 0 :
        pass
    else:
        output = output.astype({"CrossSection": int })    
        output = output.astype({"runs": int })    
    return output
#end HydXS_perXS


# pull together the output for a single run of Bankfull calc-------------------------------------------------------------------
# used in "HydXS_perXS" function above
# OUTPUT : dataframe for single XS, one row only 
#    CrossSection / BankFull / LeftDistance / RightDistance / nChannels / spar / runs
def HydXS_output ( output , i , var1, var2, var3, var4, var5, fig, spar, runs ):
    output.loc[i,"CrossSection"] = i
    if var4 == None or runs == 99:
        #bankfull still hits boundaries or no output
        output.loc[i,"BankFull"] = None
        output.loc[i,"LeftDistance"] = None
        output.loc[i,"RightDistance"] = None   
        output.loc[i,"nChannels"] = None 
    else:
        output.loc[i,"CrossSection"] = i
        output.loc[i,"BankFull"] = var4
        output.loc[i,"LeftDistance"] = var1
        output.loc[i,"RightDistance"] = var2 
        output.loc[i,"nChannels"] = var5 
    #common output
    output.loc[i,"spar"] = spar
    output.loc[i,"runs"] = runs
    return output
#end HydXS_output


