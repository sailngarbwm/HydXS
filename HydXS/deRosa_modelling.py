###############################################################################################################################
#
# created by Russell-MDAP team March-September 2021
# deRosa_modelling.py
#
# "deRosa_run" function used in step 3  
# INPUT: pre-processed XS dataframe from step 2 
# OUTPUT: 
#   dataframe and .csv PER run, with one row per XS 
#       CrossSection / BankFull / LeftDistance / RightDistance / nChannels / spar / runs
#   AND single .csv for ALL runs, with one row per XS and 3 columns per run (n)
#       CrossSection / BankFull(n) / LeftDistance(n) / RightDistance(n) 
# results are then combined and exported into csv using deRosa_output.py
# example, used in deRosa: 
#     nVsteps = 200
#     minVdep = 0.2
#     maxr = 3         
#     nruns = 11       #make an odd number of runs, so mode is possible (if even, and split, then mode cannot be calc'd)
#     XSdata3 = deRosa_run( XSdata2, first,last, num_runs=nruns, output_path=path, maxrun=maxr, steps=nVsteps, minV=minVdep )
#
# a single XS can be run once by using 
#   deRosa1 = deRosa_perXS(XSdata2,641,641,maxrun=maxr,steps=nVsteps,minV=minVdep,plot=True)
#   print(deRosa1) 
#  the output will be the printed values and a graph
#
###############################################################################################################################


# importing libraries etc  ----------------------------------------------------------------------------------------------------
import pandas as pd
import numpy as np
from pathlib import Path
# specific library name  -----------------------------------------------------------------------------------------------------
from riv_extract.d00_data.dataset import create_modelled_deRosa
from riv_extract.d03_modelling.deRosa.BankFullDetection_NEW import mainFun as deRosa_amended
from riv_extract.d03_modelling.deRosa.BankFullDetection_orig import mainFun as deRosa_orig
from riv_extract.d03_modelling.utils import save_config_files


# multiple runs of AMENDED Russell-MDAP deRosa Bankfull calculation , over single/multiple XSs---------------------------------
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
# results are then combined and exported into csv using deRosa_output.py
def deRosa_run ( data , a,b, num_runs , model_type = 'amended', output_path = None , boundary=False, maxrun=3, steps=200, minV=0.1 ):
    modelled = create_modelled_deRosa()
    if type(output_path) == type(None):
        output_path = modelled.run_folder  
    for k in range ( 1 , num_runs+1 ):
        print("run: " , k)
        #variable names
        run_name = "run_" + str(k)
        csv_name = output_path/("deRosa_run" + str(k) + ".csv")
        bankfull_name = "bankfull_" + str(k)
        left_name = "left_" + str(k)
        right_name = "right_" + str(k)
        #individual run
        model = deRosa_perXS(data,a,b,model_type, allow_boundary=boundary,maxrun=maxrun,steps=steps,minV=minV)
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
    # save the config files
    # save_config_files(modelled)
    return results
##end deRosa_run


# single run of Bankfull calculation, over single/multiple XS------------------------------------------------------------------
# can be run stand-alone 
# used in "deRosa_run" function above
# this code tries "maxrun" number of times to get a BankFull calc that doesn't hit the left or right boundaries
# INPUT : full dataframe from pre-processing step 
# OUTPUT : dataframe for all XSs in the single run, one row per XS
#    CrossSection / BankFull / LeftDistance / RightDistance / nChannels / spar / runs
def deRosa_perXS ( full_dataset , a,b, model_type, allow_boundary = False, maxrun = 3, steps=200, minV=0.1, plot=False ):

    if model_type == 'amended':
        print('running amended algorithm')
        deRosa = deRosa_amended
        import inspect
        print(inspect.getsource(deRosa))
    elif model_type == 'original':
        print('running original algorithm')
        deRosa = deRosa_orig
        import inspect
        print(inspect.getsource(deRosa))
    else:
        raise ValueError(f'{model_type} not an accepted model schema, please use "amended" or "original"')

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
                    if model_type == 'amended':
                        var1, var2, var3, var4, var5, fig, spar = deRosa( dtemp, nVsteps=steps, minVdep=minV, create_plot=plot) 
                    elif model_type == 'original':
                        var1, var2, var3, var4, var5= deRosa( dtemp, nVsteps=steps, minVdep=minV)
                        spar = None
                        fig = None
                except:
                    var1, var2, var3, var4, var5, fig, spar = None, None, None, None, None, "-" ,None                     
            else:
                var1 = min(subset["Distance"])
                var2 = max(subset["Distance"])
                while ( ( var1 == min(subset["Distance"]) ) or ( var2 == max(subset["Distance"]) ) ) and runs < maxrun:
                    runs = runs + 1
                    try:
                        if model_type == 'original':
                            raise ValueError('original methodology must allow boundary')
                        var1, var2, var3, var4, var5, fig, spar  = deRosa(dtemp, nVsteps=steps, minVdep=minV, create_plot=plot) 

                    except:
                        var1, var2, var3, var4, var5, fig, spar = var1, var2, None, None, None, "-" ,None  
                if runs == maxrun and ( ( var1 == min(subset["Distance"]) ) or ( var2 == max(subset["Distance"]) ) ):
                    runs = 99  #set for output trigger
            output = deRosa_output( output , i , var1, var2, var3, var4, var5, fig, spar ,runs )                
    if len(output) == 0 :
        pass
    else:
        output = output.astype({"CrossSection": int })    
        output = output.astype({"runs": int })    
    return output
#end deRosa_perXS


# pull together the output for a single run of Bankfull calc-------------------------------------------------------------------
# used in "deRosa_perXS" function above
# OUTPUT : dataframe for single XS, one row only 
#    CrossSection / BankFull / LeftDistance / RightDistance / nChannels / spar / runs
def deRosa_output ( output , i , var1, var2, var3, var4, var5, fig, spar, runs ):
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
#end deRosa_output


