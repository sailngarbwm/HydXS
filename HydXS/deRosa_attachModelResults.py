###############################################################################################################################
#
# created by Russell-MDAP team March-September 2021
# deRosa_attachModelResults.py
#
# attaches the derived results from deRosa_output.py to the whole original XS dataset, for purposes of comparison to 'truth'
# single function: attach_deRosa
#
# INPUT: XS dataset from pre_processing + dataframe from deRosa_output.py (BankFull + BankLeft + BankRight + CountBankFull)
# DOES: uses output from runs, and determines if each datapoint is under/above Bankfull (inRiver = True/False)
# OUTPUT: dataframe = pre-processed XS data + InRiver + BankFull + BankLeft + BankRight + CountBankFull
#       where inRiver = True / False ; using Distance and BankLeft and BankRight
#
# example: XSdata4 = attach_deRosa( XSdata2, XSdata3_out )
#
###############################################################################################################################


import pandas as pd
from riv_extract.d04_model_evaluation.utils.apply_results import get_pred_results


def prepare_deRosa_points(results):
	# results = pd.read_csv(model_eval.run_folder/'results_with_cross_secton_data.csv')
	results['ground_truth'] = results['ground_truth'] ==1
	results['prediction_result'] = results.apply(get_pred_results,axis=1)
	out =  results[['index', 'x_sec_id', 'seg_id', 'POINT_X',
       'POINT_Y', 'POINT_Z', 'Sort_Value','CurCentre',
       'NewCentre','category', 'ground_truth', 'PointXY',
       'Distance', 'PointDZ', 'inXS', 'InRiver', 'BankFull',
       'BankLeft', 'BankRight', 'CountAtBankFull','prediction_result']]
	return out

def attach_deRosa ( xs , results  ) :
    
    for i in range(1,max(xs["x_sec_id"])+1):
        print(i)
        subset = xs[xs["x_sec_id"] == i].reset_index()
        
        #initialise
        left = None
        right = None
        bankfull = None
        count = None
        #from deRosa results
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
    output = prepare_deRosa_points(output)
    return output

#end attach_deRosa