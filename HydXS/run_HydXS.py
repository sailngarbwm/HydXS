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
# 01: data input

## run HydXS ------------------------------------------------------------------------------------------------------

# 01: wrangling
# XSdata1 = wrangle_cross_section(XSdata)
# CHANGE: to the name of the variable in your dataset that identifies the x_sec_id that is the centre line ; see additional note above
# CHANGE : identifiers of x_sec_id to be excluded due to anomalies etc; may be empty

# KEEP / CHANGE : HydXS default is 1 ; may change if you're testing a small subset

# CHANGE : to maximum number of x_sec_id in your dataset ; or if you're running a test on a smaller subset

# KEEP / CHANGE : HydXS default is 10 ; number of points either side of centre line to look for min depth

# KEEP / CHANGE : deRosa originally had this at 100; HydXS default is 200 due to complexity of riverbanks the work was based on

# KEEP / CHANGE : deRosa originally had this at 1.0; HydXS default is 0.2 due to the nature of the riverbanks the work was based on

# KEEP / CHANGE : HydXS default is 3 ; how many times HydXS tries to get a result that doesn't hit boundary ; the higher the number, the longer the running

# KEEP / CHANGE : HydXS default is 11; make an odd number of runs, so mode is possible (if even, and split, then mode cannot be calc'd)

# CHANGE : where output CSV are saved


def run_hydxs(
    point_df: geopandas.GeoDataFrame | pandas.DataFrame,
    input_type: str = "DF",
    xy_col: tuple[str, str] = ("POINT_X", "POINT_Y"),
    z_col: str = "POINT_Z",
    xs_id_col: str = "x_sec_id",
    xs_order_col: str = "x_sec_order",
    riv_centre: str = "RivCentre",
    # 02: pre-processing
    exclude: list[int] = (),
    first: int = 1,
    last: int = 648,
    window: int = 10,
    # 03: modelling
    nVsteps: int = 200,
    minVdep=0.2,
    maxr: int = 3,
    nruns: int = 11,
    out_data_path: str | Path = "model_outputs/test01/",
) -> pd.DataFrame:
    """Main function to run the entire pipeline on a set of cross section point data.

    Args:
        point_df (geopandas.GeoDataFrame | pandas.DataFrame): input dataframe or GeoDataFrame with points along cross sections
        input_type (str, optional): type of Dataframe, "DF" if Dataframe, "GDF" if GeoDataFrame. Defaults to "DF".
        xy_col (tuple[str, str], optional): tuple of x and y column names. Defaults to ("POINT_X", "POINT_Y").
        z_col (str, optional): name of column that holds elevation data for each point. Defaults to "POINT_Z".
        xs_id_col (str, optional): Name of column that holds an integer cross section ID. Defaults to "x_sec_id".
        xs_order_col (str, optional): Name of column that holds the position of that point in the order of the cross section. Defaults to "x_sec_order".
        riv_centre (str, optional): name of Boolean column, where the point closest to the centre of the river is True. Defaults to "RivCentre".
        exclude (list[int], optional): list of cross section ID's to skip. Defaults to ().
        first (int, optional): First cross section ID to run. Defaults to 1.
        last (int, optional): Last cross section ID to run. Defaults to 648.
        window (int, optional): Window in map units to cut out from other minimums far away from . Defaults to 10.
        nVsteps (int, optional): Number of vertical steps to iterate over starting at minVdep. Defaults to 200.
        minVdep (float, optional): Minimum height above river centre (the thalweg) where the first hydraulic depth is measured. Defaults to 0.2.
        maxr (int, optional): Maximum number of sub runs for each cross section per run. Defaults to 3.
        nruns (int, optional): Number of runs over entire set of cross sections. Defaults to 11.
        out_data_path (str | Path, optional): data path where intermediate outputs are stored. Defaults to "model_outputs/test01/".

    Returns:
        pandas.DataFrame: output aggregate dataframe, it will have a value for each point, though some of them are cross section aggregated values.

            Note that it aggregates all 11 runs, and only shows either the mode (most often bankfull value arrived at) or the mean
            Output columns:
                x_sec_id - Cross section id
                x_sec_order - Order of point in the cross section
                POINT_X - x coordinate
                POINT_Y - y coordinate
                POINT_Z - z coordinate
                PointXY - XY shapely point
                Distance - Distance along cross section at that point
                PointDZ - Shapely point of (Distance, Z)
                RivCentre - True fals as whether at the centre of the river
                riverMin - Minimum elevation in the river
                inXS - True if point is in the Bankfull Cross section (includes point next to bankfull)
                InRiver - True if point is in the river (doesn't include bankfull point)
                BankFull - Bankfull width
                BankLeft - Distance along cross section where first non river point is on left
                BankRight - Distance along cross section where first non river point is on right
                CountAtBankFull - Number of runs that produces this bankfull measurement (only usefull for Mode outputs)

    """
    if isinstance(point_df, (str, Path)) == True:
        point_df = pd.read_csv(point_df)

    if isinstance(out_data_path, (str)):
        out_data_path = Path(out_data_path)
        out_data_path.mkdir(exist_ok=True, parents=True)

    XSdata1 = wrangle_cross_section(
        point_df=point_df,
        input_type=input_type,
        xy_col=xy_col,
        z_col=z_col,
        xs_id_col=xs_id_col,
        xs_order_col=xs_order_col,
        riv_centre=riv_centre,
    )

    # 02: pre-processing
    XSdata2 = preprocess_cross_section(
        XSdata1,
        dR_first=first,
        dR_last=last,
        dR_cutoff=True,
        dR_centre=riv_centre,
        dR_window=window,
        dR_excl=exclude,
    )

    # 03: model runs
    XSdata3 = HydXS_run(
        XSdata2,
        first,
        last,
        num_runs=nruns,
        output_path=out_data_path,
        maxrun=maxr,
        steps=nVsteps,
        minV=minVdep,
    )

    # 04: model output
    XSdata4 = calcoutputs(XSdata3, nruns)

    # 05: attach to original XS dataset
    XSdata5 = attach_HydXS(XSdata2, XSdata4)
    return XSdata5


## end -------------------------------------------------------------------------------------------------------------
