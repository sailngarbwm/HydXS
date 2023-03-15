import typer
from pathlib import Path
from typing import Optional, Union, Tuple
from HydXS.run_HydXS import run_hydxs


app = typer.Typer()

import HydXS

def version_callback(value: bool):
    if value:
        version = HydXS.__version__
        typer.echo(version)
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True
    ),
):
    """This tool is used to automatically identify bankfull boundaries from river cross sections"""
    pass

@app.command()
def run(
    point_df: Path, 
    input_type: str = 'DF',
    xy_col: Tuple[str, str] = ('POINT_X','POINT_Y'),
    z_col: str = 'POINT_Z',
    xs_id_col: str = 'x_sec_id',
    xs_order_col: str = 'x_sec_order',
    riv_centre: str = 'CurCentre'  ,       #CHANGE: to the name of the variable in your dataset that identifies the x_sec_id that is the centre line ; see additional note above
    #02: pre-processing
    exclude: Tuple[int,int] = (239,648)    ,          #CHANGE : identifiers of x_sec_id to be excluded due to anomalies etc; may be empty
    first: int = 1               ,         #KEEP / CHANGE : HydXS default is 1 ; may change if you're testing a small subset
    last: int = 648            ,           #CHANGE : to maximum number of x_sec_id in your dataset ; or if you're running a test on a smaller subset
    window: int = 10            ,          #KEEP / CHANGE : HydXS default is 10 ; number of points either side of centre line to look for min depth
    centre: str = 'RivCentre'    ,          
    #03: modelling
    nVsteps: int = 200           ,         #KEEP / CHANGE : deRosa originally had this at 100; HydXS default is 200 due to complexity of riverbanks the work was based on
    minVdep: float = 0.2          ,          #KEEP / CHANGE : deRosa originally had this at 1.0; HydXS default is 0.2 due to the nature of the riverbanks the work was based on
    maxr: int = 3               ,          #KEEP / CHANGE : HydXS default is 3 ; how many times HydXS tries to get a result that doesn't hit boundary ; the higher the number, the longer the running
    nruns: int = 11             ,          #KEEP / CHANGE : HydXS default is 11; make an odd number of runs, so mode is possible (if even, and split, then mode cannot be calc'd)
    out_data_path: Path = "model_outputs/test01/"   #CHANGE : where output CSV are saved
    ):
    out = run_hydxs(
        point_df,
        input_type,
        xy_col ,
        z_col,
        xs_id_col ,
        xs_order_col ,
        riv_centre,       #CHANGE: to the name of the variable in your dataset that identifies the x_sec_id that is the centre line ; see additional note above
        #02: pre-processing
        exclude ,          #CHANGE : identifiers of x_sec_id to be excluded due to anomalies etc; may be empty
        first ,         #KEEP / CHANGE : HydXS default is 1 ; may change if you're testing a small subset
        last ,           #CHANGE : to maximum number of x_sec_id in your dataset ; or if you're running a test on a smaller subset
        window  ,          #KEEP / CHANGE : HydXS default is 10 ; number of points either side of centre line to look for min depth
        centre ,          
        #03: modelling
        nVsteps  ,         #KEEP / CHANGE : deRosa originally had this at 100; HydXS default is 200 due to complexity of riverbanks the work was based on
        minVdep ,          #KEEP / CHANGE : deRosa originally had this at 1.0; HydXS default is 0.2 due to the nature of the riverbanks the work was based on
        maxr  ,          #KEEP / CHANGE : HydXS default is 3 ; how many times HydXS tries to get a result that doesn't hit boundary ; the higher the number, the longer the running
        nruns  ,          #KEEP / CHANGE : HydXS default is 11; make an odd number of runs, so mode is possible (if even, and split, then mode cannot be calc'd)
        out_data_path   #CHANGE : where output CSV are saved
        )
    
    out.to_csv(out_data_path/'final_results.csv')


if __name__ == '__main__':
    app()