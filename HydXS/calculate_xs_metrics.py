
from riv_extract.d04_model_evaluation.utils.metrics import dice_coefficient_1d, jaccard_coefficient_1d
import pandas as pd

def prepare_xs_data(modelled, results):
	res_xs = pd.read_csv(modelled.run_folder/'calculated_results.csv')
	res_xs.rename(columns={'CrossSection':'x_sec_id'}, inplace=True)
	def find_right(x, results=results):
		res = results[(results['x_sec_id']==x) & (results['ground_truth']==True)]
		return res['Distance'].max()

	def find_left(x, results=results):
		res = results[(results['x_sec_id']==x) & (results['ground_truth']==True)]
		return res['Distance'].min()

	def find_bf_h(x, results=results):
		res = results[(results['x_sec_id']==x) & (results['ground_truth']==True)]
		return res['POINT_Z'].max()
	def find_bf_pred_h(x, results=results):
		res = results[(results['x_sec_id']==x) & (results['InRiver']==True)]
		return res['POINT_Z'].max()

	def find_point_Dice(x, results=results):
		res = results[(results['x_sec_id']==x)]
		tp = (res['prediction_result'] == 'TP').sum()
		fp = (res['prediction_result'] == 'FP').sum()
		fn = (res['prediction_result'] == 'FN').sum()
		return 2*tp/(2*tp+fp+fn)
	
	def find_point_jaccard(x, results=results):
		res = results[(results['x_sec_id']==x)]
		tp = (res['prediction_result'] == 'TP').sum()
		fp = (res['prediction_result'] == 'FP').sum()
		fn = (res['prediction_result'] == 'FN').sum()
		return tp/(tp+fp+fn)

	res_xs['gt_left'] = res_xs['x_sec_id'].apply(find_left)
	res_xs['gt_right'] = res_xs['x_sec_id'].apply(find_right)
	res_xs['bf_elev'] = res_xs['x_sec_id'].apply(find_bf_h)
	res_xs['bf_elev_pred'] = res_xs['x_sec_id'].apply(find_bf_pred_h)
	res_xs['point_dice'] = res_xs['x_sec_id'].apply(find_point_Dice)
	res_xs['point_jaccard'] = res_xs['x_sec_id'].apply(find_point_jaccard)


	left_cols = [x for x in res_xs.columns if 'left_' in x]
	right_cols = [x for x in res_xs.columns if 'right_' in x]

	res_xs['right_min'] =  res_xs[right_cols].min(axis=1)
	res_xs['right_max'] =  res_xs[right_cols].max(axis=1)

	res_xs['left_min'] =  res_xs[left_cols].min(axis=1)
	res_xs['left_max'] =  res_xs[left_cols].max(axis=1)
	run_func_dice = lambda x: dice_coefficient_1d(x['RightOutput'], x['LeftOutput'], x['gt_right'], x['gt_left'])
	jaccard_func = lambda x: jaccard_coefficient_1d(x['RightOutput'], x['LeftOutput'], x['gt_right'], x['gt_left'])
	res_xs['dice_1d'] = res_xs.apply(run_func_dice, axis=1)
	res_xs['jaccard_1d'] = res_xs.apply(jaccard_func, axis=1)
	return res_xs