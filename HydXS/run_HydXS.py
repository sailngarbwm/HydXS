###############################################################################################################################
#
# created by Russell-MDAP team March-September 2021
#
# Russell-MDAP amended deRosa code -> HydXS
#
# input: XSdata = cross section data
#      : requires the following column names: x_sec_id , POINT_X , POINT_Y , POINT_Z , x_sec_order 
#      : requires a centreline, 0 for all rows but the centre line row
#        this variable name can be anything and is specified in function call (in this example code is "RivCentre")
#        BUT if data doesn't not have centre line, set dR_cutoff=False, and the cross-section is passed through untrimmed (and dR_centre and dR_window are not used)
#
###############################################################################################################################

## imports ---------------------------------------------------------------------------------------------------------
from __future__ import annotations
from typing import Union, Tuple, List

import geopandas
import pandas

from .wrangle_cross_section import *
from .xs_preprocessor import *
from .HydXS_modelling import *
from .HydXS_output import *
from .HydXS_attachModelResults import *
from pathlib import Path

## parameters ------------------------------------------------------------------------------------------------------
#01: data input

## run HydXS ------------------------------------------------------------------------------------------------------

#01: wrangling
#XSdata1 = wrangle_cross_section(XSdata)

def run_hydxs(
    point_df: geopandas.GeoDataFrame | pandas.DataFrame | str | Path,
    input_type:str = 'DF',
    xy_col: tuple[str, str]= ('POINT_X','POINT_Y'),
    z_col: str = 'POINT_Z',
    xs_id_col: str = 'x_sec_id',
    xs_order_col: str = 'x_sec_order',
    riv_centre: str = 'RivCentre'  ,       #CHANGE: to the name of the variable in your dataset that identifies the x_sec_id that is the centre line ; see additional note above
    #02: pre-processing
    exclude: list[int] = (239,648)    ,          #CHANGE : identifiers of x_sec_id to be excluded due to anomalies etc; may be empty
    first: int = 1               ,         #KEEP / CHANGE : HydXS default is 1 ; may change if you're testing a small subset
    last: int = 648            ,           #CHANGE : to maximum number of x_sec_id in your dataset ; or if you're running a test on a smaller subset
    window: int = 10            ,          #KEEP / CHANGE : HydXS default is 10 ; number of points either side of centre line to look for min depth
    centre: str = 'RivCentre'    ,          
    #03: modelling
    nVsteps: int = 200           ,         #KEEP / CHANGE : deRosa originally had this at 100; HydXS default is 200 due to complexity of riverbanks the work was based on
    minVdep = 0.2          ,          #KEEP / CHANGE : deRosa originally had this at 1.0; HydXS default is 0.2 due to the nature of the riverbanks the work was based on
    maxr: int= 3               ,          #KEEP / CHANGE : HydXS default is 3 ; how many times HydXS tries to get a result that doesn't hit boundary ; the higher the number, the longer the running
    nruns: int = 11             ,          #KEEP / CHANGE : HydXS default is 11; make an odd number of runs, so mode is possible (if even, and split, then mode cannot be calc'd)
    out_data_path: str | Path = "model_outputs/test01/"   #CHANGE : where output CSV are saved
    ):

    if isinstance(point_df, (str, Path)) == True:
        point_df = pd.read_csv(point_df)

    if isinstance(out_data_path, (str)):
        out_data_path = Path(out_data_path)
        out_data_path.mkdir(exist_ok=True, parents=True)
        
    XSdata1 = wrangle_cross_section( point_df=point_df , input_type=input_type , xy_col=xy_col , z_col=z_col , xs_id_col=xs_id_col , xs_order_col=xs_order_col , riv_centre=riv_centre )

    #02: pre-processing
    XSdata2 = preprocess_cross_section( XSdata1 , dR_first=first , dR_last=last , dR_cutoff=True , dR_centre=centre , dR_window=window , dR_excl=exclude )

    #03: model runs 
    XSdata3 = HydXS_run( XSdata2, first,last, num_runs=nruns, output_path=out_data_path, maxrun=maxr, steps=nVsteps, minV=minVdep )

    #04: model output 
    XSdata4 = calcoutputs( XSdata3 , nruns )

    #05: attach to original XS dataset 
    XSdata5 = attach_HydXS( XSdata2, XSdata4 )
    return XSdata5

## end -------------------------------------------------------------------------------------------------------------
