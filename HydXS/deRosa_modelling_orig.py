###############################################################################################################################
#
# created by Russell-MDAP team March-September 2021
# deRosa_modelling_orig.py
#
# mirrors deRosa_modelling.py / but is using original deRosa code - for testing
#
###############################################################################################################################
#
## refer to deRosa_modelling.py for code explanation and documentation
## the only difference here is the use of deRosa.BankFullDetection_orig
## and changing the deRosa call 
#
###############################################################################################################################


import pandas as pd
import numpy as np

from riv_extract.d03_modelling.deRosa.BankFullDetection_orig import mainFun as deRosa
#mainFun(pointList,nVsteps=100,minVdep=1,Graph=0):
#return boundsOK[0],boundsOK[2],wetArea.bounds[1], wetArea.bounds[3], nchannel 


def deRosa_perXS ( full_dataset , a,b, allow_boundary = False, maxrun = 3, steps=200, minV=0.1, plot=False ):
    output = pd.DataFrame()
    for i in range(a,b+1):
        print(i)
        subset = full_dataset[(full_dataset["x_sec_id"] == i) & (full_dataset["inXS"] == True)].reset_index()
        if len(subset) == 0 :
            pass
        else:
            dtemp = list(subset.PointDZ)
            #for original run only - as original deRosa doesn't have the same output as amended
            fig = "-"
            spar = 99.999
            runs=0
            #end
            if allow_boundary :
                try:
                    var1, var2, var3, var4, var5 = deRosa( dtemp, nVsteps=steps, minVdep=minV ) 
                except:
                    var1, var2, var3, var4, var5 = None, None, None, None, None                  
            else:
                var1 = min(subset["Distance"])
                var2 = max(subset["Distance"])
                while ( ( var1 == min(subset["Distance"]) ) or ( var2 == max(subset["Distance"]) ) ) and runs < maxrun:
                    runs = runs + 1
                    try:
                        var1, var2, var3, var4, var5, fig, spar = deRosa( dtemp, nVsteps=steps, minVdep=minV ) 
                    except:
                        var1, var2, var3, var4, var5, fig, spar = var1, var2, None, None, None  
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


def deRosa_run ( data , a,b, num_runs , output_path , boundary=False, maxrun=3, steps=200, minV=0.1 ):
    for k in range ( 1 , num_runs+1 ):
        print("run: " , k)
        #variable names
        run_name = "run_" + str(k)
        csv_name = output_path + "deRosa_run" + str(k) + ".csv"
        bankfull_name = "bankfull_" + str(k)
        left_name = "left_" + str(k)
        right_name = "right_" + str(k)
        #individual run
        model = deRosa_perXS(data,a,b,allow_boundary=boundary,maxrun=maxrun,steps=steps,minV=minV)
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
##end deRosa_run