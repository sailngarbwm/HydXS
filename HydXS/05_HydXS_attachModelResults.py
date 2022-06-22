###############################################################################################################################
#
# created by Russell-MDAP team March-September 2021
# 05_HydXS_attachModelResults.py
#
# attaches the derived results from HydXS_output.py to the whole original XS dataset
# single function: attach_HydXS
#
# INPUT: XS dataset from pre_processing + dataframe from HydXS_output.py (BankFull + BankLeft + BankRight + CountBankFull)
# DOES: uses output from runs, and determines if each datapoint is under/above Bankfull (inRiver = True/False)
# OUTPUT: dataframe = pre-processed XS data + InRiver + BankFull + BankLeft + BankRight + CountBankFull
#       where inRiver = True / False ; using Distance and BankLeft and BankRight
#
# example: XSdata4 = attach_HydXS( XSdata2, XSdata3_out )
#
###############################################################################################################################

import pandas as pd

def attach_HydXS ( xs , results  ) :
    
    for i in range(1,max(xs["x_sec_id"])+1):
        print(i)
        subset = xs[xs["x_sec_id"] == i].reset_index()
        
        #initialise
        left = None
        right = None
        bankfull = None
        count = None
        #from HydXS results
        if not len(results[results["CrossSection"]==i])==0 :
            left = float(results["LeftOutput"][results["CrossSection"]==i])
            right = float(results["RightOutput"][results["CrossSection"]==i])
            bankfull = float(results["BankFullOutput"][results["CrossSection"]==i])
            count = int(results["CountatBankFull"][results["CrossSection"]==i])

        #initialise
        subset["InRiver"] = False
        subset["BankFull"] = bankfull 
        subset["BankLeft"] = left 
        subset["BankRight"] = right 
        subset["CountAtBankFull"] = count
        #set true if between left and right boundaries
        for j in range(0,len(subset)):
            if not (left==None or right==None): 
                if subset.loc[j,"Distance"] > left and subset.loc[j,"Distance"] < right:
                    subset.loc[j,"InRiver"] = True
            else:
                subset["CountAtBankFull"] = 0
                
        if i == 1 :
            output = subset
        else:
            output = output.append(subset,ignore_index=True)
    return output

#end attach_HydXS