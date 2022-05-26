###############################################################################################################################
#
# created by Russell-MDAP team March-September 2021
# deRosa_output.py
#
# bring together the outputs from deRosa_modelling.py
# single function: calcoutputs
#
# INPUT: the dataframe from deRosa_modelling.py : one row per XS, Bankfull/Left/Right for each calc run
#        Bankfull calc run across a set of XS for num_runs times
# DOES: accounts for variability of BankFull due to randomised spar in spline_with R
#       attempts to find mode of BankFull / sets "BankFullType" = mode
#       count how many runs give BankFull within "window" (default 5cm) of mode = "CountatBankFull"
#       if this is less than 2/3rd (this can be altered below) of the total number of runs (ie. for 11 runs, if less than 7)
#          then 3 bins are used to find a 'result' BankFull ; BankFullType" = binned
#       the left and right bank distance are then calculated
# OUTPUT: dataframe = input + BankFullType + BankFullOutput + CountatBankFull + LeftOutput + RightOutput
# currently overwrites INPUT
#
# this data is intended to be examined by users, to understand variability of results
# ie. the more variable the BankFull calc between runs, the more likely it is to require manual intervention of expert
#
# example: XSdata3_out = calcoutputs( XSdata3 , nruns )
#
###############################################################################################################################


# importing libraries etc  ----------------------------------------------------------------------------------------------------
import statistics
import pandas as pd
import numpy as np
from scipy import stats
import math


# bring together results for num_run calc runs ---------------------------------------------------------------------------------
def calcoutputs (dataset , num_runs , window=0.05 ):
    
    for i in range(0,len(dataset)):
        
        #column for each run output
        for j in range ( 1 , num_runs+1 ):
            bankvar = "bankfull_" + str(j)
            leftvar = "left_" + str(j)
            rightvar = "right_" + str(j)
            var1 = dataset.loc[i,bankvar]
            var2 = dataset.loc[i,leftvar]
            var3 = dataset.loc[i,rightvar]
            if j == 1 :
                group_bank = [var1]
                group_left = [var2]
                group_right = [var3]
            else:
                group_bank.append(var1)
                group_left.append(var2)            
                group_right.append(var3)
        
        #exclude XS with no results
        if math.isnan(statistics.mean(group_bank)) :
            dataset.loc[i,"CountatBankFull"] = 0
        
        else:
            #initially set to mode of bankfull calcs
            bank_mode =  statistics.mode(group_bank)
            dataset.loc[i,"BankFullType"] = "mode"
            dataset.loc[i,"BankFullOutput"] = bank_mode
            dataset.loc[i,"CountatBankFull"] = sum(map(lambda x : bank_mode-window <= x <= bank_mode+window , group_bank))

            #the mode of bankfull doesn't always line up with mode of banks edges
            # dataset.loc[i,"LeftOutput"] = statistics.mode(group_left)
            # dataset.loc[i,"RightOutput"] = statistics.mode(group_right)
            done = False
            k = 0
            while done == False:
                if group_bank[k] == bank_mode:
                    done = True
                    dataset.loc[i,"LeftOutput"] = group_left[k]
                    dataset.loc[i,"RightOutput"] = group_right[k]
                else:
                    k = k+1

            ##if there is a split in possible bankfull calcs - if less than 2/3rds of calcs are approx. mode
            if dataset.loc[i,"CountatBankFull"] < num_runs * 2/3 :
                dataset.loc[i,"BankFullType"] = "binned"

                #Bankfull 
                bin_means, bin_edges, binnum = stats.binned_statistic(group_bank, group_bank, statistic='mean', bins=3)   
                maxbin = max ( (binnum == 1).sum(), (binnum == 2).sum(), (binnum == 3).sum() )  
                # this ordering will mean that if there are equal numbers for any bins, the lowest bankfull will be chosen
                # which is likely to be one with less smoothing
                if maxbin == (binnum == 1).sum():
                    thebin = 1
                elif maxbin == (binnum == 2).sum():
                    thebin = 2
                elif maxbin == (binnum == 3).sum():
                    thebin = 3
                bank_by_bin = round(bin_means[thebin-1],2)
                dataset.loc[i,"BankFullOutput"] = bank_by_bin

                #now for the left and right bank limits 
                done = False
                k = 0
                while done == False and k < num_runs:
                    if group_bank[k] == bank_by_bin:
                        done = True
                        dataset.loc[i,"LeftOutput"] = group_left[k]
                        dataset.loc[i,"RightOutput"] = group_right[k]
                    else:
                        k = k+1
                #if needs interpolation
                if k == num_runs :
                    templ = []
                    for m in range(0,len(binnum)):
                        if binnum[m] == thebin:
                            if templ==[] :
                                templ = [group_left[m]]
                                tempr = [group_right[m]]
                            else:
                                templ.append(group_left[m])
                                tempr.append(group_right[m])
                    dataset.loc[i,"LeftOutput"] = statistics.mean(templ)
                    dataset.loc[i,"RightOutput"] = statistics.mean(tempr)

    dataset = dataset.astype({"CountatBankFull": int })
    return dataset

#end calcoutputs
