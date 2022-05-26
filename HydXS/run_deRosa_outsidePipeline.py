###############################################################################################################################
#
# created by Russell-MDAP team March-September 2021
#
# uses Russell-MDAP ameneded deRosa code
#
# input: XS = cross section data
#      : requires the following column names: x_sec_id , POINT_X , POINT_Y , POINT_Z , Sort_Value 
#      : requires a centreline, 0 (was BLANK in original dataset) for all rows but the centre line row
#        this variable name can be anything and is specified in function call (here is "CurCentre")
#        BUT if data doesn't not have centre line, set dR_cutoff=False, and the cross-section is passed through untrimmed
#          (and dR_centre and dR_window are not used)
#
###############################################################################################################################

## imports ---------------------------------------------------------------------------------------------------------
from riv_extract.d01_wrangling.cross_section.wrangle_cross_section import *
from riv_extract.d02_preprocessing.cross_section.xs_preprocessor import *
from riv_extract.d03_modelling.deRosa.deRosa_modelling import *
from riv_extract.d03_modelling.deRosa.deRosa_output import *
from riv_extract.d04_model_evaluation.deRosa.deRosa_attachModelResults import *


## parameters ------------------------------------------------------------------------------------------------------
#02: pre-processing
exclude = (239,242,374,647,648)
first = 1 
last = 648
window = 10        #number of points either side of centre line to look for min depth
centre = "CurCentre"
#03: model run
nVsteps = 200
minVdep = 0.2
maxr = 3         #how many times deRosa tries to get a result that doesn't hit boundary
nruns = 11       #make an odd number of runs, so mode is possible (if even, and split, then mode cannot be calc'd)
path = "notebooks/karen/model_outputs/test10/"   #where output CSV are saved


## run deRosa ------------------------------------------------------------------------------------------------------

#01: wrangling
XSdata1 = wrangle_cross_section()

#02: pre-processing
XSdata2 = preprocess_cross_section( XSdata1 , model="deRosa" , dR_first = first , dR_last = last ,
                                   dR_cutoff=True , dR_centre = centre , dR_window = window , dR_excl = exclude )

#03: model runs 
XSdata3 = deRosa_run( XSdata2, first,last, num_runs=nruns, output_path=path, maxrun=maxr, steps=nVsteps, minV=minVdep )
XSdata3_out = calcoutputs( XSdata3 , nruns )

#04: attach to original XS dataset for comparison to ground truth
XSdata4 = attach_deRosa( XSdata2, XSdata3_out )



##single XS run ; comment out after checking runs okay
#deRosa1 = deRosa_perXS(XSdata2,641,641,maxrun=maxr,steps=nVsteps,minV=minVdep,plot=True)
#print(deRosa1)


##If want CSV of each datastep - manually change the output folder
#XSdata1.to_csv(r'notebooks/karen/model_outputs/test10/XSdata1.csv', index = False)
#XSdata2.to_csv(r'notebooks/karen/model_outputs/test10/XSdata2.csv', index = False)
#XSdata3_out.to_csv(r'notebooks/karen/model_outputs/test10/XSdata3.csv', index = False)
#XSdata4.to_csv(r'notebooks/karen/model_outputs/test10/XSdata4.csv', index = False)

## end -------------------------------------------------------------------------------------------------------------
